# Agent delivery contract

The coding execution order is defined in [07-implementation-plan.md](07-implementation-plan.md). Deliver a runnable local application and an auditable measured experiment.

| Artifact | Required contents |
|---|---|
| Application | Start episode, compare explanations, select and reveal an archived assay, update ranking, nominate or abstain, export |
| Data bundle | Permitted source snapshots or retrieval instructions, hashes, normalized tables, exclusions and identity tiers |
| Model bundle | Configuration, representation settings, five policies and deterministic replay |
| Evaluation bundle | Frozen episodes, complete policy comparisons, verification coverage, unresolved cases and failure examples |
| Evidence view | Source-backed observation, tentative identity, measured assay and prediction distinguished by evidence type |
| Offline release | Locked environment, exact commands, cached permitted inputs and a reproducible real episode |

Use the existing three-assay and one-isolation constraints. The offline demonstration follows an actual episode from competing explanations through measured reveals to the final nomination. Display uncertainty and unresolved identities as part of the application behavior. Export the same state shown on screen.

The integration agent verifies a clean install, deterministic replay, transactional reveal behavior, hidden-data isolation and interface execution. Scientific performance is reported from the frozen comparison regardless of which policy wins. Remaining source or identity gaps are attached to the release as explicit limitations.
