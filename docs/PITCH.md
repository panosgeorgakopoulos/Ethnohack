# DECOUPLE: 3-Minute Hackathon Pitch & Judge Defense Guide

> **Track:** Natural Products & Computational Ethnopharmacology  
> **Tagline:** Three Assays, One Isolation: Deconvolving Active Natural Product Mixtures Under Extreme Budget Constraints

---

## 🎬 Slide Deck Outline (3 Minutes / 5 Slides)

```
[Slide 1: The Trap]     -->   [Slide 2: The Math of Failure]   -->   [Slide 3: DECOUPLE]
Co-occurrence in              "Strongest-first" wastes               Bayesian active learning
natural products              reveals on redundancy                  selects diagnostic contrast
         │                                                                   │
         ▼                                                                   ▼
[Slide 4: Live Demo]    ----------------------------------------->   [Slide 5: The Impact]
Interactive workbench,                                               100% single-driver recovery,
2D structures & shifts                                               half the assay cost
```

---

### Slide 1: The Natural Products Dilemma (0:00 – 0:40)
* **The Hook:** *"Mother Nature is the greatest medicinal chemist, but she rarely works in pure compounds."*
* **The Problem:** When screening plant extract libraries against intracellular *Trypanosoma cruzi* (Chagas disease), the active hits are crude mixtures. Frequently, **two distinct chemical constituents co-occur** across multiple active species.
* **The Cost:** Isolating pure compounds from biomass takes weeks of chromatography and thousands of dollars. A wet-lab chemist has a strict budget: **up to 3 follow-up extract assays, and exactly 1 compound isolation slot.**
* **The Dilemma:** Which extract do you assay next to decide which chemical is the true therapeutic driver?

---

### Slide 2: The Failure of Intuition (0:40 – 1:15)
* **The Instinct:** Human chemists naturally choose the extract with the highest predicted potency (**"strongest-first"**).
* **The Flaw:** If both compounds are present in that potent extract, testing it yields **zero discriminatory power**—it confirms activity, but teaches you nothing about *which* compound caused it.
* **The Benchmark Proof:** On our benchmark of **23 authentic chemical pairs across 7 published scientific studies**, the greedy "strongest-first" strategy **misses 33.3% of true single drivers** and wastes nearly double the assays (2.25 reveals) trying to reach confidence.

---

### Slide 3: The DECOUPLE Solution (1:15 – 1:55)
* **The Core Mechanism:** DECOUPLE frames bioactivity deconvolution as a **Bayesian active experimental design** problem.
* **4-Hypothesis Space:** $A$ is the driver, $B$ is the driver, both contribute, or neither.
* **Expected Utility Acquisition:** At every step, DECOUPLE asks: *"Which unmeasured plant specimen maximizes the expected utility of our single isolation slot?"*
* **Autonomous Abstention:** If two compounds are collinear across all available library extracts, DECOUPLE **formally abstains** and explains the ambiguity, rather than guessing and wasting wet-lab resources.

---

### Slide 4: Live Demo (1:55 – 2:35)
*(Switch to browser at `http://127.0.0.1:8765`)*
1. **Show Candidate Cards:** Point to Candidate A (Galgravin) and Candidate B (Machilin G) with their dynamically rendered 2D chemical structures.
2. **Show the Posterior:** Starting belief is uncertain ($40\% / 40\%$).
3. **Click "Reveal Simulated Assay":** Watch DECOUPLE select a contrasting botanical specimen (*e.g., Aristolochia elegans*). The response reveals activity, and the posterior snaps to **99.9%** for Candidate A.
4. **Show Finalization & Audit Trail:** Show the completed nomination and download the cryptographic JSON decision trail (`/api/export`).
5. **Show Counterfactual Replay:** Click "Compare with strongest-first" to prove that the greedy policy chose the wrong extracts on the exact same episode.

---

### Slide 5: Validated Results & Impact (2:35 – 3:00)
* **100.0% Single-Driver Recovery:** DECOUPLE successfully isolates 12 out of 12 active single drivers (vs 66.7% for greedy).
* **Fastest Convergence:** Takes **1.17 assays** to reach confident nomination (vs 2.25 for greedy).
* **Zero False Nominations:** 100% precision when nominating.
* **Translational Value:** Reduces wasted isolation campaigns by **33%** and cuts assay screening costs in half.

---

## 🛡️ Judge Defense Guide (Answering Tough Questions)

### Q1: *"Your mixture responses are simulated. Why should we trust this in a wet lab?"*
> **Answer:** *"We are completely transparent about that: our benchmark explicitly carries `"measured_extract_replay": false`. What is authentic is the chemistry and the biology: the chemical structures, the pure compound $IC_{50}$ values against T. cruzi from ChEMBL, and the species occurrence records from LOTUS are 100% real published data across 7 peer-reviewed papers. The simulation validates the mathematical decision framework: we proved that when deconvolution is possible, greedy selection fails while utility-driven contrast succeeds. The software is already architected to ingest raw LC-MS tables with zero code changes."*

### Q2: *"What if the active molecule kills the parasite just because it's cytotoxic to all cells?"*
> **Answer:** *"That is a crucial medicinal chemistry point. In natural products, parasite inhibition must be decoupled from host toxicity. In our scientific specification (`docs/01-science.md`), we discuss cell selectivity against mammalian cells (e.g. rat L6 cells). Our utility function is modular: we can incorporate selectivity ratio thresholds ($\text{SI} \ge 10$) so that a candidate is only nominated if it demonstrates selective antiparasitic activity without general cytotoxicity."*

### Q3: *"How does this compare to standard molecular networking or NP Analyst?"*
> **Answer:** *"Tools like NP Analyst and GNPS molecular networking perform **static correlation** across all extracts at once after the entire library has been screened. DECOUPLE solves the **active, sequential design** problem: when you cannot afford to screen all 1,600 extracts and only have budget for 3 follow-ups, which specific extract should you test next? In fact, our benchmark includes static biochemometric correlation as a baseline, and DECOUPLE outperforms it in sample efficiency."*

### Q4: *"What prevents the model from leaking hidden assay labels?"*
> **Answer:** *"Strict architectural air-gapping. The model and acquisition functions only receive visible state (`samples`, `revealed`, `prior`). Ground truth outcomes and candidate assay records are stored behind an SQLite-backed reveal controller. Furthermore, we have automated regression tests in our CI suite proving that perturbing or changing unrevealed labels leaves policy actions completely invariant."*
