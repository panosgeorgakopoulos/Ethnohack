"""Full-factorial benchmark of the nomination system. Writes results/benchmark.json.

Episode construction follows scripts/threshold_curve.py (confounded rotenoid pairs,
semi-synthetic responses from real abundances, 8 seed reveals, budget 3, pool 250),
and additionally (1) keeps easy episodes and flags them, so the hard episodes are
identical to threshold_curve's while the overall stratum is also reported, (2) simulates
a second response channel (L6 cytotoxicity) as in scripts/selectivity_test.py, and
(3) adds a same-batch pool variant.

Under test: the 4-hypothesis posterior (scripts/decision_model.py), gain fitted by
decouple.calibration.fit_gain, background 0.05, threshold 0.85, every nomination rule,
and every selection policy. Overrides live in this file; config/default.json is untouched.

Run: python3.12 scripts/benchmark.py   (from the repo root)
"""
import sys, os, json, math, random, itertools, time
import numpy as np
sys.path.insert(0, 'scripts'); sys.path.insert(0, '.')
import decision_model as H
from decouple.calibration import fit_gain
from decouple.selectivity import dual_posterior, selective_decision
from decouple.setvalued import set_decision
import decouple.model as DM
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures

BUDGET, HITS, POOL_N, BOOT = 3, 8, 250, 2000
THR, TOX_CAP, BACKGROUND = 0.85, 0.5, 0.05
SET_MASS = 0.95
SET_KINDS = ('nominate', 'shortlist', 'joint', 'cytotoxic', 'abstain')
SET_PROPOSING = ('nominate', 'shortlist', 'joint')   # verdicts that propose something to isolate
SMOKE = int(os.environ.get('SMOKE', '0'))  # >0: only first N pairs, for a quick test

comp = build_compounds('pos'); stru = load_structures()
rot = {k for k, v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c = [c for c, v in comp.items() if any(k in rot for k in v['isdb_keys'])]
samples = sorted({s for v in comp.values() for s in v['abundance']})
pairs = []
for a, b in itertools.combinations(rot_c, 2):
    Sa, Sb = set(comp[a]['abundance']), set(comp[b]['abundance'])
    if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa):
        pairs.append((a, b))

GAIN = fit_gain([v for c in rot_c for v in comp[c]['abundance'].values()])
CFG = dict(H.CFG, gain=GAIN, background=BACKGROUND, nomination_threshold=THR, tox_cap=TOX_CAP)
plate = lambda s: s.split('_')[0]


def gen_his(x_by, drivers, rng):
    idx = 0 if drivers == ('A',) else (1 if drivers == ('B',) else 2)
    return {s: float(H.means(x_by[s], CFG)[idx] + CFG['noise_sd'] * rng.gauss(0, 1)) for s in samples}


def gen_ours(x_by, drivers, rng):
    out = {}
    for s in samples:
        a, b = x_by[s]
        load = a if drivers == ('A',) else (b if drivers == ('B',) else 0.5 * (a + b))
        v = 0.0 if load <= 0 else 1.10 / (1.0 + math.exp(-((math.log10(load) - math.log10(0.02)) / 0.6)))
        out[s] = float(max(0.0, v + rng.gauss(0, 0.08)))
    return out


def build(generator, two_driver, seed):
    """Episode builder; easy episodes are kept and flagged."""
    eps, rng0 = [], random.Random(seed)
    sel_pairs = rng0.sample(pairs, len(pairs))
    if SMOKE:
        sel_pairs = sel_pairs[:SMOKE]
    for i, (A, B) in enumerate(sel_pairs):
        for sd in range(4):
            r = random.Random(H.seed_for(seed, i, sd))
            x_by = {s: (comp[A]['abundance'].get(s, 0.0), comp[B]['abundance'].get(s, 0.0)) for s in samples}
            out = generator(x_by, ('A', 'B') if two_driver else ('A',), r)
            known = sorted(samples, key=lambda s: -out[s])[:HITS]
            pa = tuple(x_by[s][0] >= 0.02 for s in known); pb = tuple(x_by[s][1] >= 0.02 for s in known)
            hard = pa == pb
            rest = [s for s in samples if s not in known]
            pool_u = r.sample(rest, min(POOL_N, len(rest)))
            plates = {plate(s) for s in known}
            sb = [s for s in rest if plate(s) in plates]
            pool_b = random.Random(H.seed_for(seed, i, sd, 'batch')).sample(sb, min(POOL_N, len(sb)))
            # cytotoxicity channel (selectivity_test.py design): A drives tox in half the episodes
            nonsel = (i + sd) % 2 == 0
            rt = random.Random(H.seed_for(seed, i, sd, 'tox'))
            tidx = 0 if nonsel else 3
            y_tox = {s: float(H.means(x_by[s], CFG)[tidx] + CFG['noise_sd'] * rt.gauss(0, 1)) for s in samples}
            eps.append(dict(id=f"e{i}_{sd}", k=len(eps), A=A, B=B, pair=(A, B), x=x_by, out=out, tox=y_tox,
                            known=known, pools={'unconstrained': pool_u, 'same_batch': pool_b},
                            truth='both' if two_driver else 'A', hard=hard, nonsel=nonsel))
    return eps


