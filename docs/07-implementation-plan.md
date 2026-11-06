# Coding-agent implementation plan

Execute the existing scientific specification as an autonomous software build. This document supersedes previous human staffing and time estimates. Use 02-data.md, 03-specification.md and 04-evaluation.md as the data, behavior and evaluation contracts. The coordinator assigns bounded tasks to coding agents and integrates their outputs.

**Target deliverable.** A local application that runs a real plant-extract episode, selects up to three archived assays, nominates one chemical feature or abstains, exposes its evidence, and compares the policy with four baselines. Include reproducible commands, frozen results and an offline replay.

| Agent | Owns | Required outputs |
|---|---|---|
| Coordinator/integration | Contracts, configuration, dependency lock, integration, release | Working environment, versioned interfaces, integrated application and reproduction commands |
| Data | Ingestion, normalization, chemical grouping and provenance | Source manifest, eligible tables, exclusions, identity crosswalk and data readiness report |
| Methods | Episode engine, response model, policies and evaluator | Persisted replay, five policies, frozen comparison report and scientific invariants |
| Interface | Application view and evidence presentation | Interactive episode, source cards, comparison results and export controls |

Run no more than three workers alongside the coordinator. Shared contracts belong to the coordinator. Each worker edits its assigned area and proposes contract changes through the coordinator. A single agent can execute the same dependency order sequentially.

**First coordinator task.** Inspect the repository and local instructions. Reuse existing working infrastructure. For a new repository, choose a single Python application, local tables, SQLite episode storage and a lightweight local web interface. Pin dependencies after confirming installation. Define shared typed records and one small synthetic development fixture. Mark fixture data as synthetic in every output. Place historical hidden outcomes outside the visible policy payload.

| Step | Assigned agent | Dependencies | Implementation and completion evidence |
|---|---|---|---|
| A0 | Coordinator | Existing handoff | Create environment, module boundaries and shared records; imports and fixture validation pass |
| A1 | Data | A0 | Download minimal source files from 06-sources.md, retain hashes, parse assays and sample observations; produce numerical join counts and exclusions |
| A2 | Methods | A0 | Implement episode transitions and transactional event storage against the fixture; repeated reveal, resume and budget invariants pass |
| A3 | Interface | A0 | Implement start, compare, reveal, nominate, abstain and export against the shared records; fixture mode is visible |
| A4 | Data | A1 | Group ions, freeze comparable assay subset and trace identity matches; export original identifiers, units, mapping tiers and evidence |
| A5 | Coordinator + Methods | A2, A4 | Run one authentic episode through a baseline; replay from saved events yields the same outcome |
| A6 | Methods | A5 | Implement competing explanations, expected-utility acquisition and four baselines; use identical candidates and starting observations |
| A7 | Interface | A3, A5 | Connect real persisted episodes and source evidence; prediction updates and remaining budget match the engine |
| A8 | Methods | A6 | Freeze evaluation configuration, execute paired episodes and export all outcomes, uncertainty and verification coverage |
| A9 | Coordinator | A7, A8 | Integrate, reproduce from a clean environment, exercise the real application and package offline inputs and results |

A1, A2 and A3 may run concurrently after A0. Complete A5 before adding model extensions or visual polish. A8 can run while the interface agent completes A7. Integration changes must preserve the frozen dataset and evaluation boundary.

**Repository ownership.** The data agent owns src/ingest and generated data manifests. The methods agent owns src/episodes, src/policies and src/evaluate. The interface agent owns src/app. The coordinator owns shared records, configuration, dependency files and top-level entry points. Generated outputs have explicit destinations and are written atomically. Agents must not overwrite another worker's files.

**Executable contract.** Implement prepare, audit, replay, evaluate and serve entry points. Every operation accepts an explicit configuration path and produces a structured success or failure result. Document the exact invocations after implementation. One configuration records source hashes, eligible assay condition, candidate filters, split identifiers, seeds, budget and model settings.

A visible episode contains permitted sample features, revealed assays, candidate IDs, budget and state revision. A policy returns a sample ID, acquisition score and competing predictions. The reveal controller receives episode ID, sample ID, expected revision and idempotency key. It validates eligibility and budget, appends one event and advances state in one transaction. Retries return the prior result. Nomination or abstention seals the episode. The evaluator alone loads hidden isolate outcomes and the crosswalk.

**Efficient model implementation.** Start with background and single-driver hypotheses, one endpoint and one ionization mode. Share the response model and final nomination rule across random, strongest-predicted, correlation, disagreement and expected-utility acquisition. Use frozen candidate filters derived from permitted observations. Cache feature matrices and reusable likelihood terms. Seed predictive simulation and compare 64 versus 128 draws on development episodes to establish action stability. Add pair hypotheses or DreaMS embeddings only after the complete measured comparison runs, and record their effect through an ablation.

**Agent handling of incomplete evidence.** Produce an explicit readiness artifact with matched sample counts, missing assays and identity tiers. Preserve ambiguous features. Continue implementation using the eligible measured subset. If only extract outcomes are evaluable, label the result as extract-level and keep compound-recovery status incomplete. Synthetic fixtures can exercise code but cannot satisfy the measured-replay requirement. A missing identity match must never be replaced with an invented label. Record unresolved implementation blockers with exact source, attempted action and affected requirement.

**Required automated acceptance.**

- Changing hidden labels or later compound names leaves the next policy action identical before reveal.
- A retry or concurrent reveal produces one charge and one event; a fourth reveal and a second nomination are rejected.
- Resume reconstructs the same visible state and deterministic action.
- Units, qualifiers, specimen grouping and identity tiers survive ingestion and export.
- Every policy sees the same episode, candidate pool and assay budget.
- Sentinel assays remain inaccessible to training, acquisition and tuning.
- Perfectly co-occurring candidates yield an ambiguity explanation.
- The interface completes a real start-to-export session and accurately displays persisted results.
- Fresh-environment reproduction generates the frozen report from the documented inputs.

**Agent completion report.** Return exact run commands, changed files, measured cohort size, evaluation results, passed acceptance checks and unresolved requirements. Include source hashes, configuration and replay logs in the release. Declare completion only when the actual measured application satisfies the contract; a working fixture is intermediate progress.
