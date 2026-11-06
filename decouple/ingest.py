"""Source downloads, exact identity matching, and explicitly reconstructed episodes."""
import csv
import gzip
import hashlib
import itertools
import json
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from .model import means, seed_for, HYPOTHESES
from .engine import save

LOTUS_URL = 'https://zenodo.org/api/records/19360665/files/260413_frozen_metadata.csv.gz/content'
ACTIVITY_URL = 'https://www.ebi.ac.uk/chembl/api/data/activity.json'
LIMITATIONS = [
    'RECONSTRUCTED: responses and concentrations are simulated, not measured extract assays.',
    'LOTUS records documented occurrence. Unrecorded occurrences are encoded as zero only for this benchmark; they are not confirmed biological absences.',
    'Compound IC50 labels are thresholded within each assay. They do not establish which constituent drives a real mixture.',
    'The simulator and inference use the same response family. Results test acquisition under those assumptions, not prospective discovery performance.',
    'Species occurrence aggregates literature across specimens, tissues, doses and extraction methods.',
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(url, path):
    path = Path(path)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=120) as response:
            content = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return path


def manifest_entry(path, url, license):
    path = Path(path)
    return {'file': str(path), 'url': url, 'sha256': digest(path), 'bytes': path.stat().st_size,
            'downloaded_at': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), 'license': license}