def posterior_picks(ep, pool, policy):
    smp = [{'id': s, 'x': list(ep['x'][s])} for s in ep['known'] + pool]
    choices = [{'id': s, 'x': list(ep['x'][s])} for s in pool]
    rev = {s: ep['out'][s] for s in ep['known']}; picks = []
    for step in range(BUDGET):
        sid = H.recommend(list(H.posterior_of(smp, rev, CFG)), choices, rev, policy, CFG, ep['id'], step)
        if sid is None:
            break
        rev[sid] = ep['out'][sid]; picks.append(sid)
    return picks


# 'strongest-first' and 'contrast-spread' pick from abundances (src.selection); 'decouple' and
# 'strongest-first-posterior' pick through the posterior model's recommender (decouple.policies).
POLICIES = ['no_budget', 'random', 'strongest-first', 'contrast-spread', 'adaptive_contrast',
            'decouple', 'strongest-first-posterior']


def picks_for(policy, ep, pool):
    cands = [ep['A'], ep['B']]
    if policy == 'no_budget':
        return []
    if policy == 'random':
        return random.Random(1000 + ep['k']).sample(pool, BUDGET)
    if policy == 'strongest-first':      # src.selection 'strongest': current practice
        return select('strongest', cands, set(ep['known']), pool, BUDGET, comp)
    if policy == 'contrast-spread':
        return select('contrast-spread', cands, set(ep['known']), pool, BUDGET, comp)
    if policy == 'adaptive_contrast':              # picks are assayed sequentially
        return select('adaptive_contrast', cands, set(ep['known']), pool, BUDGET, comp, activity=ep['out'],
                      rng=random.Random(1))
    if policy == 'decouple':
        return posterior_picks(ep, pool, 'decouple')
    if policy == 'strongest-first-posterior':
        return posterior_picks(ep, pool, 'strongest-first')
    raise ValueError(policy)


def judge(ep, pool, picks):
    """-> {rule: (nominated, named_truth, developable_correct)}"""
    rev = list(ep['known']) + list(picks)
    smp = [{'id': s, 'x': list(ep['x'][s])} for s in ep['known'] + pool]
    ry = {s: ep['out'][s] for s in rev}; rt = {s: ep['tox'][s] for s in rev}
    p_par, p_tox = dual_posterior(smp, ry, rt, CFG)
    res = {}
    d = H.decision(p_par, smp, ry, CFG)                       # potency-only (the decision rule)
    nom = d['kind'] == 'nominate'; named = nom and d['candidate'] == ep['truth']
    res['potency-only'] = (nom, named, named and not ep['nonsel'])
    d = selective_decision(p_par, p_tox, smp, ry, CFG)         # selectivity-aware
    nom = d['kind'] == 'nominate'; named = nom and d['candidate'] == ep['truth']
    res['selectivity-aware'] = (nom, named, named and not ep['nonsel'])
    # set-valued rule (additive): truth is 'A' (single driver) or 'both' (two drivers)
    sd = set_decision(p_par, p_tox, smp, ry, CFG, mass=SET_MASS, names=('A', 'B'))
    cand = list(sd['candidates']); na = sd['kind'] != 'abstain'          # cytotoxic is NOT an abstention
    pr = sd['kind'] in SET_PROPOSING; cy = sd['kind'] == 'cytotoxic'
    # cols: non_abstain, proposing, contained(proposing only), size(proposing only), 5 kind counts,
    #       cytotoxic verdicts, cytotoxic verdicts whose candidates[0] is the cytotoxic compound (A in this design)
    res['__set__'] = [int(na), int(pr), int(pr and ep['truth'] in cand), len(cand) if pr else 0] + \
        [int(sd['kind'] == k) for k in SET_KINDS] + [int(cy), int(cy and bool(cand) and cand[0] == 'A')]
    return res


