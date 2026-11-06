"""Emit results/evaluation-enpkg.json in the schema the UI's results panel reads,
populated from the real benchmark (results/benchmark.json) rather than the
reference evaluation. Without it /api/results 500s under config/enpkg.json."""
import json, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
b = json.loads((ROOT / "results/benchmark.json").read_text())
reg = b["regimes"]["well_specified/single_driver"]

def cell(policy, rule="selectivity-aware", stratum="overall", scoring="developable"):
    for c in reg["cells"]:
        if (c["pool"], c["policy"], c["stratum"], c["rule"], c["scoring"]) == \
           ("unconstrained", policy, stratum, rule, scoring):
            return c
    return None

def m(v, ci=None):
    return {"estimate": v, "ci95": ci}

POLICIES = ["no_budget", "random", "strongest-first", "decouple", "adaptive_contrast"]
pol = {}
for p in POLICIES:
    c = cell(p)
    if not c:
        continue
    pol[p] = {
        "correct_nomination_rate": m(c["accuracy"], c.get("accuracy_ci95")),
        "abstention_rate": m(1 - c["coverage"], None),
        "precision_when_nominating": m(c["precision"], c.get("precision_ci95")),
        "single_driver_recovery": m(c["accuracy"], None),
        "hypothesis_accuracy": m(c["accuracy"], None),
        "mean_assays_to_correct_threshold_among_recovered": m(None),
        "unrecovered_single_driver_rate": m(1 - c["accuracy"], None),
    }

sc = [c for c in reg.get("set_cells", [])
      if (c.get("pool"), c.get("policy"), c.get("stratum"), c.get("truth_cytotoxic"))
      == ("unconstrained", "adaptive_contrast", "overall", "all")]
sc = sc[0] if sc else {}

def sha(p):
    f = ROOT / p
    return hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None

out = {
    "schema_version": 2,
    "tier": "Tier R · measured extracts (ENPKG)",
    "config": b.get("config", {}),
    "episodes_sha256": sha("data/real/episodes.json"),
    "manifest_sha256": sha("data/real/manifest.json"),
    "episodes": reg.get("n_episodes"),
    "unique_pairs": reg.get("n_distinct_pairs"),
    "unique_source_documents": 1,
    "source_documents": ["Zenodo 7824642 (ENPKG)"],
    "uncertainty": (
        "Benchmark responses are simulated on real measured LC-MS abundances and real "
        "co-occurrence; the chemistry is real, the response is not. Intervals are "
        f"pair-clustered over {reg.get('n_distinct_pairs')} compound pairs, not over episodes."),
    "measured_extract_replay": True,
    "acquisition_objective": "Expected gain in threshold-aware nomination utility; unitless.",
    "policies": pol,
    "paired_difference_vs_strongest": {
        "metric": "correct_nomination_rate",
        "estimate": (cell("adaptive_contrast")["accuracy"] - cell("strongest-first")["accuracy"])
                    if cell("adaptive_contrast") and cell("strongest-first") else None,
        "ci95": None},
    "set_valued": {
        "label": "Set-valued verdicts (mass 0.95)",
        "coverage": sc.get("set_coverage"),
        "proposal_rate": sc.get("set_proposal_rate"),
        "containment": sc.get("set_containment"),
        "mean_size": sc.get("set_mean_size"),
        "cytotoxic_rate": sc.get("cytotoxic_rate"),
        "kind_counts": sc.get("set_kind_counts")},
    "indistinguishable_diagnostic": {
        "label": "Episodes where no available extract separates the pair",
        "episodes": reg.get("n_episodes"),
        "unique_pairs": reg.get("n_distinct_pairs"),
        "abstentions": (sc.get("set_kind_counts") or {}).get("abstain"),
        "rate": ((sc.get("set_kind_counts") or {}).get("abstain", 0) / reg["n_episodes"])
                if reg.get("n_episodes") else None,
        "ci95": None,
        "note": "Abstentions under the set-valued rule; the cytotoxic verdict is an answer, not a decline."},
}
p = ROOT / "results/evaluation-enpkg.json"
p.write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote {p.relative_to(ROOT)}  ({p.stat().st_size/1024:.0f} KB)")
print(f"  episodes {out['episodes']}  pairs {out['unique_pairs']}  policies {len(pol)}")
print(f"  set-valued coverage {sc.get('set_coverage')}  containment {sc.get('set_containment')}")
