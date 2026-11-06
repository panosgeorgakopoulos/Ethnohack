"""Acquisition functions accept visible state only, never labels or future assays."""
import numpy as np
from .model import means, expected_nomination_gain, seed_for

POLICIES = ('random', 'strongest-first', 'correlation', 'disagreement', 'decouple')


def recommend(visible, policy, cfg):
    if policy not in POLICIES:
        raise ValueError('Unknown acquisition policy')
    if visible['remaining'] <= 0 or visible.get('decision'):
        return None
    eligible = [s for s in visible['samples'] if s['id'] not in visible['revealed']]
    if not eligible:
        return None
    p = np.array(visible['posterior'])
    seed = seed_for(cfg['seed'], visible['id'], len(visible['revealed']))
    rng = np.random.default_rng(seed)
    observed = [(s['x'], visible['revealed'][s['id']]) for s in visible['samples'] if s['id'] in visible['revealed']]
    scores = []
    for sample in eligible:
        mu = means(sample['x'], cfg)
        if policy == 'random':
            score = float(rng.random())
        elif policy == 'strongest-first':
            score = float(p @ mu)
        elif policy == 'disagreement':
            score = float(abs(mu[0] - mu[1]))
        elif policy == 'correlation':
            # Rank features using visible measurements only, then assay a specimen
            # richest in the leading positively associated feature.
            correlations = np.zeros(2)
            if len(observed) >= 2:
                x = np.array([value[0] for value in observed])
                y = np.array([value[1] for value in observed])
                for index, column in enumerate(x.T):
                    if np.std(column) > 1e-10 and np.std(y) > 1e-10:
                        correlations[index] = np.corrcoef(column, y)[0, 1]
            score = float(sample['x'][int(correlations.argmax())])
        else:
            score = expected_nomination_gain(p, sample['x'], cfg, seed)
        scores.append({'sample_id': sample['id'], 'score': score, 'predictions': dict(zip(('A','B','both','neither'), map(float, mu)))})
    scores.sort(key=lambda s: (-s['score'], s['sample_id']))
    return {'policy': policy, **scores[0], 'ranking': scores}
