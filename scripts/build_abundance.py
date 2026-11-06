"""Pass 1: ISDB annotations -> (sample,scan) -> candidate InChIKey2D (+score).
   Pass 2: features -> relative areas, keeping per-sample totals and per-key abundance.
   Writes abundance.tsv + rotenoid_profile.tsv to data/."""
import gzip, re, collections, pickle, sys, pathlib
D = pathlib.Path("data/enpkg"); OUT = pathlib.Path("data"); OUT.mkdir(exist_ok=True)

# --- rotenoid key set + SMILES ---
rot, smiles, npc = set(), {}, {}
cur = None
with gzip.open(D/"structures_metadata.ttl.gz", "rt", errors="replace") as fh:
    for line in fh:
        m = re.match(r"enpkg:([A-Z]{14}) ", line)
        if m: cur = m.group(1)
        if not cur: continue
        s = re.search(r'has_smiles "([^"]+)"', line)
        if s: smiles[cur] = s.group(1)
        c = re.search(r"has_npc_class enpkg:npc_(\w+)", line)
        if c: npc[cur] = c.group(1)
        if "npc_Rotenoids" in line: rot.add(cur)
print(f"rotenoid keys: {len(rot)}", file=sys.stderr)

# --- pass 1: annotations ---
rx_node = re.compile(r"kg/isdb_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_pos\.mgf:scan:(\d+)")
rx_key = re.compile(r"enpkg:([A-Z]{14})\b")
ann = {}            # (sample,scan) -> tuple of candidate keys
cur_id, keys = None, []
def flush():
    if cur_id: ann[cur_id] = tuple(keys)
with gzip.open(D/"isdb_pos.ttl.gz", "rt", errors="replace") as fh:
    for line in fh:
        m = rx_node.search(line)
        if m and "a enpkg:IsdbAnnotation" in line:
            flush(); cur_id, keys = (m.group(1), m.group(2)), []
        elif cur_id: keys += rx_key.findall(line)
flush()
print(f"annotated features: {len(ann)}", file=sys.stderr)

# --- pass 2: feature areas ---
rx_feat = re.compile(r"kg/lcms_feature_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_pos\.mgf:scan:(\d+)> a enpkg:LCMSFeature")
tot_rel = collections.Counter()        # sample -> sum of relative areas (all features)
tot_abs = collections.Counter()
n_feat  = collections.Counter()
rot_rel = collections.Counter()        # sample -> summed relative area of rotenoid-annotated
key_rel = collections.defaultdict(collections.Counter)   # key -> sample -> rel area
ann_rel = collections.Counter()        # sample -> rel area of ANY annotated feature
cur = None; rel = absa = None
def emit():
    if cur is None or rel is None: return
    s = cur[0]
    tot_rel[s] += rel; tot_abs[s] += absa or 0.0; n_feat[s] += 1
    cands = ann.get(cur)
    if cands:
        ann_rel[s] += rel
        r = [k for k in cands if k in rot]
        if r:
            rot_rel[s] += rel
            # split the feature's area evenly across its rotenoid candidates
            for k in r: key_rel[k][s] += rel/len(r)
with gzip.open(D/"features_pos.ttl.gz", "rt", errors="replace") as fh:
    for line in fh:
        m = rx_feat.search(line)
        if m:
            emit(); cur = (m.group(1), m.group(2)); rel = absa = None
        elif cur is not None:
            a = re.search(r'has_relative_feature_area "([-\d.eE+]+)"', line)
            if a: rel = float(a.group(1)); continue
            b = re.search(r'has_feature_area "([-\d.eE+]+)"', line)
            if b: absa = float(b.group(1))
emit()
print(f"samples with features: {len(tot_rel)}", file=sys.stderr)

pickle.dump(dict(tot_rel=dict(tot_rel), rot_rel=dict(rot_rel), n_feat=dict(n_feat),
                 ann_rel=dict(ann_rel), key_rel={k:dict(v) for k,v in key_rel.items()},
                 smiles=smiles, npc=npc, rot=rot),
            open(OUT/"abundance.pkl","wb"))
print("wrote data/abundance.pkl", file=sys.stderr)
