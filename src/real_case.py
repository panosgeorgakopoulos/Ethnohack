"""Real-data demo, no simulation: two cases run through attribution + selection. Stdlib only.

Case 1 (positive mode, annotation='isdb'): rotenoid-annotated compounds in the 6 rotenoid-bearing
selective anti-T. cruzi actives. The rotenoid finding is Gaudry et al., RSC Adv 2025; reproduced
here as a pipeline check, not claimed as ours.
Case 2 (NEGATIVE mode, annotation='union'): Melochia umbellata VGF156_A06. annotation='isdb' would
erase the quinoline lead (0 quinoline compounds vs 1 under union, VALIDATION.md 7d).

EVERYTHING HERE IS A LEAD / HYPOTHESIS, NOT AN IDENTIFICATION. MS annotations are candidate
structures. Run: python3 -m src.real_case
"""
import json
import math
import random
from pathlib import Path

from . import compounds as cm, enpkg_io as io, ethno
from .attribution import attribute, should_abstain
from .selection import select

OUT = Path(__file__).resolve().parent.parent / "results" / "real_case.json"
ASSAY = "Tcruzi_10ugml"
N_BACKGROUND, BG_SEED, BUDGET = 24, 7, 3
CAVEAT = ("Computational hypothesis requiring experimental confirmation; NOT an identification. "
          "MS annotations are candidate structures, not confirmed identities. Correlation of "
          "abundance with activity across a few extracts does not establish that a compound is "
          "responsible for the activity.")
ANNOT_NOTE = ("Rotenone and deguelin are isomers of identical exact mass that compete to explain "
              "the same peak; an ISDB match cannot tell them apart.")


def _f(x):
    return None if isinstance(x, float) and not math.isfinite(x) else x


def _cand(comp, cid, mode, annotation):
    c = comp[cid]
    cls = c["canopus"]
    return {"cid": cid, "mode": mode, "annotation_setting": annotation,
            "mz": round(c["mz"], 4), "rt_min": round(c["rt"], 3),
            "canopus_class": cls[0] if cls else None,
            "canopus_prob": round(cls[1], 3) if cls else None,
            "isdb_keys": c["isdb_keys"][:10], "n_isdb_keys": len(c["isdb_keys"]),
            "n_extracts_present": len(c["abundance"]),
            "status": "hypothesis", "caveat": CAVEAT}


def _rank(res, comp, mode, annotation, top=None):
    rows = []
    for i, r in enumerate(res[:top], 1):
        d = _cand(comp, r["cid"], mode, annotation)
        d.update({"rank": i, "score": _f(r["score"]),
                  "ci95": [_f(r["ci"][0]), _f(r["ci"][1])], "n_informative": r["n_informative"]})
        rows.append(d)
    return rows


class _Imputed(dict):
    """Activity of not-yet-assayed extracts is unknown at selection time: use the assayed mean,
    so the selector never peeks at held-out measurements."""
    def __init__(self, d):
        super().__init__(d)
        self.m = sum(d.values()) / len(d)
    def __missing__(self, k):
        return self.m


def _stage(name, cands, assayed, y, comp, mode, annotation, top=10):
    res = attribute(cands, assayed, y, comp)
    return {"stage": name, "n_assayed": len(assayed), "abstain": should_abstain(res),
            "abstain_threshold": 0.6, "top_score": _f(res[0]["score"]) if res else None,
            "ranking_top": _rank(res, comp, mode, annotation, top),
            "status": "hypothesis", "caveat": CAVEAT}, res


