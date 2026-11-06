"""Where does coverage go? Classify every abstention by its cause.

Different causes have different fixes:
  NOT-SINGLE   posterior says 'both' or 'neither' -> a set/class answer may serve
  LOW-CONF     argmax is A or B but below threshold -> threshold or evidence
  CYTOTOXIC    would nominate on potency, blocked by tox_cap -> correct decline
  INSEPARABLE  no available sample distinguishes the pair -> needs fractionation
"""
import sys, math, random, itertools, collections, json
sys.path.insert(0, 'scripts')
import numpy as np, decision_model as H
from decouple.calibration import fit_gain
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures

BUDGET, HITS, POOL_N, TOX_CAP = 3, 8, 250, 0.5
comp = build_compounds('pos'); stru = load_structures()
rot = {k for k, v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c = [c for c, v in comp.items() if any(k in rot for k in v['isdb_keys'])]
samples = sorted({s for v in comp.values() for s in v['abundance']})
GAIN = fit_gain([a for c in rot_c for a in comp[c]['abundance'].values() if a > 0])
CFG = dict(H.CFG, gain=GAIN, background=0.05, nomination_threshold=0.85)
pairs = []
for a, b in itertools.combinations(rot_c, 2):
    Sa, Sb = set(comp[a]['abundance']), set(comp[b]['abundance'])
    if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa): pairs.append((a, b))

def chan(x_by, idx, rng):
    return {s: float(H.means(x_by[s], CFG)[idx] + CFG['noise_sd'] * rng.gauss(0, 1)) for s in samples}

rows = collections.Counter(); margin_gap = []; set2_correct = 0; total = 0
rng0 = random.Random(77)
for i, (A, B) in enumerate(rng0.sample(pairs, len(pairs))):
    for sd in range(4):
        r = random.Random(H.seed_for(77, i, sd))
        x = {s: (comp[A]['abundance'].get(s, 0.0), comp[B]['abundance'].get(s, 0.0)) for s in samples}
        y_par = chan(x, 0, r)
        non_sel = (i + sd) % 2 == 0
        y_tox = chan(x, 0 if non_sel else 3, r)
        known = sorted(samples, key=lambda s: -y_par[s])[:HITS]
        pool = r.sample([s for s in samples if s not in known], POOL_N)
        picks = select('adaptive_contrast', [A, B], set(known), pool, BUDGET, comp,
                       activity=y_par, rng=r)
        rev = list(known) + list(picks)
        smp = [{'id': s, 'x': list(x[s])} for s in rev]
        p_par = H.posterior_of(smp, {s: y_par[s] for s in rev}, CFG)
        p_tox = H.posterior_of(smp, {s: y_tox[s] for s in rev}, CFG)
        total += 1
        k = int(np.argmax(p_par))
        separable = any(abs(x[s][0] - x[s][1]) > 1e-10 for s in rev)
        if not separable:                      rows['INSEPARABLE'] += 1; continue
        if k >= 2:                             rows[f'NOT-SINGLE ({H.HYPOTHESES[k]})'] += 1
        elif p_par[k] < CFG['nomination_threshold']:
            rows['LOW-CONF (A/B top, under threshold)'] += 1
            margin_gap.append(CFG['nomination_threshold'] - p_par[k])
        elif p_tox[k] > TOX_CAP:               rows['CYTOTOXIC (correct decline)'] += 1
        else:                                  rows['NOMINATED'] += 1
        # would a SET of the top two have contained the truth? (truth is always A)
        top2 = list(np.argsort(p_par)[::-1][:2])
        if 0 in top2: set2_correct += 1
print(f"episodes: {total}\n")
print(f"{'outcome':44}{'n':>6}{'share':>9}")
for k, v in rows.most_common():
    print(f"  {k:42}{v:>6}{v/total:>8.1%}")
print(f"\n  set-of-2 would contain the true driver: {set2_correct}/{total} = {set2_correct/total:.1%}")
if margin_gap:
    margin_gap.sort()
    print(f"\n  LOW-CONF cases: how far below 0.85?")
    for q, lab in ((0.25,'q25'),(0.5,'median'),(0.75,'q75')):
        print(f"    {lab}: {margin_gap[int(q*(len(margin_gap)-1))]:.3f} below")
    for t in (0.70, 0.75, 0.80):
        n = sum(1 for g in margin_gap if 0.85 - g >= t)
        print(f"    would clear a {t:.2f} threshold: {n} ({n/total:.1%} of all episodes)")
