"""Does a SECOND response channel let the model avoid the rotenone trap?

Rotenone is the most potent rotenoid and the worst candidate: SI 51.7 against
deguelin's 1148.5, because it is also broadly cytotoxic. A potency-only model
nominates it and is 'correct' by its own metric and wrong in the lab.

ENPKG measures Tcruzi inhibition AND L6 host cytotoxicity on the SAME extracts
in the SAME screen, so one reveal buys both readouts -- no extra assay cost.

Setup: the decision model run twice over identical x, once per channel.
  potency-only   nominate i if P_par(i) >= thr                (the decision model today)
  selectivity    nominate i if P_par(i) >= thr AND P_tox(i) <= tox_cap
Half the episodes make the parasite driver ALSO the cytotoxicity driver
(rotenone-like, undevelopable); half leave it clean.
"""
import sys, math, random, itertools
import numpy as np
sys.path.insert(0, 'scripts'); import decision_model as H
from decouple.selectivity import dual_posterior, selective_decision
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures, load_assays

CFG = dict(H.CFG, gain=50.0); BUDGET, HITS, POOL_N = 3, 8, 250
THR, TOX_CAP = 0.9, 0.5
comp = build_compounds('pos'); stru = load_structures()
rot = {k for k, v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c = [c for c, v in comp.items() if any(k in rot for k in v['isdb_keys'])]
samples = sorted({s for v in comp.values() for s in v['abundance']})
pairs = []
for a, b in itertools.combinations(rot_c, 2):
    Sa, Sb = set(comp[a]['abundance']), set(comp[b]['abundance'])
    if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa): pairs.append((a, b))

def channel(x_by, hyp_idx, rng):
    out = {}
    for s in samples:
        mu = H.means(x_by[s], CFG)[hyp_idx]
        out[s] = float(mu + CFG['noise_sd'] * rng.gauss(0, 1))
    return out

def build(n, seed):
    eps, r0 = [], random.Random(seed)
    order = [(i, p, sd) for i, p in enumerate(r0.sample(pairs, len(pairs))) for sd in range(14)]
    for i, (A, B), sd in order:
        r = random.Random(H.seed_for(seed, i, sd))
        x = {s: (comp[A]['abundance'].get(s, 0.0), comp[B]['abundance'].get(s, 0.0)) for s in samples}
        y_par = channel(x, 0, r)                      # A drives the parasite
        non_selective = (i + sd) % 2 == 0
        y_tox = channel(x, 0 if non_selective else 3, r)   # A drives tox, or nothing does
        known = sorted(samples, key=lambda s: -y_par[s])[:HITS]
        if tuple(x[s][0] >= .02 for s in known) != tuple(x[s][1] >= .02 for s in known): continue
        pool = r.sample([s for s in samples if s not in known], POOL_N)
        eps.append(dict(id=f"e{i}_{sd}", A=A, B=B, x=x, par=y_par, tox=y_tox,
                        known=known, pool=pool, non_selective=non_selective))
        if len(eps) >= n: break
    return eps

def judge(ep):
    smp = [{'id': s, 'x': list(ep['x'][s])} for s in ep['known'] + ep['pool']]
    picks = select('adaptive_contrast', [ep['A'], ep['B']], set(ep['known']), ep['pool'],
                   BUDGET, comp, activity=ep['par'], rng=random.Random(1))
    rev = list(ep['known']) + list(picks)          # ONE reveal buys BOTH channels
    p_par, p_tox = dual_posterior(smp, {s: ep['par'][s] for s in rev},
                                  {s: ep['tox'][s] for s in rev}, CFG)
    i = int(np.argmax(p_par[:2]))
    nom_potency = p_par[i] >= THR
    d = selective_decision(p_par, p_tox, smp, {s: 1 for s in rev}, dict(CFG, tox_cap=TOX_CAP))
    nom_select = d['kind'] == 'nominate'
    # developable = drives the parasite AND is not the cytotoxicity driver
    developable = (i == 0) and not ep['non_selective']
    return nom_potency, nom_select, developable, ep['non_selective']

eps = build(400, 909)
ns = sum(e['non_selective'] for e in eps)
print(f"episodes {len(eps)}  (non-selective drivers: {ns}, clean: {len(eps)-ns})\n")
rows = {'potency-only (the decision model today)': [0, 0, 0], 'selectivity-aware (2 channels)': [0, 0, 0]}
for ep in eps:
    np_, ns_, dev, bad = judge(ep)
    for key, fired in (('potency-only (the decision model today)', np_), ('selectivity-aware (2 channels)', ns_)):
        if fired:
            rows[key][0] += 1
            rows[key][1] += dev
            rows[key][2] += (not dev)
N = len(eps)
print(f"{'rule':34}{'nominates':>11}{'developable':>13}{'UNDEVELOPABLE':>15}")
for k, (nm, dv, bd) in rows.items():
    print(f"{k:34}{nm/N:>7.1%} (n={nm:3d}){(dv/nm if nm else float('nan')):>13.1%}{(bd/nm if nm else float('nan')):>15.1%}")
print("\n  'UNDEVELOPABLE' = nominated a compound that drives the parasite AND the")
print("   host-cell toxicity. That is the rotenone trap, and it is what a chemist")
print("   would waste weeks of chromatography on.")

# ---- real-data sanity check: measured Tcruzi and measured L6, no simulation ----
A_ = load_assays()
act = [s for s in samples if A_[s]['Tcruzi_10ugml'] > 80]
sel = [s for s in act if A_[s]['L6_10ugml'] < 50]
print(f"\nREAL DATA: extracts with >80% T. cruzi inhibition: {len(act)}")
print(f"           of those, non-cytotoxic (L6 < 50%):      {len(sel)}")
print(f"           potency-only would advance {len(act)}; {len(act)-len(sel)} are cytotoxic decoys "
      f"({(len(act)-len(sel))/len(act):.0%})")