def _recommend(cands, assayed, res0, y, comp, samples, mode, annotation, top_k=5):
    picks = select("adaptive_contrast", cands, assayed, samples, BUDGET, comp, activity=_Imputed({s: y[s] for s in assayed}))
    meta = io.load_samples()
    focus = [r["cid"] for r in res0[:top_k]]
    out = []
    for s in picks:
        present = [(c, comp[c]["abundance"].get(s, 0.0)) for c in focus]
        have = [f"cid {c} (rel_area {a:.3g})" for c, a in present if a > 0]
        lack = [f"cid {c}" for c, a in present if a <= 0]
        out.append({"sample": s, "species": meta[s]["species"], "organ": meta[s]["organ"],
                    "tissue": meta[s]["tissue"], "measured_" + ASSAY: None,
                    "separates_top_candidates": {"contains": [c for c, a in present if a > 0],
                                                 "lacks": [c for c, a in present if a <= 0]},
                    "rationale": ("Chosen by adaptive_contrast for maximal abundance spread across the currently "
                                  f"top-ranked/ambiguous candidates. Contains: {', '.join(have) or 'none'}; "
                                  f"lacks: {', '.join(lack) or 'none'}. Assaying it would help separate "
                                  "candidates that currently co-occur in the active extracts."),
                    "status": "hypothesis", "caveat": CAVEAT})
    return picks, out


def _run(case_id, title, mode, annotation, cands, known, comp, y, samples, extra):
    s0, res0 = _stage("initial (known hits + reference extracts)", cands, known, y, comp, mode, annotation)
    picks, rec = _recommend(cands, known, res0, y, comp, samples, mode, annotation)
    for r in rec:   # retrospective reveal: real measured value, only used AFTER the recommendation
        r["measured_" + ASSAY] = y[r["sample"]]
    s1, _ = _stage("after assaying the 3 recommended extracts (real measured values)", cands,
                   known + picks, y, comp, mode, annotation)
    s2, _ = _stage("reference: all 1600 extracts (full library)", cands, samples, y, comp, mode, annotation)
    return {"case": case_id, "title": title, "mode": mode, "annotation": annotation,
            "status": "hypothesis", "caveat": CAVEAT, "annotation_note": ANNOT_NOTE,
            "n_candidates": len(cands), "candidates": [_cand(comp, c, mode, annotation) for c in cands],
            "attribution": {"initial": s0, "after_recommended": s1, "full_library_reference": s2},
            "abstention": {"initial": s0["abstain"], "after_recommended": s1["abstain"],
                           "full_library": s2["abstain"]},
            "recommended_extracts": rec, **extra}


def run():
    samples = sorted(io.load_samples())
    assays = io.load_assays()
    y = {s: assays[s][ASSAY] for s in samples if ASSAY in assays.get(s, {})}
    actives = ethno.selective_actives()
    meta = io.load_samples()
    rng = random.Random(BG_SEED)
    bg = rng.sample([s for s in samples if s not in actives], N_BACKGROUND)
    known = sorted(actives) + bg    # a screen yields hits and non-hits; both are real measurements

    # ---- case 1: rotenoids, positive mode, ISDB universe
    pos = cm.build_compounds("pos", annotation="isdb")
    rk = ethno.rotenoid_keys()
    six = [s for s in actives if any(any(k in rk for k in c["isdb_keys"]) and s in c["abundance"]
                                     for c in pos.values())]
    rot = [c for c, v in pos.items() if any(k in rk for k in v["isdb_keys"])]
    cands1 = [c for c in rot if any(s in pos[c]["abundance"] for s in six)]
    k1 = [s for s in known]
    c1 = _run("rotenoid", "Rotenoid case (positive mode)", "pos", "isdb", cands1, k1, pos, y, samples,
              {"rotenoid_bearing_actives": [{"sample": s, "species": meta[s]["species"],
                                             "organ": meta[s]["organ"], ASSAY: y[s]} for s in six],
               "provenance": "Rotenoid hypothesis: Gaudry et al., RSC Adv 2025 (reproduced, not ours).",
               "n_rotenoid_compounds_in_library": len(rot)})

    # ---- case 2: Melochia, NEGATIVE mode, UNION universe (isdb would erase the lead)
    S = "VGF156_A06"
    neg = cm.build_compounds("neg", annotation="union")
    inS = [c for c, v in neg.items() if S in v["abundance"]]
    quin = [c for c in inS if neg[c]["canopus"] and any(w in neg[c]["canopus"][0] for w in ("Quinoline", "Isoquinoline"))]
    others = sorted((c for c in inS if c not in quin), key=lambda c: -neg[c]["abundance"][S])[:12]
    cands2 = quin + others
    tot = sum(neg[c]["abundance"][S] for c in inS)
    quin_rank = None
    if quin:
        q = neg[quin[0]]["abundance"]
        order = sorted(q, key=lambda s: -q[s])
        quin_rank = {"rank_of_melochia": order.index(S) + 1, "n_extracts_with_signal": len(order),
                     "more_signal_and_inactive": [
                         {"sample": s, "species": meta[s]["species"], ASSAY: y[s]}
                         for s in order[:order.index(S)]]}
    c2 = _run("melochia_umbellata", "Melochia umbellata VGF156_A06 (negative mode)", "neg", "union",
              cands2, known, neg, y, samples,
              {"sample": S, "species": meta[S]["species"], "organ": meta[S]["organ"],
               "melochia_tcruzi_inhibition": y[S], "melochia_L6_cytotoxicity": assays[S].get("L6_10ugml"),
               "n_quinoline_compounds": len(quin), "quinoline_share_of_signal": (
                   sum(neg[c]["abundance"][S] for c in quin) / tot if tot else None),
               "quinoline_signal_rank_in_library": quin_rank,
               "why_union": "annotation='isdb' yields 0 quinoline compounds in negative mode; the lead "
                            "only exists under 'union' (VALIDATION.md 7d).",
               "documented_class_level_context": "VALIDATION.md: quinoline-class signal ranks "
                            "4th of 1600 extracts and three extracts carry more and are inactive "
                            "(documented class-level figure, pos+neg; not recomputed here). The "
                            "single-compound rank above is a narrower, separate measure.",
               "lead_framing": "A lead, not an identification: extracts with more quinoline signal than "
                               "Melochia are inactive in this assay."})
    out = {"status": "hypothesis", "caveat": CAVEAT, "annotation_note": ANNOT_NOTE,
           "provenance": "Real ENPKG data, no simulation. Activity = " + ASSAY + ". Selector never sees "
                         "held-out activities (imputed); real values revealed only after the recommendation.",
           "initial_assayed_set": {"n": len(known), "hits": sorted(actives), "reference_extracts": bg},
           "cases": [c1, c2]}
    return out


