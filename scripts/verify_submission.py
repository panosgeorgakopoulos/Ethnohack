"""Offline integrity checks for the submitted measured-data demo and headline metrics."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    episodes_path = ROOT / 'data/real/episodes.json'
    episodes = json.loads(episodes_path.read_text())
    manifest = json.loads((ROOT / 'data/real/manifest.json').read_text())
    assert hashlib.sha256(episodes_path.read_bytes()).hexdigest() == manifest['episodes_sha256']
    assert len(episodes) == 12
    assert all(e['hidden']['truth'] is None for e in episodes)
    benchmark = json.loads((ROOT / 'results/benchmark.json').read_text())
    regime = benchmark['regimes']['well_specified/single_driver']
    assert regime['n_episodes'] == 952 and regime['n_distinct_pairs'] == 238
    assert regime['n_hard'] == 58 and regime['n_distinct_pairs_hard'] == 16
    def cell(policy, rule='potency-only', stratum='hard', scoring='named'):
        return next(c for c in regime['cells'] if
                    (c['pool'], c['policy'], c['rule'], c['stratum'], c['scoring']) ==
                    ('unconstrained', policy, rule, stratum, scoring))
    assert cell('adaptive_contrast')['accuracy'] == cell('strongest-first')['accuracy']
    assert round(cell('adaptive_contrast')['accuracy'] * 100, 1) == 19.0
    assert round(cell('adaptive_contrast', stratum='overall', scoring='developable')['wasted_per_100'], 2) == 32.35
    assert round(cell('adaptive_contrast', 'selectivity-aware', 'overall', 'developable')['wasted_per_100'], 2) == 0.21
    print('Verified 12 measured replay episodes, source-manifest hash, and submission headline metrics.')

if __name__ == '__main__':
    main()
