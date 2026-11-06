# DECOUPLE · Engineering & Scientific Handover for AI Agents (Codex)

> **Purpose:** This document is an onboarding and knowledge-transfer briefing for incoming AI coding agents (such as OpenAI Codex) or human software engineers. It details the architecture, scientific invariants, recent upgrades, and exact contracts of the **DECOUPLE** repository.

---

## 1. Executive Summary & Problem Formulation

* **Project Name:** DECOUPLE (Three Assays, One Isolation)
* **Target Domain:** Computational Natural Products Chemistry & Bioactivity Deconvolution
* **Disease Model:** *Trypanosoma cruzi* intracellular amastigotes (causative agent of Chagas disease; ChEMBL Target ID `CHEMBL368`).
* **The Core Problem:** Natural product drug discovery frequently suffers from **botanical chemical co-occurrence**. In crude plant extract libraries, two active constituents often appear together across active extracts. Wet-lab compound isolation is slow, labor-intensive, and expensive.
* **The Budget Constraint:** A chemist has a budget of:
  * **Up to 3 extract assay reveals**
  * **Exactly 1 compound isolation nomination**
* **The Core Discovery / Finding:**
  * Intuitive human screening (**"strongest-first"** / greedy exploitation) chooses the most potent extracts. But because both molecules are present in those extracts, the measurement provides **zero discriminatory power** (misses 33.3% of true single drivers).
  * **DECOUPLE** treats experiment selection as a Bayesian active experimental design problem. It identifies extracts that maximize the **expected utility of the final isolation choice**, intentionally seeking diagnostic contrast. DECOUPLE achieves **100% single-driver recovery** on the exact same budget.

---

## 2. Benchmark & Dataset Summary

* **Benchmark Scale:** **23 unique confounded chemical pairs** derived from authentic *T. cruzi* assays across **7 published scientific studies** in ChEMBL and plant occurrences in the LOTUS database:
  `CHEMBL1143992`, `CHEMBL1146457`, `CHEMBL1212812`, `CHEMBL1944624`, `CHEMBL3044681`, `CHEMBL3997809`, `CHEMBL4261582`.
* **Multi-Policy Benchmark Results (Frozen in `results/evaluation-v1.json`):**

| Policy | Strategy | Correct Nomination | Single-Driver Recovery | Precision / Nominated | Assays to Threshold |
|---|---|:---:|:---:|:---:|:---:|
| `strongest-first` | Greedy exploitation (highest predicted response) | 34.8% | 66.7% | 100.0% | 2.25 |
| `correlation` | Leading biochemometric feature correlation | 43.5% | 83.3% | 100.0% | 1.30 |
| `random` | Uniform random sampling baseline | 47.8% | 91.7% | 100.0% | 1.64 |
| `disagreement` | Maximal hypothesis divergence | 47.8% | 91.7% | 100.0% | 1.18 |
| **`decouple`** | **Expected isolation utility gain** | **52.2%** | **100.0%** | **100.0%** | **1.17** |

---

## 3. Repository Architecture & File Responsibilities

```
Ethnohack/
├── config/
│   └── default.json          # Core hyperparameters, budget (3), prior, and noise floor
├── data/
│   ├── audit.json            # Numerical record counts, exclusions, and verification hashes
│   ├── episodes.json         # Reconstructed paired candidate episodes (23 pairs)
│   ├── manifest.json         # Cryptographic SHA-256 hashes of raw source downloads
│   ├── raw/                  # Downloaded ChEMBL activities & LOTUS occurrence records
│   └── sessions/             # SQLite session database (`episodes.sqlite3`)
├── decouple/
│   ├── __main__.py           # Unified CLI interface (audit, replay, evaluate, serve, demo, report)
│   ├── engine.py             # Transactional episode state machine, budget enforcement, data air-gapping
│   ├── evaluate.py           # Paired multi-policy benchmark runner & metrics aggregator
│   ├── ingest.py             # ChEMBL / LOTUS parser, InChIKey matcher, and episode generator
│   ├── model.py              # 4-hypothesis Gaussian response model, Bayesian belief updates, utility
│   ├── policies.py           # 5 acquisition policies (random, strongest, correlation, etc.)
│   ├── report.py             # Standalone HTML Hit Prioritization Dossier generator
│   ├── server.py             # HTTP server, SQLite session store, RDKit SVG renderer, properties
│   └── static/               # Web workbench (HTML5, responsive CSS, vanilla JS, Geist font)
├── docs/
│   ├── 01-science.md         # Scientific brief & Chagas disease context
│   ├── 02-data.md            # Data contract, identity tiers, and exclusions
│   ├── 03-specification.md   # Mathematical and product specifications
│   ├── 04-evaluation.md      # Retrospective evaluation protocol
│   ├── 05-delivery.md        # Delivery acceptance criteria
│   ├── 06-sources.md         # Prior art and literature sources
│   ├── 07-implementation-plan.md # Agent implementation plan & contracts
│   ├── HANDOVER.md           # This onboarding document for incoming agents
│   └── PITCH.md              # 3-minute hackathon pitch deck & judge defense guide
├── results/
│   ├── evaluation-v1.json    # Frozen evaluation metrics across all 23 episodes
│   ├── evaluation-summary.json # High-level summary of policy comparison
│   ├── replay.json           # Detailed event trace of a sample episode run
│   └── dossier.html          # Sample generated printable laboratory hit dossier
├── tests/
│   └── test_decouple.py      # 21 automated integration and unit acceptance tests
└── requirements.txt          # Minimal pinned dependencies (numpy, pytest, rdkit, etc.)
```