def prepare(cfg):
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog('rdApp.warning')
    raw = Path(cfg['data_dir']) / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = []
    lotus = fetch(LOTUS_URL, raw / 'lotus_metadata.csv.gz')
    manifest.append(manifest_entry(lotus, LOTUS_URL, 'CC-BY-4.0'))
    record = fetch('https://zenodo.org/api/records/19360665', raw / 'lotus_record.json')
    manifest.append(manifest_entry(record, 'https://zenodo.org/api/records/19360665', 'CC-BY-4.0'))
    activity_url = f"{ACTIVITY_URL}?target_chembl_id={cfg['target_chembl_id']}&standard_type=IC50&limit=1000"
    first = fetch(activity_url, raw / 'chembl_activity.json')
    first_json = json.loads(first.read_text())
    total = first_json['page_meta']['total_count']
    activities = []
    for i in range((total + 999) // 1000):
        url = activity_url if i == 0 else activity_url + f'&offset={i * 1000}'
        path = first if i == 0 else fetch(url, raw / f'chembl_activity_{i}.json')
        data = json.loads(path.read_text())
        activities.extend(data['activities'])
        manifest.append(manifest_entry(path, url, 'CC-BY-SA-3.0'))
    counts = Counter(activity_rows=len(activities), api_total=total)
    if len(activities) != total or len({r['activity_id'] for r in activities}) != total:
        raise ValueError('Activity pagination is incomplete or has duplicates')
    # No censored, flagged or duplicate values enter labels; originals remain in raw snapshots.
    filtered = []
    for r in activities:
        if (r['standard_units'] != 'nM' or r['standard_relation'] != '=' or not r['standard_value']
                or r['data_validity_comment'] or r['potential_duplicate'] or not r['canonical_smiles']):
            counts['excluded_activity_quality_or_censoring'] += 1
            continue
        if float(r['standard_value']) <= 0:
            counts['excluded_nonpositive'] += 1
            continue
        filtered.append(r)
    counts['eligible_activity_rows'] = len(filtered)
    keys = {}
    for r in filtered:
        mid = r['molecule_chembl_id']
        if mid not in keys:
            m = Chem.MolFromSmiles(r['canonical_smiles'])
            keys[mid] = Chem.MolToInchiKey(m) if m else None
    wanted = set(keys.values()) - {None}
    occurrences = defaultdict(dict)
    for r in csv.DictReader(gzip.open(lotus, 'rt')):
        counts['lotus_rows'] += 1
        if r['organism_taxonomy_03phylum'] != 'Streptophyta':
            continue
        counts['lotus_plant_rows'] += 1
        key = r['structure_inchikey']
        if key not in wanted:
            continue
        # Species-level names only, keyed by source Wikidata identity.
        if not r['organism_taxonomy_09species'] or r['organism_name'] != r['organism_taxonomy_09species']:
            counts['excluded_non_species_occurrence'] += 1
            continue
        counts['matched_occurrence_rows'] += 1
        sid = r['organism_wikidata'].rsplit('/', 1)[-1]
        if sid not in occurrences[key]:
            occurrences[key][sid] = {'id': sid, 'name': r['organism_name'], 'url': r['organism_wikidata'],
                                      'compound_url': r['structure_wikidata'], 'references': []}
        ref = r['reference_doi'] or r['reference_wikidata']
        if ref and ref not in occurrences[key][sid]['references']:
            occurrences[key][sid]['references'].append(ref)
    counts['matched_full_inchikeys'] = len(occurrences)
    groups = defaultdict(lambda: defaultdict(list))
    for r in filtered:
        key = keys[r['molecule_chembl_id']]
        if key in occurrences:
            groups[r['assay_chembl_id']][key].append(r)
    pairs = []
    seen_pairs = set()
    for assay in sorted(groups):
        for ka, kb in itertools.combinations(sorted(groups[assay]), 2):
            counts['same_assay_pairs_examined'] += 1
            sa, sb = set(occurrences[ka]), set(occurrences[kb])
            shared, union = sa & sb, sa | sb
            jaccard = len(shared) / len(union)
            if len(shared) < cfg['min_shared_species'] or jaccard < cfg['min_jaccard']:
                continue
            counts['confounded_assay_pairs'] += 1
            if len(union) < cfg['budget'] + 1:
                counts['excluded_insufficient_specimens'] += 1
                continue
            # Require all repeats within an assay to agree on binary threshold.
            labels = []
            for k in (ka, kb):
                label_set = {float(r['standard_value']) <= cfg['active_threshold_nM'] for r in groups[assay][k]}
                labels.append(next(iter(label_set)) if len(label_set) == 1 else None)
            if None in labels:
                counts['excluded_conflicting_activity_pair'] += 1
                continue
            if (ka, kb) in seen_pairs:
                counts['excluded_repeated_chemical_pair'] += 1
                continue
            seen_pairs.add((ka, kb))
            pairs.append((assay, ka, kb, shared, union, labels, jaccard))
    counts['eligible_unique_pairs'] = len(pairs)
    # Deterministic hash selection: no policy results used to select episodes.
    pairs.sort(key=lambda p: seed_for(cfg['seed'], p[1], p[2]))
    pairs = pairs[:cfg['max_pairs']]
    counts['selected_unique_pairs'] = len(pairs)
    episodes = []
    for assay, ka, kb, shared, union, labels, jaccard in pairs:
        truth = ('both' if all(labels) else 'A' if labels[0] else 'B' if labels[1] else 'neither')
        candidates = []
        for key in (ka, kb):
            records = groups[assay][key]
            r = records[0]
            candidates.append({'id': r['molecule_chembl_id'], 'name': r['molecule_pref_name'] or r['molecule_chembl_id'],
                'inchikey': key, 'smiles': r['canonical_smiles'], 'identity_match_tier': 'exact-full-InChIKey',
                'activity_records': [{k: q[k] for k in ('activity_id','assay_chembl_id','assay_description','document_chembl_id',
                   'standard_type','standard_units','standard_value','standard_relation','units','value','relation')} for q in records],
                'source_url': f"https://www.ebi.ac.uk/chembl/explore/compound/{r['molecule_chembl_id']}"})
        # The available pool has up to eight co-occurrences and four documented contrasts.
        rank = lambda sid: seed_for(cfg['seed'], ka, kb, sid)
        pool = sorted(shared, key=rank)[:8] + sorted(union - shared, key=rank)[:4]
        samples = []
        for sid in pool:
            occurrence = [occurrences[k].get(sid) for k in (ka, kb)]
            item = next(o for o in occurrence if o)
            concentration = .35 + (seed_for('concentration', sid) % 10000) / 10000 * 1.15
            samples.append({'id': sid, 'name': item['name'], 'x': [round(concentration if o else 0.0, 5) for o in occurrence],
                'units': 'simulated relative concentration', 'occurrence_status': ['documented' if o else 'not recorded; simulated zero' for o in occurrence],
                'evidence': occurrence})
        pair_id = f"{candidates[0]['id']}-{candidates[1]['id']}"
        for rep in range(cfg['replicates']):
            eid = f'{pair_id}-r{rep}'
            rng = np.random.default_rng(seed_for(cfg['seed'], eid))
            outcomes = {s['id']: float(means(s['x'], cfg)[HYPOTHESES.index(truth)] + rng.normal(0,cfg['noise_sd'])) for s in samples}
            episodes.append({'id': eid, 'pair_id': pair_id, 'tier': 'Simulation diagnostic', 'candidates': candidates,
                'samples': samples, 'initial': [pool[0]], 'hidden': {'truth': truth, 'outcomes': outcomes},
                'provenance': {'assay': assay, 'lotus_record': '19360665', 'jaccard': jaccard, 'shared_species': len(shared),
                    'union_species': len(union), 'replicate': rep, 'source_manifest': 'data/manifest.json'}, 'limitations': LIMITATIONS})
    if not episodes:
        save(Path(cfg['data_dir']) / 'audit.json', dict(counts))
        raise ValueError('No eligible authentic pairs; inspect data/audit.json')
    counts['episodes'] = len(episodes)
    counts['naturally_indistinguishable_episodes'] = sum(all(s['x'][0] == s['x'][1] for s in e['samples']) for e in episodes)
    counts['truth_distribution'] = dict(Counter(e['hidden']['truth'] for e in episodes))
    save(Path(cfg['data_dir'])/'manifest.json', {'sources': manifest, 'derived_license': 'CC-BY-SA-4.0', 'attribution': 'LOTUS Initiative; ChEMBL, EMBL-EBI', 'modifications': 'Filtered, identity-matched, thresholded and simulated by DECOUPLE.'})
    save(Path(cfg['data_dir'])/'episodes.json', episodes)
    save(Path(cfg['data_dir'])/'audit.json', dict(counts))
    return dict(counts)
