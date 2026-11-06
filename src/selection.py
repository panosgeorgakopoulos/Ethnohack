"""Choose which extracts to assay next, under a budget. Stdlib only.

"contrast-spread" scores every unassayed extract by the spread (max - min) of
log10(abundance + 1e-6) across the WHOLE candidate set, picks the best, adds it to
the assayed set and re-scores. It never privileges a pair of candidates: two
earlier rules that did (pairwise decorrelation, two-candidate information gain)
lost to random (see EVALUATION.md). Abundance is never binarised.
"""
import math
import random

EPS = 1e-6
# Oracle must search the FULL pool to be a valid upper bound. At 400 it scored
# 73.2% while adaptive_contrast scored 78.6% on the same trials -- i.e. it was not a ceiling
# at all. On the full pool it scores 92.9%. Lower this only to speed up a smoke
# run, never when reporting a ceiling.
ORACLE_SUBSAMPLE = None  # None = full pool
AMBIG_MARGIN = 0.15      # candidates within this of the top score are 'ambiguous'
REDUNDANCY_WEIGHT = 1.0  # fixed a priori (equal weight of two [0,1] terms); not tuned


def _logab(compounds, cid, s):
    return math.log10(compounds[cid]["abundance"].get(s, 0.0) + EPS)


def _spread(candidates, compounds, s):
    v = [_logab(compounds, c, s) for c in candidates]
    return max(v) - min(v)


def _pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sxx * syy)
    return sxy / den if den > 1e-12 else -1e9


def _scores(candidates, rows, activity, compounds):
    y = [activity[s] for s in rows]
    return {c: _pearson([_logab(compounds, c, s) for s in rows], y) for c in candidates}


def select(strategy, candidates, assayed, pool, budget, compounds, *,
           activity=None, true_cid=None, rng=None):
    """-> list of up to `budget` sample ids drawn from pool minus assayed."""
    candidates = list(candidates)
    done = set(assayed)
    avail = [s for s in pool if s not in done]
    budget = min(budget, len(avail))

    if strategy == "random":
        return (rng or random.Random()).sample(avail, budget)

    if strategy == "strongest":
        key = {s: max(compounds[c]["abundance"].get(s, 0.0) for c in candidates) for s in avail}
        return sorted(avail, key=lambda s: -key[s])[:budget]

    if strategy == "contrast-spread":
        chosen = []
        remaining = set(avail)
        for _ in range(budget):
            # deterministic tie-break on sample id
            best = max(sorted(remaining), key=lambda s: _spread(candidates, compounds, s))
            chosen.append(best)
            remaining.discard(best)
        return chosen

    if strategy == "adaptive_contrast":
        if activity is None:
            raise ValueError("adaptive_contrast needs activity for the assayed extracts")
        from .attribution import attribute
        k = len(candidates)
        maxd = 6.0 * math.sqrt(k)          # largest possible distance (log range is 6)
        vec = lambda s: [_logab(compounds, c, s) for c in candidates]
        cur = list(assayed)
        chosen, picked_v = [], []
        remaining = sorted(avail)
        for _ in range(budget):
            res = attribute(candidates, cur, activity, compounds, n_boot=0)
            top = res[0]["score"]
            amb = [r["cid"] for r in res if top != float("-inf") and r["score"] >= top - AMBIG_MARGIN]
            if len(amb) < 2:
                amb = [r["cid"] for r in res[:3]]
            best, bs = None, None
            for s in remaining:
                v = [_logab(compounds, c, s) for c in amb]
                spread = (max(v) - min(v)) / 6.0               # in [0,1]
                x = vec(s)
                sim = max((1.0 - math.dist(x, pv) / maxd for pv in picked_v), default=0.0)
                score = spread - REDUNDANCY_WEIGHT * sim       # both terms in [0,1], weight 1
                if bs is None or score > bs:
                    best, bs = s, score
            chosen.append(best)
            picked_v.append(vec(best))
            cur.append(best)
            remaining.remove(best)
        return chosen

    if strategy == "oracle":
        if true_cid is None or activity is None:
            raise ValueError("oracle needs true_cid and activity")
        pool_sorted = sorted(avail)
        sub = (pool_sorted if ORACLE_SUBSAMPLE is None
               else random.Random(3).sample(pool_sorted, min(ORACLE_SUBSAMPLE, len(pool_sorted))))
        cur = list(assayed)
        chosen = []
        for _ in range(budget):
            best, bkey = None, None
            for s in sub:
                if s in chosen:
                    continue
                sc = _scores(candidates, cur + [s], activity, compounds)
                comp = [v for c, v in sc.items() if c != true_cid]
                margin = sc[true_cid] - (max(comp) if comp else -1e9)
                key = (margin > 0, margin)
                if bkey is None or key > bkey:
                    best, bkey = s, key
            if best is None:
                break
            chosen.append(best)
            cur.append(best)
        return chosen

    raise ValueError(f"unknown strategy {strategy!r}")


