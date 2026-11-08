# FINDINGS — canonical record

> **8 Nov clarification:** statements below that the system cannot say “both” refer to the threshold-based single-compound nomination rule. The current workbench uses `decouple/setvalued.py`, which can return a joint hypothesis. `results/benchmark.json` contains separate `cells` and `set_cells` evaluations. A joint verdict is a model output, not proof of synergy or loss of activity after fractionation. Historical compliance checkmarks below are not a current submission sign-off.


Single source of truth for everything established in this project. Compiled 6 Nov 2026, reconciled to `results/benchmark.json` and `results/real_case.json`.
If a number appears here and elsewhere and they disagree, **this file wins** and the other should be fixed.

**Provenance tags:** ✅ verified hands-on from data · 📄 from literature · 🤖 reported by an automated implementation step and independently re-checked · ⏳ not yet verified

**Where the detail lives:** [RESEARCH.md](RESEARCH.md) field map · [VALIDATION.md](VALIDATION.md) premise testing · [ETHNOBOTANY.md](ETHNOBOTANY.md) traditional-use layer · [COMPLIANCE.md](COMPLIANCE.md) rules · `results/benchmark.json` benchmark numbers · `results/real_case.json` real-data run.

---

# PART 1 — Verified constants

Any module disagreeing with these has a bug. Reproduce with `python3.12 -m pytest tests/ -q` (**43 tests**: 17 `decouple`, 23 `src`, 3 selectivity). The benchmark regenerates with `python3.12 scripts/benchmark.py`.

```
DATA                                        SCREEN
samples                     1600            selective T. cruzi actives        8
assay values                9600            of those rotenoid-bearing         6
structures                102,330           background mean rot features  0.123
rotenoid structure keys       174           per-active counts: 84,17,14,12,10,9,0,0
multi-class structures      3,997
features pos              716,131           CONSENSUS COMPOUNDS (pos)
canopus pos               548,831           clusters before filtering    40,596
isdb pos                  288,332           ubiquity-dropped (>240)         147
distinct NPC class names      627           rare-dropped (<3 extracts)   27,896
  ...of which contain commas   22           surviving (isdb)             12,553
```

**Fitted gain: 43.91** (`decouple.calibration.fit_gain` on all rotenoid compound abundances; source: `results/benchmark.json` config). `scripts/threshold_curve.py` fits the same gain with `fit_gain` (`results/threshold_curve.json` records 43.91). **Nomination threshold: 0.85** (`config/enpkg.json`, `results/benchmark.json` config).

**Compound universe by annotation setting** ✅ — this choice decides what exists:

| mode | isdb | canopus | union |
|---|---|---|---|
| pos | 12,553 | 24,526 | 26,140 |
| neg | 4,675 | 13,416 | 13,720 |

**Assay panel** ✅ — asymmetric, and this decided the project's scope:

| organism | concentrations | >80% raw | selective (+L6<50%) |
|---|---|---|---|
| T. cruzi | 10 µg/mL **only** | 15 | **8** |
| T. brucei rhod. | 2 and 10 | 33 | 23 |
| L. donovani | 2 and 10 | 41 | 33 |

At 2 µg/mL only 2 extracts are selectively active for *L. donovani*, 4 for *T. brucei*.

---

# PART 2 — Scientific findings

### 2.1 Class-level counting does not work ✅ — this is the project's justification
Rotenoid share vs T. cruzi activity across 1,600 extracts: **Spearman ρ = 0.095**. The single most rotenoid-rich extract in the library — *Clitoria macrophylla* roots at **91.4% share** — is **not** a selective active (71.8% inhibition, 46.8% cytotoxicity). Rotenoid content is **neither necessary** (2 of 8 actives have none) **nor sufficient**. The published approach would hand a chemist a false lead.

**The same pattern holds independently for quinoline alkaloids** — three extracts carry more quinoline signal than *Melochia* and are inactive. Demonstrated twice, on unrelated chemotypes.

### 2.2 Confounding is real and decorrelating samples exist ✅
```
confounded distinct rotenoid pairs (co-occur >=3 extracts)  486
pairs where BOTH compounds appear in a selective active     362
pairs with >=1 strict decorrelating sample            485/486 = 99.8%
pairs with >=5-fold A:B ratio shift                   327/486 = 67.3%
decorrelating options per pair          median 25, max 1500, zero-option pairs 1
```
**Pair counts — two different quantities, both correct.** **486** = pairs that co-occur in >=3 extracts (confounded; the VALIDATION.md analysis). **238** = pairs in the benchmark: confounded (>=3 co-occurring extracts) **and** decorrelatable (each compound has an extract without the other), in the `pos` compound universe with no isomer filter. The 486 and 238 come from different scripts and are not reconciled against each other here.

