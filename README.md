# Which molecule did it?

**Budget-constrained experiment selection for natural-product dereplication.**
EthnoHack 2026 — Track 2: Natural Products & Drug Discovery.

**In brief.** When a plant extract is active, the compounds that co-occur in it cannot be separated by the data already in hand. The tool picks which few extracts to assay next with **adaptive contrast**, and nominates a lead only when the evidence supports it, on **selectivity** (parasite inhibition against host-cell cytotoxicity) rather than potency alone. On semi-synthetic benchmarks built from the real ENPKG abundance matrix, choosing which three extracts to assay roughly doubles the hit rate on the hard cases over spending no assays (8.6% to 19.0%), and three extracts chosen at random are worth nothing (8.6%). Adaptive contrast **ties** the strongest-first rule chemists already use (19.0% each, margin +0.0 points); its value is in what it nominates. Nominating on selectivity gives identical developable accuracy with 154× fewer wasted isolations, in simulation.

---

## The problem

A plant extract kills a parasite. It contains hundreds of compounds. Which one did it?

Isolating a compound takes weeks of chromatography, so a chemist gets a few shots. The trap is that candidate compounds **co-occur**: in the ENPKG anti-trypanosomatid screen, rotenone and deguelin appear together across the same active extracts, so no amount of staring at existing data assigns credit between them. It is two suspects alibiing each other — every crime scene has both.

The information isn't in the data. You need a new observation: **a sample where the suspects come apart.**

In pooled drug screening you *design* the pools. Here you cannot — nature composed each plant millions of years ago. The only freedom is **which pools to open**. This tool chooses them.

## What it does

Given active extracts, candidate compounds, and a budget of *k* assays, **adaptive contrast** returns the *k* extracts that best resolve which compound is responsible, and the attribution step reports the result with uncertainty, including the option to conclude **neither**.

- **Attribution** is continuous in log-abundance, with a detection floor below which a sample is uninformative rather than negative.
- **Adaptive contrast** scores each candidate extract by its abundance spread across the candidates the current evidence cannot yet separate, recomputed after every pick, with a redundancy penalty against extracts already chosen.
- **Nomination** uses two readouts from the same assay: *T. cruzi* inhibition and L6 host-cell cytotoxicity. One assayed extract yields both, so the second channel costs no extra assay.
- **The verdict is a set, not a single name.** It returns the smallest set of explanations carrying 95% of the posterior, so the answer can be one compound, "one of these two", "both contribute — do not fractionate", or "the best explanation is a general cytotoxin, do not isolate it". The interactive demo and the benchmark run this same rule.

## Results

Measured on semi-synthetic benchmarks built from the **real** ENPKG abundance matrix, so the co-occurrence structure is genuine while ground truth is known. Hard cases are those the primary screen leaves unresolved — the only cases the tool is for.

### Selection

952 episodes from **238 compound pairs** (pairs that co-occur in ≥3 extracts *and* can be decorrelated), pair-clustered 95% CIs. Hard stratum: the 58 episodes from 16 pairs the primary screen cannot resolve. "Accuracy" means *nominated the true driver, counted over all episodes* — an abstention is a miss — and precision was 100% for every policy. Source: `results/benchmark.json`; canonical interpretation in [FINDINGS.md](FINDINGS.md).

| selection | hard accuracy | 95% CI |
|---|---|---|
| No assays spent (reference) | 8.6% | [0.0, 24.1] |
| Random 3 (reference) | 8.6% | [0.0, 24.1] |
| Strongest-first, current practice (reference) | 19.0% | [6.9, 34.4] |
| **Adaptive contrast** | 19.0% | [6.9, 34.4] |

**Choosing which three extracts to assay roughly doubles the hit rate over spending no budget** (8.6% to 19.0%; adaptive contrast minus no assays, hard: +10.3 points, CI [+3.8, +17.2], 16 pairs). **Three extracts chosen at random are worth nothing** on the hard cases (8.6%, identical to no assays). **Adaptive contrast matches current practice on selection**: the margin over strongest-first is +0.0 points, CI [0.0, 0.0] on the hard stratum (16 pairs), +0.7 [−0.3, +1.8] on easy and +0.6 [−0.3, +1.7] overall. We do not claim it beats the chemist's default; its value is in what it nominates (next section).