def _benchmark():
    import itertools
    from . import compounds as cm, enpkg_io as io
    from .attribution import attribute

    MZ_TOL, RT_TOL, HITS, THRESH, SCALE, NOISE = 0.01, 0.20, 8, 0.02, 0.6, 8.0
    comp = {}
    for mode in ("pos", "neg"):
        for cid, v in cm.build_compounds(mode).items():
            comp[(mode, cid)] = v
    samples = sorted(io.load_samples())
    rotkeys = {k for k, v in io.load_structures().items() if "Rotenoids" in v["npc_class"]}
    rot_c = [c for c in comp if any(k in rotkeys for k in comp[c]["isdb_keys"])]
    pairs = []
    for a, b in itertools.combinations(sorted(rot_c), 2):
        ca, cb = comp[a], comp[b]
        if abs(ca["mz"] - cb["mz"]) < 2 * MZ_TOL and abs(ca["rt"] - cb["rt"]) < 2 * RT_TOL:
            continue
        Sa, Sb = set(ca["abundance"]), set(cb["abundance"])
        if len(Sa & Sb) >= 3 and (Sa - Sb) and (Sb - Sa):
            pairs.append((a, b))
    print(f"rotenoid compounds {len(rot_c)}, confounded pairs {len(pairs)}")

    def sim(cid, r):
        ab = comp[cid]["abundance"]
        act = {}
        for s in samples:
            a = ab.get(s, 0.0)
            v = 0.0 if a <= 0 else 110.0 / (1.0 + math.exp(-((math.log10(a) - math.log10(THRESH)) / SCALE)))
            act[s] = max(0.0, v + r.gauss(0, NOISE))
        return act

    order = random.Random(21)
    pairs = order.sample(pairs, len(pairs))
    names = ("no_budget", "random", "strongest", "contrast-spread", "adaptive_contrast", "oracle")
    hit = {k: 0 for k in names}
    nhard = 0
    ov = {"contrast-spread": 0, "adaptive_contrast": 0}
    TARGET, SEEDS = 400, 12
    for i, (A, B) in enumerate(pairs):
        for seed in range(SEEDS):
            r = random.Random(hash((i, seed, 31)) & 0xffffffff)
            act = sim(A, r)
            known = sorted(samples, key=lambda x: -act[x])[:HITS]
            pa = tuple(comp[A]["abundance"].get(s, 0) >= THRESH for s in known)
            pb = tuple(comp[B]["abundance"].get(s, 0) >= THRESH for s in known)
            if pa != pb:
                continue
            dec = [c for c in rot_c if c not in (A, B)
                   and any(comp[c]["abundance"].get(s, 0) > 0 for s in known)]
            cands = [A, B] + r.sample(dec, min(3, len(dec)))
            nhard += 1
            hit["no_budget"] += attribute(cands, known, act, comp)[0]["cid"] == A
            picks = {}
            for st in ("random", "strongest", "contrast-spread", "adaptive_contrast", "oracle"):
                extra = select(st, cands, known, samples, 3, comp, activity=act, true_cid=A,
                               rng=random.Random(1000 + nhard))
                picks[st] = extra
                hit[st] += attribute(cands, known + extra, act, comp)[0]["cid"] == A
            for k in ov:
                ov[k] += len(set(picks[k]) & set(picks["strongest"]))
        if nhard >= TARGET:
            break
    print(f"HARD trials: {nhard} (budget 3, {HITS} initial hits)\n")
    print(f"{'strategy':14}{'correct':>9}{'accuracy':>10}")
    for k in names:
        print(f"{k:14}{hit[k]:>9}{hit[k] / nhard:>10.1%}")
    for k in ov:
        print(f"mean overlap of {k} picks with strongest picks: {ov[k] / nhard:.2f}/3")


if __name__ == "__main__":
    _benchmark()
