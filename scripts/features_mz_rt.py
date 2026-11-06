"""Extract per-feature m/z, RT, relative area for ANNOTATED features, then cluster
features across samples into consensus compounds by (parent_mass, RT) proximity."""
import gzip, re, pickle, collections, pathlib, sys
D=pathlib.Path("data/enpkg")
rx_node=re.compile(r"kg/isdb_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_pos\.mgf:scan:(\d+)")
rx_key=re.compile(r"enpkg:([A-Z]{14})\b")
ann={}; cur=None; keys=[]
def fl():
    if cur: ann[cur]=tuple(keys)
with gzip.open(D/"isdb_pos.ttl.gz","rt",errors="replace") as fh:
    for line in fh:
        m=rx_node.search(line)
        if m and "a enpkg:IsdbAnnotation" in line: fl(); cur=(m.group(1),m.group(2)); keys=[]
        elif cur: keys+=rx_key.findall(line)
fl()
rx_f=re.compile(r"kg/lcms_feature_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_pos\.mgf:scan:(\d+)> a enpkg:LCMSFeature")
feat={}; cur=None; rel=mz=rt=None
def ef():
    if cur and cur in ann and None not in (rel,mz,rt): feat[cur]=(rel,mz,rt)
with gzip.open(D/"features_pos.ttl.gz","rt",errors="replace") as fh:
    for line in fh:
        m=rx_f.search(line)
        if m: ef(); cur=(m.group(1),m.group(2)); rel=mz=rt=None
        elif cur is not None:
            for pat,var in ((r'has_relative_feature_area "([-\d.eE+]+)"','rel'),
                            (r'has_parent_mass "([-\d.eE+]+)"','mz'),
                            (r'has_retention_time "([-\d.eE+]+)"','rt')):
                g=re.search(pat,line)
                if g:
                    v=float(g.group(1))
                    if var=='rel': rel=v
                    elif var=='mz': mz=v
                    else: rt=v
                    break
ef()
print(f"annotated features with mz/RT: {len(feat)}",file=sys.stderr)
pickle.dump({'feat':feat,'ann':ann},open("data/features_mzrt.pkl","wb"))