def run(eps, tag):
    cells, overlap, t0 = {}, {}, time.time()
    set_cells = {}
    for n, ep in enumerate(eps):
        for pool_name, pool in ep['pools'].items():
            picks = {pol: picks_for(pol, ep, pool) for pol in POLICIES}
            for pol, pk in picks.items():
                jr = judge(ep, pool, pk)
                set_cells.setdefault((pool_name, pol), np.zeros((len(eps), 11), int))[n] = jr.pop('__set__')
                for rule, v in jr.items():
                    cells.setdefault((pool_name, pol, rule), np.zeros((len(eps), 3), int))[n] = v
            for pol in ('contrast-spread', 'adaptive_contrast', 'decouple'):
                overlap.setdefault((pool_name, pol), []).append(len(set(picks[pol]) & set(picks['strongest-first'])))
        if n % 100 == 0:
            print(f"  [{tag}] episode {n}/{len(eps)}  {time.time()-t0:.0f}s", flush=True)
    return cells, overlap, set_cells


# ---------------- statistics: pair-clustered bootstrap ----------------
def strata_masks(eps):
    hard = np.array([e['hard'] for e in eps])
    return {'easy': ~hard, 'hard': hard, 'overall': np.ones(len(eps), bool)}


def pair_sums(arr, mask, pair_ix):
    """per-pair sums of [N, nominated, named, developable] over episodes in mask; pairs with N>0 only."""
    P = pair_ix.max() + 1
    w = [np.bincount(pair_ix[mask], minlength=P).astype(float)]
    for j in range(3):
        w.append(np.bincount(pair_ix[mask], weights=arr[mask, j], minlength=P))
    w = np.array(w)
    return w[:, w[0] > 0]


def stat(S, kind, score):
    N, nom = S[0], S[1]; cor = S[2] if score == 'named' else S[3]
    with np.errstate(invalid='ignore', divide='ignore'):
        return {'coverage': nom / N, 'precision': cor / nom, 'accuracy': cor / N,
                'wasted_per_100': 100 * (nom - cor) / N}[kind]


def boot_idx(P, seed=7):
    return np.random.default_rng(seed + P).integers(0, P, size=(BOOT, P))


def ci(vals):
    v = np.asarray(vals)[np.isfinite(vals)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) > 50 else [None, None]


def cell_stats(S, score):
    idx = boot_idx(S.shape[1]); T = S.sum(1); out = {}
    boots = S[:, idx].sum(2)
    for k in ('coverage', 'precision', 'accuracy', 'wasted_per_100'):
        pt = float(stat(T, k, score)); out[k] = pt if np.isfinite(pt) else None
        out[k + '_ci95'] = ci(stat(boots, k, score))
    out['n_episodes'] = int(T[0]); out['n_distinct_pairs'] = int(S.shape[1])
    out['n_nominations'] = int(T[1]); out['n_correct'] = int(T[2] if score == 'named' else T[3])
    return out


def margin(S1, S2, score, kind='accuracy'):
    """cell1 - cell2 on aligned pairs (same episodes). Percentage points (wasted: per-100 units)."""
    idx = boot_idx(S1.shape[1]); scale = 1 if kind == 'wasted_per_100' else 100
    pt = scale * (stat(S1.sum(1), kind, score) - stat(S2.sum(1), kind, score))
    b = scale * (stat(S1[:, idx].sum(2), kind, score) - stat(S2[:, idx].sum(2), kind, score))
    return dict(point=float(pt), ci95=ci(b), n_distinct_pairs=int(S1.shape[1]), n_episodes=int(S1[0].sum()))


def set_pair_sums(arr, mask, pair_ix):
    """per-pair sums of [N, nonabstain, contained, size, 4 kind counts]; pairs with N>0 only."""
    P = pair_ix.max() + 1
    w = [np.bincount(pair_ix[mask], minlength=P).astype(float)]
    for j in range(arr.shape[1]):
        w.append(np.bincount(pair_ix[mask], weights=arr[mask, j], minlength=P))
    w = np.array(w)
    return w[:, w[0] > 0]


def set_stat(S, kind):
    N, na, pr, co, sz, cy, cyt = S[0], S[1], S[2], S[3], S[4], S[10], S[11]
    with np.errstate(invalid='ignore', divide='ignore'):
        return {'set_coverage': na / N, 'set_proposal_rate': pr / N, 'set_containment': co / pr,
                'set_mean_size': sz / pr, 'cytotoxic_rate': cy / N, 'cytotoxic_names_true_driver': cyt / cy}[kind]


