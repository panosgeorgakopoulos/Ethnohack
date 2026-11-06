"""Four-hypothesis Gaussian response model. No hidden outcomes enter this module."""
import hashlib
import numpy as np

HYPOTHESES = ('A', 'B', 'both', 'neither')


def seed_for(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str, parts)).encode()).digest()[:8], 'big')


def means(x, cfg):
    a, b = np.asarray(x, dtype=float)
    loads = np.array([a, b, a + b, 0.0])
    return cfg['background'] + (1 - cfg['background']) * (1 - np.exp(-cfg['gain'] * loads))


def update(posterior, x, y, cfg):
    p = np.asarray(posterior)
    logp = np.log(np.maximum(p, 1e-300)) - 0.5 * ((y - means(x, cfg)) / cfg['noise_sd']) ** 2
    q = np.exp(logp - logp.max())
    return q / q.sum()


def entropy(p):
    p = np.asarray(p)
    return -np.sum(p * np.log2(np.maximum(p, 1e-300)), axis=-1)


def information_gain(p, x, cfg, seed):
    """Stratified posterior predictive Monte Carlo; fixed draws per hypothesis."""
    p = np.asarray(p)
    mu = means(x, cfg)
    rng = np.random.default_rng(seed)
    y = mu[:, None] + cfg['noise_sd'] * rng.normal(size=(4, cfg['simulation_draws']))
    logp = np.log(np.maximum(p, 1e-300)) - .5 * ((y[:, :, None] - mu) / cfg['noise_sd']) ** 2
    q = np.exp(logp - logp.max(axis=-1, keepdims=True))
    q /= q.sum(axis=-1, keepdims=True)
    return float(max(0, entropy(p) - np.dot(p, entropy(q).mean(axis=1))))


def nomination_utility(posterior, threshold):
    """Utility of a confident single-driver nomination; abstention has value zero.

    A and B are exclusive single-driver hypotheses in this diagnostic. A false
    nomination costs threshold/(1-threshold), giving the same threshold as the
    final decision rule. Both/neither support abstention.
    """
    probability = np.max(np.asarray(posterior)[..., :2], axis=-1)
    return np.maximum(0.0, (probability - threshold) / (1.0 - threshold))


def expected_nomination_gain(posterior, x, cfg, seed):
    """One-step expected improvement in final nomination utility."""
    p = np.asarray(posterior)
    mu = means(x, cfg)
    rng = np.random.default_rng(seed)
    responses = mu[:, None] + cfg['noise_sd'] * rng.normal(size=(4, cfg['simulation_draws']))
    log_weights = np.log(np.maximum(p, 1e-300)) - 0.5 * (
        (responses[:, :, None] - mu) / cfg['noise_sd']
    ) ** 2
    updated = np.exp(log_weights - log_weights.max(axis=-1, keepdims=True))
    updated /= updated.sum(axis=-1, keepdims=True)
    threshold = cfg['nomination_threshold']
    expected = np.dot(p, nomination_utility(updated, threshold).mean(axis=1))
    return float(max(0.0, expected - nomination_utility(p, threshold)))


def decision(visible, cfg):
    p = np.array(visible['posterior'])
    samples = visible['samples']
    names = [c['name'] for c in visible['candidates']]
    separable = any(abs(s['x'][0] - s['x'][1]) > 1e-10 for s in samples)
    i = int(p.argmax())
    if separable and i < 2 and p[i] >= cfg['nomination_threshold']:
        return {'kind': 'nominate', 'candidate': HYPOTHESES[i], 'probability': float(p[i]),
                'explanation': f'{names[i]} is the single-driver hypothesis above the configured threshold. Confirm with purified-compound assays.'}
    untested = [s for s in samples if s['id'] not in visible['revealed']]
    contrast = max(untested, key=lambda s: abs(s['x'][0]-s['x'][1]), default=None)
    if not separable:
        reason = f'{names[0]} and {names[1]} have identical profiles in every available specimen. No assay here can distinguish the two single-driver explanations.'
    elif i >= 2 and p[i] >= cfg['nomination_threshold']:
        reason = f'The evidence favors {HYPOTHESES[i]}, so it does not justify isolating one driver.'
    else:
        reason = f'The evidence cannot confidently separate {names[0]}, {names[1]}, both, and neither at the configured threshold.'
    return {'kind': 'abstain', 'candidate': None, 'probability': float(p[i]), 'explanation': reason,
            'next_contrast': contrast['id'] if contrast and abs(contrast['x'][0]-contrast['x'][1]) > 1e-10 else None}
