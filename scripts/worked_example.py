import pickle,gzip,re,collections,itertools,statistics as st,pathlib
MZ_TOL,RT_TOL=0.01,0.20
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
TC={s:a.get('Tcruzi_10ugml',0.0) for s,a in assay.items()}; L6={s:a.get('L6_10ugml',0.0) for s,a in assay.items()}
ACT={s for s in TC if TC[s]>80 and L6.get(s,100)<50}
meta=gzip.open(D/"metadata_enpkg.ttl.gz","rt",errors="replace").read()
sp={}
for rm,body in re.findall(r"enpkg:(\S+) a enpkg:RawMaterial ;(.*?)\.\n",meta,re.S):
    p=re.search(r"has_lab_process enpkg:(\S+)",body); t=re.search(r'submitted_taxon "([^"]+)"',body)
    if p: sp[p.group(1)]=t.group(1) if t else '?'
comp=collections.defaultdict(dict); cinfo={}
for (s,scan),(rel,mz,rt) in feat.items():
    cid=(round(mz/MZ_TOL),round(rt/RT_TOL)); comp[cid][s]=max(comp[cid].get(s,0.0),rel)
    if cid not in cinfo: cinfo[cid]=[mz,rt,collections.Counter()]
    cinfo[cid][2].update(ann.get((s,scan),()))
rot_c=[cid for cid,(mz,rt,kc) in cinfo.items() if any(k in rot for k in kc) and len(comp[cid])>=3]

print("="*84); print("DATA QUALITY: rotenoid-annotated compounds present in implausibly many extracts"); print("="*84)
for cid in sorted(rot_c,key=lambda c:-len(comp[c]))[:5]:
    mz,rt,kc=cinfo[cid]
    top=kc.most_common(3)
    print(f"  m/z {mz:9.4f} @ RT {rt:5.2f}  in {len(comp[cid]):4d}/1600 extracts   "
          f"top candidates: {', '.join(k for k,_ in top)}")
print("  -> compounds in >500 extracts are near-certainly misannotations or ubiquitous")
print("     background ions; they must be filtered before attribution.\n")

print("="*84); print("WORKED EXAMPLE: a confounded pair that the method can actually resolve"); print("="*84)
best=None
for a,b in itertools.combinations(sorted(rot_c),2):
    if abs(cinfo[a][0]-cinfo[b][0])<MZ_TOL*2 and abs(cinfo[a][1]-cinfo[b][1])<RT_TOL*2: continue
    Sa,Sb=set(comp[a]),set(comp[b])
    if len(comp[a])>200 or len(comp[b])>200: continue        # drop ubiquitous
    if len(Sa&Sb)<3: continue
    if not (Sa&ACT and Sb&ACT): continue
    onlyA,onlyB=Sa-Sb,Sb-Sa
    if not onlyA or not onlyB: continue
    score=len(Sa&Sb)*min(len(onlyA),len(onlyB))
    if best is None or score>best[0]: best=(score,a,b,Sa,Sb,onlyA,onlyB)
if best:
    _,a,b,Sa,Sb,onlyA,onlyB=best
    print(f"A = m/z {cinfo[a][0]:.4f} @ RT {cinfo[a][1]:.2f}  ({len(Sa)} extracts, {len(Sa&ACT)} active)")
    print(f"B = m/z {cinfo[b][0]:.4f} @ RT {cinfo[b][1]:.2f}  ({len(Sb)} extracts, {len(Sb&ACT)} active)")
    print(f"co-occur in {len(Sa&Sb)} extracts -> confounded\n")
    print("  CO-OCCURRING (uninformative - both present, cannot assign credit):")
    for s in sorted(Sa&Sb,key=lambda x:-TC.get(x,0))[:4]:
        print(f"    {s:12} A={comp[a].get(s,0):.4f} B={comp[b].get(s,0):.4f} "
              f"T.cruzi={TC.get(s,0):6.1f}%  {sp.get(s,'?')}{'  *ACTIVE*' if s in ACT else ''}")
    for lab,S,other in (("A present, B ABSENT",onlyA,b),("B present, A ABSENT",onlyB,a)):
        print(f"\n  {lab} -- THESE ARE THE INFORMATIVE EXPERIMENTS ({len(S)} available):")
        for s in sorted(S,key=lambda x:-TC.get(x,0))[:4]:
            v=comp[a].get(s,0.0) if 'A present' in lab else comp[b].get(s,0.0)
            print(f"    {s:12} area={v:.4f}  T.cruzi={TC.get(s,0):6.1f}%  L6={L6.get(s,0):5.1f}  "
                  f"{sp.get(s,'?')}{'  *ACTIVE*' if s in ACT else ''}")
    accA=[TC.get(s,0) for s in onlyA]; accB=[TC.get(s,0) for s in onlyB]
    print(f"\n  VERDICT from the held-out evidence:")
    print(f"    A-only extracts: median T.cruzi = {st.median(accA):6.1f}%  (n={len(accA)})")
    print(f"    B-only extracts: median T.cruzi = {st.median(accB):6.1f}%  (n={len(accB)})")
    print(f"    -> credit assigns to {'A' if st.median(accA)>st.median(accB) else 'B'}")
else:
    print("no qualifying pair found")
