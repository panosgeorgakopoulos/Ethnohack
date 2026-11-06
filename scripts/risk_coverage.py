"""Risk-coverage curve for the SHIPPED product (cytotoxicity filter applied).
Is 0.85 binding, or is the posterior simply under-confident?"""
import sys, math, random, itertools, collections
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
        k=int(np.argmax(p))
        recs.append(dict(pair=i, k=k, p=float(p[k]), ptox=float(ptox[k]),
                         correct=(k==0), cytotoxic=non_sel))
N=len(recs)
print(f"episodes {N}   (half have a cytotoxic driver by construction)\n")
print("Shipped product: nominate iff argmax in {A,B}, p >= t, AND P_tox <= 0.5\n")
print(f"{'t':>6}{'coverage':>10}{'precision':>11}{'wasted/100':>12}{'95% upper err':>15}")
def clopper_upper(k,n):
    if n==0: return float('nan')
    lo,hi=0.0,1.0
    for _ in range(60):
        m=(lo+hi)/2
        # P(X<=k | n,m) >= 0.05  ->  m is plausible
        s=sum(math.comb(n,j)*m**j*(1-m)**(n-j) for j in range(k+1))
        if s<0.05: hi=m
        else: lo=m
    return hi
for t in (0.50,0.60,0.70,0.75,0.80,0.85,0.90,0.95):
    sel=[r for r in recs if r['k']<2 and r['p']>=t and r['ptox']<=TOX_CAP]
    n=len(sel); ok=sum(r['correct'] for r in sel)
    if n==0: continue
    bad=n-ok
    print(f"{t:>6.2f}{n/N:>9.1%}{ok/n:>10.1%}{bad/N*100:>11.2f}{clopper_upper(bad,n):>14.1%}")
print("\n  'wasted/100' counts nominations of the wrong compound per 100 episodes.")
