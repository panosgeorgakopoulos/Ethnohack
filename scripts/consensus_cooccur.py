"""Cluster annotated features into consensus compounds by (m/z, RT), then measure
TRUE cross-sample co-occurrence between DISTINCT compounds."""
import pickle,gzip,re,math,collections,itertools,statistics as st,pathlib
MZ_TOL, RT_TOL = 0.01, 0.20       # Da, minutes
P=pickle.load(open("data/features_mzrt.pkl","rb")); feat,ann=P['feat'],P['ann']
A=pickle.load(open("data/abundance.pkl","rb")); rot,smiles=A['rot'],A['smiles']
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
meta=gzip.open(D/"metadata_enpkg.ttl.gz","rt",errors="replace").read()
sp={}
for rm,body in re.findall(r"enpkg:(\S+) a enpkg:RawMaterial ;(.*?)\.\n",meta,re.S):
    p=re.search(r"has_lab_process enpkg:(\S+)",body); t=re.search(r'submitted_taxon "([^"]+)"',body)
    if p: sp[p.group(1)]=t.group(1) if t else '?'

# --- consensus compounds via (mz,RT) grid ---
comp=collections.defaultdict(dict)          # cid -> sample -> max rel area
cinfo={}
for (s,scan),(rel,mz,rt) in feat.items():
    cid=(round(mz/MZ_TOL), round(rt/RT_TOL))
    comp[cid][s]=max(comp[cid].get(s,0.0), rel)
    if cid not in cinfo: cinfo[cid]=[mz,rt,collections.Counter()]
    cinfo[cid][2].update(ann.get((s,scan),()))
print(f"annotated features {len(feat)} -> consensus compounds {len(comp)} "
      f"(tol {MZ_TOL} Da / {RT_TOL} min)")
rot_c={cid for cid,(mz,rt,kc) in cinfo.items() if any(k in rot for k in kc)}
print(f"consensus compounds with >=1 rotenoid candidate annotation: {len(rot_c)}")
multi={cid for cid in rot_c if len(comp[cid])>=3}
print(f"  ... of which present in >=3 extracts: {len(multi)}")

print("\n"+"="*86); print("TRUE CO-OCCURRENCE between DISTINCT rotenoid compounds"); print("="*86)
pairs=[]
for a,b in itertools.combinations(sorted(multi),2):
    mza,rta,_=cinfo[a]; mzb,rtb,_=cinfo[b]
    if abs(mza-mzb)<MZ_TOL*2 and abs(rta-rtb)<RT_TOL*2: continue   # same peak, skip
    Sa,Sb=set(comp[a]),set(comp[b]); inter=Sa&Sb
    if len(inter)<3: continue
    pairs.append((len(inter)/len(Sa|Sb), len(inter), a,b,Sa,Sb))
pairs.sort(key=lambda x:-x[0])
print(f"distinct rotenoid compound pairs co-occurring in >=3 extracts: {len(pairs)}")
print(f"\n{'Jacc':>6}{'both':>6}  {'cmpd A (m/z @ RT)':24}{'cmpd B (m/z @ RT)':24}{'|A|':>5}{'|B|':>5}{'A&B in actives':>16}")
for j,ni,a,b,Sa,Sb in pairs[:8]:
    ia=f"{cinfo[a][0]:.3f} @ {cinfo[a][1]:.2f}"; ib=f"{cinfo[b][0]:.3f} @ {cinfo[b][1]:.2f}"
    print(f"{j:>6.2f}{ni:>6}  {ia:24}{ib:24}{len(Sa):>5}{len(Sb):>5}{len(Sa&Sb&ACT):>16}")

if pairs:
    print("\n"+"="*86); print("DECORRELATING SAMPLES for the most-confounded distinct pair"); print("="*86)
    j,ni,a,b,Sa,Sb=pairs[0]
    print(f"A = m/z {cinfo[a][0]:.4f} @ RT {cinfo[a][1]:.2f}   in {len(Sa)} extracts")
    print(f"B = m/z {cinfo[b][0]:.4f} @ RT {cinfo[b][1]:.2f}   in {len(Sb)} extracts")
    print(f"Jaccard {j:.2f}, co-occur in {ni}\n")
    onlyA, onlyB = Sa-Sb, Sb-Sa
    print(f"  A-only extracts: {len(onlyA)}   B-only extracts: {len(onlyB)}")
    for lab,S,other in (("A only",onlyA,b),("B only",onlyB,a)):
        for s in sorted(S,key=lambda x:-TC.get(x,0))[:5]:
            m=" *ACTIVE*" if s in ACT else ""
            print(f"    {lab:7} {s:12} T.cruzi={TC.get(s,0):6.1f}%  L6={L6.get(s,0):5.1f}  {sp.get(s,'?')}{m}")
    # the money question
    print("\n  >>> Do decorrelating samples with activity data exist for this pair?",
          "YES" if (onlyA or onlyB) else "NO")
