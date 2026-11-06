# Ethnobotanical Provenance Layer

Built 6 Nov 2026. Reproduce with `python3 scripts/ethno_provenance.py`.

**Why this exists.** Track 2 doesn't require traditional knowledge, but the judges are ethnopharmacologists and the event is an ethnopharmacology hackathon. Without this layer the project is excellent cheminformatics with no ethnobotany in it. This layer connects every screening hit to the plant species, the plant *organ*, and the documented traditional use of that same species and part — and it turns out to carry real scientific weight, not just framing.

---

## 1. The eight selective anti-*T. cruzi* actives

Reproduced from [Zenodo 7824642](https://zenodo.org/records/7824642) (CC-BY-4.0). Rotenoid counts are features with at least one rotenoid candidate annotation (NPClassifier `npc_Rotenoids`); background mean across the other 1,592 extracts is **0.12**.

| Sample | T. cruzi % | L6 cytotox % | Rotenoid/annot | Species | Organ |
|---|---|---|---|---|---|
| VGF155_D05 | 117.4 | 46.6 | 10 / 359 | *Desmodium heterophyllum* | multiple (root tissue) |
| VGF139_H07 | 112.2 | 45.1 | **84 / 325** | *Pachyrhizus erosus* | **leaves** |
| VGF146_E08 | 112.1 | 38.0 | 12 / 166 | *Cnestis palala* | roots |
| VGF146_F09 | 112.0 | 38.2 | 9 / 183 | *Cnestis palala* | woody stems |
| VGF145_G09 | 110.0 | 37.5 | **0** / 171 | *Phyllanthus pulcher* | multiple |
| VGF150_H08 | 108.6 | 7.3 | 17 / 379 | *Chadsia grevei* | roots |
| VGF150_A09 | 104.1 | 3.8 | 14 / 468 | *Chadsia grevei* | bark |
| VGF156_A06 | 89.9 | 11.6 | **0** / 325 | *Melochia umbellata* | green stems |

## 2. Traditional use, checked species by species

Each claim verified against sources; **negatives reported as negatives.**

| Species | Documented traditional use | Relevance | Status |
|---|---|---|---|
| ***Pachyrhizus erosus*** (jicama) | Seeds and leaves used as **insecticide and fish poison**; rotenone is the active principle. **Tubers are the edible part** — the plant is a food crop. | Direct. Traditional practice already identified the rotenoid toxicity *and* which part carries it. | **Confirmed** ([PFAF](https://pfaf.org/user/Plant.aspx?LatinName=Pachyrhizus+erosus), [Wikipedia](https://en.wikipedia.org/wiki/Pachyrhizus_erosus), [Antioxidants 2022](https://doi.org/10.3390/antiox11010058); rotenone isolated from this species in [Nat Prod Res 2014](https://www.tandfonline.com/doi/full/10.1080/14786419.2014.939081)) |
| ***Cnestis palala*** | Seeds used to **poison rats and stray dogs**. Roots used medicinally (stomach-ache, colonic obstruction, urinary troubles). Toxic principle reported as methionine sulfoximine. | Direct. Known poison plant; the active organs here are roots and stems. | **Confirmed** ([PROSEA/Pl@ntUse](https://plantuse.plantnet.org/en/Cnestis_palala_(PROSEA)), [AJTCAM 2015](https://www.ajol.info/index.php/ajtcam/article/view/120121)) |
| ***Melochia umbellata*** | Used in **Cameroonian folk medicine to treat malaria**. Leaf extract gave 86.2% chemosuppression of *Plasmodium berghei* parasitaemia in rats. | **Direct antiparasitic use** — and this is one of the two actives with *zero* rotenoids. | **Confirmed** ([PMC12709862](https://pmc.ncbi.nlm.nih.gov/articles/PMC12709862)) |
| ***Chadsia grevei*** | No traditional-use record found. Endemic to dry thorn scrub in SW Madagascar. | None found. But its rotenoid chemistry was published in 1994: *"Dequeline: a rotenoid constituent of Chadsia grevei"*, Manjary et al., *Planta Med* 60(6):602. | **No ethnobotanical record** (chemistry independently corroborated) |
| ***Desmodium heterophyllum*** | Genus-level only: *Desmodium* has 100+ recorded uses across 43 countries (inflammatory, GI, infectious, pain). A fragmentary record links this species to postpartum use in Indonesia. | Weak. Genus-level claims should not be assumed to apply to the species. | **Unconfirmed at species level** |
| ***Phyllanthus pulcher*** | Malaya: stomach- and tooth-ache, boils, carbuncles, dermatosis, sores (Duke 1992). Also ulcer and kidney complaints. | Not antiparasitic. | **Confirmed, but no antiparasitic use** |

### A claim we checked and rejected

One PROSEA-derived source mentions a root decoction of *C. palala* taken **with *P. pulcher*** for malaria. That would have been a striking result, since both species are in our active list. A dedicated search on *P. pulcher* found **no support** for antimalarial or antiparasitic use; the malaria records in that genus belong to *P. niruri*, *P. amarus* and *P. reticulatus*. **We are not claiming it.** Settling it would need a primary source (Duke 1992, or Jantan et al.).

The project is about honest attribution under uncertainty; a rejected hypothesis is reported as such.

## 3. The pattern, stated honestly

Traditional knowledge flags these plants through **two different routes**:

- **The rotenoid actives are traditional *poisons*** — insecticide, fish poison, rat poison. Traditional practice recognised the toxicity centuries ago; the screen rediscovered the same chemistry. This is toxicity-led knowledge, not medicinal knowledge, and it predicts the rotenoid chemotype well.
- **One non-rotenoid active is a traditional *antimalarial*.** *Melochia umbellata* has zero rotenoid annotations yet 89.9% inhibition, and is used against malaria in Cameroon. Traditional antiparasitic use points at a **different, unexplained mechanism** — which makes it the most interesting lead in the set, not a leftover.

The other non-rotenoid active (*P. pulcher*) has only topical and GI uses, and *C. grevei* has no record at all. So: 3 of 6 species carry directly relevant traditional use, 1 has none, 2 are weak or unrelated. That is a real and useful signal, and overstating it would be easy and wrong.

## 4. The methodological payoff: organs are nature's decorrelating experiments

The layer is not just narrative. The library contains **the same species sampled as different organs**, and those are exactly the "rich in one, poor in the other" samples the core method hunts for:

```
Pachyrhizus erosus
  VGF139_H07   leaves        T.cruzi=112.2%   rotenoid= 84/325   <== ACTIVE
  VGF139_A08   woody_stems   T.cruzi= 53.7%   rotenoid= 11/162
  VGF139_B08   roots         T.cruzi=  0.0%   rotenoid= 10/107

Cnestis palala
  VGF146_E08   roots         T.cruzi=112.1%   rotenoid= 12/166   <== ACTIVE
  VGF146_F09   woody_stems   T.cruzi=112.0%   rotenoid=  9/183   <== ACTIVE
  VGF147_F02   leaves        T.cruzi=  0.0%   rotenoid=  0/185

Melochia umbellata
  VGF156_A06   green_stems   T.cruzi= 89.9%   rotenoid=  0/325   <== ACTIVE
  VGF156_B06   leaves        T.cruzi= 31.8%   rotenoid=  0/164
```

Same genotype, same collection, different chemistry and different activity. This controls for species, provenance and extraction in a way that cross-species comparison cannot, and they are the contrasts a selection method should be able to find.

*P. erosus* also reproduces the traditional food-versus-poison split inside one plant: leaves (the poison part) active, roots (the food part) inert.

### Resolved: abundance, not count

Counts do not show the gradient — *P. erosus* woody stems (53.7% inhibition) and roots (0.0%) carry nearly identical rotenoid feature *counts*. Using `has_relative_feature_area` resolves it. Measured as **rotenoid share of annotated signal**, the organ series is a clean monotonic dose-response:

| Organ | Rotenoid share | T. cruzi % |
|---|---|---|
| leaves | **65.5%** | 112.2 |
| woody stems | 11.6% | 53.7 |
| roots | 4.0% | 0.0 |

So the traditional food-versus-poison split inside this plant is quantitative, not just qualitative. See [VALIDATION.md](VALIDATION.md) for the full abundance analysis for the full abundance analysis.

## 5. Data and licensing

- ENPKG data: [Zenodo 7824642](https://zenodo.org/records/7824642), **CC-BY-4.0**. Cite Gaudry et al., *ACS Cent Sci* 2024.
- ENPKG ontology file: declares **CC-BY-NC-SA-4.0** — a different licence from the data. List both separately in the README.
- Ethnobotanical sources are cited individually in §2. Dr. Duke's database: https://phytochem.nal.usda.gov

## 6. For the submission

- **Devpost / video:** open on *Pachyrhizus erosus* — a food crop whose leaves poison fish and whose tuber you eat, where the screen independently recovered that exact split. It is concrete, visual, and makes the ethnopharmacology case in fifteen seconds.
- **Rigor:** keep the rejected *P. pulcher* malaria claim in the write-up. Showing a discarded hypothesis is worth more to the *Best Scientific Rigor* award than one more confirmed row.
- **Community impact:** Chagas, leishmaniasis and sleeping sickness are diseases of poor rural populations, and the knowledge pointing at these plants came from the communities living with them. Attribution of that knowledge belongs in the README.
