"""Full benchmark through the production modules. Stdlib only.

python3 -m src.evaluate  -> results/benchmark.json, results/sweep.json

Real ENPKG composition, simulated activity from one true driver. Reports
easy / hard / overall separately, pick-overlap with `strongest`, and
pair-clustered bootstrap CIs (trials sharing a compound pair are not independent).
"""
import itertools
import json
import math
import os
import random
import time

from . import compounds as cm, enpkg_io as io
from .attribution import attribute
from .selection import select, ORACLE_SUBSAMPLE

MZ_TOL, RT_TOL, HITS, SCALE, BUDGET = 0.01, 0.20, 8, 0.6, 3
SEEDS, N_BOOT = 12, 2000
ORACLE_EASY_EVERY = 10     # oracle on every k-th EASY trial only (speed); ALL hard trials
STRATS = ("random", "strongest", "contrast-spread", "adaptive_contrast", "oracle")
NAMES = ("no_budget",) + STRATS
RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def load():
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
    pairs = random.Random(21).sample(pairs, len(pairs))
    return comp, samples, rot_c, pairs


def run(comp, samples, rot_c, pairs, noise, thresh, strategies, oracle_easy_every=None):
    """-> list of trial dicts. Strategies run on hard trials; on easy trials only if
    `oracle_easy_every` is not None (oracle then only on every k-th easy trial)."""
    lt = math.log10(thresh)
    trials, n_easy = [], 0
    for i, (A, B) in enumerate(pairs):
        abA = comp[A]["abundance"]
        for seed in range(SEEDS):
            r = random.Random(hash((i, seed, 31)) & 0xffffffff)
            act = {}
            for s in samples:
                a = abA.get(s, 0.0)
                v = 0.0 if a <= 0 else 110.0 / (1.0 + math.exp(-((math.log10(a) - lt) / SCALE)))
                act[s] = max(0.0, v + r.gauss(0, noise))
            known = sorted(samples, key=lambda x: -act[x])[:HITS]
            pa = tuple(abA.get(s, 0) >= thresh for s in known)
            pb = tuple(comp[B]["abundance"].get(s, 0) >= thresh for s in known)
            hard = pa == pb
            t = {"pair": i, "seed": seed, "hard": hard}
            trials.append(t)
            if not hard:
                n_easy += 1
                if oracle_easy_every is None:
                    continue
            dec = [c for c in rot_c if c not in (A, B)
                   and any(comp[c]["abundance"].get(s, 0) > 0 for s in known)]
            cands = [A, B] + r.sample(dec, min(3, len(dec)))
            t["correct"] = {"no_budget": attribute(cands, known, act, comp)[0]["cid"] == A}
            picks = {}
            for st in strategies:
                if st == "oracle" and not hard and (n_easy % oracle_easy_every):
                    continue
                extra = select(st, cands, known, samples, BUDGET, comp, activity=act, true_cid=A,
                               rng=random.Random(1000 + len(trials)))
                picks[st] = extra
                t["correct"][st] = attribute(cands, known + extra, act, comp)[0]["cid"] == A
            t["overlap"] = {k: len(set(picks[k]) & set(picks["strongest"]))
                            for k in ("contrast-spread", "adaptive_contrast") if k in picks and "strongest" in picks}
    return trials


def _acc(trials, st):
    v = [t["correct"][st] for t in trials if "correct" in t and st in t["correct"]]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


def _clustered(trials, fns, rng, n_boot=N_BOOT):
    """Resample whole compound pairs (with all seeds). fns: {name: f(list_of_trials)->float|None}.
    -> {name: {"point", "ci95"}}"""
    by = {}
    for t in trials:
        by.setdefault(t["pair"], []).append(t)
    keys = sorted(by)
    out = {n: [] for n in fns}
    for _ in range(n_boot):
        samp = [t for k in (rng.choice(keys) for _ in keys) for t in by[k]]
        for n, f in fns.items():
            v = f(samp)
            if v is not None:
                out[n].append(v)
    res = {}
    for n, f in fns.items():
        xs = sorted(out[n])
        p = f(trials)
        if xs:
            lo, hi = xs[int(0.025 * len(xs))], xs[min(len(xs) - 1, int(0.975 * len(xs)))]
            res[n] = {"point": p, "ci95": [lo, hi], "n_valid_resamples": len(xs)}
        else:
            res[n] = {"point": p, "ci95": None, "n_valid_resamples": 0}
    return res


def _fns(st_list):
    f = {st: (lambda ts, st=st: _acc(ts, st)[0]) for st in st_list}
    f["margin_adaptive_contrast_minus_strongest"] = lambda ts: (
        None if _acc(ts, "adaptive_contrast")[0] is None else _acc(ts, "adaptive_contrast")[0] - _acc(ts, "strongest")[0])
    f["margin_adaptive_contrast_minus_random"] = lambda ts: (
        None if _acc(ts, "adaptive_contrast")[0] is None else _acc(ts, "adaptive_contrast")[0] - _acc(ts, "random")[0])
    return f


def _summ(trials, names):
    d = {"n_trials": len(trials), "n_pairs": len({t["pair"] for t in trials}), "accuracy": {}, "n_scored": {}}
    for st in names:
        a, n = _acc(trials, st)
        d["accuracy"][st], d["n_scored"][st] = a, n
    return d


