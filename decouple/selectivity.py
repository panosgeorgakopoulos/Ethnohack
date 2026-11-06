"""Dual-channel selectivity: parasite potency AND host-cell cytotoxicity.

One extract reveal yields both readouts (ENPKG measures T. cruzi and L6 in the
same screen), so the single-channel inference in decouple.model is run twice
over identical x, once per channel. Nothing in model.py is reimplemented.
A candidate is nominated only if it drives the parasite channel and does NOT
drive the cytotoxicity channel.
"""
import numpy as np

from .model import HYPOTHESES, update

DEFAULT_TOX_CAP = 0.5


def _posterior(samples, revealed, cfg):
    p = np.array(cfg['prior'], dtype=float)
    by_id = {s['id']: s for s in samples}
    for sid, y in revealed.items():
        p = update(p, by_id[sid]['x'], y, cfg)
    return p


def dual_posterior(samples, revealed_parasite, revealed_cytotox, cfg):
    """Return (p_par, p_tox): posteriors over HYPOTHESES for each channel."""
    return (_posterior(samples, revealed_parasite, cfg),
            _posterior(samples, revealed_cytotox, cfg))


def selective_decision(p_par, p_tox, samples, revealed, cfg, names=('A', 'B')):
    """Drop-in alternative to model.decision(); same return shape."""
    p_par, p_tox = np.asarray(p_par), np.asarray(p_tox)
    thr = cfg['nomination_threshold']
    cap = cfg.get('tox_cap', DEFAULT_TOX_CAP)
    separable = any(abs(s['x'][0] - s['x'][1]) > 1e-10 for s in samples)
    i = int(p_par.argmax())
    if separable and i < 2 and p_par[i] >= thr and p_tox[i] <= cap:
        return {'kind': 'nominate', 'candidate': HYPOTHESES[i], 'probability': float(p_par[i]),
                'explanation': f'{names[i]} is the single-driver hypothesis for the parasite above the '
                               f'threshold and is not the host-cytotoxicity driver '
                               f'(P_tox={p_tox[i]:.2f} <= {cap}). Confirm with purified-compound assays.'}
    untested = [s for s in samples if s['id'] not in revealed]
    contrast = max(untested, key=lambda s: abs(s['x'][0] - s['x'][1]), default=None)
    if not separable:
        reason = (f'{names[0]} and {names[1]} have identical profiles in every available specimen. '
                  'No assay here can distinguish the two single-driver explanations.')
    elif i < 2 and p_par[i] >= thr:
        # confident parasite driver, so the toxicity condition is what failed
        reason = (f'{names[i]} drives the parasite (P={p_par[i]:.2f}) but also the host cells '
                  f'(P_tox={p_tox[i]:.2f} > cap {cap}): likely cytotoxic, not a selective lead.')
    elif i >= 2 and p_par[i] >= thr:
        reason = f'The evidence favors {HYPOTHESES[i]}, so it does not justify isolating one driver.'
    else:
        reason = (f'The parasite evidence cannot confidently separate {names[0]}, {names[1]}, '
                  'both, and neither at the configured threshold.')
    return {'kind': 'abstain', 'candidate': None, 'probability': float(p_par[i]), 'explanation': reason,
            'next_contrast': contrast['id'] if contrast and abs(contrast['x'][0] - contrast['x'][1]) > 1e-10 else None}
