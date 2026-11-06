"""Continuous attribution of activity to candidate compounds. Stdlib only.

score = Pearson r of log10(abundance + 1e-6) against activity over the assayed
extracts. Abundance is NEVER binarised here: a presence/absence rule ties the
candidates in 99.4% of hard cases (see EVALUATION.md). An absent compound has
abundance 0.0 -> log10(1e-6) = -6, an informative observation, not a missing value.
"""
import math
import random

EPS = 1e-6
N_BOOT = 400
SEED = 12345
_NEG_INF = float("-inf")


def _pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sxx = syy = sxy = 0.0
    for a, b in zip(x, y):
        da = a - mx
        db = b - my
        sxx += da * da
        syy += db * db
        sxy += da * db
    den = math.sqrt(sxx * syy)
    return sxy / den if den > 1e-12 else None


def attribute(candidates, assayed, activity, compounds, n_boot=N_BOOT, seed=SEED):
    """-> [{"cid","score","ci":(lo,hi),"n_informative"}] sorted by score descending.

    Zero-variance candidates get score -inf, ci (nan, nan), and sort last.
    The same bootstrap resamples are used for every candidate (paired comparison).
    """
    assayed = list(assayed)
    n = len(assayed)
    y = [activity[s] for s in assayed]
    rng = random.Random(seed)
    boots = [[rng.randrange(n) for _ in range(n)] for _ in range(n_boot)] if n > 1 else []
    log10 = math.log10
    out = []
    for cid in candidates:
        ab = compounds[cid]["abundance"]
        raw = [ab.get(s, 0.0) for s in assayed]
        n_inf = sum(1 for a in raw if a > 0)
        x = [log10(a + EPS) for a in raw]
        r = _pearson(x, y) if n > 1 else None
        if r is None:
            out.append({"cid": cid, "score": _NEG_INF, "ci": (float("nan"), float("nan")),
                        "n_informative": n_inf})
            continue
        rs = []
        for idx in boots:
            bx = [x[i] for i in idx]
            by = [y[i] for i in idx]
            b = _pearson(bx, by)
            if b is not None:
                rs.append(b)
        if len(rs) >= 20:
            rs.sort()
            m = len(rs)
            ci = (rs[int(0.025 * (m - 1))], rs[int(math.ceil(0.975 * (m - 1)))])
        else:
            ci = (float("nan"), float("nan"))
        out.append({"cid": cid, "score": r, "ci": ci, "n_informative": n_inf})
    out.sort(key=lambda d: -d["score"])   # stable; -inf last
    return out


def should_abstain(results, threshold=0.6):
    """True when there is no result or the top score is below threshold (-inf included)."""
    return not results or not results[0]["score"] >= threshold


# --------------------------------------------------------------------------
# Calibration: does the top score separate "driver among candidates" from "absent"?
# Setup follows scripts/robustness.py TEST 2.
# --------------------------------------------------------------------------
def _calibrate():
    import itertools
    import statistics as st
    from . import compounds as cm, enpkg_io as io

    MZ_TOL, RT_TOL, HITS, THRESH, SCALE, NOISE = 0.01, 0.20, 8, 0.02, 0.6, 8.0
    comp = {}
    for mode in ("pos", "neg"):
        for cid, v in cm.build_compounds(mode).items():
            comp[(mode, cid)] = v
    samples = sorted(io.load_samples())
    rotkeys = {k for k, v in io.load_structures().items() if "Rotenoids" in v["npc_class"]}
    rot_c = [c for c in comp if any(k in rotkeys for k in comp[c]["isdb_keys"])]
    print(f"compounds {len(comp)}  rotenoid compounds {len(rot_c)}")
    pairs = []
    for a, b in itertools.combinations(sorted(rot_c), 2):
        ca, cb = comp[a], comp[b]
        if abs(ca["mz"] - cb["mz"]) < 2 * MZ_TOL and abs(ca["rt"] - cb["rt"]) < 2 * RT_TOL:
            continue
        Sa, Sb = set(ca["abundance"]), set(cb["abundance"])
        if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa):
            pairs.append((a, b))
    print(f"confounded rotenoid pairs {len(pairs)}")

    def sim(cid, rng):
        ab = comp[cid]["abundance"]
        act = {}
        for s in samples:
            a = ab.get(s, 0.0)
            v = 0.0 if a <= 0 else 110.0 / (1.0 + math.exp(-(math.log10(a) - math.log10(THRESH)) / SCALE))
            act[s] = max(0.0, v + rng.gauss(0, NOISE))
        return act

    def sel_contrast(known, cands, budget=3):
        ks = set(known)
        pool = [s for s in samples if s not in ks]
        def g(s):
            v = [math.log10(comp[c]["abundance"].get(s, 0.0) + EPS) for c in cands]
            return max(v) - min(v)
        return sorted(pool, key=lambda s: -g(s))[:budget]

    rng = random.Random(5)
    sc = rng.sample(pairs, 120)
    present, absent = [], []
    for i, (A, B) in enumerate(sc):
        r = random.Random(i + 99)
        act = sim(A, r)
        known = sorted(samples, key=lambda x: -act[x])[:HITS]
        dec = [c for c in rot_c if c not in (A, B) and any(comp[c]["abundance"].get(s, 0) > 0 for s in known)]
        if len(dec) < 4:
            continue
        with_true = [A, B] + r.sample(dec, 3)
        without = [B] + r.sample(dec, 4)
        for cands, bucket in ((with_true, present), (without, absent)):
            res = attribute(cands, known + sel_contrast(known, cands), act, comp)
            bucket.append(res[0]["score"])
    mp, ma = st.median(present), st.median(absent)
    fc = sum(1 for w in absent if w > mp)
    print(f"trials: {len(present)} present / {len(absent)} absent")
    print(f"top score, true driver PRESENT: median {mp:.3f}   (target ~0.949)")
    print(f"top score, true driver ABSENT : median {ma:.3f}   (target ~0.415)")
    print(f"false-confidence: {fc}/{len(absent)}   (target 0/120)")
    for t in (0.5, 0.6, 0.7):
        print(f"  threshold {t}: abstain on absent {sum(w < t for w in absent)}/{len(absent)}, "
              f"abstain on present {sum(w < t for w in present)}/{len(present)}")


if __name__ == "__main__":
    _calibrate()