### Nominate on selectivity, not potency

Rotenone is the most potent rotenoid and the worst candidate — it is broadly cytotoxic. ENPKG measures parasite inhibition and host-cell cytotoxicity on the same extracts in the same screen, so a second channel costs **no extra assay**:

| nomination rule | nominates | precision | **wasted isolations / 100** |
|---|---|---|---|
| potency-only | 65.0% | 50.2% | **32.35** |
| selectivity-aware | 32.9% | 99.4% | **0.21** |

Developable accuracy is identical (32.7% vs 32.7%). **Identical accuracy, 154× fewer wasted isolations** — and each wasted nomination is weeks of a chemist's life. This is the project's headline.

Table: adaptive contrast selection, all 952 episodes, threshold 0.85. Hard stratum only (58 episodes, 16 pairs): wasted isolations fall from 6.9 to 0.0 per 100. At the same threshold, on episodes where two compounds act together (decision-model generator, 952 episodes), potency-only false-nominates a single driver on 1.5% [0.7, 2.3]; selectivity-aware does so on 0.8% [0.3, 1.5].

⚠️ **These numbers come from simulated activity.** Composition and co-occurrence are real; the pharmacology is not. The 50% cytotoxic prevalence is a modelling assumption, so the absolute waste rates are not measured. Its only real-data support is that **7 of 15** measured potency hits are cytotoxic decoys ([FINDINGS.md](FINDINGS.md) §3.6). Hard cases are 6.7% of the confounded, decorrelatable pairs (16 of 238) — a real but narrow slice. Selectivity-aware nomination is supported on wasted isolations in simulation, not validated.

## Quick start

```bash
python3.12 -m pip install -r requirements.txt
python3.12 -m src.enpkg_io          # downloads ~130 MB from Zenodo on first run
python3.12 scripts/benchmark.py            # regenerates results/benchmark.json, the source of the numbers above
python3.12 -m pytest tests/ -q                   # 52 tests
python3.12 -m decouple serve --config config/enpkg.json     # interactive demo on the measured extracts
```

`config/enpkg.json` is the shipped operating point and the one the benchmark uses: fitted gain 43.91, threshold 0.85, cytotoxicity cap 0.5, run against the measured ENPKG extracts. `config/default.json` holds the earlier reconstructed-tier defaults (gain 2.0, threshold 0.9, single readout) and is kept so the frozen regression results stay reproducible. The threshold is the lowest on the grid that keeps precision at 95% or better and the false-nomination rate under two-driver synergy within a 5% budget: at 0.80 that rate is 8.3% (2 of 24 hard episodes), at 0.85 it is 4.2% (1 of 24) (`results/threshold_curve.json`).

Data is downloaded at runtime and never committed.

## What is new, what is pre-existing

The rules require this split, and it matters here because we reproduce a published result as a *pipeline check*, not as a finding.

| Pre-existing (not our work) | Built during 2–8 Nov 2026 |
|---|---|
| ENPKG dataset & knowledge graph — Gaudry et al., *ACS Cent Sci* 2024 | Continuous log-abundance attribution rule |
| The 1,600-extract anti-trypanosomatid screen | Budget-constrained extract selection (adaptive contrast) |
| The rotenoid finding — Gaudry et al., *RSC Adv* 2025, 15:15240 | Semi-synthetic benchmark + stratification |
| CANOPUS / SIRIUS / ISDB annotations | Ethnobotanical provenance & organ-contrast analysis |
| Published ethnobotanical records | The *Melochia umbellata* quinoline lead |
| | The ISDB taxonomic-circularity finding |

**We reproduced the published rotenoid result from open data in minutes, then showed why class-level counting cannot generalise, and built a method that does.** The reproduction is a validation step. The contribution is everything in the right-hand column.

## Why class-level counting fails

Across all 1,600 extracts, rotenoid abundance barely predicts activity (Spearman ρ = 0.095). The single most rotenoid-rich extract in the library — *Clitoria macrophylla* roots at a **91.4%** rotenoid share — is not a selective active. Rotenoid content is neither necessary (2 of 8 actives have none) nor sufficient. The same pattern holds independently for quinoline alkaloids.

