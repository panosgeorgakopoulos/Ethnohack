# 03 · Product, model and feature specification

## User journey and acceptance criteria

| Feature | User action or system output | Acceptance criterion |
|---|---|---|
| Start a replay | Choose a frozen, eligible episode | Show endpoint, dose, known anchors, hidden assay count, three remaining reveals, one isolation slot and dataset version. |
| Compare explanations | Inspect the top competing feature groups | Show sample-level detection, assay evidence, number of discordant samples, batch and botanical context. Label tentative identities. |
| Select next assay | Display one sample and why it matters | Give the competing explanations, their predicted responses and the ranking change expected under each response. Use arbitrary feature IDs for blinded identities. |
| Reveal | Reveal one archived measurement | Charge one unit, show value and units, update ranking, append event to log. Repeated click or retry must reuse the event. |
| Nominate or abstain | Spend the isolation slot once or explain the ambiguity | Show nomination, closest competitor, evidence chain and model limitations. Terminate the episode. |
| Open evaluation | Reveal published outcomes after final decision | Show eligible matches, unresolved nominations, baselines and failures. Report model inputs separately from later evidence. |
| Export replay | Download a machine-readable audit trail | Include configuration, seed, dataset hashes, model version, selected samples, before/after rankings and result. Replaying with the same inputs reproduces the decisions. |

## Model the decision before adding a foundation model

1. **Chemical representation.** Begin with a normalized sample-by-ion-group matrix and conventional MS/MS similarity. Estimate preprocessing parameters using development data. If spectra and weights are accessible, cache frozen DreaMS vectors. Compare them with cosine similarity under the same candidate set. Spectral resemblance may suggest a family while leaving exact identities unresolved. [DreaMS](https://doi.org/10.1038/s41587-025-02663-3)
2. **Competing explanations.** In a small prespecified candidate set, enumerate a background-only hypothesis, each single driver and a limited number of two-driver combinations. For each fit a regularized response model on visible extract measurements. Use normalized feature abundances as predictors and account for measurable batch differences. For a continuous inhibition readout, model residual variation from training data; for a binary endpoint use a Bernoulli likelihood. Fix the endpoint and model class before evaluation. Compare additive and single-driver assumptions on development data. Co-occurrence alone cannot identify synergy.
3. **Belief update.** Weight hypotheses by prior probability and likelihood of visible results. Integrate coefficient uncertainty or use a frozen, documented approximation. Estimate the noise floor using replicates when present. Check predictive interval coverage on held-out assay observations. With poor calibration display scenario predictions and disagreements rather than precise confidence percentages.
4. **Value of one measurement.** Let the current utility be the largest estimated probability that a nominated feature contributes to parasite inhibition. For each hidden sample, draw possible assay results from the current predictive distribution, update the competing hypotheses for each draw, and recompute that maximum. The acquisition score is the expected increase in utility divided by assay cost. Use equal costs in the primary comparison. Recompute after each actual reveal. This is a one-step approximation to a three-step decision problem. [Bayesian experiment design](https://pmc.ncbi.nlm.nih.gov/articles/PMC8924111/)
5. **Selectivity boundary.** If comparable seed cytotoxicity data exist, a separately calibrated host-response model could inform utility. Otherwise the policy optimizes attribution of parasite activity; selectivity is evaluated only after the reveal. Never use later L6 results as a selection feature. Report the mismatch between the available training objective and the desirable isolation outcome.
6. **Stopping.** Stop at three reveals, exhaustion of informative samples, or a frozen decision threshold chosen on development episodes. Resolve score ties deterministically by sample ID. In a near-tie show the alternative action. Report acquisition scores below the estimated simulation error as indistinguishable.

**Illustrative decision.** Extract X contains A and B. Extract Y contains A while B is below detection. Both hypotheses expect X to inhibit the parasite. They disagree about Y. The policy may choose Y even if its predicted mean inhibition is lower. If Y is from a different batch with a different solvent, the contrast may be unusable. This example is schematic.

## System boundaries

Data ingestion → eligible sample/feature store → visible-view builder → policy → reveal controller → append-only episode log. Separately, outcome vault + frozen crosswalk → evaluator → result card. The policy receives features, visible labels, remaining budget and permitted metadata. Only the reveal controller can fetch a hidden extract result. Only the evaluator can fetch isolate outcomes. Enforce the boundary in data loading as well as the display.

Model a graph edge as subject, predicate, object, evidence type, assay or acquisition ID, source locator and visibility partition. Useful predicates include “observed in”, “resembles”, “confirmed by standard”, “measured in assay” and “predicted contributor”. A path must preserve whether an edge is measured, inferred or hypothetical.

**MVP:** local tabular storage, cached spectra where permitted, one endpoint, deterministic replay, four comparison policies and one evidence card. **Stretch:** spectral embeddings, richer acquisition costs, measured host-cell modelling, or a second collection. Choose extensions only after completing the blind replay. A graph database and a language model are optional.
