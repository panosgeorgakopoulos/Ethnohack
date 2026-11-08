"""ENPKG (Zenodo 7824642) Turtle -> tidy Python structures. Stdlib only.

Files in data/enpkg/ are used if present; only missing ones are downloaded.
Each loader caches its result to data/cache/<name>[_<mode>].pkl.
"""
import shutil
import gzip, pickle, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "enpkg"
CACHE = ROOT / "data" / "cache"
ZENODO = "https://zenodo.org/api/records/7824642/files/{}/content"
FILES = ["metadata_enpkg.ttl.gz", "metadata_demo.ttl.gz", "structures_metadata.ttl.gz",
         "isdb_pos.ttl.gz", "isdb_neg.ttl.gz", "features_pos.ttl.gz", "features_neg.ttl.gz",
         "canopus_pos.ttl.gz", "canopus_neg.ttl.gz"]
ASSAY_SUFFIXES = ("Tcruzi_10ugml", "Tbruceirhod_10ugml", "Tbruceirhod_2ugml",
                  "Ldonovani_10ugml", "Ldonovani_2ugml", "L6_10ugml")

_NUM = r'"([-\d.eE+]+)"'


def _opener():
    """Some interpreters ship without a usable system trust store, so an
    otherwise-correct download dies with CERTIFICATE_VERIFY_FAILED. Prefer
    certifi's bundle when it is available and fall back to the default."""
    try:
        import ssl, certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    except Exception:
        return urllib.request.build_opener()


def _path(name):
    """Local path of an ENPKG file, downloading it only if absent."""
    p = DATA / name
    if not p.exists():
        DATA.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".part")
        with _opener().open(ZENODO.format(name)) as r, open(tmp, "wb") as out:
            shutil.copyfileobj(r, out)
        tmp.rename(p)
    return p


def _lines(name):
    return gzip.open(_path(name), "rt", errors="replace")


def _text(name):
    with _lines(name) as fh:
        return fh.read()


def _cached(name, fn):
    f = CACHE / f"{name}.pkl"
    if f.exists():
        with open(f, "rb") as fh:
            return pickle.load(fh)
    out = fn()
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(f, "wb") as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return out


def _check_mode(mode):
    if mode not in ("pos", "neg"):
        raise ValueError("mode must be 'pos' or 'neg'")


def _node_rx(kind, mode):
    return re.compile(r"kg/" + kind + r":[^:]+:(VGF\d+_[A-Z]\d+)_features_ms2_" + mode
                      + r"\.mgf:scan:(\d+)>? a enpkg:(\w+)")


# ---------------------------------------------------------------- samples
def load_samples():
    """{sample_id: {"species","wikidata","organ","tissue"}}"""
    def build():
        meta, demo = _text("metadata_enpkg.ttl.gz"), _text("metadata_demo.ttl.gz")
        raw = {}
        for rm, body in re.findall(r"enpkg:(\S+) a enpkg:RawMaterial ;(.*?)\.\n", meta, re.S):
            proc = re.search(r"has_lab_process enpkg:(\S+)", body)
            if not proc:
                continue
            tax = re.search(r'submitted_taxon "([^"]+)"', body)
            wd = re.search(r"has_wd_id wd:(\S+)", body)
            raw[rm] = (proc.group(1), tax.group(1) if tax else None, wd.group(1) if wd else None)
        organ = {}
        for rm, body in re.findall(r"enpkg:(\S+) enpkgmodule:has_broad_organe(.*?)\.\n", demo, re.S):
            def g(p):
                m = re.search(r"enpkgmodule:" + p + r" enpkgmodule:(\w+)", body)
                return m.group(1) if m else None
            organ[rm] = (g("has_organe"), g("has_tissue"))
        return {s: {"species": sp, "wikidata": wd,
                    "organ": organ.get(rm, (None, None))[0],
                    "tissue": organ.get(rm, (None, None))[1]}
                for rm, (s, sp, wd) in raw.items()}
    return _cached("samples", build)


# ----------------------------------------------------------------- assays
def load_assays():
    """{sample_id: {assay_name: inhibition_percentage}}"""
    def build():
        demo = _text("metadata_demo.ttl.gz")
        out = {}
        for node, body in re.findall(r"enpkgmodule:(\S+?) a enpkgmodule:\w+ ;(.*?)\.\n", demo, re.S):
            m = re.search(r'inhibition_percentage "([-\d.eE+]+)"', body)
            if not m:
                continue
            for suf in ASSAY_SUFFIXES:
                if node.endswith("_" + suf):
                    out.setdefault(node[: -len(suf) - 1], {})[suf] = float(m.group(1))
                    break
        return out
    return _cached("assays", build)


