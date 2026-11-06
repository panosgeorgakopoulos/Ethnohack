# 04 · Retrospective evaluation protocol

## Freeze before opening the outcome vault

Write a dated configuration covering endpoint, eligible samples, dose, candidate groups, known anchors, utility, budget, baselines, metrics, matching tiers and seeds. State who already knows the tephrosin result. Assign a separate evaluator if available. This is a retrospective replay designed with knowledge of a published case; a fresh independent collection is required for prospective generalization.

**Two budgets.** A reveal buys one archived extract assay in a specified condition. An isolation slot buys one final feature nomination. The replay does not create a wet-lab measurement. Keep all replicate measurements from a specimen in the same partition; decide in advance whether one reveal returns a prespecified replicate or the full replicate summary.

## Episode construction

- Separate development and locked evaluation specimens by botanical group when feasible. Keep repeat acquisitions and derived samples together. Predeclare a second leave-genus-out analysis if enough groups survive; publish exclusions and per-group counts.
- Within an evaluation episode, expose a fixed seed set of measured extract outcomes and mask remaining eligible extract assays behind the controller. All policies receive identical seed information, candidates, masks, anchors and budget. A hidden assay can be selected only if an archived result exists.
- Define eligible candidates without later outcomes. Exclude known anchors from final nominations or show anchor recovery separately. Do not filter by whether a compound was later isolated. Score a second, clearly labelled comparison restricted to the mapped, tested panel to quantify performance conditional on verification.
- Keep later names, spectra-derived annotations, graph inference paths, publication text and assay labels out of policy access. Audit pretrained representation overlap if identifiable; publish unknown pretraining overlap. Keep the classical spectral baseline available.
- Hold a second pool of sentinel extract assays outside the purchasable pool so predictive performance can be evaluated after three queries without scoring the training reveals.

## Comparators

| Policy | Action at each turn |
|---|---|
| Random | Uniform eligible hidden sample; repeat with declared seeds. |
| Strongest predicted extract | Highest predicted parasite inhibition under the same response model. Tests whether exploiting strength is enough. |
| Static biochemometric ranking | Rank feature groups by correlation with visible response. Choose the untested extract richest in the leading group; recompute after each reveal. Document as our operational baseline. |
| Disagreement | Select the sample where candidate hypotheses disagree most. Tests whether accounting for the eventual isolation decision adds value. |
| Proposed policy | Expected improvement in final nomination utility per assay. |

Keep the final nomination rule the same when comparing acquisition policies. Compare cosine vs learned spectra with acquisition fixed. Include a zero-reveal result. Avoid attributing differences in representation, nomination and acquisition to the same change.

## Scorecard

**Primary decision endpoint.** With three assay reveals, report the share of final nominations meeting a frozen parasite potency and selectivity criterion among independently verified nominations. A proposed development criterion is parasite IC₅₀ ≤ 1 µM and reported L6 selectivity index ≥ 10. These are project operating thresholds. Freeze them before running comparisons and show sensitivity to both bounds. Record each decision as verified positive, verified below criterion, unresolved, or abstained.

**Verification coverage.** Report all four counts, the fraction of nominations with a verified outcome, and confirmed hits per episode across the entire open pool. For success fractions, give conservative and optimistic bounds by assigning unresolved nominations failure and success respectively; abstentions yield no isolation hit. These are bounds, not imputed measurements. A “hit rate among knowns” on its own rewards policies that select well-studied molecules.

**Other endpoints.** Record the rank of each verified hit after 0, 1, 2 and 3 reveals. Report time to first correct *provisional* nomination; episodes never reaching it are censored at the budget. In the fixed tested panel, show candidate count, anchors removed, and rank versus each baseline. Keep false confidence, assay duplicates and invalid identity links as separate checks.

**Extract-only fallback.** If exact compound identities cannot be linked, use reduction in prediction error on the untouched sentinel assays as the decision metric. For continuous measurements report paired change in mean absolute error from zero to three reveals. Clearly label this as an extract-level evaluation.

**Uncertainty.** Compare policies on paired episodes. Report group-level outcomes and bootstrap intervals over independent botanical groups only where sample size warrants. Repeated seeds on the same isolates describe policy sensitivity; they do not create additional biological discoveries.

## Failure tests and release conditions

1. Changing an unrevealed label or a later isolate name cannot change the policy's next action.
2. With perfectly co-occurring candidates, the system reports ambiguity; with shuffled assay labels, any gain must be scrutinized for leakage.
3. A repeat reveal cannot charge twice. A fourth reveal and a second isolation request must be rejected.
4. No isolate in a fresh acquisition is mapped by feature ID equality alone. An unresolved match remains unresolved after export.
5. Publish the fixed protocol, denominators, full comparison and a failure episode alongside the stage demo. If the baseline wins, report it.