def set_cell_stats(S):
    idx = boot_idx(S.shape[1]); T = S.sum(1); boots = S[:, idx].sum(2); out = {}
    for k in ('set_coverage', 'set_proposal_rate', 'set_containment', 'set_mean_size', 'cytotoxic_rate',
              'cytotoxic_names_true_driver'):
        pt = float(set_stat(T, k)); out[k] = pt if np.isfinite(pt) else None
        out[k + '_ci95'] = ci(set_stat(boots, k))
    out['set_kind_counts'] = {k: int(T[5 + i]) for i, k in enumerate(SET_KINDS)}
    out['n_episodes'] = int(T[0]); out['n_distinct_pairs'] = int(S.shape[1])
    out['n_non_abstain'] = int(T[1]); out['n_proposing'] = int(T[2]); out['n_cytotoxic'] = int(T[10])
    out['mass'] = SET_MASS
    return out


def analyse(eps, cells, overlap, set_cells=None):
    uniq = {p: i for i, p in enumerate(sorted({e['pair'] for e in eps}))}
    pair_ix = np.array([uniq[e['pair']] for e in eps])
    masks = strata_masks(eps); S = {}
    for key, arr in cells.items():
        for st_, m in masks.items():
            S[key + (st_,)] = pair_sums(arr, m, pair_ix)
    table = []
    for (pool, pol, rule, st_), s in S.items():
        for score in ('named', 'developable'):
            table.append(dict(pool=pool, policy=pol, rule=rule, stratum=st_, scoring=score, **cell_stats(s, score)))
    margins = []
    for pool in ('unconstrained', 'same_batch'):
        for rule in ('potency-only', 'selectivity-aware'):
            score = 'named' if rule == 'potency-only' else 'developable'
            for st_ in ('hard', 'easy', 'overall'):
                for a, b in (('adaptive_contrast', 'strongest-first'), ('adaptive_contrast', 'random'), ('adaptive_contrast', 'no_budget'),
                             ('adaptive_contrast', 'contrast-spread'), ('adaptive_contrast', 'decouple'), ('decouple', 'strongest-first'),
                             ('strongest-first', 'random'), ('strongest-first', 'no_budget')):
                    m = margin(S[(pool, a, rule, st_)], S[(pool, b, rule, st_)], score)
                    margins.append(dict(comparison=f'{a} - {b}', a=a, b=b, pool=pool, rule=rule,
                                        stratum=st_, scoring=score, metric='accuracy', **m))
    comp_cost = []
    for pol in POLICIES:
        for rule in ('potency-only', 'selectivity-aware'):
            for st_ in ('hard', 'easy', 'overall'):
                for score in ('named', 'developable'):
                    m = margin(S[('same_batch', pol, rule, st_)], S[('unconstrained', pol, rule, st_)], score)
                    comp_cost.append(dict(policy=pol, rule=rule, stratum=st_, scoring=score,
                                          same_batch_minus_unconstrained=m))
    rules = []
    for pool in ('unconstrained', 'same_batch'):
        for pol in POLICIES:
            for st_ in ('hard', 'easy', 'overall'):
                a, b = S[(pool, pol, 'selectivity-aware', st_)], S[(pool, pol, 'potency-only', st_)]
                rules.append(dict(pool=pool, policy=pol, stratum=st_,
                                  wasted_per_100=margin(a, b, 'developable', 'wasted_per_100'),
                                  developable_accuracy=margin(a, b, 'developable', 'accuracy'),
                                  coverage=margin(a, b, 'developable', 'coverage')))
    set_table = []
    cyt_truth = np.array([e['nonsel'] for e in eps])   # A (the true driver) is the host-cytotoxic compound
    for (pool, pol), arr in (set_cells or {}).items():
        for st_, m in masks.items():
            for tt, tm in (('all', np.ones(len(eps), bool)), ('cytotoxic_truth', cyt_truth), ('non_cytotoxic_truth', ~cyt_truth)):
                set_table.append(dict(pool=pool, policy=pol, rule='set-valued', stratum=st_, truth_cytotoxic=tt,
                                      **set_cell_stats(set_pair_sums(arr, m & tm, pair_ix))))
    ov = {f'{p}|{k}': float(np.mean(v)) for (p, k), v in overlap.items()}
    return dict(cells=table, set_cells=set_table, margins=margins, comparability_cost=comp_cost, rule_comparison=rules,
                pick_overlap_with_strongest_first=ov)


