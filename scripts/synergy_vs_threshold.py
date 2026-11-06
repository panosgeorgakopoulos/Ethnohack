"""0.85 was chosen over 0.80 on a synergy false-nomination constraint measured on
24 episodes (2/24 vs 1/24 -- a one-episode difference). Re-measure on all 952."""
import sys, math, random, itertools
sys.path.insert(0,'scripts')
import numpy as np, decision_model as H
from decouple.calibration import fit_gain
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures
BUDGET,HITS,POOL_N,TOX_CAP=3,8,250,0.5
comp=build_compounds('pos'); stru=load_structures()
rot={k for k,v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c=[c for c,v in comp.items() if any(k in rot for k in v['isdb_keys'])]
samples=sorted({s for v in comp.values() for s in v['abundance']})
GAIN=fit_gain([a for c in rot_c for a in comp[c]['abundance'].values() if a>0])
CFG=dict(H.CFG,gain=GAIN,background=0.05)
pairs=[]
for a,b in itertools.combinations(rot_c,2):
    Sa,Sb=set(comp[a]['abundance']),set(comp[b]['abundance'])
    if len(Sa&Sb)>=3 and (Sa-Sb) and (Sb-Sa): pairs.append((a,b))
def chan(x,i,r): return {s: float(H.means(x[s],CFG)[i]+CFG['noise_sd']*r.gauss(0,1)) for s in samples}

recs=[]
rng0=random.Random(91)
for i,(A,B) in enumerate(rng0.sample(pairs,len(pairs))):
    for sd in range(4):
        r=random.Random(H.seed_for(91,i,sd))
        x={s:(comp[A]['abundance'].get(s,0.0),comp[B]['abundance'].get(s,0.0)) for s in samples}
        y=chan(x,2,r)                      # TWO drivers act together: truth = 'both'
        ytox=chan(x,3,r)                   # keep the selectivity channel clean
        known=sorted(samples,key=lambda s:-y[s])[:HITS]
        pool=r.sample([s for s in samples if s not in known],POOL_N)
        picks=select('adaptive_contrast',[A,B],set(known),pool,BUDGET,comp,activity=y,rng=r)
        rev=list(known)+list(picks); smp=[{'id':s,'x':list(x[s])} for s in rev]
        p=H.posterior_of(smp,{s:y[s] for s in rev},CFG)
        ptox=H.posterior_of(smp,{s:ytox[s] for s in rev},CFG)
        k=int(np.argmax(p))
        recs.append((k,float(p[k]),float(ptox[k])))
N=len(recs)
print(f"two-driver episodes: {N}   (every single-compound nomination here is WRONG)\n")
print(f"{'t':>6}{'false nominations':>20}{'rate':>9}")
for t in (0.50,0.60,0.70,0.75,0.80,0.85,0.90):
    bad=sum(1 for k,p,pt in recs if k<2 and p>=t and pt<=TOX_CAP)
    print(f"{t:>6.2f}{bad:>20}{bad/N:>8.1%}")
