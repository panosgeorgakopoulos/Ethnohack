import gzip,re,collections,statistics as st,pathlib
D=pathlib.Path("data/enpkg")
def canopus(p):
    out={};cur=None;cls=prob=None
    rx=re.compile(r"kg/canopus_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_(?:pos|neg)\.mgf:scan:(\d+)")
    with gzip.open(p,"rt",errors="replace") as fh:
        for line in fh:
            m=rx.search(line)
            if m and "a enpkg:SiriusCanopusAnnotation" in line:
                if cur and cls: out[cur]=(cls,prob or 0.0)
                cur=(m.group(1),m.group(2));cls=prob=None
            elif cur:
                c=re.search(r"has_canopus_npc_class enpkg:npc_(\w+)",line)
                if c: cls=c.group(1);continue
                q=re.search(r'has_canopus_npc_class_prob "([-\d.eE+]+)"',line)
                if q: prob=float(q.group(1))
    if cur and cls: out[cur]=(cls,prob or 0.0)
    return out
def feats(p,mode):
    out={};cur=None;rel=None
    rx=re.compile(r"kg/lcms_feature_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_"+mode+r"\.mgf:scan:(\d+)> a enpkg:LCMSFeature")
    with gzip.open(p,"rt",errors="replace") as fh:
        for line in fh:
            m=rx.search(line)
            if m:
                if cur and rel is not None: out[cur]=rel
                cur=(m.group(1),m.group(2));rel=None
            elif cur is not None:
                a=re.search(r'has_relative_feature_area "([-\d.eE+]+)"',line)
                if a: rel=float(a.group(1))
    if cur and rel is not None: out[cur]=rel
    return out
cn=canopus(D/"canopus_neg.ttl.gz"); fn=feats(D/"features_neg.ttl.gz","neg")
cp=canopus(D/"canopus_pos.ttl.gz"); fp=feats(D/"features_pos.ttl.gz","pos")
demo=gzip.open(D/"metadata_demo.ttl.gz","rt",errors="replace").read()
assay=collections.defaultdict(dict)
for n,b in re.findall(r"enpkgmodule:(\S+?) a enpkgmodule:\w+ ;(.*?)\.\n",demo,re.S):
    m=re.search(r'inhibition_percentage "([-\d.eE+]+)"',b)
    if not m: continue
    for suf in ("_Tcruzi_10ugml","_L6_10ugml"):
        if n.endswith(suf): assay[n[:-len(suf)]][suf.strip('_')]=float(m.group(1))
TC={s:a.get('Tcruzi_10ugml',0.) for s,a in assay.items()};L6={s:a.get('L6_10ugml',0.) for s,a in assay.items()}
ACT={s for s in TC if TC[s]>80 and L6.get(s,100)<50}

print("="*80);print("A) QUINOLINE ALKALOID LEAD in Melochia umbellata -- verification");print("="*80)
S='VGF156_A06'
rows=[(rel,cn[k][1],k[1]) for k,rel in fn.items() if k[0]==S and cn.get(k,('',0))[0]=="Quinoline_alkaloids"]
tot=sum(rel for k,rel in fn.items() if k[0]==S)
print(f"  features classed Quinoline_alkaloids (any prob): {len(rows)}; sample total rel area {tot:.3f}")
for rel,pr,scan in sorted(rows,reverse=True)[:6]:
    print(f"    scan {scan:>5}  relArea={rel:.4f} ({rel/tot*100:5.2f}% of sample)  CANOPUS prob={pr:.2f}")
lib=collections.Counter(); libtot=collections.Counter()
for k,rel in fn.items():
    libtot[k[0]]+=rel
    c=cn.get(k)
    if c and c[0]=="Quinoline_alkaloids" and c[1]>=0.5: lib[k[0]]+=rel
shares=sorted(((lib.get(s,0)/libtot[s],s) for s in libtot if libtot[s]>0),reverse=True)
print(f"\n  Library ranking by quinoline-alkaloid share (neg mode), top 8:")
for sh,s in shares[:8]:
    print(f"    {s:12} {sh*100:6.2f}%   T.cruzi={TC.get(s,0):6.1f}%  L6={L6.get(s,0):5.1f}"
          f"{'   *SELECTIVE ACTIVE*' if s in ACT else ''}")
rank=[s for _,s in shares].index(S)+1
print(f"\n  >>> {S} ranks {rank}/{len(shares)} in the library for this class.")
nz=[sh for sh,_ in shares if sh>0]
print(f"  >>> extracts with ANY quinoline-alkaloid signal: {len(nz)}/{len(shares)}")

print("\n"+"="*80);print("B) DOSE-RESPONSE under CANOPUS (was ISDB-based)");print("="*80)
def shr(cq,fq,cls):
    tot=collections.Counter();hit=collections.Counter()
    for k,rel in fq.items():
        tot[k[0]]+=rel
        c=cq.get(k)
        if c and c[1]>=0.5 and c[0]==cls: hit[k[0]]+=rel
    return {s:(hit.get(s,0)/tot[s] if tot[s] else 0) for s in tot}
rp=shr(cp,fp,"Rotenoids")
print(f"  {'sample':12}{'organ':13}{'CANOPUS rot share':>19}{'T.cruzi%':>10}")
for s,o in (('VGF139_H07','leaves'),('VGF139_A08','woody_stems'),('VGF139_B08','roots')):
    print(f"  {s:12}{o:13}{rp.get(s,0)*100:>18.2f}%{TC.get(s,0):>10.1f}")
print("\n  Cnestis palala organ series:")
for s,o in (('VGF146_E08','roots'),('VGF146_F09','woody_stems'),('VGF147_F02','leaves')):
    print(f"  {s:12}{o:13}{rp.get(s,0)*100:>18.2f}%{TC.get(s,0):>10.1f}")