# ---------------- printing ----------------
def f(x, pct=True):
    return 'n/a' if x is None else (f'{100*x:5.1f}' if pct else f'{x:6.2f}')


def print_tables(title, res, pool, score):
    print(f"\n=== {title} | pool={pool} | scoring={score} ===")
    for st_ in ('hard', 'easy', 'overall'):
        rows = [c for c in res['cells'] if c['pool'] == pool and c['scoring'] == score and c['stratum'] == st_]
        n = rows[0]
        print(f"-- {st_}: {n['n_episodes']} episodes, {n['n_distinct_pairs']} distinct pairs")
        print(f"{'policy':22}{'rule':19}{'cover%':>7}{'prec%':>7}{'acc%':>7}  {'acc 95% CI':>16}{'wasted/100':>11}")
        for pol in POLICIES:
            for rule in ('potency-only', 'selectivity-aware'):
                c = next(c for c in rows if c['policy'] == pol and c['rule'] == rule)
                lo, hi = c['accuracy_ci95']
                print(f"{pol:22}{rule:19}{f(c['coverage']):>7}{f(c['precision']):>7}{f(c['accuracy']):>7}  "
                      f"{'[%s, %s]' % (f(lo), f(hi)):>16}{f(c['wasted_per_100'], False):>11}")


