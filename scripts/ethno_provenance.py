#!/usr/bin/env python3
"""
Ethnobotanical provenance layer for the EthnoHack Track 2 project.

Joins the ENPKG 1,600-extract anti-trypanosomatid screen to plant identity and
plant organ, so that screening hits can be read against documented traditional
use of the same species and the same plant part.

Data: Zenodo 7824642 (CC-BY-4.0), Gaudry et al., ACS Cent Sci 2024.
      https://zenodo.org/records/7824642

Run:  python3 scripts/ethno_provenance.py [--data-dir DIR]
      Downloads ~22 MB on first run, then caches.

Self-check: asserts the two published results this reproduces
      (8 selective T. cruzi actives; 6 of them rotenoid-bearing).
"""
import argparse, collections, gzip, pathlib, re, sys, urllib.request

ZENODO = "https://zenodo.org/api/records/7824642/files/{}/content"
FILES = ["metadata_enpkg.ttl.gz", "metadata_demo.ttl.gz",
         "structures_metadata.ttl.gz", "isdb_pos.ttl.gz"]

# Assay thresholds. ponytail: the published screen's own cutoffs, not tuned by us.
ACTIVE_CUT, CYTOTOX_CUT = 80.0, 50.0

RX_KEY = re.compile(r"enpkg:([A-Z]{14})\b")
RX_ISDB_NODE = re.compile(r"kg/isdb_mzspec:[^:]+:(VGF\d+_[A-Z]\d+)_features")