def _print(out):
    print("REAL-DATA DEMO (no simulation). ALL FINDINGS ARE HYPOTHESES, NOT IDENTIFICATIONS.")
    print(CAVEAT, "\n" + ANNOT_NOTE)
    for c in out["cases"]:
        print(f"\n=== {c['title']} | mode={c['mode']} annotation={c['annotation']} | "
              f"{c['n_candidates']} candidates ===")
        if "melochia_tcruzi_inhibition" in c:
            print(f"{c['sample']} {c['species']}: inhibition {c['melochia_tcruzi_inhibition']}%, "
                  f"cytotox {c['melochia_L6_cytotoxicity']}%, quinoline compounds {c['n_quinoline_compounds']}")
            q = c["quinoline_signal_rank_in_library"]
            if q:
                print(f"  quinoline signal rank {q['rank_of_melochia']}/{q['n_extracts_with_signal']} extracts "
                      f"with signal; higher-signal extracts: "
                      + "; ".join(f"{x['sample']} {x['species']} ({x[ASSAY]:.0f}%)" for x in q["more_signal_and_inactive"]))
        for key, st in c["attribution"].items():
            print(f"\n [{st['stage']}] abstain={st['abstain']} (top score {st['top_score']})")
            for r in st["ranking_top"][:5]:
                ci = r["ci95"]
                print(f"   #{r['rank']} cid {r['cid']:>6} mz {r['mz']:.4f} rt {r['rt_min']:.2f} "
                      f"score {r['score']:.3f} CI [{ci[0]:.2f},{ci[1]:.2f}] n_inf {r['n_informative']} "
                      f"{r['canopus_class']} ({r['canopus_prob']})")
        print("\n 3 recommended extracts (adaptive_contrast):")
        for r in c["recommended_extracts"]:
            print(f"   {r['sample']} {r['species']} / {r['organ']} measured {r['measured_'+ASSAY]:.1f}% -- "
                  f"contains {r['separates_top_candidates']['contains']}, lacks {r['separates_top_candidates']['lacks']}")
    print("\nWrote", OUT)


def main():
    out = run()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    _print(out)


if __name__ == "__main__":
    main()
