# DECOUPLE — Which molecule did it?

## Selected challenge track
Track 2: Natural Products & Drug Discovery

## Short description
DECOUPLE helps researchers choose which plant extracts to assay next when candidate compounds co-occur. It combines parasite inhibition with host-cell toxicity to support cautious compound nomination under a limited assay budget.

## Problem and motivation
An active plant extract contains many compounds. Compounds that occur together can explain the same activity, so existing observations may not distinguish them. Choosing a compound for isolation too early can waste experimental effort. Potency alone also risks prioritising general cytotoxins. We wanted to help researchers decide which observation would reduce that uncertainty before committing to isolation.

## Solution and approach
DECOUPLE selects extracts whose candidate abundances differ, using adaptive contrast and a redundancy penalty. After each reveal it updates competing explanations: A, B, both, or neither. Continuous log-abundance modelling treats trace signals differently from informative negative evidence.

The workbench uses expected gain in threshold-aware nomination utility; adaptive contrast is a separate evaluated selection policy. The workbench shows assay recommendations, archived measured outcomes, model probabilities, and an exportable decision trace. Its set-valued decision rule can return a nomination, shortlist, joint explanation, abstention, or cytotoxicity veto. These are model-based hypotheses requiring experimental confirmation. A joint explanation does not establish synergy or prove that fractionation would lose activity.

Two distinct evaluations appear in the project: threshold-based single-compound nomination benchmarks, and evaluation of the current set-valued decision rule. Their metrics are not interchangeable.

## Technologies used
Python, NumPy, RDKit, pytest, and a browser interface built with HTML, CSS and JavaScript. The data pipeline uses ENPKG mass-spectrometry annotations and assay records. Manim and FFmpeg produce the presentation videos, with ElevenLabs narration and Geist typography. AI coding assistance supported development. DECOUPLE's scientific decisions use explicit statistical rules rather than an LLM.

## Data sources and attribution
The ENPKG archive provides measured abundance and assay data for 1,600 extracts. The benchmark uses real composition and co-occurrence with simulated activity and cytotoxicity. Compound annotations are candidate identities, not structures confirmed with authentic standards.

ENPKG: https://zenodo.org/records/7824642 — Gaudry et al., *A Sample-Centric and Knowledge-Driven Computational Framework for Natural Products Drug Discovery*, ACS Central Science (2024). Project documentation records the data licence as CC BY 4.0 and the ontology's separate licence as CC BY-NC-SA 4.0. ChEMBL cross-references are attributed separately under CC BY-SA 3.0. Dataset files are downloaded by the pipeline rather than bundled as source code. See README.md and ETHNOBOTANY.md for attribution and individual traditional-use sources.

The published rotenoid result belongs to Gaudry and colleagues (RSC Advances, 2025). Reproducing it checks our pipeline. Our work comprises the attribution and selection implementation, nomination rules, benchmark, workbench and provenance analyses.

## Results and prototype demonstration
On semi-synthetic benchmarks of 952 episodes from 238 compound pairs, adaptive contrast and strongest-first each nominate the true driver in 19.0% of hard episodes, compared with 8.6% without extra assays. The hard stratum contains only 58 episodes from 16 pairs. The 95% pair-clustered interval for each 19.0% estimate is 6.9–34.4%. Adaptive contrast does not outperform strongest-first on this stratum.

In the same semi-synthetic benchmark, selectivity-aware nomination reduces simulated wasted isolations from 32.35 to 0.21 per 100 episodes while preserving 32.7% developable accuracy overall. This assumes 50% cytotoxic-driver prevalence. On hard episodes, developable accuracy is 12.1% for both rules and wasted isolations fall from 6.9 to 0.0 per 100. These are simulation results, not measured isolation savings or validated clinical outcomes.

The measured screen provides a separate motivation: 7 of 15 extracts above 80% parasite inhibition fail the host-toxicity criterion. That observation does not validate the simulated effect size.

The product demo is a Manim reconstruction using states captured from the engine on archived ENPKG measurements. It is not a live browser recording or a new laboratory experiment. Model probabilities and verdicts are computed outputs. The benchmark panel uses simulated responses.

## Team members
- Panos Georgakopoulos
- Apostolos Dedeloudis

## Impact and future development
The intended benefit is better allocation of limited follow-up assays and fewer premature isolation decisions. This benefit still requires prospective testing. Next steps are to test recommendations against strongest-first in a blinded laboratory study, expand beyond the small hard stratum, test sensitivity to response-model assumptions and cytotoxic prevalence, and confirm candidate identities and joint effects with purified-compound and mixture experiments.

## Responsible research and limitations
Nothing here is clinically validated. Attribution is a hypothesis for experimental follow-up, not evidence of therapeutic efficacy. Simulation and inference share modelling assumptions, so benchmark success is not independent biological validation. Annotation uncertainty, taxonomic priors and the small hard stratum limit interpretation.

Traditional knowledge belongs to its knowledge holders. We claim no ownership over it. Published records retain their source attribution and cultural context. Any future collection, access or development requires review of applicable permissions and benefit-sharing obligations. This project does not establish legal clearance for downstream use.

## Submission links to complete
- Source repository: https://github.com/panosgeorgakopoulos/Ethnohack
- Pitch video: add the final hosted video URL
- Slide deck: attach the accompanying deck
- Optional app: add a tested public URL, or use the README's local launch instructions
