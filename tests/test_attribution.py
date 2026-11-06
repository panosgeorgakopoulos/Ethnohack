"""Tests for src.attribution, using small hand-built fixtures.

Fixture conventions: `compounds[cid]["abundance"]` is a
sparse {sample: rel_area} dict (absent sample = 0), `assayed` is a list of
sample ids and `activity` is {sample: value}. Score = Pearson correlation of
log10(abundance + 1e-6) with activity over `assayed`.

Run: python3 -m tests.test_attribution   or   python3 -m unittest discover tests
"""
import math
import unittest

from src.attribution import attribute, should_abstain


def mk(abund):
    return {"abundance": dict(abund), "mz": 300.0, "rt": 1.0,
            "canopus": ("x", 1.0), "isdb_keys": []}


SAMPLES = ["s%02d" % i for i in range(1, 13)]
ACT = {s: float(i) for i, s in enumerate(SAMPLES, 1)}   # activity 1..12


def by_cid(results):
    return {r["cid"]: r for r in results}


class TestAttribution(unittest.TestCase):
    def test_sorted_and_keys(self):
        comps = {
            "up": mk({s: 0.01 * i for i, s in enumerate(SAMPLES, 1)}),
            "down": mk({s: 0.01 * (13 - i) for i, s in enumerate(SAMPLES, 1)}),
            "flat": mk({s: 0.05 for s in SAMPLES}),
        }
        res = attribute(list(comps), SAMPLES, ACT, comps)
        self.assertEqual(len(res), 3, "one result per candidate")
        for r in res:
            self.assertTrue({"cid", "score", "ci", "n_informative"} <= set(r),
                            "every result needs cid, score, ci, n_informative (A3 API)")
        scores = [r["score"] for r in res]
        self.assertEqual(scores, sorted(scores, reverse=True),
                         "results must be score-descending (A3 API)")

    def test_perfect_positive_scores_one(self):
        comps = {"up": mk({s: 0.001 * 2 ** i for i, s in enumerate(SAMPLES, 1)})}
        res = attribute(["up"], SAMPLES, ACT, comps)
        self.assertGreater(res[0]["score"], 0.95,
                           "abundance rising monotonically with activity must correlate ~1")

    def test_zero_variance_is_neg_inf_and_last(self):
        comps = {
            "flat": mk({s: 0.05 for s in SAMPLES}),
            "up": mk({s: 0.01 * i for i, s in enumerate(SAMPLES, 1)}),
            "down": mk({s: 0.01 * (13 - i) for i, s in enumerate(SAMPLES, 1)}),
        }
        res = attribute(list(comps), SAMPLES, ACT, comps)
        self.assertEqual(res[-1]["cid"], "flat",
                         "undefined-correlation compound must sort last")
        self.assertEqual(res[-1]["score"], -math.inf,
                         "zero variance across assayed -> score = -inf (A3 spec)")

    def test_absent_samples_are_minus_six_not_missing(self):
        # Present only in the two lowest-activity extracts, rising 0.1 -> 0.5.
        # Present-only correlation would be +1; with absent = log10(1e-6) = -6
        # for the four high-activity extracts, the correlation is strongly negative.
        assayed = SAMPLES[:6]
        comps = {"c": mk({"s01": 0.1, "s02": 0.5})}
        res = attribute(["c"], assayed, ACT, comps)
        self.assertLess(res[0]["score"], 0,
                        "absent extracts must enter as log10(1e-6) = -6, not be dropped; "
                        "dropping them would give a positive score")

    def test_ci_brackets_and_is_reproducible(self):
        noise = [0.3, -0.2, 0.25, -0.35, 0.1, -0.1, 0.2, -0.3, 0.15, -0.25, 0.3, -0.15]
        comps = {"c": mk({s: 10 ** (-3 + 0.2 * i + n) for i, (s, n) in
                          enumerate(zip(SAMPLES, noise), 1)})}
        r1 = attribute(["c"], SAMPLES, ACT, comps)[0]
        r2 = attribute(["c"], SAMPLES, ACT, comps)[0]
        lo, hi = r1["ci"]
        self.assertLessEqual(lo, r1["score"], "CI lower bound must not exceed the point estimate")
        self.assertGreaterEqual(hi, r1["score"], "CI upper bound must not fall below the point estimate")
        self.assertEqual(r1["ci"], r2["ci"], "bootstrap must use a fixed seed (reproducible)")
        self.assertEqual(r1["score"], r2["score"], "scores must be deterministic")

    def test_n_informative_counts_detected_only(self):
        # Same detection count (4 extracts), opposite relationship to activity.
        comps = {
            "a": mk({"s09": 0.1, "s10": 0.2, "s11": 0.3, "s12": 0.4}),
            "b": mk({"s09": 0.4, "s10": 0.3, "s11": 0.2, "s12": 0.1}),
            "c": mk({"s01": 0.1}),
        }
        r = by_cid(attribute(list(comps), SAMPLES, ACT, comps))
        self.assertEqual(r["a"]["n_informative"], 4, "n_informative = extracts with abundance > 0")
        self.assertEqual(r["b"]["n_informative"], 4, "independent of score: same count, different score")
        self.assertNotEqual(r["a"]["score"], r["b"]["score"], "fixture sanity: scores differ")
        self.assertEqual(r["c"]["n_informative"], 1, "single detection counts as 1")
        # Detections outside the assayed set must not count.
        r2 = by_cid(attribute(["a"], SAMPLES[:10], ACT, comps))
        self.assertEqual(r2["a"]["n_informative"], 2,
                         "only detections inside `assayed` count (s09, s10)")

    def test_should_abstain(self):
        self.assertTrue(should_abstain([{"cid": "x", "score": 0.4}]),
                        "top score 0.4 < default 0.6 -> abstain (absent-driver median 0.415)")
        self.assertFalse(should_abstain([{"cid": "x", "score": 0.95}]),
                         "top score 0.95 >= 0.6 -> confident (present-driver median 0.949)")
        self.assertTrue(should_abstain([{"cid": "x", "score": 0.7}], threshold=0.8),
                        "explicit threshold must override the default")
        self.assertFalse(should_abstain([{"cid": "x", "score": 0.7}], threshold=0.5),
                         "explicit threshold must override the default")

    def test_regression_guard_continuous_not_binary(self):
        """REGRESSION GUARD: attribution must be continuous, never presence/absence.

        EVALUATION.md Rounds 3-4: a binary presence/absence rule ties the two
        candidates in 99.4% of hard cases, which drops even an ORACLE selector
        to 53.5% (chance). Continuous log-abundance correlation cuts ties to
        1.3%. Two compounds with IDENTICAL presence patterns but DIFFERENT
        abundance profiles must therefore score differently.
        """
        present = SAMPLES[:6]
        rising = {s: 0.01 * i for i, s in enumerate(present, 1)}
        falling = {s: 0.01 * (7 - i) for i, s in enumerate(present, 1)}
        self.assertEqual(set(rising), set(falling), "fixture: identical presence patterns")
        comps = {"A": mk(rising), "B": mk(falling)}
        r = by_cid(attribute(["A", "B"], SAMPLES, ACT, comps))
        self.assertNotEqual(r["A"]["score"], r["B"]["score"],
                            "identical presence/absence but different abundance MUST score "
                            "differently; equal scores means a binary rule was reintroduced")
        self.assertNotEqual(r["A"]["score"], -math.inf, "A has variance and must be scored")
        self.assertGreater(abs(r["A"]["score"] - r["B"]["score"]), 0.01,
                           "scores must separate meaningfully, not by float noise")


if __name__ == "__main__":
    unittest.main()