---

## 4. Key Work Accomplished in Recent Sprints

1. **Cohort Expansion (from $N=2$ to $N=23$ Unique Pairs):**
   - Configured `min_shared_species: 2` and `min_jaccard: 0.10` in `config/default.json`.
   - Ingested 15,996 ChEMBL activity records and 709,740 LOTUS plant occurrence records.
   - Generated 23 authentic confounded episodes across 7 independent scientific publications.
2. **2D Chemical Structure Rendering:**
   - Implemented `render_svg(smiles, width, height)` in `decouple/server.py` using RDKit (`rdMolDraw2D`).
   - Added server endpoint `GET /api/structure?id=<id>` with in-memory caching.
   - Rendered 2D vector structures in candidate cards and in the detail modal.
3. **Medicinal Chemistry & Drug-Likeness Layer:**
   - Implemented `compute_properties(smiles)` in `decouple/server.py` returning: Molecular Weight (MW), cLogP, TPSA, Fraction $sp^3$ carbons ($F_{sp3}$), H-bond donors/acceptors (HBD/HBA), and Lipinski Rule of 5 status.
   - Created sleek CSS property cards in the UI detail modal and printed them in the CLI demo.
4. **Interactive Terminal Demo (`decouple demo`):**
   - Created `python -m decouple demo` in `decouple/__main__.py` printing a colorized terminal walkthrough contrasting greedy vs. DECOUPLE choices step-by-step.
5. **Printable Laboratory Hit Dossier Generator (`decouple report`):**
   - Created `decouple/report.py` and connected the UI button **"Lab dossier 📄"** and CLI command `python -m decouple report --output results/dossier.html`.
   - Produces a self-contained, printable HTML dossier with 2D structures, drug-likeness metrics, assay deconvolution trace, and confirmatory wet-lab SOPs.
6. **Hackathon Pitch & Judge Defense Guide (`docs/PITCH.md`):**
   - Wrote a 5-slide, 3-minute visual pitch outline and pre-crafted defenses against judge pushback.
7. **Test Suite Expansion:**
   - Expanded tests from 17 to **21 passing tests** covering budget caps, revision conflicts, idempotency, SVG generation, property calculation, and report generation.

---

## 5. Non-Negotiable Invariants & Safety Constraints

Incoming agents modifying this codebase **must adhere to the following contracts**:

1. **The Air-Gap Boundary:**
   - The acquisition policies (`decouple/policies.py`) and response model (`decouple/model.py`) must **only** receive the projection returned by `visible()`.
   - Hidden ground truth (`episode['hidden']`), future unrevealed assays, and private compound metadata must **never** enter the visible state before explicit reveal.
2. **Budget Invariant:**
   - An episode allows **at most 3 assay reveals** and **at most 1 nomination/abstention**.
   - Attempting a 4th reveal or a 2nd nomination **must raise `ValueError`**.
3. **Idempotency & Concurrency:**
   - Calling `reveal()` for an already revealed `sample_id` must return the current state without deducting budget or appending duplicate events.
   - Transactions must check `expected_revision` against `state['revision']`. Stale requests must raise `ValueError`.
4. **Autonomous Abstention Rule:**
   - If candidate molecules are collinear across all available library specimens, DECOUPLE must formally abstain with an explanatory reason (`identical profiles in every available specimen`). It must never guess.
5. **Simulation Diagnostic Transparency:**
   - The dataset must always carry `"measured_extract_replay": false` and `tier: "Simulation diagnostic"`. Never remove this flag or misrepresent simulated mixture responses as wet-lab measurements.

---

## 6. CLI Execution Cheat-Sheet

All commands must be run within the virtual environment (`.venv`):

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run all 21 automated tests
python3 -m pytest tests/

# 3. Verify source data hashes and record counts
python3 -m decouple audit --config config/default.json

# 4. Run the live interactive terminal demo
python3 -m decouple demo --config config/default.json

# 5. Run single-episode deterministic replay
python3 -m decouple replay --config config/default.json

# 6. Run full multi-policy benchmark across all 23 episodes
python3 -m decouple evaluate --config config/default.json

# 7. Generate a printable laboratory hit dossier
python3 -m decouple report --config config/default.json --output results/dossier.html

# 8. Start local web server (http://127.0.0.1:8765)
python3 -m decouple serve --config config/default.json --port 8765
```

---

## 7. Recommended Next Steps for Future Agents

* **Selectivity Penalty:** Incorporate host-cell cytotoxicity (mammalian L6 cells) into the acquisition utility function to penalize non-selective pan-cytotoxins.
* **Leave-One-Study-Out Evaluation:** Add a cross-study validation report in `decouple/evaluate.py` demonstrating policy generalization across the 7 independent publications.
* **Wet-Lab LC-MS Ingestion:** Once untargeted metabolomics feature tables from accession `MSV000087728` are processed, replace simulated mixture concentrations with physical peak intensities (`measured_extract_replay: true`).
