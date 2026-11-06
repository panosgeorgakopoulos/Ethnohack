"""NumPy reference implementation of the four-hypothesis decision model.

Mirrors decouple/model.py so analysis scripts can drive it directly with
arbitrary abundance matrices. benchmark.py asserts the two agree.
"""
import hashlib, numpy as np

HYPOTHESES = ('A', 'B', 'both', 'neither')
CFG = dict(seed=20261106, budget=3, prior=[0.4, 0.4, 0.1, 0.1], noise_sd=0.12,
           background=0.05, gain=2.0, nomination_threshold=0.9, simulation_draws=128)

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

def nomination_utility(posterior, threshold):
    probability = np.max(np.asarray(posterior)[..., :2], axis=-1)
    return np.maximum(0.0, (probability - threshold) / (1.0 - threshold))

def expected_nomination_gain(posterior, x, cfg, seed):
    p = np.asarray(posterior); mu = means(x, cfg)
    rng = np.random.default_rng(seed)
    r = mu[:, None] + cfg['noise_sd'] * rng.normal(size=(4, cfg['simulation_draws']))
    lw = np.log(np.maximum(p, 1e-300)) - 0.5 * ((r[:, :, None] - mu) / cfg['noise_sd']) ** 2
    up = np.exp(lw - lw.max(axis=-1, keepdims=True)); up /= up.sum(axis=-1, keepdims=True)
    th = cfg['nomination_threshold']
    return float(max(0.0, np.dot(p, nomination_utility(up, th).mean(axis=1))
                     - nomination_utility(p, th)))

def recommend(posterior, samples, revealed, policy, cfg, ep_id, step):
    step = len(revealed)   # the policies.py: seed_for(seed, id, len(revealed))
    elig = [s for s in samples if s['id'] not in revealed]
    if not elig: return None
    p = np.array(posterior)
    rng = np.random.default_rng(seed_for(cfg['seed'], ep_id, step))
    obs = [(s['x'], revealed[s['id']]) for s in samples if s['id'] in revealed]
    scored = []
    for s in elig:
        mu = means(s['x'], cfg)
        if policy == 'random':            sc = float(rng.random())
        elif policy == 'strongest-first': sc = float(p @ mu)
        elif policy == 'disagreement':    sc = float(abs(mu[0] - mu[1]))
        elif policy == 'correlation':
            cors = np.zeros(2)
            if len(obs) >= 2:
                X = np.array([o[0] for o in obs]); y = np.array([o[1] for o in obs])
                for i, col in enumerate(X.T):
                    if np.std(col) > 1e-10 and np.std(y) > 1e-10:
                        cors[i] = np.corrcoef(col, y)[0, 1]
            sc = float(s['x'][int(cors.argmax())])
        else:
            sc = expected_nomination_gain(p, s['x'], cfg, seed_for(cfg['seed'], ep_id, step))
        scored.append((sc, s['id']))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[0][1]

def decision(posterior, samples, revealed, cfg):
    p = np.array(posterior)
    separable = any(abs(s['x'][0] - s['x'][1]) > 1e-10 for s in samples)
    i = int(p.argmax())
    if separable and i < 2 and p[i] >= cfg['nomination_threshold']:
        return {'kind': 'nominate', 'candidate': HYPOTHESES[i], 'p': float(p[i])}
    return {'kind': 'abstain', 'candidate': None, 'p': float(p[i])}

def run_episode(samples, outcomes, initial, policy, cfg, ep_id, pool=None):
    """pool: optional restricted list of sample dicts the policy may choose from."""
    revealed = {s: outcomes[s] for s in initial}
    choices = pool if pool is not None else samples
    for step in range(cfg['budget']):
        sid = recommend(_post(posterior_of(samples, revealed, cfg)), choices, revealed,
                        policy, cfg, ep_id, step)
        if sid is None: break
        revealed[sid] = outcomes[sid]
    post = posterior_of(samples, revealed, cfg)
    return decision(post, samples, revealed, cfg), post

def posterior_of(samples, revealed, cfg):
    post = np.array(cfg['prior'], dtype=float)
    by = {s['id']: s for s in samples}
    for sid, y in revealed.items():
        post = update(post, by[sid]['x'], y, cfg)
    return post

def _post(p): return list(p)
