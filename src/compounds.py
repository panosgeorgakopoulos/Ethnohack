"""Consensus compounds from annotated LC-MS features. Stdlib only.

Cluster key (round(mz/0.01), round(rt/0.20)) across all samples. Per-sample abundance
is the max rel_area of member features. Compounds in more than 15% of the constant
1600-extract library (>240) or in fewer than 3 extracts are dropped.

annotation selects which features enter the compound universe: "isdb" (default),
"canopus", or "union" (either). The default is "isdb" because it reproduces the
validated benchmark universe (12,553 compounds in pos); use "union" for real-case
lead generation. It is NOT a claim that ISDB is the better annotation source (ISDB
carries a taxonomic prior; CANOPUS is the preferred class source).
"""
import pickle
from collections import defaultdict

from . import enpkg_io as io

N_LIBRARY = 1600
MAX_EXTRACTS = int(0.15 * N_LIBRARY)   # 240
MIN_EXTRACTS = 3
LAST_STATS = {}
_KEEP = {"isdb": lambda i, c: i, "canopus": lambda i, c: c, "union": lambda i, c: i or c}


def _build(mode, annotation):
    feats, canopus, isdb = io.load_features(mode), io.load_canopus(mode), io.load_isdb(mode)
    clusters = defaultdict(list)
    for fid, f in feats.items():
        if _KEEP[annotation](fid in isdb, fid in canopus):
            clusters[(round(f["mz"] / 0.01), round(f["rt"] / 0.20))].append(fid)
    out, dropped_ubiq, dropped_rare = {}, 0, 0
    for members in clusters.values():
        ab = {}
        for fid in members:
            s, r = fid[0], feats[fid]["rel_area"]
            if r > ab.get(s, float("-inf")):
                ab[s] = r
        if len(ab) > MAX_EXTRACTS:
            dropped_ubiq += 1
            continue
        if len(ab) < MIN_EXTRACTS:
            dropped_rare += 1
            continue
        best = None
        for fid in members:
            c = canopus.get(fid)
            if c and (best is None or c["prob"] > best[1]):
                best = (c["npc_class"], c["prob"])
        keys, seen = [], set()
        for fid in members:
            for a in isdb.get(fid, ()):
                sc = a["spectral_score"]
                if sc is not None and sc > 0 and a["key"] not in seen:
                    seen.add(a["key"])
                    keys.append(a["key"])
        out[len(out)] = {"abundance": ab,
                         "mz": sum(feats[m]["mz"] for m in members) / len(members),
                         "rt": sum(feats[m]["rt"] for m in members) / len(members),
                         "canopus": best, "isdb_keys": keys}
    stats = {"clusters": len(clusters), "dropped_ubiquitous": dropped_ubiq,
             "dropped_rare": dropped_rare, "kept": len(out)}
    return out, stats


def build_compounds(mode="pos", annotation="isdb"):
    """{cid: {"abundance":{sample:rel_area}, "mz","rt","canopus":(cls,prob)|None, "isdb_keys":[...]}}"""
    io._check_mode(mode)
    if annotation not in _KEEP:
        raise ValueError('annotation must be "isdb", "canopus" or "union"')
    suffix = "" if annotation == "isdb" else "_" + annotation
    f = io.CACHE / f"compounds_{mode}{suffix}.pkl"
    if f.exists():
        with open(f, "rb") as fh:
            out, stats = pickle.load(fh)
    else:
        out, stats = _build(mode, annotation)
        io.CACHE.mkdir(parents=True, exist_ok=True)
        with open(f, "wb") as fh:
            pickle.dump((out, stats), fh, protocol=pickle.HIGHEST_PROTOCOL)
    LAST_STATS.clear()
    LAST_STATS.update(stats)
    return out


def compound_matrix(compounds):
    """-> (cids, samples, {(cid,sample): rel_area}); samples = all 1600 library extracts."""
    samples = sorted(io.load_samples())
    cids = list(compounds)
    mat = {(c, s): a for c in cids for s, a in compounds[c]["abundance"].items()}
    return cids, samples, mat