### 2.3 Dose-response is real within species ✅
*P. erosus* — the traditional food/poison split, reproduced as a gradient inside one plant:

| organ | rotenoid share (ISDB) | (CANOPUS) | T. cruzi |
|---|---|---|---|
| leaves (poison part) | 65.5% | 21.9% | 112.2% |
| woody stems | 11.6% | 5.0% | 53.7% |
| roots (food part) | 4.0% | 0.2% | 0.0% |

Monotonic under both annotation tools. Feature **counts** do not show it (11 vs 10 features, opposite activity); abundance does.

### 2.4 ISDB is partly circular ✅
ISDB reweights candidates by plant taxonomy, so "Fabaceae contain rotenoids" risks being assumed rather than measured:
```
                        rotenoid calls    all other calls
spectral_score median        0.462             0.479      <- NOT better spectrally
taxo_score median            6.000             4.000      <- but boosted more
final_score median           8.750             6.882
taxo/final ratio             71.4%             68.5%
ZERO spectral support        17.8%              3.3%      <- 5.4x enrichment
```
**Mitigation adopted:** CANOPUS for class (spectra-only, no taxonomic prior); ISDB filtered to `spectral_score > 0`.

### 2.5 The annotation choice silently erases findings ✅
For *Melochia umbellata* (VGF156_A06), negative mode:

| annotation | compounds | in Melochia | quinoline compounds |
|---|---|---|---|
| isdb | 4,675 | 12 | **0** |
| canopus | 13,416 | 78 | 1 |
| union | 13,720 | 77 | 1 |

Under the ISDB-only universe the quinoline lead **does not exist** — no error, no empty result, nothing to notice. The benchmark universe (`isdb`, for reproducibility) and the lead-generation universe (`union`) are kept as separate explicit settings for this reason.

### 2.6 Ethnobotanical layer ✅📄
3 of 6 active species carry directly relevant traditional use, via **two different routes**:
- **Rotenoid actives are traditional poisons** — *P. erosus* seeds/leaves as insecticide and fish poison; *C. palala* seeds to poison rats and dogs. Toxicity-led knowledge.
- **One non-rotenoid active is a traditional antimalarial** — *Melochia umbellata*, Cameroonian folk medicine, 0 rotenoids yet 89.9% inhibition, quinoline-alkaloid signal.

*C. grevei* has no ethnobotanical record (its rotenoid chemistry was published in 1994). *D. heterophyllum* genus-level only. *P. pulcher*: topical/GI uses, **no antiparasitic record**.

**Rejected claim:** one source linked *P. pulcher* with *C. palala* for malaria. A dedicated search found no support; the malaria records in that genus belong to other species. Not claimed.

# PART 3 — Method findings

The shipped method has three parts: continuous attribution, **adaptive contrast** selection, and selectivity-aware nomination.

### 3.1 Attribution is continuous in abundance ✅
Decorrelating abundances are small (A-only extracts carry A at areas 0.0008–0.0188), below any sensible presence threshold. A compound present at trace level in an inactive extract does not exonerate it, so presence/absence carries no usable signal in the pairs that matter. Attribution therefore regresses activity on log-abundance and carries a detection floor, below which a sample is uninformative rather than negative. The worked example in [VALIDATION.md](VALIDATION.md) §5 shows the dosage effect on a real confounded pair.

### 3.2 Benchmark ✅ — `results/benchmark.json`
**Setup:** decision-model generator, single driver, potency-only nomination rule, unconstrained pool of 250 extracts, threshold 0.85, fitted gain 43.91, background 0.05, budget 3, 8 seed reveals, nominated candidate scored against the true driver. **"Accuracy" here means nominated-and-correct over all episodes — an abstention counts as a miss.** Sample: **952 episodes from 238 distinct compound pairs** (pairs that co-occur in ≥3 extracts and where each compound has an extract without the other). Hard stratum: **58 episodes from 16 pairs**. Easy: 894 episodes from 224 pairs. Reproduce: `python3.12 scripts/benchmark.py`.

