"""Fit the response-curve parameters of decouple.model.means to the data's scale.

model.means:  mu = background + (1 - background) * (1 - exp(-gain * load))

IMPORTANT: `gain` is only meaningful relative to what `x` represents. It must be
refitted for every representation and never inherited from another one:
    individual compound relative abundance (ENPKG rotenoids)  ->  ~44
    rotenoid *share* of an extract                            ->  ~0.75
    the shipped default 2.0 was tuned for simulated
    concentrations (median 0.68) and silently pins real data (median 0.0157)
    to background, so the engine abstains on ~100% of episodes.

Both fitters are closed-form / quantile based, hence deterministic.
"""
import copy
import numpy as np


def _present(abundances):
    a = np.asarray(list(abundances) if not isinstance(abundances, np.ndarray) else abundances,
                   dtype=float).ravel()
    return a[np.isfinite(a) & (a > 0)]


def fit_gain(abundances, target_mu=0.5):
    """gain = -ln(1 - target_mu) / median(abundance | abundance > 0).

    Makes the median *present* abundance land at `target_mu` of the saturating
    curve (for target_mu=0.5 the curve's 1-exp(-gain*x) term equals 0.5, i.e.
    gain = ln2 / median). Absent values (<= 0, NaN) are ignored: they carry no
    information about scale. Units of the result are 1/units(x).
    """
    if not 0 < target_mu < 1:
        raise ValueError('target_mu must be in (0, 1)')
    a = _present(abundances)
    if a.size == 0:
        raise ValueError('no present (>0) abundances to fit gain')
    return float(-np.log(1.0 - target_mu) / np.median(a))


def fit_background(abundances, responses, low_quantile=0.25):
    """Floor of the response: median response of the lowest-abundance extracts.

    `abundances` and `responses` are paired per extract (the load x that the
    model sees, and the measured response on the 0-1 scale). Extracts with
    abundance <= the `low_quantile` quantile of all abundances (absent extracts
    included, they are the purest floor) are selected; the median response of
    that group is the estimate, clipped to [0, 0.99]. Median, not mean, so a
    few outlying actives in the group do not inflate the floor.
    """
    a = np.asarray(abundances, dtype=float).ravel()
    r = np.asarray(responses, dtype=float).ravel()
    if a.shape != r.shape:
        raise ValueError('abundances and responses must be paired (same length)')
    ok = np.isfinite(a) & np.isfinite(r)
    a, r = a[ok], r[ok]
    if a.size == 0:
        raise ValueError('no finite (abundance, response) pairs')
    low = a <= np.quantile(a, low_quantile)
    return float(np.clip(np.median(r[low]), 0.0, 0.99))


def calibrate(abundances, responses=None, cfg=None):
    """Return a copy of cfg with fitted `gain` (and `background` if responses given)."""
    out = copy.deepcopy(cfg) if cfg is not None else {}
    out['gain'] = fit_gain(abundances)
    if responses is not None:
        out['background'] = fit_background(abundances, responses)
    return out
