"""Instead of 'one compound or nothing', return the smallest SET whose posterior
mass clears a level. For a chemist 'it is one of these two' is actionable; an
abstention is not."""
import sys, math, random, itertools, collections
sys.path.insert(0,'scripts')
import numpy as np, decision_model as H
from decouple.calibration import fit_gain
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures
BUDGET,HITS,POOL_N,TOX_CAP = 3,8,250,0.5
comp=build_compounds('pos'); stru=load_structures()
rot={k for k,v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c=[c for c,v in comp.items() if any(k in rot for k in v['isdb_keys'])]
samples=sorted({s for v in comp.values() for s in v['abundance']})
GAIN=fit_gain([a for c in rot_c for a in comp[c]['abundance'].values() if a>0])
CFG=dict(H.CFG,gain=GAIN,background=0.05,nomination_threshold=0.85)
pairs=[]
for a,b in itertools.combinations(rot_c,2):
    Sa,Sb=set(comp[a]['abundance']),set(comp[b]['abundance'])
    if len(Sa&Sb)>=3 and (Sa-Sb) and (Sb-Sa): pairs.append((a,b))
def chan(x,i,r): return {s: float(H.means(x[s],CFG)[i]+CFG['noise_sd']*r.gauss(0,1)) for s in samples}

LEVELS=[0.80,0.90,0.95,0.99]
stat={L:{'cov':0,'contain':0,'size':[]} for L in LEVELS}
single=0; tot=0
rng0=random.Random(77)
for i,(A,B) in enumerate(rng0.sample(pairs,len(pairs))):
    for sd in range(4):
        r=random.Random(H.seed_for(77,i,sd))
        x={s:(comp[A]['abundance'].get(s,0.0),comp[B]['abundance'].get(s,0.0)) for s in samples}
        y=chan(x,0,r); non_sel=(i+sd)%2==0; ytox=chan(x,0 if non_sel else 3,r)
        known=sorted(samples,key=lambda s:-y[s])[:HITS]
        pool=r.sample([s for s in samples if s not in known],POOL_N)
        picks=select('adaptive_contrast',[A,B],set(known),pool,BUDGET,comp,activity=y,rng=r)
        rev=list(known)+list(picks); smp=[{'id':s,'x':list(x[s])} for s in rev]
        p=H.posterior_of(smp,{s:y[s] for s in rev},CFG)
        ptox=H.posterior_of(smp,{s:ytox[s] for s in rev},CFG)
        tot+=1
        k=int(np.argmax(p))
        if k<2 and p[k]>=CFG['nomination_threshold'] and ptox[k]<=TOX_CAP: single+=1
        # smallest set over the two single-driver hypotheses + 'both', mass-ordered
        order=np.argsort(p)[::-1]
        for L in LEVELS:
            cum=0.0; S=[]
            for j in order:
                S.append(int(j)); cum+=p[j]
                if cum>=L: break
            # a set is useful only if it excludes nothing actionable: drop sets
            # that are just "everything"
            if len(S)>=4: continue
            stat[L]['cov']+=1; stat[L]['size'].append(len(S))
            # truth is A (index 0); a set "contains" it if 0 in S
            if 0 in S: stat[L]['contain']+=1
print(f"episodes {tot}")
print(f"  single-compound nomination (current rule): {single/tot:.1%} coverage\n")
print(f"{'level':>7}{'coverage':>11}{'contains truth':>16}{'mean size':>11}{'size<=2':>9}")
for L in LEVELS:
    s=stat[L]; n=s['cov']
    if not n: continue
    sz=s['size']
    print(f"{L:>7.2f}{n/tot:>10.1%}{s['contain']/n:>15.1%}{sum(sz)/n:>11.2f}"
          f"{sum(1 for z in sz if z<=2)/n:>8.1%}")
