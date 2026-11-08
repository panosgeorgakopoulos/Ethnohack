> **Historical design documents.** These describe earlier planning and reconstructed-data prototypes. For the submitted measured-data workbench, use the root [README](../README.md), [FINDINGS](../FINDINGS.md) and [submission checklist](../submission/READINESS.md).

# Three assays, one isolation

**Project handoff · updated 6 November 2026 · research and design stage**

A natural-products chemist has several plant extracts that inhibit intracellular *Trypanosoma cruzi*. Two chemicals often appear together. Which extract should the chemist assay next to decide which chemical is worth isolating? The proposed system chooses up to three measurements and makes one nomination, with an evidence trail. It can also report that the library cannot resolve the question.

| Read in order | What the reader can decide |
|---|---|
| [07 · Implementation plan](07-implementation-plan.md) | Coding entry point, dependency-ordered tickets, interfaces, time limits and completion checks |
| [01 · Scientific brief](01-science.md) | What the project contributes, why Chagas fits, and which claims the evidence supports |
| [02 · Data and identity audit](02-data.md) | Whether the experiments and chemical identities can actually be joined |
| [03 · Product and model specification](03-specification.md) | What to implement, what a user sees, and how to select a measurement |
| [04 · Evaluation protocol](04-evaluation.md) | How to hide outcomes, compare policies and interpret incomplete ground truth |
| [05 · Delivery and demo](05-delivery.md) | Required application artifacts and release acceptance |
| [06 · Sources and prior art](06-sources.md) | Which dataset, paper, attachment or comparator supports each decision |

**Implementation status.** The collection and its follow-up exist. The coding agents must establish the usable feature-to-isolate crosswalk and produce the measured replay. The earlier BACE1 prototype is a separate project.

**Execution model.** A coordinator coding agent owns integration and shared contracts. Data, methods and interface agents execute bounded tasks with explicit file ownership. Start with [the coding-agent implementation plan](07-implementation-plan.md). The software retains three assay reveals, one isolation decision and reproducible offline evaluation.
