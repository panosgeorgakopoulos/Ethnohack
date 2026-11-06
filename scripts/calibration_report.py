"""M2 evidence: the shipped gain vs fitted gain on real ENPKG abundances.

Run from repo root:  python3.12 scripts/calibration_report.py
"""
import sys, json, random, itertools
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from decouple.calibration import fit_gain, fit_background, calibrate
from decouple.model import decision, means
from decouple.engine import run
from src.compounds import build_compounds
from src.enpkg_io import load_structures, load_assays

cfg0 = json.load(open(ROOT / 'config/default.json'))
comp = build_compounds('pos')
rot = {k for k, v in load_structures().items() if 'Rotenoids' in v['npc_class']}
rot_c = [c for c, v in comp.items() if any(k in rot for k in v['isdb_keys'])]
ab = [a for c in rot_c for a in comp[c]['abundance'].values()]
allab = [a for v in comp.values() for a in v['abundance'].values()]
print(f"rotenoid compounds {len(rot_c)}, present abundances {len(ab)}, median {np.median(ab):.4f}")
print(f"all compounds median present abundance {np.median(allab):.4f}")
g = fit_gain(ab); print(f"fit_gain(rotenoid compounds) = {g:.2f}   (all compounds: {fit_gain(allab):.2f})")

# background: per-extract total rotenoid abundance vs measured T. cruzi activity (0-1)
assays = load_assays()
samples = sorted({s for v in comp.values() for s in v['abundance']})
load = {s: 0.0 for s in samples}
for c in rot_c:
    for s, a in comp[c]['abundance'].items(): load[s] += a
ss = [s for s in samples if s in assays and 'Tcruzi_10ugml' in assays[s]]
x = [load[s] for s in ss]; y = [assays[s]['Tcruzi_10ugml'] / 100 for s in ss]
bg = fit_background(x, y)
print(f"fit_background (n={len(ss)} extracts, lowest quartile of rotenoid load) = {bg:.4f}"
      f"   (shipped 0.05; zero-load extracts median response {np.median([v for a, v in zip(x, y) if a == 0] or [np.nan]):.4f})")

# episodes: real confounded rotenoid pairs, 1 driver (A), gain-independent logistic generator
pairs = []
for a, b in itertools.combinations(rot_c, 2):
    Sa, Sb = set(comp[a]['abundance']), set(comp[b]['abundance'])
    if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa): pairs.append((a, b))
rng = random.Random(7)
sel = rng.sample(pairs, min(60, len(pairs)))
def episode(i, A, B):
    r = random.Random(i)
    xs = {s: (comp[A]['abundance'].get(s, 0.0), comp[B]['abundance'].get(s, 0.0)) for s in samples}
    def resp(a):
        if a <= 0: return max(0.0, r.gauss(0, .08))
        return max(0.0, 1.1 / (1 + np.exp(-(np.log10(a) - np.log10(0.02)) / 0.6)) + r.gauss(0, .08))
    out = {s: resp(xs[s][0]) for s in samples}
    known = sorted(samples, key=lambda s: -out[s])[:8]
    pool = r.sample([s for s in samples if s not in known], 250)
    sm = [{'id': s, 'name': s, 'x': list(xs[s]), 'units': 'rel', 'occurrence_status': 'real', 'evidence': ''} for s in known + pool]
    return {'id': f'e{i}', 'tier': 'real', 'samples': sm, 'initial': known, 'hidden': {'outcomes': out},
            'candidates': [{'id': 'A', 'name': A}, {'id': 'B', 'name': B}]}
eps = [episode(i, A, B) for i, (A, B) in enumerate(sel)]
print(f"\nepisodes: {len(eps)} real confounded rotenoid pairs (of {len(pairs)}), truth=A, budget {cfg0['budget']}")

def abstain_rate(cfg):
    ab = nom = 0
    for e in eps:
        d = run(e, 'decouple', cfg)['decision']
        ab += d['kind'] == 'abstain'; nom += d['kind'] == 'nominate' and d['candidate'] == 'A'
    return ab / len(eps), nom / len(eps)
med = float(np.median(ab))
rows = [('shipped gain=2.0, bg=0.05', cfg0),
        (f'fitted gain={g:.1f}, bg=0.05', dict(cfg0, gain=g)),
        (f'fitted gain={g:.1f}, bg={bg:.3f}', calibrate(ab, y and [0]*0 or None, cfg0) | {'background': bg})]
print(f"\n{'config':32}{'mu@median':>10}{'abstain':>9}{'correct nominate':>18}")
for name, c in rows:
    a, n = abstain_rate(c)
    print(f"{name:32}{means([med, 0], c)[0]:>10.3f}{a:>9.1%}{n:>18.1%}")
