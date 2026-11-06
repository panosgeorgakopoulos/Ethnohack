"""(construction reused from set_product.py) The shipped rule returns one compound or nothing. Return instead the smallest
set whose posterior mass clears a level -- keeping the cytotoxicity veto, which
is a correct decline and must not be relaxed."""
import sys, math, random, itertools, collections
sys.path.insert(0,'scripts')
import numpy as np, decision_model as H
from decouple.setvalued import set_decision
from decouple.calibration import fit_gain
from src.compounds import build_compounds
from src.selection import select
from src.enpkg_io import load_structures
BUDGET,HITS,POOL_N,TOX_CAP,THR=3,8,250,0.5,0.85
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

def run(truth_idx, seed):
    out=[]
    rng0=random.Random(seed)
    for i,(A,B) in enumerate(rng0.sample(pairs,len(pairs))):
        for sd in range(4):
            r=random.Random(H.seed_for(seed,i,sd))
            x={s:(comp[A]['abundance'].get(s,0.0),comp[B]['abundance'].get(s,0.0)) for s in samples}
            y=chan(x,truth_idx,r)
            cyto = (truth_idx==0) and ((i+sd)%2==0)
            ytox=chan(x,0 if cyto else 3,r)
            known=sorted(samples,key=lambda s:-y[s])[:HITS]
            pool=r.sample([s for s in samples if s not in known],POOL_N)
            picks=select('adaptive_contrast',[A,B],set(known),pool,BUDGET,comp,activity=y,rng=r)
            rev=list(known)+list(picks); smp=[{'id':s,'x':list(x[s])} for s in rev]
            p=H.posterior_of(smp,{s:y[s] for s in rev},CFG)
            ptox=H.posterior_of(smp,{s:ytox[s] for s in rev},CFG)
            out.append((p,ptox,cyto,smp,rev))
    return out


def report(rows, truth_idx, label):
    N=len(rows); cur_cov=cur_ok=0
    for p,ptox,cyto,smp,rev in rows:
        k=int(np.argmax(p))
        if k<2 and p[k]>=THR and ptox[k]<=TOX_CAP:
            cur_cov+=1; cur_ok+=(k==truth_idx)
    print(f"\n  {label}  (n={N})")
    print(f"    current rule        coverage {cur_cov/N:6.1%}   contains truth "
          f"{(cur_ok/cur_cov if cur_cov else float('nan')):6.1%}   mean size 1.00")
    T=H.HYPOTHESES[truth_idx]
    for flag in sorted({r[2] for r in rows}):
        sub=[r for r in rows if r[2]==flag]; n=len(sub)
        ds=[set_decision(p,pt,smp,set(rev),dict(tox_cap=TOX_CAP)) for p,pt,c,smp,rev in sub]
        sets=[d for d in ds if d['kind'] not in ('abstain','cytotoxic')]
        cy=[d for d in ds if d['kind']=='cytotoxic']
        ab=sum(d['kind']=='abstain' for d in ds)
        cont=sum(T in d['candidates'] for d in sets)
        right=sum(d['candidates']==[T] for d in cy)
        print(f"    cytotoxic-truth={flag!s:5} n={n}: set answer {len(sets)/n:6.1%} "
              f"(contains truth {(cont/len(sets) if sets else float('nan')):6.1%}, mean size "
              f"{(sum(d['size'] for d in sets)/len(sets) if sets else float('nan')):.2f}); "
              f"'cytotoxic' {len(cy)/n:6.1%} (names true driver {right}, WRONG compound {len(cy)-right}); "
              f"abstain {ab/n:6.1%}")

if __name__=='__main__':
    report(run(0,77), 0, "SINGLE DRIVER (truth = compound A)")
    report(run(2,91), 2, "TWO DRIVERS   (truth = 'both')")