| selection | hard accuracy | 95% CI | overall accuracy |
|---|---|---|---|
| No assays spent (reference) | 8.6% | [0.0, 24.1] | 22.1% |
| Random 3 (reference) | 8.6% | [0.0, 24.1] | 23.4% |
| Strongest-first, current practice (reference) | 19.0% | [6.9, 34.4] | 64.4% |
| **Adaptive contrast** | 19.0% | [6.9, 34.4] | 65.0% |

Precision is 100% for every selection (every nomination made was correct); selections differ only in how often they nominate.

**Pair-clustered CIs ✅** (2,000 resamples of whole compound pairs — episodes are *not* independent):

| margin | point | clustered 95% CI | pairs |
|---|---|---|---|
| Adaptive contrast − no assays, hard | +10.3 | [+3.8, +17.2] | 16 |
| Adaptive contrast − Random 3, hard | +10.3 | [+3.8, +17.2] | 16 |
| Adaptive contrast − strongest-first, **hard** | **+0.0** | **[0.0, 0.0]** — exact tie | 16 |
| Adaptive contrast − strongest-first, easy | +0.7 | [−0.3, +1.8] | 224 |
| Adaptive contrast − strongest-first, overall | +0.6 | [−0.3, +1.7] | 238 |
| Adaptive contrast − strongest-first, hard, **logistic generator** | +0.0 | [0.0, 0.0] — identical results | 14 |

**Reading:** on the hard stratum, no assays = random (8.6%) < strongest-first = adaptive contrast (19.0%). Choosing which three extracts to assay roughly doubles the hit rate over spending no budget; three extracts chosen at random are worth nothing. Adaptive contrast **ties current practice** on selection, so **we do not claim that it beats the chemist's default. Its value is in what it nominates (§3.6).** (Under the logistic generator the easy and overall margins are +1.3 [+0.3, +2.8] and +1.3 [+0.3, +2.5]; that is a small stress-test effect on the easy stratum, not a hard-stratum or headline claim.)

⚠️ **The hard stratum is 16 pairs.** That is the real sample size. Always quote the pair count next to any hard-stratum margin.

### 3.3 The baseline that matters is strongest-first, not random ✅
Strongest-first beats random by **+10.3 points on hard** [+3.8, +17.2], **+43.0 on easy** [+38.3, +47.6] and **+41.0 overall** [+36.7, +45.3] (238 pairs). Adaptive contrast does the same, no more: on the hard stratum the two are identical. Any claim framed against random alone overstates what adaptive contrast buys; the comparison against strongest-first is a tie.

### 3.4 Adaptive contrast ✅
Adaptive contrast restricts spread to the candidates the current evidence **cannot yet separate** (recomputed after each pick) and applies a redundancy penalty against extracts already picked. Mean pick overlap with strongest-first is **1.73 / 3** on the unconstrained 250-extract pool, so it does choose different extracts; the accuracy difference from strongest-first is +0.0 on hard [0.0, 0.0] and +0.6 overall [−0.3, +1.7]. **Accuracy alone cannot show how different two selections are; report pick overlap alongside accuracy.**

### 3.5 Chemist-realism checks ✅
These check the selection protocol against how a chemist would actually work, on the benchmark above (`results/benchmark.json`).

**(a) COVERAGE — the tool nominates only some of the time.** Adaptive contrast, threshold 0.85, nominating candidate scored against the true driver, abstentions counted as misses:

| stratum | nominates (= accuracy) | 95% CI | precision when it nominates |
|---|---|---|---|
| hard (58 episodes, 16 pairs) | **19.0%** | [6.9, 34.4] | 100% |
| easy (894 episodes, 224 pairs) | 68.0% | [63.8, 72.4] | 100% |
| overall (952 episodes, 238 pairs) | 65.0% | [60.4, 69.5] | 100% |

**On the hard cases the tool answers about one time in five; the overall 65% is dominated by easy episodes. Name the stratum whenever you quote a coverage figure.**

**(b) SYNERGY — it cannot express "both".** Truth = two drivers acting together (952 episodes, 238 pairs), adaptive contrast, threshold 0.85. Any single-driver nomination is wrong, so the false-nomination rate is simply the nomination rate:

