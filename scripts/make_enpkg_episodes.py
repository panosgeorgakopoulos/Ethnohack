"""Build data/real/episodes.json from measured ENPKG chemistry (no simulation, no ground truth).

Schema matches data/episodes.json / decouple.engine. Pair construction follows
scripts/setvalued_report.py. hidden.truth is deliberately null: on real data the
driving compound is the unknown the tool exists to find.
"""
import sys, json, itertools, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.compounds import build_compounds
from src.enpkg_io import load_structures, load_assays, load_samples

N_PAIRS, SEED_N, SEL_T, SEL_L6 = 12, 3, 80.0, 50.0   # 3 seed reveals: the demo needs room to move
OUT = ROOT / 'data' / 'real'
ZENODO = 'https://zenodo.org/records/7824642'

comp, stru, assays, smeta = build_compounds('pos'), load_structures(), load_assays(), load_samples()
rot = {k for k, v in stru.items() if 'Rotenoids' in v['npc_class']}
rot_c = [c for c, v in comp.items() if any(k in rot for k in v['isdb_keys'])]
actives = sorted(s for s, a in assays.items() if a['Tcruzi_10ugml'] > SEL_T and a['L6_10ugml'] < SEL_L6)


def pairs():
    for a, b in itertools.combinations(rot_c, 2):
        Sa, Sb = set(comp[a]['abundance']), set(comp[b]['abundance'])
        if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa):
            u = Sa | Sb
            yield a, b, len(set(actives) & u), min(len(Sa - Sb), len(Sb - Sa)), len(u)


ranked = sorted(pairs(), key=lambda p: (-p[2], -p[3], p[0], p[1]))
n_total = len(ranked)
# Greedy selection with a reuse cap: taking the top-N by score alone made a few
# compounds appear in 4-5 episodes each, so the episodes were not independent.
MAX_REUSE = 2
_seen = {}
chosen = []
for p_ in ranked:
    if len(chosen) >= N_PAIRS:
        break
    if _seen.get(p_[0], 0) >= MAX_REUSE or _seen.get(p_[1], 0) >= MAX_REUSE:
        continue
    chosen.append(p_)
    _seen[p_[0]] = _seen.get(p_[0], 0) + 1
    _seen[p_[1]] = _seen.get(p_[1], 0) + 1


def candidate(cid):
    c = comp[cid]
    key = next((k for k in c['isdb_keys'] if k in rot), c['isdb_keys'][0])
    cls = c['canopus'][0] if c['canopus'] else 'Rotenoids'
    name = f"m/z {c['mz']:.3f} @ RT {c['rt']:.2f} · {cls}"
    return {'id': f'C{cid}', 'name': name, 'inchikey': key, 'smiles': stru[key]['smiles'],
            'identity_match_tier': 'MS annotation candidate (ISDB 2D InChIKey match, positive mode); '
                                   'NOT a confirmed structure',
            'source_url': f'https://pubchem.ncbi.nlm.nih.gov/#query={key}'}


def episode(a, b):
    cands = [candidate(a), candidate(b)]
    ids = sorted(set(comp[a]['abundance']) | set(comp[b]['abundance']))
    ids = [s for s in ids if s in assays and s in smeta]
    seed = sorted(ids, key=lambda s: (-assays[s]['Tcruzi_10ugml'], s))[:SEED_N]
    samples = []
    for s in ids:
        m, x, st, ev = smeta[s], [], [], []
        for cid, cd in zip((a, b), cands):
            ab = comp[cid]['abundance'].get(s)
            x.append(float(ab) if ab is not None else 0.0)
            st.append('detected' if ab is not None else 'not-detected')
            ev.append({'id': s, 'name': m['species'], 'species': m['species'], 'wikidata': m['wikidata'],
                       'organ': m['organ'], 'url': f"http://www.wikidata.org/entity/{m['wikidata']}",
                       'compound_url': cd['source_url'], 'references': [ZENODO]} if ab is not None else None)
        samples.append({'id': s, 'name': f"{m['species']} · {m['organ']}", 'x': x,
                        'units': 'relative LC-MS feature area', 'occurrence_status': st, 'evidence': ev})
    sel = sorted(set(ids) & set(actives))
    return {'id': f'{cands[0]["id"]}-{cands[1]["id"]}-r0', 'pair_id': f'{cands[0]["id"]}-{cands[1]["id"]}',
            'tier': 'Tier R · measured extracts (ENPKG)', 'candidates': cands, 'samples': samples,
            'initial': seed,
            'hidden': {'truth': None, 'truth_basis': 'unknown — real measured data, no ground truth',
                       'outcomes': {s: assays[s]['Tcruzi_10ugml'] / 100 for s in ids},
                       'outcomes_cytotox': {s: assays[s]['L6_10ugml'] / 100 for s in ids}},
            'provenance': {'source': 'ENPKG Zenodo 7824642', 'replicate': 0, 'mode': 'pos',
                           'extracts': len(ids), 'selective_actives_present': sel,
                           'assay': 'Tcruzi_10ugml', 'cytotox_assay': 'L6_10ugml'},
            'limitations': [
                'MEASURED: extract abundances (LC-MS/MS feature area) and T. cruzi / L6 inhibition are real ENPKG data; nothing is simulated.',
                'Candidates are MS annotation candidates (ISDB spectral match), not confirmed structures.',
                'NO GROUND TRUTH: which compound, if either, drives activity is unknown.',
                'Responses are whole-extract inhibition at one concentration (10 ug/mL), a mixture of many constituents.',
                'Absence (x = 0) means not detected in positive-mode LC-MS, not confirmed biological absence.']}


eps = [episode(a, b) for a, b, *_ in chosen]
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'episodes.json').write_text(json.dumps(eps, allow_nan=False))
audit = {'source': 'ENPKG Zenodo 7824642 (measured)', 'extracts': len(smeta), 'rotenoid_compounds': len(rot_c),
         'confounded_pairs_eligible': n_total, 'episodes': len(eps),
         'selective_actives_total': len(actives), 'truth_distribution': {'unknown': len(eps)}}
(OUT / 'audit.json').write_text(json.dumps(audit, indent=1))
covered = sorted({s for e in eps for s in e['provenance']['selective_actives_present']})
manifest = {'generator': 'scripts/make_enpkg_episodes.py', 'source': ZENODO, 'selective_def':
            f'Tcruzi_10ugml > {SEL_T} and L6_10ugml < {SEL_L6}', 'selective_actives': actives,
            'actives_covered': covered, 'pairs': [{'pair_id': e['pair_id'], 'extracts': e['provenance']['extracts'],
            'actives': e['provenance']['selective_actives_present']} for e in eps],
            'eligible_pairs_total': n_total, 'truth': 'null for every episode (unknown)',
            'episodes_sha256': hashlib.sha256((OUT / 'episodes.json').read_bytes()).hexdigest()}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print(f'{len(eps)} episodes of {n_total} eligible pairs; actives covered: {covered}')
for e in eps:
    print(e['pair_id'], e['provenance']['extracts'], 'extracts', e['provenance']['selective_actives_present'])
