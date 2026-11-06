# Validation: Testing the Project's Premise on Real Data

Run 6 Nov 2026. Every number here was computed locally from [Zenodo 7824642](https://zenodo.org/records/7824642) (CC-BY-4.0); nothing is quoted from a paper.

**Verdict: the premise holds.** Scripts: `scripts/build_abundance.py`, `features_mz_rt.py`, `consensus_cooccur.py`, `decorrelatability.py`, `worked_example.py`.

---

## 0. What we extracted

Quantitative abundance from `features_pos.ttl.gz`:

```
annotated features with m/z + RT + relative area : 288,332
consensus compounds (m/z ±0.01 Da, RT ±0.2 min)  :  40,596
  ... carrying >=1 rotenoid candidate annotation :     225
  ... of those, present in >=3 extracts          :     121
```

Runtime ~14 s, pure standard library, no numpy or RDKit. The whole pipeline is dependency-free, which is worth keeping for reproducibility.

**A naming trap to avoid in the write-up:** "84 rotenoid features" (features with a rotenoid candidate) and "25 rotenoid compounds" (distinct structures implicated) are different quantities for the same sample. Label them explicitly every time.

---

## 1. Dose-response confirmed — abundance beats count

Feature counts do not show the *P. erosus* gradient (11 vs 10 features, opposite activity). On abundance it is a clean monotonic series:

| Sample | Organ | Rotenoid share of annotated signal | T. cruzi % |
|---|---|---|---|
| VGF139_H07 | leaves | **65.5%** | 112.2 |
| VGF139_A08 | woody stems | 11.6% | 53.7 |
| VGF139_B08 | roots | 4.0% | 0.0 |

**Design consequence:** every downstream model uses relative area. Presence/absence is not a usable signal, and neither is feature count.

---

## 2. The simple rotenoid story does not generalise — and that is the project's justification

Across all 1,600 extracts, rotenoid share is a **weak** global predictor of activity:

```
Spearman(rotenoid share, T. cruzi %), n=1600 :  rho = 0.095
extracts WITH rotenoid signal    n=  86 : median T. cruzi =  0.0%  (mean 13.3%)
extracts WITHOUT                 n=1514 : median T. cruzi =  0.0%  (mean  3.1%)
Top-15 extracts by rotenoid share -> only 5 are selective actives
```

The single most rotenoid-rich extract in the library, *Clitoria macrophylla* roots at a **91.4%** rotenoid share, reaches only 71.8% inhibition with 46.8% cytotoxicity — it is not a selective active. *Flacourtia jangomas* at 12% share is flat at 0.0%.

So rotenoid content is **neither necessary** (2 of the 8 actives have none) **nor sufficient** (many rotenoid-rich extracts are inactive).

This is the strongest argument for the project. The published approach — count rotenoid annotations per extract and follow the enrichment — would hand a chemist *Clitoria macrophylla* as a top lead. Class-level counting is not enough; attribution has to be quantitative and compound-level. **That gap is exactly what we are building to close.**

---

## 3. Confounding is real and widespread

Among the 121 rotenoid compounds present in ≥3 extracts, after excluding pairs that are really the same chromatographic peak:

```
distinct rotenoid compound pairs co-occurring in >=3 extracts : 486   (confounded pairs; NOT the benchmark's 238 confounded-and-decorrelatable pairs)
pairs where BOTH compounds appear in >=1 selective active     : 362
```

The premise is not hypothetical. There are hundreds of genuinely confounded pairs in this dataset, and 362 of them touch an active extract.

---

## 4. Decorrelating samples almost always exist — this is the key result

The core move depends on finding a sample where co-occurring candidates come apart. They do:

```
STRICT    (one compound present, the other absent) : 485/486 = 99.8%
PRACTICAL (A:B abundance ratio shifts >=5-fold)    : 327/486 = 67.3%

decorrelating options per pair : median 25, max 1500, pairs with zero options: 1
max A:B fold-shift across co-occurring extracts : median 11.5x, 90th pct 268x, max 8827x
```

**Median 25 available options per confounded pair.** That is the ideal shape for the project: enough choices that selection is a real decision, not enough that any choice works. If there were one option the problem would be trivial; if there were none it would be impossible.

---

## 5. Dosage: presence is not exoneration

A worked example on a confounded pair where both compounds appear in actives and both have ample decorrelating samples:

```
A = m/z 353.1024 @ RT 3.05   (28 extracts,  2 active)
B = m/z 355.1176 @ RT 2.98   (33 extracts,  1 active)
co-occurring: 11 extracts     A-only: 17     B-only: 22

VERDICT from held-out evidence:
  A-only extracts: median T. cruzi =  0.0%  (n=17)
  B-only extracts: median T. cruzi =  0.0%  (n=22)
```

Both medians are zero. A presence/absence reading of this pair would assign credit to B, a verdict that is **statistically meaningless**.

The reason is dosage. In most A-only extracts, A is at trace level (areas 0.0008–0.0188). A compound present at trace in an inactive extract does **not** exonerate it, and the §1 dose-response is why.

**Design consequences:**
1. Attribution must regress activity on **abundance**, not presence — and it carries a detection floor, below which a sample is uninformative rather than negative.
2. The selection objective is not "find a sample where B is absent" but **"find a sample where A is abundant and B is below its effect threshold."** That is a meaningfully harder and better-posed criterion.
3. The model must be able to conclude **"neither"** — most candidate compounds are not drivers, and a method that always names a culprit will name the wrong one.

---

## 6. Data quality: ubiquitous misannotations must be filtered

```
m/z 295.2268 @ RT 4.81  annotated as rotenoid in 1502/1600 extracts
m/z 343.1182 @ RT 3.24  in 44/1600
m/z 343.1183 @ RT 3.31  in 39/1600
```

A "rotenoid" in 94% of all plant extracts is a ubiquitous background ion or a misannotation, not a rotenoid. Left in, such compounds inflate the mean decorrelating-option count (372, against a median of 25).

**Filter rule for the pipeline:** drop compounds present in more than ~10–15% of the library before attribution, and report how many were dropped. This is cheap and defensible.

---

## 7. Annotation tool choice changes the numbers — and ISDB is partly circular

ISDB, CANOPUS (spectral class prediction with probabilities) and negative-ionization mode give different views of the same extracts.

**7a. ISDB and CANOPUS agree on *which* extracts, disagree on *how much*:**

| Sample | Species | ISDB pos | CANOPUS pos | CANOPUS neg |
|---|---|---|---|---|
| VGF139_H07 | *Pachyrhizus erosus* | 65.5% | 21.9% | 1.5% |
| VGF146_E08 | *Cnestis palala* | **2.7%** | **49.6%** | 6.8% |
| VGF146_F09 | *Cnestis palala* | 2.2% | 51.8% | 4.8% |
| VGF155_D05 | *Desmodium heterophyllum* | 0.4% | 15.1% | 4.2% |

Agreement on presence is 7/8; magnitudes differ by up to 20×. **Cross-species magnitude comparisons are not stable across annotation tools.** Within-species organ contrasts *are* — the dose-response reproduces under both:

```
P. erosus   leaves 21.9%  ->  stems 5.0%  ->  roots 0.2%     (CANOPUS)
            112.2%            53.7%           0.0%           (T. cruzi)
C. palala   roots 49.6% / stems 51.8% active;  leaves 0.4% inactive
```

This is a second, independent argument for building on organ contrasts rather than cross-species comparison.

**7b. ISDB rotenoid calls are disproportionately taxonomy-driven.** ISDB reweights candidates by the plant's taxonomy, so "Fabaceae extracts contain rotenoids" risks being partly assumed rather than measured:

```
                      ROTENOID calls      all other calls
spectral_score  median      0.462               0.479      <- no better spectrally
taxo_score      median      6.000               4.000      <- but boosted more
final_score     median      8.750               6.882

taxo_score / final_score:   71.4%               68.5%
rotenoid calls with ZERO spectral support: 17.8%  vs  3.3%  (5.4x enrichment)
```

Rotenoid annotations have **no better spectral evidence** than average yet score higher overall, purely through the taxonomic prior, and are **5.4× more likely to rest on zero spectral support**.

**Mitigations, both adopted:** require `spectral_score > 0` (retains 82.2% of rotenoid calls) or `> 0.4` (retains 58.3%), and prefer **CANOPUS for class assignment**, since it is spectra-only with no taxonomic prior. Anyone working from raw ISDB final scores is exposed to this.

**7c. Negative mode adds nothing for rotenoids** (all ≤6.8%) — they ionize positive, as expected. But it is essential for the next finding.

**7d. The annotation choice is not cosmetic — it decides what exists.** Measured with `src/compounds.py`, which exposes `annotation = "isdb" | "canopus" | "union"`:

| Mode | isdb | canopus | union |
|---|---|---|---|
| pos | 12,553 | 24,526 | 26,140 |
| neg | **4,675** | **13,416** | 13,720 |

In negative mode ISDB-only retains barely a third of what CANOPUS does. Tested against the actual lead, for *Melochia umbellata* (VGF156_A06):

```
annotation   compounds   in Melochia   quinoline compounds
isdb              4675            12                     0
canopus          13416            78                     1   (1.0% of its signal)
union            13720            77                     1
```

**Under ISDB-only the quinoline lead does not exist at all.** An ISDB-only universe — the natural choice, since it is what the benchmark is calibrated on — silently erases the project's best ethnopharmacological finding, with no error and no empty result to notice.

This is the practical cost of §7b's taxonomic-circularity problem: the biased annotation source is also the sparser one, and in negative mode the sparsity is severe. The benchmark universe (`isdb`, for reproducibility of the validated numbers) and the lead-generation universe (`union`) are therefore kept as separate explicit settings rather than one buried default.

## 8. The two "unexplained" actives now have candidate mechanisms

The 2025 paper explained 6 of 8 actives via rotenoids and left two untouched. CANOPUS class enrichment, mostly in **negative mode**, gives both a lead:

| Sample | Species | Enriched classes (share, fold vs library) |
|---|---|---|
| VGF156_A06 | *Melochia umbellata* | **Quinoline alkaloids** 4% (71×), coumarinolignans 2% (59×), isoquinoline alkaloids 5% (23×, pos) |
| VGF145_G09 | *Phyllanthus pulcher* | Cyclic peptides 5% (7×), dipeptides 7% (5×), oleanane triterpenoids 8% (3×) |

***Melochia umbellata* is the standout convergence.** Traditional use: antimalarial in Cameroon. Chemistry: quinoline alkaloids — the quinine class. Screen: 89.9% T. cruzi inhibition at 11.6% cytotoxicity. Three independent lines pointing the same way, on an extract the published work did not explain.

**It is a lead, not a result:**

```
Library ranking by quinoline-alkaloid share (neg mode):
  VGF143_H08   26.48%   T.cruzi= 10.1%          <- inactive
  VGF157_E08   19.41%   T.cruzi=  0.0%          <- inactive
  VGF157_D08   15.44%   T.cruzi=  0.0%          <- inactive
  VGF156_A06    3.97%   T.cruzi= 89.9%   *SELECTIVE ACTIVE*   (rank 4 / 1600)
```

Three extracts have **more** quinoline signal and are inactive. The individual CANOPUS probabilities on the largest contributing features are mixed (0.41, 0.81, 0.26, 0.78). The 71× enrichment is inflated by averaging against a library where 1,444 of 1,600 extracts have zero signal.

So the finding is the **same structural result as §2**: chemical class, at any abundance, does not determine activity. It held for rotenoids; it holds for quinolines. Class-level reasoning is insufficient in both directions — which is the project's thesis, now demonstrated twice on independent chemotypes.

The honest framing: *traditional antimalarial use plus a quinoline-alkaloid signal ranking 4/1600 is a convergence worth spending one of three assays on.* That is literally the tool's use case, and it makes a far better demo than a claimed answer.

## 8b. Running the method on real data (no simulation) — `src/real_case.py`

**The top-ranked candidates are not rotenone, and that is chemically coherent rather than a failure.** All five leading candidates carry CANOPUS `Rotenoids` at 0.98–0.9999:

| cid | m/z | neutral | likely formula | CANOPUS | notes |
|---|---|---|---|---|---|
| 2820 | 409.128 | 408.121 | C₂₃H₂₀O₇ | 0.9997 | deguelin-type gem-dimethyl chromene, oxidised |
| 7923 | 427.138 | 426.131 | C₂₃H₂₂O₈ | 0.982 | dihydroxylated — tephrosin family |
| 6530 | 395.150 | 394.143 | C₂₃H₂₂O₆ | 0.9999 | **ISDB candidates include rotenone (JUVIOZPCNVVQFO)** |
| 5659 | 393.133 | 392.126 | C₂₃H₂₀O₆ | 0.9999 | dehydro-deguelin, RT 3.75 |
| 9244 | 393.134 | 392.126 | C₂₃H₂₀O₆ | 0.9986 | **same ISDB key as 5659**, RT 4.58 |

The published isolation reported rotenone (IC₅₀ 0.01 µM), deguelin (0.02) **and tephrosin (0.04)** — tephrosin being the hydroxylated member. Our top candidates are oxygenated rotenoids, i.e. the same chemical family the experimental work converged on. Rotenone itself appears as cid 6530 at rank 5 of 64.

**cid 5659 and 9244 share one ISDB key at different retention times** — chromatographic isomers that annotation cannot separate. That is the project's core problem appearing unprompted in real data.

### The method abstains on the full library — and should

*Source: `results/real_case.json`; see FINDINGS.md §3.7.*

| Stage | Top score | Abstains? |
|---|---|---|
| 8 hits + 24 reference extracts | 0.769 (CI 0.51–0.99) | no |
| after 3 recommended assays | 0.753 | no |
| full 1,600-extract library | **0.468** (CI 0.22–0.63) | **yes** |

On the full library the evidence does not support naming any single rotenoid, and the tool says so. Given §2 — rotenoid abundance has ρ = 0.095 with activity library-wide — abstaining is the correct answer, not a shortfall. The *Melochia* case abstains at **every** stage (top score 0.42 → 0.20), which is also right: it is a weak lead.

**This is the demo's best moment.** A tool that declines to name a culprit when the evidence is thin is more credible than one that always produces an answer, and it directly evidences the "must be able to conclude *neither*" requirement from §5.

### Quinoline rank: class level versus per compound

The "**4th of 1600**" figure is a **class-level** share (all quinoline-classed features, negative mode). Measured **per compound**, the single quinoline compound (cid 13063, m/z 318.207, CANOPUS 0.631) occurs in only **3 extracts**, with *Melochia umbellata* 2nd — and the extract above it is **VGF156_B06, the other *Melochia umbellata* sample** (leaves, 31.8% inhibition). The two figures measure different things; quote the class-level one only with the words "class-level share", never as a per-compound rank.

## 9. What the data establish

Confirmed from the data:

- [x] Quantitative abundance extractable and usable (288k features → 40.6k compounds)
- [x] Dose-response real within species (65.5% → 11.6% → 4.0% share maps to 112% → 54% → 0%)
- [x] Confounding real and widespread (486 confounded pairs co-occurring in >=3 extracts, 362 touching actives; the benchmark uses a separate set of 238 confounded and decorrelatable pairs, see FINDINGS.md §2.2)
- [x] Decorrelating samples exist for 99.8% of pairs, median 25 options
- [x] Class-level counting demonstrably insufficient (rho = 0.095; top-ranked extract is a false lead)
- [x] Trace-level abundance makes presence/absence uninformative (worked example returns a null verdict)
- [x] A concrete misannotation filter identified

Model requirements that follow from the data:

1. **Abundance-based**, with a detection floor and an effect threshold.
2. **Able to answer "neither"**, with uncertainty, rather than always naming a culprit.
3. **Prefilter** ubiquitous annotations.
4. **Selection objective**: under a 3-assay budget, pick extracts whose abundance contrast separates the candidates the current evidence cannot yet separate (adaptive contrast) — abundance contrast, not presence contrast.
5. **Carry annotation ambiguity** through to the output; candidates competing for one peak are not independent hypotheses.

6. **Use CANOPUS for class, ISDB for structure candidates**, and filter ISDB on `spectral_score` (§7b).
7. **Use both ionization modes.** Negative mode found the only lead for the two unexplained actives (§8).

### Scope: settled by the data

The assay panel is asymmetric, which decides it:

```
organism          concentrations    >80% raw   selective (+ L6 < 50%)
T. cruzi          10 ug/mL only           15        8
T. brucei rhod.   2 and 10 ug/mL          33       23
L. donovani       2 and 10 ug/mL          41       33
```

*T. cruzi* has a **single concentration**, so it carries no extract-level dose information — and §5 showed dose is exactly what the attribution model needs. *L. donovani* has two concentrations and **4× more selective actives** (33 vs 8). The three-parasite panel also broadens the story to three neglected tropical diseases rather than one.

One caveat on the two-concentration argument: at 2 µg/mL only **2** extracts are selectively active for *L. donovani* and **4** for *T. brucei*. So the second concentration adds a dose point for the extracts active at 10 but not at 2, rather than a second full set of hits.