Full analysis: [VALIDATION.md](VALIDATION.md).

## Ethnobotanical layer

Every hit is joined to species, plant organ, and documented traditional use ([ETHNOBOTANY.md](ETHNOBOTANY.md)).

The clearest case is *Pachyrhizus erosus* — jicama. You eat the tuber; the leaves poison fish. The screen reproduces that split as a dose gradient inside one plant:

| Organ | Rotenoid share | T. cruzi inhibition |
|---|---|---|
| leaves (the poison part) | 65.5% | 112.2% |
| woody stems | 11.6% | 53.7% |
| roots (the food part) | 4.0% | 0.0% |

We also report a claim we checked and **rejected** — an antimalarial use for *Phyllanthus pulcher*, for which a dedicated search found no support. The project is about honest attribution under uncertainty.

## Documentation

| File | Contents |
|---|---|
| [RESEARCH.md](RESEARCH.md) | Field map, prior art, data provenance |
| [VALIDATION.md](VALIDATION.md) | Premise testing on real data |
| [FINDINGS.md](FINDINGS.md) | **Canonical record** of every established number |
| [ETHNOBOTANY.md](ETHNOBOTANY.md) | Traditional-use layer, verified species by species |
| [COMPLIANCE.md](COMPLIANCE.md) | Rules review |

## Data and licensing

| Asset | Licence |
|---|---|
| ENPKG data — [Zenodo 7824642](https://zenodo.org/records/7824642) | **CC-BY-4.0** |
| ENPKG ontology file | **CC-BY-NC-SA-4.0** (different licence — note the NC and SA terms) |
| ChEMBL cross-references | CC-BY-SA-3.0 |
| Our code | MIT (see LICENSE) |

Neither ENPKG file set is redistributed here; both are fetched from Zenodo at runtime.

Cite: Gaudry A. et al. *A Sample-Centric and Knowledge-Driven Computational Framework for Natural Products Drug Discovery.* ACS Cent Sci 2024.

## Traditional knowledge and benefit-sharing

The knowledge that pointed at these plants originated with the communities who hold it — in Malaysia, Cameroon, Madagascar, the Philippines and elsewhere. Each ethnobotanical record we use is cited individually in [ETHNOBOTANY.md](ETHNOBOTANY.md).

We make **no claim of ownership** over any traditional knowledge described here. Nagoya Protocol and Access & Benefit-Sharing obligations attach to the original collection of these plants and to any commercial development arising from them, not to secondary analysis of already-published data; any downstream development would need to address them directly.

## Limitations

- Activity in the benchmarks is **simulated** — logistic dose-response, additive noise, a simulated cytotoxicity channel with an assumed 50% prevalence. Synergy appears only as a stress test; no matrix effects.
- Hard cases are **6.7%** of confounded, decorrelatable pairs (16 of 238).
- **The tool cannot say "both".** When two compounds act together it names a single driver on 1.5% of episodes under the decision-model generator and 13.4% under the logistic generator (adaptive contrast, potency-only, threshold 0.85, 952 episodes: 14 and 128 nominations); every such nomination is wrong.
- **Coverage is stratum-dependent.** At threshold 0.85 the system nominates on 19.0% of hard episodes and 65.0% overall; precision when it nominates was 100% in the single-driver benchmark.
- **Adaptive contrast does not beat strongest-first.** The hard-stratum margin is +0.0 points, CI [0.0, 0.0], 16 pairs; the selection method ties current practice.
- Compound identities are **MS annotation candidates, not confirmed structures.** Rotenone and deguelin are isomers of identical exact mass and compete to explain the same peak. The published team resolved this with authentic standards; we cannot.
- ISDB annotations carry a taxonomic prior that makes them partly circular ([VALIDATION.md](VALIDATION.md) §7b); we mitigate by using CANOPUS for class assignment and filtering ISDB on spectral score.
- **Nothing here is clinically validated.** Predicted attribution is a hypothesis for experimental follow-up, not evidence of therapeutic effect, and nothing in this project is medical advice.

## Team & tooling

*(team members — add names and roles)*

Analysis code in this project was written during the hackathon window with AI coding assistance. All methodological decisions, tests and interpretations were reviewed by the team.