def main():
    t0 = time.time()
    print(f"confounded rotenoid pairs: {len(pairs)}   fitted gain = {GAIN:.2f}  (the shipped 2.0)")
    print(f"background={BACKGROUND} threshold={THR} tox_cap={TOX_CAP}  bootstrap draws={BOOT}")
    ps = np.array(CFG['prior']); ps2 = np.array(CFG['prior'])
    for x, y in (((0.01, 0.002), .6), ((0.0, 0.03), .1)):
        ps = H.update(ps, x, y, CFG); ps2 = DM.update(ps2, x, y, CFG)
    assert np.allclose(ps, ps2), 'decision_model port diverges from decouple.model'
    out = dict(config=dict(gain=GAIN, gain_method='decouple.calibration.fit_gain on all rotenoid compound abundances (present>0)',
                           background=BACKGROUND, nomination_threshold=THR, tox_cap=TOX_CAP, budget=BUDGET,
                           seed_reveals=HITS, pool_size=POOL_N, bootstrap_draws=BOOT,
                           n_pairs_available=len(pairs), smoke=SMOKE,
                           truth_scoring=dict(named='nominated candidate == truth driver (two-driver truth: always wrong)',
                                              developable='named AND not the cytotoxicity driver (half the episodes make A cytotoxic)')),
               regimes={})
    for gname, gen in (('well_specified', gen_his), ('misspecified', gen_ours)):
        for regime, two, seed in (('single_driver', False, 101), ('two_driver', True, 202)):
            tag = f'{gname}/{regime}'; print(f"\nbuilding {tag}")
            eps = build(gen, two, seed)
            nh = sum(e['hard'] for e in eps)
            batch_sizes = [len(e['pools']['same_batch']) for e in eps]
            print(f"  {len(eps)} episodes ({nh} hard, {len(eps)-nh} easy), {len({e['pair'] for e in eps})} pairs; "
                  f"same-batch pool size min {min(batch_sizes)} median {int(np.median(batch_sizes))}; "
                  f"hard pairs {len({e['pair'] for e in eps if e['hard']})}")
            cells, overlap, set_cells = run(eps, tag)
            res = analyse(eps, cells, overlap, set_cells)
            res.update(n_episodes=len(eps), n_hard=nh, n_easy=len(eps) - nh,
                       n_distinct_pairs=len({e['pair'] for e in eps}),
                       n_distinct_pairs_hard=len({e['pair'] for e in eps if e['hard']}),
                       same_batch_pool_size=dict(min=int(min(batch_sizes)), median=float(np.median(batch_sizes))),
                       same_batch_feasible_fraction=float(np.mean([b >= BUDGET for b in batch_sizes])))
            out['regimes'][tag] = res
            if gname == 'well_specified':
                for pool in ('unconstrained', 'same_batch'):
                    print_tables(tag, res, pool, 'named')
                    print_tables(tag, res, pool, 'developable')
    R = out['regimes']['well_specified/single_driver']
    print("\n" + "=" * 78 + "\nHEADLINE: adaptive_contrast - strongest-first (single driver, the generator, potency-only, "
          "naming accuracy, unconstrained pool)")
    for m in R['margins']:
        if (m['a'], m['b'], m['pool'], m['rule']) == ('adaptive_contrast', 'strongest-first', 'unconstrained', 'potency-only'):
            lo, hi = m['ci95']
            print(f"  {m['stratum']:8} {m['point']:+6.1f} pts  95% CI pair-clustered [{lo:+.1f}, {hi:+.1f}]  "
                  f"({m['n_episodes']} episodes, {m['n_distinct_pairs']} distinct pairs)")
    for gname in ('well_specified', 'misspecified'):
        for regime in ('single_driver',):
            RR = out['regimes'][f'{gname}/{regime}']
            print(f"\nMargins, {gname}/{regime}, unconstrained, potency-only (accuracy pts, pair-clustered 95% CI):")
            for st_ in ('hard', 'easy', 'overall'):
                for m in RR['margins']:
                    if (m['pool'], m['rule'], m['stratum']) == ('unconstrained', 'potency-only', st_):
                        lo, hi = m['ci95']
                        print(f"  {st_:8}{m['comparison']:34}{m['point']:+6.1f}  [{lo:+.1f}, {hi:+.1f}]")
    print("\nCOMPARABILITY COST (same-batch minus unconstrained, accuracy pts, named, potency-only, the generator, single driver):")
    for st_ in ('hard', 'easy', 'overall'):
        for c in R['comparability_cost']:
            if c['stratum'] == st_ and c['rule'] == 'potency-only' and c['scoring'] == 'named':
                m = c['same_batch_minus_unconstrained']; lo, hi = m['ci95']
                print(f"  {st_:8}{c['policy']:22}{m['point']:+6.1f}  [{lo:+.1f}, {hi:+.1f}]")
    print("\nRULE COMPARISON (selectivity-aware minus potency-only, developable scoring, unconstrained):")
    for r in R['rule_comparison']:
        if r['pool'] == 'unconstrained' and r['policy'] in ('adaptive_contrast', 'strongest-first', 'decouple'):
            w, a = r['wasted_per_100'], r['developable_accuracy']
            print(f"  {r['stratum']:8}{r['policy']:18} wasted/100 {w['point']:+6.2f} [{w['ci95'][0]:+.2f}, {w['ci95'][1]:+.2f}]"
                  f"   dev. accuracy {a['point']:+5.1f} [{a['ci95'][0]:+.1f}, {a['ci95'][1]:+.1f}]")
    print("\npick overlap with strongest-first (of 3), single driver, unconstrained:",
          {k: round(v, 2) for k, v in R['pick_overlap_with_strongest_first'].items() if k.startswith('unconstrained')})
    print(f"\nSET-VALUED vs SCALAR (overall stratum, unconstrained pool; scalar = potency-only named; set @{SET_MASS})")
    for tag, RR in out['regimes'].items():
        for pol in POLICIES:
            sc = next(c for c in RR['cells'] if (c['pool'], c['policy'], c['rule'], c['stratum'], c['scoring']) ==
                      ('unconstrained', pol, 'potency-only', 'overall', 'named'))
            print(f"  {tag:28}{pol:22} scalar cov {f(sc['coverage'])} acc {f(sc['accuracy'])}")
            for tt in ('all', 'cytotoxic_truth', 'non_cytotoxic_truth'):
                st = next(c for c in RR['set_cells'] if (c['pool'], c['policy'], c['stratum'], c['truth_cytotoxic']) ==
                          ('unconstrained', pol, 'overall', tt))
                print(f"      set {tt:20} n={st['n_episodes']:5} cov {f(st['set_coverage'])} prop {f(st['set_proposal_rate'])} "
                      f"cont {f(st['set_containment'])} size {f(st['set_mean_size'], False)} cytotox {f(st['cytotoxic_rate'])} "
                      f"cyto-names-driver {f(st['cytotoxic_names_true_driver'])} kinds {st['set_kind_counts']}")
    os.makedirs('results', exist_ok=True)
    dest = 'results/benchmark.json' if not SMOKE else os.path.join(os.environ.get('OUTDIR', '/tmp'), 'benchmark_smoke.json')
    json.dump(out, open(dest, 'w'), indent=1)
    print(f"\nwrote {dest}  ({time.time()-t0:.0f}s)")


if __name__ == '__main__':
    main()
