"""Ethnobotanical provenance layer: screening hits -> species, organ, chemical class.

Ports scripts/ethno_provenance.py onto the src.enpkg_io API. Stdlib only.
Rotenoid finding: Gaudry et al., RSC Adv 2025 (reproduced here as a pipeline check).

Run: python3 -m src.ethno [Organism]
"""
import sys
from collections import defaultdict

from . import enpkg_io

ACTIVE_CUT, CYTOTOX_CUT = 80.0, 50.0   # the published screen's own cutoffs


def _assay(a, organism, conc):
    return a.get(f"{organism}_{conc}")


def selective_actives(organism="Tcruzi", active_cut=ACTIVE_CUT, cytotox_cut=CYTOTOX_CUT,
                      conc="10ugml"):
    """{sample: {"activity", "cytotox", **taxonomy}}: parasite inhibition > cut, L6 < cytotox cut."""
    samples = enpkg_io.load_samples()
    out = {}
    for s, a in enpkg_io.load_assays().items():
        act = _assay(a, organism, conc)
        tox = a.get("L6_10ugml", 100.0)
        if act is not None and act > active_cut and tox < cytotox_cut:
            out[s] = {"activity": act, "cytotox": a.get("L6_10ugml", 0.0),
                      **samples.get(s, {})}
    return out


def rotenoid_keys():
    return {k for k, v in enpkg_io.load_structures().items() if "Rotenoids" in v["npc_class"]}


def rotenoid_counts():
    """{sample: (features with >=1 rotenoid candidate, annotated features)}, ISDB positive mode."""
    rot = rotenoid_keys()
    n_rot, n_feat = defaultdict(int), defaultdict(int)
    for (sample, _scan), cands in enpkg_io.load_isdb("pos").items():
        n_feat[sample] += 1
        if any(c["key"] in rot for c in cands):
            n_rot[sample] += 1
    return {s: (n_rot[s], n_feat[s]) for s in set(n_feat) | set(enpkg_io.load_assays())}


def provenance_table(organism="Tcruzi", **kw):
    """Rows (sample, activity, cytotox, "rot/annot", species, organ, tissue), activity descending."""
    counts = rotenoid_counts()
    rows = []
    for s, a in selective_actives(organism, **kw).items():
        r, n = counts.get(s, (0, 0))
        rows.append((s, a["activity"], a["cytotox"], f"{r}/{n}",
                     a.get("species") or "?", a.get("organ") or "?", a.get("tissue") or "?"))
    return sorted(rows, key=lambda x: -x[1])


def organ_contrasts(species=None, organism="Tcruzi", conc="10ugml"):
    """{species: [ {sample, organ, tissue, activity, rotenoid, annotated}, ... ]}

    Same species sampled as different organs (>=2 distinct organs), sorted by activity
    descending. Default: species containing a selective active; or pass one species name.
    """
    samples, assays, counts = enpkg_io.load_samples(), enpkg_io.load_assays(), rotenoid_counts()
    by_sp = defaultdict(list)
    for s, m in samples.items():
        if m.get("species"):
            by_sp[m["species"]].append(s)
    if species is None:
        names = sorted({samples[s]["species"] for s in selective_actives(organism, conc=conc)
                        if samples.get(s, {}).get("species")})
    else:
        names = [species] if isinstance(species, str) else list(species)
    out = {}
    for sp in names:
        rows = []
        for s in by_sp.get(sp, []):
            r, n = counts.get(s, (0, 0))
            rows.append({"sample": s, "organ": samples[s]["organ"] or "?",
                         "tissue": samples[s]["tissue"] or "?",
                         "activity": _assay(assays.get(s, {}), organism, conc) or 0.0,
                         "rotenoid": r, "annotated": n})
        if len({x["organ"] for x in rows}) >= 2:
            out[sp] = sorted(rows, key=lambda x: -x["activity"])
    return out


def main(organism="Tcruzi"):
    assays = enpkg_io.load_assays()
    rot = rotenoid_keys()
    counts = rotenoid_counts()
    actives = selective_actives(organism)
    print(f"\n{len(assays)} extracts screened | {len(rot)} rotenoid structures in reference")
    print(f"\n=== Selective {organism} actives (>{ACTIVE_CUT:.0f}% parasite inhibition, "
          f"<{CYTOTOX_CUT:.0f}% L6 cytotoxicity) ===\n")
    hdr = f"{'sample':12}{'activity%':>10}{'L6%':>7}{'rot/annot':>11}  {'species':28}{'organ':13}tissue"
    print(hdr); print("-" * len(hdr))
    for s, act, tox, ra, sp, organ, tissue in provenance_table(organism):
        print(f"{s:12}{act:>10.1f}{tox:>7.1f}{ra:>11}  {sp:28}{organ:13}{tissue}")
    n_with_rot = sum(1 for s in actives if counts.get(s, (0, 0))[0] > 0)
    bg = [counts.get(s, (0, 0))[0] for s in assays if s not in actives]
    print(f"\n{n_with_rot} of {len(actives)} actives carry rotenoid annotations.")
    print(f"Background (n={len(bg)}): mean {sum(bg)/len(bg):.3f} rotenoid-annotated features.")
    print("per-active rotenoid feature counts:",
          ", ".join(str(n) for n in sorted((counts.get(s, (0, 0))[0] for s in actives),
                                           reverse=True)))

    print("\n=== Within-species organ contrasts for active species ===")
    print("(same plant, different organ -- nature's own decorrelating samples)\n")
    for sp, rows in organ_contrasts(organism=organism).items():
        print(f"  {sp}")
        for x in rows:
            mark = "  <== ACTIVE" if x["sample"] in actives else ""
            print(f"    {x['sample']:12} {x['organ']:13}{x['tissue']:14} "
                  f"{organism}={x['activity']:6.1f}%  "
                  f"rotenoid={x['rotenoid']:3d}/{x['annotated']:<4d}{mark}")
        print()
    return assays, actives, n_with_rot


if __name__ == "__main__":
    org = sys.argv[1] if len(sys.argv) > 1 else "Tcruzi"
    assays, actives, n_with_rot = main(org)
    if org == "Tcruzi":
        assert len(assays) == 1600, f"expected 1600 extracts, got {len(assays)}"
        assert len(actives) == 8, f"expected 8 selective actives, got {len(actives)}"
        assert n_with_rot == 6, f"expected 6 rotenoid-bearing actives, got {n_with_rot}"
        print("self-check OK: 1600 extracts, 8 selective actives, 6 rotenoid-bearing.")
    else:
        print(f"{org}: {len(actives)} selective actives")
