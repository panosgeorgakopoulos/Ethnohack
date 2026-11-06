import pickle, gzip, re, math, collections, statistics as st, pathlib, itertools
D=pathlib.Path("data/enpkg"); A=pickle.load(open("data/abundance.pkl","rb"))
keyr,smiles,rot,annr=A['key_rel'],A['smiles'],A['rot'],A['ann_rel']
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
SAMP=sorted(TC)
def vec(k): 
    d=keyr.get(k,{}); return [d.get(s,0.0) for s in SAMP]
def pearson(a,b):
    n=len(a); ma,mb=sum(a)/n,sum(b)/n
    num=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/den if den else 0.0

# candidate rotenoids: those present in >=2 extracts
cands=[k for k in rot if sum(1 for s in SAMP if keyr.get(k,{}).get(s,0)>0)>=2]
print(f"rotenoid candidates present in >=2 extracts: {len(cands)}")
pres={k:{s for s in SAMP if keyr.get(k,{}).get(s,0)>0} for k in cands}

print("\n"+"="*80); print("CO-OCCURRENCE: the confounded pairs, ranked by Jaccard overlap"); print("="*80)
pairs=[]
for a,b in itertools.combinations(cands,2):
    inter=pres[a]&pres[b]
    if len(inter)<2: continue
    union=pres[a]|pres[b]
    j=len(inter)/len(union)
    r=pearson(vec(a),vec(b))
    pairs.append((j,r,a,b,len(inter),len(pres[a]),len(pres[b])))
pairs.sort(key=lambda x:-x[0])
print(f"{'Jaccard':>8}{'Pearson_r':>11}  {'cmpd A':16}{'cmpd B':16}{'A&B':>5}{'|A|':>5}{'|B|':>5}  in actives")
for j,r,a,b,ni,na,nb in pairs[:10]:
    na_act=len(pres[a]&ACT); nb_act=len(pres[b]&ACT)
    print(f"{j:>8.2f}{r:>11.3f}  {a:16}{b:16}{ni:>5}{na:>5}{nb:>5}  A:{na_act} B:{nb_act}")

print("\n"+"="*80); print("CAN WE DECORRELATE? samples that separate the top confounded pair"); print("="*80)
if pairs:
    j,r,a,b,*_ = pairs[0]
    print(f"Pair: {a}  vs  {b}   (Jaccard {j:.2f}, Pearson r={r:.3f})")
    print(f"  A = {smiles.get(a,'?')[:72]}")
    print(f"  B = {smiles.get(b,'?')[:72]}")
    rows=[]
    for s in SAMP:
        va,vb = keyr.get(a,{}).get(s,0.0), keyr.get(b,{}).get(s,0.0)
        if va>0 or vb>0: rows.append((va-vb,va,vb,s))
    rows.sort(key=lambda x:-x[0])
    print(f"\n  {'sample':12}{'A_area':>9}{'B_area':>9}{'A-B':>9}{'T.cruzi%':>10}{'L6%':>7}  species")
    for d,va,vb,s in rows[:4]+[('...',)*4]+rows[-4:] if len(rows)>8 else rows:
        if d=='...': print("   ..."); continue
        m=" *ACT*" if s in ACT else ""
        print(f"  {s:12}{va:>9.4f}{vb:>9.4f}{d:>9.4f}{TC.get(s,0):>10.1f}{L6.get(s,0):>7.1f}  {sp.get(s,'?')}{m}")
    sep=[x for x in rows if (x[1]>0 and x[2]==0) or (x[2]>0 and x[1]==0)]
    print(f"\n  DECORRELATING SAMPLES (one present, other absent): {len(sep)} of {len(rows)}")
    for d,va,vb,s in sep[:8]:
        w = "A only" if vb==0 else "B only"
        print(f"    {s:12} {w:8} T.cruzi={TC.get(s,0):6.1f}%  {sp.get(s,'?')}")
