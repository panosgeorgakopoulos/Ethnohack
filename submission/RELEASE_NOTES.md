# Submission release

## Included version

The release incorporates Apostolos Dedeloudis's workbench redesign from commit `7c64284b304d081d4b2caa471596a9f4e00d5026`, including the specimen abundance strips, clearer candidate names and expandable specimen list. Scientific text was then corrected to distinguish measurements from model predictions, name the L6 assay without calling it human-cell data, and avoid treating a joint hypothesis as proven synergy.

The approved 10-slide deck and 8:14 video remain unchanged. Their captured interface precedes this redesign. The video discloses its reconstruction from archived engine states. Numbers and model behavior are preserved; the current interface has different wording and layout.

## Method distinctions

- The interactive selector is `decouple`: expected gain in threshold-aware nomination utility.
- `adaptive_contrast` is a separate policy in the benchmark/selection pipeline. Its hard-stratum accuracy ties strongest-first.
- The current workbench verdict starts with a set reaching 95% posterior mass, then applies a toxicity veto. Retained mass can fall below 95%.
- The headline 0.85-threshold nomination results and the set-valued metrics are separate evaluations.
- Archived parasite and host-toxicity outcomes are revealed together. This does not establish a prospective laboratory cost of zero for collecting a second channel.

## Reproducibility fixes

The documented `python -m src.enpkg_io` command now downloads missing inputs. The benchmark's small smoke runs now tolerate unavailable confidence intervals instead of crashing while printing them. A standalone integrity check verifies measured replay hashes and headline metrics. The browser font is served locally, so the app does not depend on Google Fonts.

## Source hygiene

Raw datasets, credentials, local sessions, Python/Node environments, intermediate renders and legacy media are excluded. Final videos belong in release assets rather than Git history. The final deck, narration, rendering source, caption files, source notices and small fixtures belong in the source tree. Existing historical branches and local originals are preserved.