| generator | rule | false-nomination rate | 95% CI |
|---|---|---|---|
| decision-model generator | potency-only | **1.5%** (14 of 952) | [0.7, 2.3] |
| decision-model generator | selectivity-aware | 0.8% (8 of 952) | [0.3, 1.5] |
| decision-model generator, hard stratum | either rule | 4.2% (1 of 24 episodes, 6 pairs) | [0.0, 12.5] |
| logistic generator | potency-only | 13.4% (128 of 952) | [10.5, 16.7] |
| logistic generator | selectivity-aware | 8.9% (85 of 952) | [6.7, 11.3] |

The system abstains correctly on almost all synergy episodes under the decision-model generator, and much less under the logistic one. Either way it can only ever name **one** compound when the truth is "both", which is the argument for a `{A, B, both, neither}` hypothesis space.

**Why the threshold is 0.85.** The rule (`scripts/threshold_curve.py`, `results/threshold_curve.json`) takes the lowest threshold on the grid with point precision of at least 95%, a pair-clustered precision lower bound of at least 85%, and a false-nomination rate under two-driver synergy of at most 5%. At 0.80 the synergy false-nomination rate is 8.3% (2 of 24 hard episodes), over the budget; at 0.85 it is 4.2% (1 of 24), within it. The response gain is fitted from the data (43.91), not hard-coded. The budget was checked on the hard stratum only (24 episodes, 6 pairs), so the 8.3% against 4.2% distinction is a single episode. Across all 952 episodes the decision-model generator is below 5% for both rules (1.5%, 0.8%); the logistic generator is above it for both (13.4%, 8.9%).

**(c) COMPARABILITY — same-batch selection.** Chemists prefer extracts from the same plate (same VGF batch) so that assays are comparable. Same-batch pool minus unconstrained pool, adaptive contrast, potency-only:

| | point | 95% CI |
|---|---|---|
| overall | −3.7 | [−7.9, +0.6] |
| hard stratum | +8.6 | [+1.6, +17.2] |

Same-batch selection was feasible in 952/952 episodes (smallest same-batch pool: 152 in the single-driver run). Caveat: the same-batch pool is drawn from the seed plates only, so it is a denser, more local sample than 250 of 1,600, which may help on its own; that design effect is not isolated. An uncomparable contrast is uninterpretable at any accuracy, so same-batch selection is kept on those grounds.

**(d) SELECTIVITY — why accuracy alone is the wrong score.** Rotenone is the most potent rotenoid and the worst candidate, so a benchmark scoring only "named the true driver" would mark the undevelopable answer correct. Real compound-level selectivity indices exist for exactly 3 compounds (rotenone 51.7, deguelin 1,148.5, tephrosin 1,937.0); the benchmark therefore scores *developable* nominations separately (§3.6).

### 3.6 Dual-channel selectivity — supported on wasted isolations, in simulation only
`scripts/selectivity_test.py` (design) and `scripts/benchmark.py` (numbers below). Semi-synthetic episodes on real abundances; **half the episodes make the parasite driver also the cytotoxicity driver by construction** (rotenone-like). Threshold 0.85, adaptive contrast selection, all 952 episodes from 238 pairs.

ENPKG measures *T. cruzi* inhibition **and** L6 host cytotoxicity on the same extracts in the same screen, so **one reveal buys both readouts at no extra assay cost**. Running the inference twice over identical `x`, once per channel, costs nothing.

| nomination rule | nominates | developable precision | **wasted isolations / 100 episodes** | developable accuracy |
|---|---|---|---|---|
| potency-only | 65.0% | 50.2% | **32.35** | 32.7% |
| selectivity-aware *(2 channels)* | 32.9% | 99.4% | **0.21** | 32.7% |

Developable accuracy is identical (difference 0.0 [0.0, 0.0]). **Identical accuracy, 154× fewer wasted isolations (32.35 to 0.21 per 100 episodes; difference −32.1 [−34.7, −29.5]). This is the project's headline.** Hard stratum only (58 episodes, 16 pairs): wasted isolations fall from 6.9 to 0.0 per 100 (difference −6.9 [−15.4, 0.0]); developable accuracy 12.1% for both rules (difference 0.0 [0.0, 0.0]).

⚠️ **The absolute rates depend on the 50% cytotoxic prevalence we assumed; they are not measured.** The simulation's trap rate is driven by that assumption, so it is not independent corroboration of the real rate.

**What real data does support:** of the 15 extracts with >80% *T. cruzi* inhibition, only 8 are non-cytotoxic — **7 of 15 (47%) raw potency hits are cytotoxic decoys** (Part 1 assay panel; not touched by the simulation). That shows the trap exists in the real screen; it does not validate the simulated rates.

