"""How often does a decorrelating sample actually EXIST for a confounded pair?
Strict test: one present, other absent. Practical test: A:B ratio shifts >= R-fold."""
import pickle,gzip,re,collections,itertools,statistics as st,pathlib,math
MZ_TOL,RT_TOL=0.01,0.20
P=pickle.load(open("data/features_mzrt.pkl","rb")); feat,ann=P['feat'],P['ann']
A=pickle.load(open("data/abundance.pkl","rb")); rot=A['rot']
D=pathlib.Path("data/enpkg")
demo=gzip.open(D/"metadata_demo.ttl.gz","rt",errors="replace").read()
assay=collections.defaultdict(dict)
for node,body in re.findall(r"enpkgmodule:(\S+?) a enpkgmodule:\w+ ;(.*?)\.\n",demo,re.S):
    m=re.search(r'inhibition_percentage "([-\d.eE+]+)"',body)
    if not m: continue
    for suf in ("_Tcruzi_10ugml","_L6_10ugml"):
        if node.endswith(suf): assay[node[:-len(suf)]][suf.strip('_')]=float(m.group(1))
TC={s:a.get('Tcruzi_10ugml',0.0) for s,a in assay.items()}
L6={s:a.get('L6_10ugml',0.0) for s,a in assay.items()}
ACT={s for s in TC if TC[s]>80 and L6.get(s,100)<50}
comp=collections.defaultdict(dict); cinfo={}
for (s,scan),(rel,mz,rt) in feat.items():
    cid=(round(mz/MZ_TOL),round(rt/RT_TOL))
    comp[cid][s]=max(comp[cid].get(s,0.0),rel)
    if cid not in cinfo: cinfo[cid]=[mz,rt,collections.Counter()]
    cinfo[cid][2].update(ann.get((s,scan),()))
rot_c=[cid for cid,(mz,rt,kc) in cinfo.items() if any(k in rot for k in kc) and len(comp[cid])>=3]

pairs=[]
for a,b in itertools.combinations(sorted(rot_c),2):
    if abs(cinfo[a][0]-cinfo[b][0])<MZ_TOL*2 and abs(cinfo[a][1]-cinfo[b][1])<RT_TOL*2: continue
    Sa,Sb=set(comp[a]),set(comp[b])
    if len(Sa&Sb)<3: continue
    pairs.append((a,b,Sa,Sb))
print(f"confounded distinct rotenoid pairs (co-occur >=3): {len(pairs)}\n")

strict=prac=both_act=0; nopt=[]; ratios=[]
for a,b,Sa,Sb in pairs:
    onlyA,onlyB=Sa-Sb,Sb-Sa
    n=len(onlyA)+len(onlyB); nopt.append(n)
    if n>0: strict+=1
    # practical: largest fold-shift in A:B ratio among co-occurring samples
    co=Sa&Sb
    rs=[]
    for s in co:
        va,vb=comp[a].get(s,0.0),comp[b].get(s,0.0)
        if va>0 and vb>0: rs.append(va/vb)
    if len(rs)>=2:
        fold=max(rs)/min(rs); ratios.append(fold)
        if fold>=5: prac+=1
    if (Sa&ACT) and (Sb&ACT): both_act+=1

print(f"STRICT  (a sample has one compound, not the other): {strict}/{len(pairs)} = {100*strict/len(pairs):.1f}%")
print(f"PRACTICAL (A:B ratio shifts >=5-fold across co-occurring extracts): {prac}/{len(pairs)} = {100*prac/len(pairs):.1f}%")
print(f"\ndecorrelating-sample count per pair: median={st.median(nopt)}, mean={st.mean(nopt):.1f}, "
      f"max={max(nopt)}, zero-option pairs={sum(1 for x in nopt if x==0)}")
if ratios:
    ratios.sort()
    print(f"max A:B fold-shift among co-occurring extracts: median={st.median(ratios):.1f}x, "
          f"90th pct={ratios[int(.9*len(ratios))]:.1f}x, max={max(ratios):.0f}x")
print(f"\npairs where BOTH compounds appear in >=1 selective active: {both_act}")

print("\n--- sparsity: how many extracts does a rotenoid compound occur in? ---")
occ=sorted(len(comp[c]) for c in rot_c)
print(f"n compounds={len(occ)}  median occurrence={st.median(occ)}  mean={st.mean(occ):.1f}  max={max(occ)}")
print(f"  present in <=5 extracts: {sum(1 for x in occ if x<=5)}/{len(occ)} "
      f"({100*sum(1 for x in occ if x<=5)/len(occ):.0f}%)")
