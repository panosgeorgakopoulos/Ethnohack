import gzip,re,collections,pickle,statistics as st,pathlib,math
D=pathlib.Path("data/enpkg")
def canopus(path):
    """ (sample,scan) -> (class, prob) """
    out={}; cur=None; cls=prob=None
    rx=re.compile(r"kg/canopus_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_(?:pos|neg)\.mgf:scan:(\d+)")
    with gzip.open(path,"rt",errors="replace") as fh:
        for line in fh:
            m=rx.search(line)
            if m and "a enpkg:SiriusCanopusAnnotation" in line:
                if cur and cls: out[cur]=(cls,prob or 0.0)
                cur=(m.group(1),m.group(2)); cls=prob=None
            elif cur:
                c=re.search(r"has_canopus_npc_class enpkg:npc_(\w+)",line)
                if c: cls=c.group(1); continue
                p=re.search(r'has_canopus_npc_class_prob "([-\d.eE+]+)"',line)
                if p: prob=float(p.group(1))
    if cur and cls: out[cur]=(cls,prob or 0.0)
    return out
def feats(path,mode):
    out={}; cur=None; rel=None
    rx=re.compile(r"kg/lcms_feature_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_"+mode+r"\.mgf:scan:(\d+)> a enpkg:LCMSFeature")
    with gzip.open(path,"rt",errors="replace") as fh:
        for line in fh:
            m=rx.search(line)
            if m:
                if cur and rel is not None: out[cur]=rel
                cur=(m.group(1),m.group(2)); rel=None
            elif cur is not None:
                a=re.search(r'has_relative_feature_area "([-\d.eE+]+)"',line)
                if a: rel=float(a.group(1))
    if cur and rel is not None: out[cur]=rel
    return out
cp=canopus(D/"canopus_pos.ttl.gz"); fp=feats(D/"features_pos.ttl.gz","pos")
cn=canopus(D/"canopus_neg.ttl.gz"); fn=feats(D/"features_neg.ttl.gz","neg")
print(f"CANOPUS pos {len(cp)} / neg {len(cn)} annotations; features pos {len(fp)} / neg {len(fn)}")
PROB=0.5
def share(cq,fq,cls_filter):
    tot=collections.Counter(); hit=collections.Counter()
    for k,rel in fq.items():
        s=k[0]; tot[s]+=rel
        c=cq.get(k)
        if c and c[1]>=PROB and cls_filter(c[0]): hit[s]+=rel
    return {s:(hit.get(s,0.0)/tot[s] if tot[s] else 0.0) for s in tot}, tot
rot_pos,_=share(cp,fp,lambda c:c=="Rotenoids")
rot_neg,_=share(cn,fn,lambda c:c=="Rotenoids")
A=pickle.load(open("data/abundance.pkl","rb"))
isdb_share={s:(A['rot_rel'].get(s,0.0)/A['ann_rel'][s] if A['ann_rel'].get(s) else 0.0) for s in A['tot_rel']}
ACTIVES=['VGF155_D05','VGF139_H07','VGF146_E08','VGF146_F09','VGF145_G09','VGF150_H08','VGF150_A09','VGF156_A06']
SP={'VGF155_D05':'Desmodium heterophyllum','VGF139_H07':'Pachyrhizus erosus','VGF146_E08':'Cnestis palala',
    'VGF146_F09':'Cnestis palala','VGF145_G09':'Phyllanthus pulcher','VGF150_H08':'Chadsia grevei',
    'VGF150_A09':'Chadsia grevei','VGF156_A06':'Melochia umbellata'}
print("\n=== ISDB vs CANOPUS rotenoid share (prob>=0.5) for the 8 actives ===")
print(f"{'sample':12}{'ISDB_pos':>10}{'CANOPUS_pos':>13}{'CANOPUS_neg':>13}  species")
for s in ACTIVES:
    print(f"{s:12}{isdb_share.get(s,0)*100:>9.2f}%{rot_pos.get(s,0)*100:>12.2f}%{rot_neg.get(s,0)*100:>12.2f}%  {SP[s]}")
bgp=[v for s,v in rot_pos.items() if s not in ACTIVES]
print(f"\nbackground CANOPUS_pos rotenoid share: median {st.median(bgp)*100:.3f}%  mean {st.mean(bgp)*100:.3f}%")
print(f"CANOPUS agrees with ISDB on which actives are rotenoid-bearing: "
      f"{sum(1 for s in ACTIVES if (rot_pos.get(s,0)>0.005)==(isdb_share.get(s,0)>0.005))}/8")

print("\n=== THE 2 UNEXPLAINED ACTIVES: enriched classes vs library background ===")
for s in ['VGF145_G09','VGF156_A06']:
    print(f"\n  {s} ({SP[s]}):")
    for mode,cq,fq in (("pos",cp,fp),("neg",cn,fn)):
        tot=sum(rel for k,rel in fq.items() if k[0]==s)
        if not tot: print(f"    {mode}: no features"); continue
        mine=collections.Counter()
        for k,rel in fq.items():
            if k[0]!=s: continue
            c=cq.get(k)
            if c and c[1]>=PROB: mine[c[0]]+=rel/tot
        # library background per class
        bg=collections.Counter(); bgtot=collections.Counter()
        for k,rel in fq.items():
            bgtot[k[0]]+=rel
            c=cq.get(k)
            if c and c[1]>=PROB: bg[c[0]]+=rel
        BT=sum(bgtot.values())
        rows=[]
        for cls,v in mine.items():
            exp=bg[cls]/BT if BT else 0
            if v>0.02 and exp>0: rows.append((v/exp,v,cls))
        rows.sort(key=lambda x:-x[0])
        print(f"    {mode}: " + "; ".join(f"{c} {v*100:.0f}% ({f:.0f}x)" for f,v,c in rows[:4]) if rows else f"    {mode}: none above 2%")
