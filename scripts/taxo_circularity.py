"""ISDB reweights candidate annotations by TAXONOMY. If rotenoid calls in Fabaceae
are driven by taxo_score rather than spectra, 'Fabaceae extracts contain rotenoids'
is partly circular. Test: do rotenoid calls survive on spectral evidence alone?"""
import gzip,re,collections,pickle,statistics as st,pathlib
D=pathlib.Path("data/enpkg")
A=pickle.load(open("data/abundance.pkl","rb")); rot=A['rot']
rx=re.compile(r"kg/isdb_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_pos\.mgf:scan:(\d+)")
rxk=re.compile(r"enpkg:([A-Z]{14})\b")
recs=[]; cur=None; keys=[]; sc={}
def fl():
    if cur and keys: recs.append((cur,tuple(keys),dict(sc)))
with gzip.open(D/"isdb_pos.ttl.gz","rt",errors="replace") as fh:
    for line in fh:
        m=rx.search(line)
        if m and "a enpkg:IsdbAnnotation" in line:
            fl(); cur=(m.group(1),m.group(2)); keys=[]; sc={}
        elif cur:
            k=rxk.findall(line)
            if k: keys+=k
            for f in ("spectral_score","taxo_score","consistency_score","final_score"):
                g=re.search(r'has_'+f+r' "([-\d.eE+]+)"',line)
                if g: sc[f]=float(g.group(1))
fl()
print(f"ISDB annotation records parsed: {len(recs)}")
rotrec=[r for r in recs if any(k in rot for k in r[1])]
other=[r for r in recs if not any(k in rot for k in r[1])]
def stat(rs,f):
    v=[r[2].get(f,0.0) for r in rs if f in r[2]]
    return (st.median(v),st.mean(v),len(v)) if v else (0,0,0)
print(f"\n{'score':20}{'ROTENOID calls':>26}{'all other calls':>26}")
print(f"{'':20}{'median':>10}{'mean':>8}{'n':>8}{'median':>10}{'mean':>8}{'n':>8}")
for f in ("spectral_score","taxo_score","consistency_score","final_score"):
    a=stat(rotrec,f); b=stat(other,f)
    print(f"{f:20}{a[0]:>10.3f}{a[1]:>8.3f}{a[2]:>8}{b[0]:>10.3f}{b[1]:>8.3f}{b[2]:>8}")

print("\n--- How much of a rotenoid call's final score is TAXONOMIC? ---")
fr=[]
for r in rotrec:
    fs=r[2].get('final_score',0); ts=r[2].get('taxo_score',0)
    if fs>0: fr.append(ts/fs)
print(f"  taxo_score / final_score for rotenoid calls: median {st.median(fr):.1%}, mean {st.mean(fr):.1%} (n={len(fr)})")
fo=[r[2]['taxo_score']/r[2]['final_score'] for r in other
    if r[2].get('final_score',0)>0 and 'taxo_score' in r[2]]
print(f"  same ratio for all other calls:              median {st.median(fo):.1%}, mean {st.mean(fo):.1%} (n={len(fo)})")

print("\n--- Would rotenoid calls survive WITHOUT taxonomic reweighting? ---")
for thr in (0.0,0.2,0.4):
    surv=sum(1 for r in rotrec if r[2].get('spectral_score',0)>thr)
    print(f"  spectral_score > {thr:.1f}: {surv:6d}/{len(rotrec)} rotenoid calls "
          f"({100*surv/len(rotrec):5.1f}%) retained")
zero=sum(1 for r in rotrec if r[2].get('spectral_score',0)==0.0)
print(f"\n  >>> rotenoid calls with ZERO spectral support (pure taxonomy/consistency): "
      f"{zero}/{len(rotrec)} = {100*zero/len(rotrec):.1f}%")
zo=sum(1 for r in other if r[2].get('spectral_score',0)==0.0)
print(f"  >>> same for all other calls: {zo}/{len(other)} = {100*zo/len(other):.1f}%")
