# Field Map: Compound-Activity Attribution in Plant Extracts

Compiled 6 Nov 2026. Everything marked **[verified]** was checked hands-on by the team; **[cited]** comes from paper text or abstracts; **[unverified]** still needs checking.

---

## 1. The problem, as the field states it

A plant extract contains hundreds to thousands of compounds. The extract inhibits a parasite. Which compound did it? Classical answer: **bioassay-guided fractionation** — split the extract, re-assay each fraction, split the active one, repeat. It is slow, expensive, and it fails in a specific way: activity that depends on a minor component, or that is spread thinly, gets lost in the splitting.

The modern answer is to skip fractionation and infer attribution statistically across many extracts at once. That is the field our project sits in.

## 2. Timeline of the approach

| Year | Work | What it did | Limitation |
|---|---|---|---|
| 2018 | **Nothias et al.**, *J Nat Prod* 81(4):758–767, [PMID 29498278](https://pubmed.ncbi.nlm.nih.gov/29498278/) | **Bioactivity-Based Molecular Networking.** Maps bioactivity scores onto MS/MS molecular networks. Case study on *Euphorbia dendroides*, where classical fractionation had found nothing. | Correlational and univariate per feature. No handling of co-occurring compounds. |
| 2020 | [Feature-Based Molecular Networking](https://www.nature.com/articles/s41592-020-0933-6), *Nat Methods* | Added quantitative feature intensities to GNPS networking, which is what makes abundance-based correlation possible at all. | Infrastructure, not attribution. |
| 2022 | **Hops study**, [PMC9312012](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9312012/) | Elastic Net + Random Forest over extract composition to find anti-inflammatory principles. Claims to identify actives "without extensive and repetitive bioassay-guided fractionation." | Multivariate but still observational. Fixed dataset, no experiment selection. |
| 2024 | **ENPKG**, Gaudry et al., [*ACS Cent Sci*](https://pubs.acs.org/doi/10.1021/acscentsci.3c00800) | Sample-centric knowledge graph over 1,600 plant extracts, linking LC-MS features, structures, taxonomy and bioactivity. | A data resource. Attribution is left to the user. |
| 2025 | **Rotenoid follow-up**, [PMC12062876](https://pmc.ncbi.nlm.nih.gov/articles/PMC12062876/), *RSC Adv* 15:15240 | Used ENPKG to find that 6 of 8 T. cruzi-active extracts contained rotenoids, across taxonomically unrelated plants. Isolated and tested the compounds. | Class-count heuristic, not an algorithm. No budget, no selection policy. |

**The gap:** every method above is *observational*. None chooses which experiment to run next. That is the opening.

## 3. Known failure modes of correlation-based attribution [cited]

These are the reasons a naive "correlate feature intensity with activity" approach misleads, and each is a point we should address explicitly:

- **Multiple testing.** Thousands of features against one activity vector. FDR control (Benjamini–Hochberg) is needed; Bonferroni over-corrects.
- **Collinearity / co-occurrence.** Compounds from the same biosynthetic pathway travel together across samples, so their activity coefficients are not separately identifiable. **This is our problem statement.**
- **Ionization bias.** Compound classes ionize with different efficiencies, so detection is systematically skewed and correlations favour well-ionizing chemotypes.
- **Spectral library coverage.** Public libraries cover a small fraction of natural product diversity, so annotations carry false positives.
- **Phylogenetic confounding.** Co-occurrence is partly driven by shared ancestry, so related plants are not independent samples. The rotenoid case is notable precisely because the active plants were *not* closely related.

## 4. Adjacent fields with the machinery we need

**Group testing and compressed sensing.** The mathematically identical problem is solved in pooled testing: given pools of items and pool-level readouts, identify which items are positive. Recovery of *k* positives among *n* items takes O(*k* log *n*) tests with suitable pooling matrices.
- [Tapestry](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8545028/), pooled RT-PCR: combinatorial group testing + compressed sensing, quantitative readout, single round.
- [Compressed phenotypic screening](https://www.nature.com/articles/s41587-024-02403-z), *Nat Biotechnol* 2024: N perturbations into pools of size P with R replicates, deconvolved with an interaction term.
- Classical orthogonal pooling in HTS: each compound assayed twice in differently-composed pools.

**The twist that makes our problem different, and is the pitch line:** in pooled screening you *design* the pools. In natural products, **nature already did the pooling** — each plant is a pool you cannot alter. The design freedom is not pool composition but **pool selection**: which of the available extracts to spend your assay budget on. That reframes it from compressed sensing to a subset-selection / optimal-design problem, and as far as this search found, nobody has published it for extract dereplication. **[unverified claim of novelty — worth one more literature check before claiming it in the video]**

**Multiple Instance Learning.** The natural ML formulation: a bag (extract) is labelled active iff at least one instance (compound) is active. MIL has been used in drug activity prediction, treating a molecule as a bag of conformers ([MILES implementation](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3439725/)), but this search found **no MIL benchmark on extracts**.

## 5. The dataset — verified today, and it is better than expected

**[verified]** [Zenodo 7824642](https://zenodo.org/records/7824642), "ENPKG from 1,600 plant extracts", **CC-BY-4.0**, ~290 MB of Turtle files. It was downloaded and parsed locally.

What is actually in it:

| Layer | Contents | File |
|---|---|---|
| Samples | 1,600 extracts, species name + Wikidata taxon ID, organ/tissue/subsystem | `metadata_enpkg.ttl.gz`, `metadata_demo.ttl.gz` |
| **Bioactivity** | **9,600 values** = 1,600 extracts × 6 assays, as `inhibition_percentage`, with `target_id` linking to ChEMBL | `metadata_demo.ttl.gz` |
| **Composition** | LC-MS features per extract with `has_feature_area` and **`has_relative_feature_area`** (quantitative abundance), parent mass, retention time | `features_pos.ttl.gz` (44 MB), `features_neg.ttl.gz` |
| Annotations | ISDB structural annotations, SIRIUS, CANOPUS chemical classes | `isdb_*.ttl.gz`, `sirius_*.ttl.gz`, `canopus_*.ttl.gz` |
| Networks | Individual and meta molecular networks, spectral pairs | `indivual_mn_*.ttl.gz`, `meta_mn_*.ttl.gz` |

The assay panel per extract: **T. cruzi** (10 µg/mL), **T. brucei rhodesiense** (2 and 10), **L. donovani** (2 and 10), and **L6 rat myoblast cytotoxicity** (10) — so selectivity, not just potency.

**[verified] The paper's headline screening result was reproduced** from this data in minutes:

```
Tcruzi_10ugml:        n=1600  median=0.0   >80% inhibition: 15
Tbruceirhod_10ugml:   n=1600  median=15.7  >80% inhibition: 33
Ldonovani_10ugml:     n=1600  median=9.5   >80% inhibition: 41
L6_10ugml (cytotox):  n=1600  median=6.7   >80% inhibition: 7

T. cruzi >80% AND L6 cytotoxicity <50%  ->  8 extracts
```

Eight selective T. cruzi actives, matching the published count exactly, and 6 of those 8 are the rotenoid-containing ones from the 2025 follow-up.

### The assay panel

Eight selective *T. cruzi* actives is a small sample. The panel is broader: raw >80% inhibition counts are 33 for *T. brucei* and 41 for *L. donovani* (selective counts after the L6 filter: 23 and 33; see FINDINGS.md Part 1). *T. cruzi* is the headline case study because its ground truth is published.

### Ground truth for the case study [cited]

From the 2025 RSC Adv paper: rotenone IC₅₀ **0.01 µM**, deguelin **0.02 µM**, tephrosin **0.04 µM** against intracellular amastigotes; compounds 29–36 inactive. Deguelin in 5 of 6 rotenoid extracts, rotenone in 4 of 6 — a genuinely confounded pair in real data. Source plants: *Derris heterophyllum*, *Cordyla grevei*, *Pachyrhizus erosus*, *Casearia palala*.

### Licence note for the submission

The Zenodo **data** record is CC-BY-4.0. The ENPKG **ontology file** declares CC-BY-NC-SA-4.0. Cite both separately in the README; the rules require per-dataset licence documentation.

## 6. Other resources checked

- **SPARQL endpoint:** https://enpkg.commons-lab.org/graphdb/repositories/ENPKG — live but returned HTTP 400 to our query formatting. **[unverified]** Working queries exist in the ACS paper and in [MetaboT](https://arxiv.org/pdf/2510.01724), an LLM agent framework over this same graph with a question→SPARQL evaluation set. Not needed if we parse the Turtle locally, which worked fine.
- **Code:** https://github.com/enpkg (`enpkg_full`, `enpkg_meta_analysis`).
- **ChEMBL:** T. cruzi organism target `CHEMBL368` has **101,929 activities [verified]** — useful as a compound-level prior, and the same ID the ENPKG bioassay nodes point to.
- **ChEMBL-NTD:** https://chembl.gitbook.io/chembl-ntd — GSK TCAKS and DNDi Chagas deposited sets, pure compounds.
- **Broad T. cruzi screen:** PubChem AID 2044. **[unverified]**

## 7. Verdict on the reference links collected

Triaged all 15. **None contains a method we can copy.** Breakdown:

- **Off-topic:** DrugRAG (pharmacy licensure Q&A), beauty/cosmetics MD perspective, TorchDrug (a library), BIT foundation model (Alibaba, structure-based), a TCM drug-likeness GNN thesis, Alzheimer's QSAR on 66 compounds.
- **Generic reviews, citable at most:** "Learning to Discover Medicines", PNNL autonomous molecular design, Romano & Tatonetti 2019 NP informatics, Lavecchia foundation models.
- **Genuinely relevant:** **Mullowney et al. 2023, "Artificial intelligence for natural product drug discovery"**, *Nat Rev Drug Discov* — the field's main review, worth reading properly. And "Nature meets machine" (*Nat Prod Bioprospect* 2026, [PMC12953908](https://pmc.ncbi.nlm.nih.gov/articles/PMC12953908/)), which frames ML-driven dereplication and notes that negative results go unpublished.
- **Possibly useful dataset:** [Medex](https://huggingface.co/datasets/medexanon/Medex), 32.3M literature-mined facts linked to SMILES, as a compound-level prior.

## 8. Where this leaves us

The position is unusually good for a hackathon:

1. The problem is real, named in the literature, and unsolved in the specific form we are attacking (collinear co-occurrence).
2. The prior art is **observational**; the design/budget framing is open.
3. The data is public, CC-BY, and verified working — composition, quantitative abundance, a four-readout assay panel, and published isolation ground truth for a real confounded pair.
4. There is a clean one-line pitch: *nature already pooled the compounds; our contribution is choosing which pools to open.*

## 9. Two feasibility checks — run 6 Nov, both pass

### Check 1: is the case study reachable from the public data? **[verified] YES**

Full join run locally: `structures_metadata.ttl.gz` → 174 rotenoid `InChIKey2D` keys (NPClassifier class `npc_Rotenoids`, rotenone `JUVIOZPCNVVQFO` among them) → `isdb_pos.ttl.gz` annotations → the 8 selective T. cruzi actives.

```
BACKGROUND (n=1592): mean rotenoid-annotated features = 0.12, median = 0, max = 29

VGF155_D05:  10 rotenoid-annotated /  359 annotated   <== ROTENOIDS
VGF139_H07:  84 rotenoid-annotated /  325 annotated   <== ROTENOIDS
VGF146_E08:  12 rotenoid-annotated /  166 annotated   <== ROTENOIDS
VGF146_F09:   9 rotenoid-annotated /  183 annotated   <== ROTENOIDS
VGF145_G09:   0 rotenoid-annotated /  171 annotated
VGF150_H08:  17 rotenoid-annotated /  379 annotated   <== ROTENOIDS
VGF150_A09:  14 rotenoid-annotated /  468 annotated   <== ROTENOIDS
VGF156_A06:   0 rotenoid-annotated /  325 annotated

==> 6 of 8 carry rotenoid annotations — exactly the published 6 of 8.
```

Background mean 0.12 versus 9–84 in the actives. The signal is enormous and the published finding is fully reproducible from CC-BY data. The same join is implemented in `src/enpkg_io.py` and `scripts/build_abundance.py`.

**Important caveat that shapes the design.** ISDB annotations are **multi-candidate per feature**, each carrying `has_spectral_score`, `has_taxo_score`, `has_consistency_score` and `has_final_score`. One feature routinely maps to several candidate structures. Rotenone's exact key appears in only 1 of the 6 rotenoid extracts, whereas the published work put deguelin in 5 of 6 and rotenone in 4 of 6 — because they confirmed identity with **authentic standards**, which ISDB cannot do. Rotenone and deguelin are isomers (both C₂₃H₂₂O₆, identical exact mass), so they compete as candidate annotations for the same feature.

Consequences for what we build:
- Attribution should operate on **annotation candidates with uncertainty**, or at **chemical-class level** (where the 6/8 signal is clean and reproducible), not on assumed-correct single-compound identities.
- Annotation ambiguity is a *second* confounder stacked on co-occurrence. Handling it explicitly is a rigor win, and pretending identities are certain would be the easiest way to get torn apart in judging.

### Check 2: novelty of "extract selection under assay budget" **[verified] CLEAR**

Two searches found no prior work selecting *extracts* to assay in order to resolve compound attribution. The nearest neighbours, all on pure compounds rather than mixtures:

| Work | What it does | Distance from us |
|---|---|---|
| **BATCHIE**, [PMC11696745](https://pmc.ncbi.nlm.nih.gov/articles/PMC11696745/) | Bayesian active learning for **combination** drug screens. Designs an optimal batch, runs it, updates the model, stops when the budget runs out or the posterior converges. | **Closest analogue — this is the template to adapt.** Same structure (which component of a combination drives the effect), same budget logic. Cite it and say what we changed. |
| [Pool-based active learning for virtual screening](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8188596/) | Surrogate models prioritise molecules by predicted docking score; compares acquisition functions and batch sizes. | Virtual, single compounds, no attribution. |
| [Batched BO for drug design](https://pubs.acs.org/doi/10.1021/acs.jcim.2c00602) | Batched Bayesian optimisation, 100 molecules/batch, robust to assay noise. | Optimisation, not deconvolution. |
| MVS-A, [PMC11046457](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11046457/) | Flags likely false positives among primary HTS hits via GBM learning dynamics. | Triage of hits, not attribution across co-occurring compounds. |

Active learning is well established for choosing *compounds* to screen. Nobody found doing it for choosing *extracts* to deconvolve mixture attribution. The novelty claim is safe to make, phrased as *"to our knowledge"* and cited against BATCHIE as the nearest prior art.
