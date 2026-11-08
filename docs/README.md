> **Historical design documents.** These describe earlier planning and reconstructed-data prototypes. For the submitted measured-data workbench, use the root [README](../README.md), [FINDINGS](../FINDINGS.md) and [release notes](../submission/RELEASE_NOTES.md).

# Three assays, one isolation

**Design notes · 6 November 2026 · research and design stage**

A natural-products chemist has several plant extracts that inhibit intracellular *Trypanosoma cruzi*. Two chemicals often appear together. Which extract should the chemist assay next to decide which chemical is worth isolating? The proposed system chooses up to three measurements and makes one nomination, with an evidence trail. It can also report that the library cannot resolve the question.

| Read in order | What the reader can decide |
|---|---|
| [01 · Scientific brief](01-science.md) | What the project contributes, why Chagas fits, and which claims the evidence supports |
| [02 · Data and identity audit](02-data.md) | Whether the experiments and chemical identities can actually be joined |
| [03 · Product and model specification](03-specification.md) | What to implement, what a user sees, and how to select a measurement |
| [04 · Evaluation protocol](04-evaluation.md) | How to hide outcomes, compare policies and interpret incomplete ground truth |
| [06 · Sources and prior art](06-sources.md) | Which dataset, paper, attachment or comparator supports each decision |

**Status at the time.** The collection and its follow-up existed; the feature-to-isolate crosswalk and the measured replay were still to be built. The earlier BACE1 prototype is a separate project.