# --------------------------------------------------------------- features
def load_features(mode):
    """{(sample, scan): {"area","rel_area","mz","rt"}}"""
    _check_mode(mode)
    def build():
        rx = _node_rx("lcms_feature_mzspec", mode)
        pats = (("area", re.compile(r'has_feature_area ' + _NUM)),
                ("rel_area", re.compile(r'has_relative_feature_area ' + _NUM)),
                ("mz", re.compile(r'has_parent_mass ' + _NUM)),
                ("rt", re.compile(r'has_retention_time ' + _NUM)))
        out, cur, rec = {}, None, {}

        def emit():
            if cur is not None and len(rec) == 4:
                out[cur] = rec
        with _lines(f"features_{mode}.ttl.gz") as fh:
            for line in fh:
                if "has_" not in line and "a enpkg:LCMSFeature" not in line:
                    continue
                m = rx.search(line)
                if m:
                    emit()
                    cur, rec = ((m.group(1), m.group(2)), {}) if m.group(3) == "LCMSFeature" else (None, {})
                elif cur is not None:
                    for k, p in pats:
                        g = p.search(line)
                        if g:
                            rec[k] = float(g.group(1))
                            break
        emit()
        return out
    return _cached(f"features_{mode}", build)


# ------------------------------------------------------------------- ISDB
def load_isdb(mode):
    """{(sample, scan): [{"key","spectral_score","taxo_score","final_score"}]}"""
    _check_mode(mode)
    def build():
        rx = _node_rx("isdb_mzspec", mode)
        rx_key = re.compile(r"enpkg:([A-Z]{14})\b")
        sc = {"spectral_score": re.compile(r'has_spectral_score ' + _NUM),
              "taxo_score": re.compile(r'has_taxo_score ' + _NUM),
              "final_score": re.compile(r'has_final_score ' + _NUM)}
        out, cur, keys, scores = {}, None, [], {}

        def emit():
            if cur is not None:
                out[cur] = [{"key": k, "spectral_score": scores.get("spectral_score"),
                             "taxo_score": scores.get("taxo_score"),
                             "final_score": scores.get("final_score")} for k in keys]
        with _lines(f"isdb_{mode}.ttl.gz") as fh:
            for line in fh:
                m = rx.search(line)
                if m and m.group(3) == "IsdbAnnotation":
                    emit()
                    cur, keys, scores = (m.group(1), m.group(2)), [], {}
                elif cur is not None:
                    if "has_InChIkey2D" in line or line.startswith("        enpkg:"):
                        keys += rx_key.findall(line)
                    else:
                        for k, p in sc.items():
                            g = p.search(line)
                            if g:
                                scores[k] = float(g.group(1))
                                break
        emit()
        return out
    return _cached(f"isdb_{mode}", build)


# ---------------------------------------------------------------- CANOPUS
def load_canopus(mode):
    """{(sample, scan): {"npc_class","prob"}}"""
    _check_mode(mode)
    def build():
        rx = _node_rx("canopus_mzspec", mode)
        rc = re.compile(r"has_canopus_npc_class enpkg:npc_(\w+)")
        rp = re.compile(r'has_canopus_npc_class_prob ' + _NUM)
        out, cur, cls, prob = {}, None, None, None
        with _lines(f"canopus_{mode}.ttl.gz") as fh:
            for line in fh:
                m = rx.search(line)
                if m and m.group(3) == "SiriusCanopusAnnotation":
                    if cur and cls:
                        out[cur] = {"npc_class": cls, "prob": prob or 0.0}
                    cur, cls, prob = (m.group(1), m.group(2)), None, None
                elif cur is not None:
                    c = rc.search(line)
                    if c:
                        cls = c.group(1)
                        continue
                    p = rp.search(line)
                    if p:
                        prob = float(p.group(1))
        if cur and cls:
            out[cur] = {"npc_class": cls, "prob": prob or 0.0}
        return out
    return _cached(f"canopus_{mode}", build)


# ------------------------------------------------------------- structures
def load_structures():
    """{inchikey2d: {"smiles", "npc_class", "npc_superclass", "npc_pathway"}}

    The three npc_* fields are LISTS (multi-valued in the Turtle, comma-continued
    across lines; empty list when absent). Records without SMILES are dropped.
    """
    def build():
        rs = re.compile(r'has_smiles "([^"]+)"')
        item = r"(?:enpkg:npc_\w+|<[^>]*npc_[^>]*>)"   # names with commas use full IRIs
        rx = {f: re.compile(r"has_npc_" + f + r"\s+(" + item + r"(?:\s*,\s*" + item + r")*)")
              for f in ("class", "superclass", "pathway")}
        rv = re.compile(r"(?:enpkg:npc_(\w+)|<[^>]*?kg/npc_([^>]+)>)")
        start = re.compile(r"enpkg:([A-Z]{14}) ")
        out = {}

        def emit(key, buf):
            if key is None:
                return
            body = "".join(buf)
            s = rs.search(body)
            if not s:
                return
            rec = {"smiles": s.group(1)}
            for f, p in rx.items():
                rec["npc_" + f] = [a or b for m in p.finditer(body) for a, b in rv.findall(m.group(1))]
            out[key] = rec
        key, buf = None, []
        with _lines("structures_metadata.ttl.gz") as fh:
            for line in fh:
                m = start.match(line)
                if m:
                    emit(key, buf)
                    key, buf = m.group(1), []
                if key is not None and not line.strip():
                    emit(key, buf)      # blank line ends the record
                    key, buf = None, []
                elif key is not None:
                    buf.append(line)
        emit(key, buf)
        return out
    return _cached("structures", build)


def main():
    """Fetch the frozen ENPKG inputs; existing files are reused."""
    for name in FILES:
        path = _path(name)
        print(f"{name}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
