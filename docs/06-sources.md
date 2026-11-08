# 06 · Sources, prior art and provenance

**Research cutoff:** 3 November 2026. The evidence below supports a scoped research proposal. No search can establish worldwide novelty, unpublished work, patentability or the performance of an unbuilt policy.

## Primary evidence and data access

| Source | What to take from it | Scope |
|---|---|---|
| [GigaScience plant extract dataset](https://doi.org/10.1093/gigascience/giac124) | Chemical profiling, scope and sample metadata for the collection | A spectral feature can be observed without a unique structure assignment. |
| [Sample-centric ENPKG paper](https://doi.org/10.1021/acscentsci.3c00800) | Existing integration of sample-level chemistry and biological screening; historical identification of the two anchors | Published identification and graph enrichment already exist. |
| [ENPKG snapshot, Zenodo record 7824642](https://zenodo.org/records/7824642) | Versioned graph files, schema and file-level checksums | Split historical observations, annotations and outcomes by provenance before use. |
| [Rotenoid follow-up, Table 1 and Fig. 2](https://doi.org/10.1039/D4RA08652J) | Compound IDs, purified-compound potency, cytotoxicity, selectivity and structural work | Selected isolates and newly prepared extracts. Verification is incomplete across the original collection. |
| [Follow-up GNPS task](https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=bef399e77f86411ab6857bce924f4b07) | Identity-ion feature-based network used in the follow-up | Preserve task ID and acquisition boundary. A completed job does not certify a cross-study identity match. |

## Closest competing methods

- **Feature–activity association.** NP Analyst maps chemical signals to biological response. Bioactivity-based molecular networking and ELINA already prioritize constituents from mixtures. Treat them as substantive prior art and comparator designs. [NP Analyst](https://doi.org/10.1021/acscentsci.1c01108) · [Bioactivity-based molecular networking](https://doi.org/10.1021/acs.jnatprod.7b00737) · [ELINA](https://pmc.ncbi.nlm.nih.gov/articles/PMC6668471/)
- **Multicomponent effects.** Interaction metabolomics explicitly studies synergists in mixtures. A single-driver assumption can be challenged by the experimental evidence. [Primary paper](https://doi.org/10.1021/acs.jnatprod.2c00518)
- **Prioritization and IP landscape.** INVENTA prioritizes extracts for chemical originality. Patent publications cover fraction screening with mass profiles. The research question here is whether sequential assay selection helps under a fixed budget. The earlier search was a public prior-art scan rather than a claims analysis. [INVENTA](https://github.com/luigiquiros/INVENTA) · [Patent publication EP2519816A2](https://patents.google.com/patent/EP2519816A2/en)
- **Spectral representation.** DreaMS self-supervises on experimental spectra and supports representation learning for unnamed chemistry. Its benefit for this isolation decision is a proposed ablation. [Original DreaMS paper](https://doi.org/10.1038/s41587-025-02663-3)
- **Experimental design.** Expected information gain and optimal experiment selection for competing models predate this project. The proposed decision score measures how much a reveal helps the final nomination. [Bayesian experimental design](https://pmc.ncbi.nlm.nih.gov/articles/PMC8924111/)

## User and organizer sources

| Source supplied | Role in this design |
|---|---|
| Benachour, Maloukh & Natsheh, *Machine Learning in Drug Discovery* | Review framing applicability limits, external validation and toxicity-aware interpretation. [Publisher record](https://doi.org/10.1109/ACCESS.2026.3741692) |
| Atalor, *Data-Driven Cheminformatics Models for Predicting Bioactivity of Natural Compounds in Oncology* | Review informing assay heterogeneity and the separation of binding, enzyme activity and cellular response. [Publisher record](https://doi.org/10.38124/ijsrmt.v1i1.496) |
| Dave et al., *Revolutionizing Natural Product Science with AI* | Review motivating provenance across modalities. Use the ENPKG deposit for executable data. [Publisher record](https://doi.org/10.18311/jnr/2025/48515) |
| Organizers’ datasets_all_tracks.docx.md | Resource directory. LOTUS can corroborate taxon–compound occurrence. PubChem can resolve structure identifiers. Neither supplies the sample-specific concentration or response needed for the decision. [LOTUS](https://lotus.naturalproducts.net/) · [PubChem](https://pubchem.ncbi.nlm.nih.gov/) |
| Earlier user-proposed Alzheimer and literature-prior papers | Context for the earlier BACE1 alternative and provenance-aware reasoning. Neither supplies the Chagas assay labels. [Alzheimer preprint](https://arxiv.org/abs/2604.18316) · [Literature priors](https://arxiv.org/abs/2508.10899) |

## Recheck before asserting originality

Search publications, preprints, public software and patent records for combinations of “active learning”, “optimal experimental design”, “bioactivity deconvolution”, “biochemometrics”, “natural product mixtures”, “isolation prioritization”, “Chagas”, “ENPKG” and “rotenoid”. Follow forward citations from ENPKG, NP Analyst and the rotenoid paper. Log search date, query, closest method, what the method selects and whether it reports a blinded, budget-matched comparison. Narrow the claim if someone has already published that workflow.

**Suggested submission wording:** “We evaluate whether selecting plant-extract assays for their ability to distinguish competing chemical explanations improves the final isolation choice under a fixed budget.” Replace “evaluate” with a measured result only after the locked replay is complete.