def fetch(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = data_dir / name
        if dest.exists():
            continue
        print(f"  downloading {name} ...", file=sys.stderr)
        urllib.request.urlretrieve(ZENODO.format(name), dest)
    return data_dir


def read(path):
    return gzip.open(path, "rt", errors="replace").read()


def bioassays(demo_text):
    """sample -> {assay: inhibition_percentage}"""
    out = collections.defaultdict(dict)
    suffixes = ("_Tcruzi_10ugml", "_Tbruceirhod_10ugml", "_Tbruceirhod_2ugml",
                "_Ldonovani_10ugml", "_Ldonovani_2ugml", "_L6_10ugml")
    for node, body in re.findall(r"enpkgmodule:(\S+?) a enpkgmodule:\w+ ;(.*?)\.\n",
                                 demo_text, re.S):
        m = re.search(r'inhibition_percentage "([-\d.eE+]+)"', body)
        if not m:
            continue
        for suf in suffixes:
            if node.endswith(suf):
                out[node[: -len(suf)]][suf.strip("_")] = float(m.group(1))
                break
    return out


def rotenoid_keys(struct_text):
    """InChIKey2D values classified by NPClassifier as rotenoids."""
    keys, cur = set(), None
    for line in struct_text.splitlines():
        m = re.match(r"enpkg:([A-Z]{14}) ", line)
        if m:
            cur = m.group(1)
        if cur and "npc_Rotenoids" in line:
            keys.add(cur)
            cur = None
    return keys


def rotenoid_counts(isdb_path, rot):
    """sample -> (features with >=1 rotenoid candidate, annotated features)"""
    n_rot, n_feat = collections.Counter(), collections.Counter()
    cur, keys = None, []

    def flush():
        if cur is None:
            return
        n_feat[cur] += 1
        if any(k in rot for k in keys):
            n_rot[cur] += 1

    with gzip.open(isdb_path, "rt", errors="replace") as fh:
        for line in fh:
            m = RX_ISDB_NODE.search(line)
            if m and "a enpkg:IsdbAnnotation" in line:
                flush()
                cur, keys = m.group(1), []
            elif cur:
                keys += RX_KEY.findall(line)
    flush()
    return n_rot, n_feat


def taxonomy(meta_text, demo_text):
    """sample -> (species, wikidata_id, organ, tissue)"""
    raw = {}
    for rm, body in re.findall(r"enpkg:(\S+) a enpkg:RawMaterial ;(.*?)\.\n",
                               meta_text, re.S):
        proc = re.search(r"has_lab_process enpkg:(\S+)", body)
        tax = re.search(r'submitted_taxon "([^"]+)"', body)
        wd = re.search(r"has_wd_id (wd:\S+)", body)
        if proc:
            raw[rm] = (proc.group(1), tax.group(1) if tax else "?",
                       wd.group(1) if wd else "?")
    # organ statements hang off the RawMaterial node, in the demo file
    organ = {}
    for rm, body in re.findall(r"enpkg:(\S+) enpkgmodule:has_broad_organe(.*?)\.\n",
                               demo_text, re.S):
        g = lambda p: (re.search(r"enpkgmodule:" + p + r" enpkgmodule:(\w+)", body)
                       or [None, "?"])[1]
        organ[rm] = (g("has_organe"), g("has_tissue"))
    return {v: (sp, wd) + organ.get(rm, ("?", "?"))
            for rm, (v, sp, wd) in raw.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/enpkg", type=pathlib.Path)
    args = ap.parse_args()
    d = fetch(args.data_dir)

    print("Parsing ENPKG ...", file=sys.stderr)
    demo_text = read(d / "metadata_demo.ttl.gz")
    assays = bioassays(demo_text)
    rot = rotenoid_keys(read(d / "structures_metadata.ttl.gz"))
    n_rot, n_feat = rotenoid_counts(d / "isdb_pos.ttl.gz", rot)
    tax = taxonomy(read(d / "metadata_enpkg.ttl.gz"), demo_text)

    # Selective anti-T. cruzi actives: potent on parasite, not merely cytotoxic.
    actives = {s: a for s, a in assays.items()
               if a.get("Tcruzi_10ugml", 0) > ACTIVE_CUT
               and a.get("L6_10ugml", 100) < CYTOTOX_CUT}

    print(f"\n{len(assays)} extracts screened | {len(rot)} rotenoid structures in reference")
    print(f"\n=== Selective anti-T. cruzi actives "
          f"(>{ACTIVE_CUT:.0f}% parasite inhibition, <{CYTOTOX_CUT:.0f}% L6 cytotoxicity) ===\n")
    hdr = f"{'sample':12}{'T.cruzi%':>9}{'L6%':>7}{'rotenoid':>9}{'annot':>7}  {'species':26}{'organ':13}tissue"
    print(hdr); print("-" * len(hdr))
    for s, a in sorted(actives.items(), key=lambda x: -x[1]["Tcruzi_10ugml"]):
        sp, wd, organ, tissue = tax.get(s, ("?", "?", "?", "?"))
        print(f"{s:12}{a['Tcruzi_10ugml']:>9.1f}{a.get('L6_10ugml',0):>7.1f}"
              f"{n_rot.get(s,0):>9}{n_feat.get(s,0):>7}  {sp:26}{organ:13}{tissue}")

    n_with_rot = sum(1 for s in actives if n_rot.get(s, 0) > 0)
    bg = [n_rot.get(s, 0) for s in assays if s not in actives]
    print(f"\n{n_with_rot} of {len(actives)} actives carry rotenoid annotations.")
    print(f"Background (n={len(bg)}): mean {sum(bg)/len(bg):.2f} rotenoid-annotated features.")

    # Within-species organ contrasts: the natural decorrelating experiments.
    by_sp = collections.defaultdict(list)
    for s, (sp, _, organ, tissue) in tax.items():
        if sp != "?":
            by_sp[sp].append((s, organ, tissue))
    print("\n=== Within-species organ contrasts for active species ===")
    print("(same plant, different organ -- nature's own decorrelating samples)\n")
    for sp in sorted({tax[s][0] for s in actives if s in tax}):
        sibs = by_sp[sp]
        if len(sibs) < 2:
            continue
        print(f"  {sp}")
        for s, organ, tissue in sorted(sibs, key=lambda x: -assays.get(x[0], {}).get("Tcruzi_10ugml", 0)):
            tc = assays.get(s, {}).get("Tcruzi_10ugml", 0.0)
            mark = "  <== ACTIVE" if s in actives else ""
            print(f"    {s:12} {organ:13}{tissue:14} T.cruzi={tc:6.1f}%  "
                  f"rotenoid={n_rot.get(s,0):3d}/{n_feat.get(s,0):<4d}{mark}")
        print()

    # ponytail: one self-check, not a test suite. Fails loudly if parsing drifts.
    assert len(assays) == 1600, f"expected 1600 extracts, got {len(assays)}"
    assert len(actives) == 8, f"expected 8 selective actives, got {len(actives)}"
    assert n_with_rot == 6, f"expected 6 rotenoid-bearing actives, got {n_with_rot}"
    print("self-check OK: 1600 extracts, 8 selective actives, 6 rotenoid-bearing "
          "(matches Gaudry et al. 2025).")


if __name__ == "__main__":
    main()
