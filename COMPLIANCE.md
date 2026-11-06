# Rules Compliance Review

For the team. Checked 6 Nov 2026 against the hackathon guidelines and the Devpost requirements.

**Summary: we are inside the rules. Four gray areas need an explicit action, and one is a genuine risk.**

---

## Clear — no action beyond documenting

| Rule | Status |
|---|---|
| Work created during 2–8 Nov | ✅ All work started 6 Nov. Nothing pre-dates the window. |
| Team of 2–5, all listed on Devpost | ✅ Confirmed — list every member on the project page. |
| Registered before 31 Oct 23:00 CET | ✅ Confirmed. |
| Addresses a declared track | ✅ Track 2: Natural Products & Drug Discovery. |
| Open data used within licence | ✅ ENPKG is CC-BY-4.0. Needs attribution, which we give. |

---

## Gray area 1 — Originality framing **(the real risk)**

We reproduce Gaudry et al. (2025): 8 selective actives, 6 rotenoid-bearing. **That is their result, not ours.** It is a validation that our pipeline works, nothing more.

The rules permit using prior work but require that we *"clearly show which parts your team built and which were pre-existing"*, and disqualification covers *"fraudulent or misleading information."* Leading the Devpost page or video with the rotenoid finding would misrepresent whose result it is.

**Action — state the split explicitly, in the README and on camera:**

| Pre-existing | Ours, built 6–8 Nov |
|---|---|
| ENPKG dataset and knowledge graph (Gaudry et al., *ACS Cent Sci* 2024) | Continuous log-abundance attribution rule |
| The 1,600-extract anti-trypanosomatid screen | Budget-constrained extract selection (adaptive contrast) |
| The rotenoid finding (Gaudry et al., *RSC Adv* 2025) | Semi-synthetic benchmark + stratification |
| Published ethnobotanical records | Ethnobotanical provenance layer and organ-contrast analysis |
| CANOPUS, SIRIUS, ISDB annotations | The *Melochia umbellata* quinoline lead |
| | The ISDB taxonomic-circularity finding |

Framing that is both accurate and stronger: *"We reproduced the published result in 10 minutes from open data, then showed why its method cannot generalise, and built one that does."*

## Gray area 2 — Redistributing the data

We cached ~130 MB of ENPKG files into `data/enpkg/`. Two problems if that gets committed:

- The ENPKG **data** is CC-BY-4.0 (redistributable with attribution), but the **ontology file** declares **CC-BY-NC-SA-4.0** — non-commercial *and* share-alike. Shipping it could impose share-alike on our derivative and conflicts with a permissive code licence.
- Repo bloat, for no benefit.

**Action:** add `data/` to `.gitignore`. Our scripts already download from Zenodo on first run, so reproducibility is unaffected. Cite both licences separately in the README.

## Gray area 3 — AI assistance

The analysis code in `scripts/` and `src/` was written with AI assistance during the event. This is **not prohibited** — the Devpost page asks only for *"responsible use of AI"*, and AI-assisted code written during the window is work created during the window, not pre-existing.

**Action, two parts:**
1. One line in the README stating the tooling. Transparency costs nothing and plays well with a rigor-focused jury.
2. **More important:** every team member presenting must actually understand the method. Judges ask questions, and "why continuous attribution rather than presence/absence?" is exactly the question they will ask. The answer is in FINDINGS.md §3.1 — decorrelating abundances are trace-level (0.0008–0.0188), below any sensible presence threshold. Know it cold.

## Gray area 4 — Traditional knowledge and benefit-sharing

The rules require care with *"provenance, attribution, cultural context and access restrictions."* This is the one where the jury's expertise is highest.

Our ethnobotanical records come from Malaysian, Cameroonian and Philippine sources; the plants were collected in Madagascar and Southeast Asia into a commercial library.

**Action — a short "Traditional knowledge and benefit-sharing" section in the README:**
- Cite each ethnobotanical source individually (already done in `ETHNOBOTANY.md` §2).
- Acknowledge that the knowledge pointing at these plants originated with the communities who hold it.
- Note that Nagoya Protocol / ABS obligations attach to the **original collection and any commercial development**, not to our secondary analysis of published data — and that any downstream development would need to address them.
- State that we make **no claim of ownership** over the traditional knowledge described.

Handled well, this is an asset rather than a liability — it is exactly what *Best Community Impact* rewards.

## Gray area 5 — Not overstating the results

Traps, all violations of *"must not present unvalidated computational findings as established medical facts"* or simply misleading. **These must not be claimed:**

1. **Accuracy without its context.** Never quote any accuracy figure (for example the hard-stratum 19.0% or the overall 65.0%, `results/benchmark.json`) without "on semi-synthetic benchmarks" in the same breath. Composition and confounding are real; the pharmacology is simulated.
2. **Pooled accuracy alone.** Always report stratified. Pooled accuracy overstates by about 45 to 46 points (overall minus hard: adaptive contrast 65.0% vs 19.0%, strongest-first 64.4% vs 19.0%) because it is dominated by cases needing no tool. Say that hard cases are 6.7% of confounded, decorrelatable pairs (16 of 238).
3. **That adaptive contrast beats the chemist's default.** It ties it: the margin over strongest-first is +0.0 points, CI [0.0, 0.0], hard stratum (16 pairs); easy +0.7 [−0.3, +1.8]; overall +0.6 [−0.3, +1.7]. What is supported is that choosing which three extracts to assay roughly doubles the hard-stratum hit rate over spending no assays (8.6% to 19.0%; +10.3 points, CI [+3.8, +17.2]), that three extracts chosen at random are worth nothing (8.6%), and that the value of adaptive contrast is in what it nominates (selectivity-aware nomination: identical developable accuracy, 154× fewer wasted isolations, in simulation).
4. **That selectivity-aware nomination is validated.** It is supported on wasted isolations in a simulation with an assumed 50% cytotoxic prevalence; the only real-data support is that 7 of 15 potency hits are cytotoxic decoys.
5. **That the tool can say "both".** It names a single driver; when two compounds act together every such nomination is wrong (1.5% of episodes under the decision-model generator, 13.4% under the logistic one, adaptive contrast, potency-only, threshold 0.85).
6. **That MS annotations are confirmed identities.** Rotenone and deguelin are isomers of identical exact mass competing for one peak; the published team used authentic standards, we cannot.
7. ***Melochia umbellata* as a finding.** It is a lead, not a finding: three extracts have more quinoline signal and are inactive. Say "worth one of three assays," never "we identified the active compound."
8. **The rotenoid finding as ours.** That is Gaudry et al., *RSC Adv* 2025; we reproduce it as a pipeline check.

**Also required:** an explicit statement that predicted attribution is a hypothesis, that nothing here is clinically validated, and that none of it is medical advice.

---

## Outstanding submission items

- [x] Test suite: `python3.12 -m pytest tests/ -q` reports 43 passed (17 `decouple`, 23 `src`, 3 selectivity)
- [ ] Public GitHub repo — **not created yet**
- [ ] `.gitignore` with `data/`
- [ ] README: problem, install, repro steps, dataset licences, pre-existing/ours split, AI tooling, traditional-knowledge statement, health disclaimer
- [ ] Devpost project page — all 10 required fields, Track 2 selected, every member listed
- [ ] Pitch video ≤ 10 min, with a demo
- [ ] Slide deck ≤ 10 slides
