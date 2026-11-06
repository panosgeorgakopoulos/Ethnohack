import pickle, gzip, re, math, collections, statistics as st, pathlib
D=pathlib.Path("data/enpkg")
A=pickle.load(open("data/abundance.pkl","rb"))
tot,rotr,nf,annr,keyr,smiles,npc,rot = (A['tot_rel'],A['rot_rel'],A['n_feat'],
                                        A['ann_rel'],A['key_rel'],A['smiles'],A['npc'],A['rot'])
# bioassays
demo=gzip.open(D/"metadata_demo.ttl.gz","rt",errors="replace").read()
assay=collections.defaultdict(dict)
for node,body in re.findall(r"enpkgmodule:(\S+?) a enpkgmodule:\w+ ;(.*?)\.\n",demo,re.S):
    m=re.search(r'inhibition_percentage "([-\d.eE+]+)"',body)
    if not m: continue
    for suf in ("_Tcruzi_10ugml","_Tbruceirhod_10ugml","_Tbruceirhod_2ugml",
                "_Ldonovani_10ugml","_Ldonovani_2ugml","_L6_10ugml"):
        if node.endswith(suf): assay[node[:-len(suf)]][suf.strip('_')]=float(m.group(1)); break
TC={s:a.get('Tcruzi_10ugml',0.0) for s,a in assay.items()}
L6={s:a.get('L6_10ugml',0.0) for s,a in assay.items()}
ACT={s for s in TC if TC[s]>80 and L6.get(s,100)<50}
# species/organ
meta=gzip.open(D/"metadata_enpkg.ttl.gz","rt",errors="replace").read()
sp={}; rm2v={}
for rm,body in re.findall(r"enpkg:(\S+) a enpkg:RawMaterial ;(.*?)\.\n",meta,re.S):
    p=re.search(r"has_lab_process enpkg:(\S+)",body); t=re.search(r'submitted_taxon "([^"]+)"',body)
    if p: sp[p.group(1)]=t.group(1) if t else '?'; rm2v[rm]=p.group(1)
org={}
for rm,body in re.findall(r"enpkg:(\S+) enpkgmodule:has_broad_organe(.*?)\.\n",demo,re.S):
    o=re.search(r"enpkgmodule:has_organe enpkgmodule:(\w+)",body)
    if rm in rm2v: org[rm2v[rm]]=o.group(1) if o else '?'

def frac(s):   # rotenoid share of ANNOTATED signal (ionisation-comparable)
    return rotr.get(s,0.0)/annr[s] if annr.get(s) else 0.0

print("="*78); print("1. ABUNDANCE vs COUNT  -- the P. erosus puzzle"); print("="*78)
PE=['VGF139_H07','VGF139_A08','VGF139_B08']
print(f"{'sample':12}{'organ':13}{'T.cruzi%':>9}{'rot_count':>10}{'rot_relArea':>13}{'rot_share':>11}")
for s in PE:
    cnt=sum(1 for k in rot if keyr.get(k,{}).get(s))
    print(f"{s:12}{org.get(s,'?'):13}{TC.get(s,0):>9.1f}{cnt:>10}{rotr.get(s,0):>13.4f}{frac(s)*100:>10.2f}%")

print("\n"+"="*78); print("2. DOES ROTENOID ABUNDANCE TRACK ACTIVITY ACROSS ALL 1600?"); print("="*78)
xs=[(frac(s),TC.get(s,0.0),s) for s in tot if s in TC]
def spearman(p):
    n=len(p)
    rx={v:i for i,(v,_) in enumerate(sorted(((a,i) for i,(a,b) in enumerate(p))))}
    ry={v:i for i,(v,_) in enumerate(sorted(((b,i) for i,(a,b) in enumerate(p))))}
    def ranks(vals):
        order=sorted(range(n),key=lambda i:vals[i]); r=[0]*n; i=0
        while i<n:
            j=i
            while j+1<n and vals[order[j+1]]==vals[order[i]]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1): r[order[k]]=avg
            i=j+1
        return r
    a=ranks([x for x,_ in p]); b=ranks([y for _,y in p])
    ma,mb=sum(a)/n,sum(b)/n
    num=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    den=math.sqrt(sum((a[i]-ma)**2 for i in range(n))*sum((b[i]-mb)**2 for i in range(n)))
    return num/den if den else 0.0
pairs=[(f,t) for f,t,_ in xs]
rho=spearman(pairs)
print(f"Spearman(rotenoid share, T.cruzi %) over n={len(pairs)}: rho = {rho:.3f}")
withrot=[t for f,t,_ in xs if f>0]; without=[t for f,t,_ in xs if f==0]
print(f"  extracts WITH rotenoid signal   n={len(withrot):4d}  median T.cruzi = {st.median(withrot):6.1f}%  mean={st.mean(withrot):.1f}%")
print(f"  extracts WITHOUT                n={len(without):4d}  median T.cruzi = {st.median(without):6.1f}%  mean={st.mean(without):.1f}%")
top=sorted(xs,key=lambda z:-z[0])[:15]
print(f"\n  Top-15 extracts by rotenoid share -> how many are selective actives? "
      f"{sum(1 for f,t,s in top if s in ACT)}/15")
print(f"  {'sample':12}{'share':>8}{'T.cruzi%':>10}{'L6%':>7}  species / organ")
for f,t,s in top:
    mark=" *ACTIVE*" if s in ACT else ""
    print(f"  {s:12}{f*100:>7.2f}%{t:>10.1f}{L6.get(s,0):>7.1f}  {sp.get(s,'?')} / {org.get(s,'?')}{mark}")

print("\n"+"="*78); print("3. WHICH ROTENOIDS? (abundance-ranked in the 6 rotenoid actives)"); print("="*78)
ROTACT=[s for s in ACT if rotr.get(s,0)>0]
agg=collections.Counter()
for k in rot:
    for s in ROTACT: agg[k]+=keyr.get(k,{}).get(s,0.0)
for k,v in agg.most_common(8):
    pres=[s for s in ROTACT if keyr.get(k,{}).get(s,0)>0]
    tag=" <<< ROTENONE" if k=="JUVIOZPCNVVQFO" else ""
    print(f"  {k}  relArea={v:7.4f}  in {len(pres)}/6 actives{tag}")
    print(f"      {smiles.get(k,'?')[:76]}")