**Verdict:** the evidence supports selectivity-aware nomination on wasted isolations, in a simulation where the second channel obeys the same model as the first. **It is not validated.**

### 3.7 Real-data run: the method abstains, correctly ✅🤖 — `results/real_case.json`
Adaptive contrast and attribution on real ENPKG data, no simulation; abstention threshold 0.6 on the attribution score. The selector never sees held-out activities.

| stage | top score | abstains? |
|---|---|---|
| 8 hits + 24 reference extracts | 0.769 (CI 0.51–0.99) | no |
| after 3 recommended assays | 0.753 | no |
| full 1,600-extract library | **0.468** (CI 0.22–0.63) | **yes** |

*Melochia* abstains at every stage (0.42 → 0.20). Given ρ = 0.095, abstention is the correct answer.

Top candidates are oxygenated rotenoids (CANOPUS 0.98–0.9999), not rotenone — chemically coherent, since the published isolation reported rotenone, deguelin **and tephrosin** (the hydroxylated member). Rotenone is rank 5 of 64. **cids 5659 and 9244 share one ISDB key at different retention times** — chromatographic isomers annotation cannot separate, i.e. the project's core problem appearing unprompted.

### 3.8 Novelty position 📄⏳
No prior work selects *extracts* to assay in order to resolve compound attribution. Nearest prior art is **BATCHIE** ([PMC11696745](https://pmc.ncbi.nlm.nih.gov/articles/PMC11696745/)) — Bayesian active learning for combination drug screens, same budget logic, but on pure compounds. Phrase as "to our knowledge" and cite BATCHIE.

---

# PART 4 — Open items

- ⏳ Only **16 distinct compound pairs** underpin the hard stratum (14 under the logistic generator, 6 and 7 in the two-driver runs). Widening it (looser decorrelatability criteria, or non-rotenoid chemotypes) would strengthen every hard-stratum claim more than any other single piece of work.
- ⏳ The 5% synergy false-nomination budget behind the 0.85 threshold was checked on the hard stratum only (24 episodes, 6 pairs; §3.5(b)). The threshold curve's primary selection policy is the code's default acquisition, not adaptive contrast: at 0.85 it nominates on 17.2% of hard episodes (10 of 58) against 19.0% (11 of 58) for adaptive contrast in the benchmark, and its own strongest-first re-score gives 19.0%. The 0.85 choice has not been re-derived with adaptive contrast picks.
- ⏳ Design choices unreviewed: starting set = 8 hits + 24 random non-hits; unknown activities of just-picked extracts imputed with the assayed mean during selection.

---

# PART 5 — Must NOT be claimed

1. **Never quote accuracy without "on semi-synthetic benchmarks."** Composition and confounding are real; the pharmacology is simulated — logistic dose-response, additive noise, a simulated cytotoxicity channel with an assumed 50% prevalence, and synergy only as a stress test.
2. **Never report pooled accuracy alone.** Hard cases are **6.7% of confounded pairs** (16 of 238 pairs; 58 of 952 episodes = 6.1%). Pooled numbers are dominated by cases needing no tool: overall minus hard is about 46 points for adaptive contrast (65.0% vs 19.0%) and about 45 for strongest-first (64.4% vs 19.0%).
3. **Never claim adaptive contrast beats current practice.** It ties strongest-first (hard stratum margin +0.0, CI [0.0, 0.0], 16 pairs; overall +0.6 [−0.3, +1.7]). Selection is worth about double the hit rate of spending no assays (8.6% to 19.0%) and random picks are worth nothing, but the same holds for strongest-first. The contribution is selectivity-aware nomination.
4. **Never call *Melochia* an identification.** It is a lead worth one of three assays.
5. **Never claim the rotenoid finding.** That is Gaudry et al., *RSC Adv* 2025. We reproduce it as a pipeline check.
6. **Never present MS annotations as confirmed identities.** Rotenone and deguelin are isomers of identical exact mass competing for one peak; the published team used authentic standards, we cannot.
7. **Never say "it can say neither" unqualified.** Quote the operating point (threshold 0.85) and the stratum: it nominates on 19.0% of hard episodes and 65.0% overall.
8. **Never call selectivity-aware nomination validated.** It is supported on wasted isolations in a simulation with an assumed 50% cytotoxic prevalence.
9. **Nothing is clinically validated.** Predicted attribution is a hypothesis; none of this is medical advice.