def benchmark(comp, samples, rot_c, pairs):
    t0 = time.time()
    trials = run(comp, samples, rot_c, pairs, 8.0, 0.02, STRATS, ORACLE_EASY_EVERY)
    hard = [t for t in trials if t["hard"]]
    easy = [t for t in trials if not t["hard"]]
    print(f"main run {time.time() - t0:.0f}s: {len(trials)} trials, {len(hard)} hard, {len(easy)} easy")
    rng = random.Random(7)
    strata = {}
    for label, ts in (("hard", hard), ("easy", easy), ("overall", trials)):
        sc = [t for t in ts if "correct" in t]
        d = _summ(sc, NAMES)
        d["n_trials_total"] = len(ts)
        d["n_pairs_total"] = len({t["pair"] for t in ts})
        names = [n for n in NAMES if n != "oracle"] if label != "hard" else list(NAMES)
        # overall/easy: oracle ran on a subset only, so its pooled number is not comparable
        if label != "hard":
            d["accuracy"]["oracle"] = None
            d["oracle_note"] = (f"oracle ran on every {ORACLE_EASY_EVERY}th easy trial only; "
                                "no pooled oracle figure reported")
        d["clustered_ci"] = _clustered(sc, _fns(names), rng)
        d["overlap_with_strongest"] = {
            k: (sum(t["overlap"][k] for t in sc) / len(sc) if sc else None) for k in ("contrast-spread", "adaptive_contrast")}
        strata[label] = d
    if hard:
        oh = [t for t in hard if "oracle" in t["correct"]]
    m = strata["hard"]["clustered_ci"]["margin_adaptive_contrast_minus_strongest"]
    ci0 = m["ci95"]
    includes_zero = ci0 is not None and ci0[0] <= 0 <= ci0[1]
    verdict = ("WARNING: clustered 95% CI on hard-case margin adaptive_contrast - strongest INCLUDES ZERO; "
               "headline margin is NOT statistically established" if includes_zero else
               "clustered 95% CI on hard-case margin adaptive_contrast - strongest excludes zero "
               f"([{ci0[0]:+.3f}, {ci0[1]:+.3f}])")
    out = {
        "config": {"hits": HITS, "budget": BUDGET, "noise": 8.0, "threshold": 0.02, "scale": SCALE,
                   "seeds_per_pair": SEEDS, "n_pairs_available": len(pairs), "n_boot": N_BOOT,
                   "bootstrap": "pair-clustered (resample compound pairs with all their seeds)",
                   "oracle_subsample": ORACLE_SUBSAMPLE,
                   "oracle_scope": f"all hard trials (full pool); every {ORACLE_EASY_EVERY}th easy trial only"},
        "strata": strata,
        "margin_ci_includes_zero": includes_zero,
        "verdict": verdict,
    }
    return out


def sweep(comp, samples, rot_c, pairs):
    cells = []
    sc = ("random", "strongest", "adaptive_contrast")
    for noise in (4.0, 8.0, 16.0):
        for th in (0.005, 0.02, 0.05):
            t0 = time.time()
            trials = run(comp, samples, rot_c, pairs, noise, th, sc)
            hard = [t for t in trials if t["hard"]]
            d = _summ(hard, ("no_budget",) + sc)
            d.update(noise=noise, threshold=th)
            ci = _clustered(hard, {"m": lambda ts: (None if _acc(ts, "adaptive_contrast")[0] is None
                            else _acc(ts, "adaptive_contrast")[0] - _acc(ts, "strongest")[0])},
                            random.Random(11), 1000)["m"]
            d["margin_adaptive_contrast_minus_strongest"] = ci["point"]
            d["margin_clustered_ci95"] = ci["ci95"]
            d["adaptive_contrast_beats_strongest"] = bool(ci["point"] is not None and ci["point"] > 0)
            cells.append(d)
            print(f"  sweep noise={noise:>4} th={th:<5} hard={d['n_trials']:>4} "
                  f"rand={d['accuracy']['random']:.3f} strong={d['accuracy']['strongest']:.3f} "
                  f"v2={d['accuracy']['adaptive_contrast']:.3f} margin={ci['point']:+.3f} "
                  f"CI={ci['ci95']} ({time.time() - t0:.0f}s)", flush=True)
    return {"cells": cells, "cells_adaptive_contrast_beats_strongest": sum(c["adaptive_contrast_beats_strongest"] for c in cells),
            "n_cells": len(cells)}


def main():
    os.makedirs(RESULTS, exist_ok=True)
    comp, samples, rot_c, pairs = load()
    print(f"rotenoid compounds {len(rot_c)}, confounded pairs {len(pairs)}")
    b = benchmark(comp, samples, rot_c, pairs)
    with open(os.path.join(RESULTS, "benchmark.json"), "w") as f:
        json.dump(b, f, indent=2)
    for label in ("hard", "easy", "overall"):
        d = b["strata"][label]
        print(f"\n[{label}] trials={d['n_trials_total']} distinct pairs={d['n_pairs_total']}")
        for st in NAMES:
            a, ci = d["accuracy"][st], d["clustered_ci"].get(st)
            if a is None:
                print(f"  {st:10} n/a (subset only)")
                continue
            print(f"  {st:10} {a:6.1%}  CI [{ci['ci95'][0]:.1%}, {ci['ci95'][1]:.1%}]"
                  + (f"  (oracle n={d['n_scored'][st]})" if st == 'oracle' else ""))
        for k in ("margin_adaptive_contrast_minus_strongest", "margin_adaptive_contrast_minus_random"):
            c = d["clustered_ci"][k]
            print(f"  {k}: {c['point']:+.1%}  CI [{c['ci95'][0]:+.1%}, {c['ci95'][1]:+.1%}]")
        print(f"  overlap with strongest: {d['overlap_with_strongest']}")
    print("\n" + b["verdict"])
    print("\nsweep (hard cases):")
    s = sweep(comp, samples, rot_c, pairs)
    with open(os.path.join(RESULTS, "sweep.json"), "w") as f:
        json.dump(s, f, indent=2)
    print(f"adaptive_contrast > strongest in {s['cells_adaptive_contrast_beats_strongest']}/{s['n_cells']} cells")


if __name__ == "__main__":
    main()
