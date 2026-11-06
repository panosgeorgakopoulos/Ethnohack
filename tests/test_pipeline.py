"""Pipeline tests for src.enpkg_io and src.compounds.

Acceptance values are the ENPKG release counts, cross-checked by scripts/ethno_provenance.py.
Run: python3 -m tests.test_pipeline   or   python3 -m unittest discover tests
"""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "enpkg")
HAVE_DATA = os.path.isdir(DATA_DIR)
SKIP_MSG = "data/enpkg/ is absent; download the ENPKG Zenodo files first (see A1)."

ASSAY_KEYS = {"Tcruzi_10ugml", "Tbruceirhod_10ugml", "Tbruceirhod_2ugml",
              "Ldonovani_10ugml", "Ldonovani_2ugml", "L6_10ugml"}


@unittest.skipUnless(HAVE_DATA, SKIP_MSG)
class TestEnpkgIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src import enpkg_io
        cls.io = enpkg_io
        cls.samples = enpkg_io.load_samples()
        cls.assays = enpkg_io.load_assays()
        cls.features = enpkg_io.load_features("pos")
        cls.canopus = enpkg_io.load_canopus("pos")
        cls.isdb = enpkg_io.load_isdb("pos")

    def test_sample_count(self):
        self.assertEqual(len(self.samples), 1600,
                         "ENPKG library has 1600 plant extracts")

    def test_assay_count(self):
        self.assertEqual(len(self.assays), 1600,
                         "every one of the 1600 extracts has an assay record (A1)")

    def test_total_readings(self):
        total = sum(len(v) for v in self.assays.values())
        self.assertEqual(total, 9600, "1600 extracts x 6 assays = 9600 readings (A1)")

    def test_assay_keys(self):
        for sid, a in self.assays.items():
            self.assertEqual(set(a), ASSAY_KEYS,
                             "assay dict for %s must have the 6 keys from the A1 API" % sid)

    def test_features_pos_size(self):
        self.assertGreater(len(self.features), 700000,
                           "positive-mode features table has >700,000 (sample,scan) entries (A1)")

    def test_canopus_pos_size(self):
        self.assertGreater(len(self.canopus), 540000,
                           "positive-mode CANOPUS table has >540,000 entries (A1)")

    def test_isdb_pos_size(self):
        n = len(self.isdb)
        self.assertTrue(250000 < n < 330000,
                        "positive-mode ISDB has ~288,000 entries (A1 spec); got %d" % n)

    def test_spot_check_pachyrhizus(self):
        s = self.samples["VGF139_H07"]
        self.assertEqual(s["species"], "Pachyrhizus erosus", "A1 acceptance spot check")
        self.assertEqual(s["organ"], "leaves", "A1 acceptance spot check")
        self.assertAlmostEqual(self.assays["VGF139_H07"]["Tcruzi_10ugml"], 112.2, delta=0.1,
                               msg="A1 acceptance: T. cruzi inhibition 112.2 %")

    def test_spot_check_chadsia(self):
        # Values from scripts/ethno_provenance.py output.
        s = self.samples["VGF150_H08"]
        self.assertEqual(s["species"], "Chadsia grevei", "ethno_provenance.py output")
        self.assertEqual(s["organ"], "roots", "ethno_provenance.py output")
        self.assertAlmostEqual(self.assays["VGF150_H08"]["Tcruzi_10ugml"], 108.6, delta=0.1,
                               msg="ethno_provenance.py output: T. cruzi 108.6 %")


@unittest.skipUnless(HAVE_DATA, SKIP_MSG)
class TestCompounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src import compounds
        cls.mod = compounds
        cls.c = compounds.build_compounds("pos")
        cls.n_samples = len({s for v in cls.c.values() for s in v["abundance"]})

    def test_compound_count(self):
        self.assertTrue(11000 < len(self.c) < 14000,
                        "A2 acceptance: 11,000 < compounds < 14,000; got %d" % len(self.c))

    def test_min_occurrence(self):
        bad = [k for k, v in self.c.items() if len(v["abundance"]) < 3]
        self.assertFalse(bad, "A2: every compound must be in >=3 extracts; violators: %s" % bad[:5])

    def test_ubiquity_filter(self):
        worst = max(len(v["abundance"]) for v in self.c.values())
        self.assertLessEqual(worst, 240,
                             "Global rule 2: no compound in >15%% of the library; 15%% of the "
                             "constant 1600-extract library = 240. The rotenoid at m/z 295.2268 "
                             "(1502/1600 extracts) must be dropped; got max %d" % worst)

    def test_no_ubiquitous_rotenoid(self):
        hits = [k for k, v in self.c.items()
                if abs(v["mz"] - 295.2268) < 0.01 and len(v["abundance"]) > 0.5 * 1600]
        self.assertFalse(hits, "the 1502-extract misannotated rotenoid must be filtered out")

    def test_record_keys(self):
        want = {"abundance", "mz", "rt", "canopus", "isdb_keys"}
        for k, v in self.c.items():
            self.assertTrue(want <= set(v), "compound %s missing keys %s" % (k, want - set(v)))

    def test_compound_matrix_shapes(self):
        cids, samples, mat = self.mod.compound_matrix(self.c)
        self.assertEqual(set(cids), set(self.c), "matrix rows must be exactly the compounds")
        self.assertEqual(len(cids), len(self.c), "no duplicate compound ids in matrix")
        self.assertEqual(len(samples), 1600,
                         "A2: samples axis holds ALL 1600 library extracts (an extract with none "
                         "of the compounds is a useful negative observation); abundance dicts "
                         "stay sparse")
        self.assertEqual(len(mat), sum(len(v["abundance"]) for v in self.c.values()),
                         "one matrix entry per (compound, sample) abundance record")
        cid = next(iter(self.c))
        s = next(iter(self.c[cid]["abundance"]))
        self.assertEqual(mat[(cid, s)], self.c[cid]["abundance"][s],
                         "matrix values must equal the compound abundance dicts")


if __name__ == "__main__":
    unittest.main()
