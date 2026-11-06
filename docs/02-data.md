# 02 · Data readiness and chemical identity

## Inventory

| Evidence | Use | Handling |
|---|---|---|
| [ENPKG v0.1.0](https://zenodo.org/records/7824642) | Original samples, spectra-related features, metadata, graph schema | Start with the schema, sample metadata and one ionization mode. Repository lists separate positive/negative feature files and checksums. Audit which triples carry screen outcomes before exposing metadata. |
| [Original profiling study](https://doi.org/10.1093/gigascience/giac124) and [ENPKG publication](https://doi.org/10.1021/acscentsci.3c00800) | Sample preparation, profiling, assay context and raw-data accession MSV000087728 | Archive version, access date, licence, checksums, preprocessing and exclusions. A study-wide accession does not guarantee every assay is complete. |
| [Later GNPS job](https://gnps.ucsd.edu/ProteoSAFe/status.jsp?task=bef399e77f86411ab6857bce924f4b07) | Network from newly prepared extracts and standards | Evaluation enclave only. Job previously returned DONE. Keep its acquisition and feature identifiers separate. |
| [Follow-up paper and supplement](https://doi.org/10.1039/D4RA08652J) | Table 1 compound outcomes, identity evidence, sample collection history | Double-enter endpoints and units. Resolve discrepancies against the original table. Literature-selected compounds give partial ground truth. |

## Data contract

Use stable composite identifiers and maintain the original identifiers beside them. One suggested interchange format is a set of tables with the following columns.

| Table · one row per | Required fields |
|---|---|
| Sample · physical extract | sample_id, study_id, voucher/specimen_id if available, taxon, plant_part, solvent, collection/batch, source_locator |
| Feature · aligned ion signal | feature_id, study/run, polarity, precursor_mz, retention_time and unit, adduct, spectral_reference, ion_group_id, alignment_method |
| Abundance · sample × feature | sample_id, feature_id, intensity, normalization, detection_status, QC_flag |
| Assay · endpoint observation | assay_id, sample_or_compound_id, organism, life_stage/cell_line, protocol, dose, value, units, qualifier, replicate_group, source_locator |
| Crosswalk · original feature × later isolate | source_feature, later_feature, compound_id, mapping_tier, supporting_evidence, conflicting_evidence, reviewer, decision |
| Manifest · source artifact | URL/accession, version/date, retrieved_at, checksum, licence or unresolved status, permitted use, visibility partition |

Keep biological absence, below-detection, failed acquisition and unmeasured distinct. Preserve censored values such as “>100”. Express concentration units on every row. A mixture measured in µg/mL cannot be directly compared with a pure compound in µM. For the MVP use a single compatible assay stratum and one ionization mode. Exclude ambiguous records with counts.

## Crosswalk audit before model development

1. Parse the schema and inspect at least one complete specimen–extract–feature path and one extract–assay path. Count uniquely joinable samples, biological replicates, missing assays, polarity, batch and genus coverage. Record counts for the actual eligible subset.
2. Confirm that local feature IDs have cross-sample meaning. Where they are file-local, align by validated chromatography and spectra or build consensus spectral groups. Group adducts, isotopes and in-source fragments before counting competing molecules. Keep the original signal IDs for traceability.
3. Trace rotenone and deguelin independently across the original collection, fresh extracts and standards. Check precursor mass, polarity/adduct, MS/MS and retention information; retention times are comparable only for compatible methods or after validated alignment. Formula or exact mass alone cannot resolve isomers.
4. Attempt every later isolate, including weak compounds. Classify matches as **A** (unique, defensible original-feature identity supported by a standard or compatible orthogonal evidence), **B** (plausible, unresolved structure), or **C** (family-level, conflicting or absent). A confirmed identity in the fresh extract alone does not qualify the historical feature for tier A. Preserve all plausible matches.
5. Freeze a reviewer-signed crosswalk before scoring. Summarize counts by tier, number of alternatives per match, and assay coverage. The policy must never read this table. Release only aggregate audit counts before evaluation.

**Compound-level go/no-go.** Require the two anchor identities plus at least one eligible non-anchor selective hit and several measured weaker competitors with uniquely auditable original features. A minimal panel demonstrates feasibility only. With one eligible selective hit, report its rank descriptively; do not estimate general discovery performance. If only family matches survive, switch explicitly to the extract-level endpoint in [the protocol](04-evaluation.md).

**Rights and availability.** Check dataset, spectra, model and code licences separately before distributing any bundle. Retain record-level attribution. When redistribution rights or a download are unresolved, link the accession and record the gap. GitHub availability alone does not establish reuse terms.
