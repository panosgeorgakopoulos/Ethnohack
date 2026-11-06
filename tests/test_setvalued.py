import unittest

from decouple.model import means
from decouple.setvalued import set_decision

CFG = {'tox_cap': 0.5}
SAMPLES = [{'id': 's1', 'x': [0.05, 0.0]}, {'id': 's2', 'x': [0.0, 0.05]},
           {'id': 's3', 'x': [0.08, 0.0]}, {'id': 's4', 'x': [0.03, 0.03]}]
NEUTRAL = [0.0, 0.0, 0.0, 1.0]  # tox posterior: nothing cytotoxic


class SetValuedTests(unittest.TestCase):
    def test_confident_single_is_nominated(self):
        d = set_decision([0.97, 0.01, 0.01, 0.01], NEUTRAL, SAMPLES, ['s1', 's2'], CFG)
        self.assertEqual((d['kind'], d['candidates'], d['size']), ('nominate', ['A'], 1))
        self.assertEqual(d['next_contrast'], 's3')

    def test_ambiguous_pair_is_shortlist(self):
        d = set_decision([0.48, 0.48, 0.02, 0.02], NEUTRAL, SAMPLES, ['s1'], CFG)
        self.assertEqual(d['kind'], 'shortlist')
        self.assertEqual(sorted(d['candidates']), ['A', 'B'])
        self.assertGreaterEqual(d['mass'], 0.95)

    def test_synergy_is_joint(self):
        d = set_decision([0.01, 0.01, 0.97, 0.01], NEUTRAL, SAMPLES, ['s1'], CFG)
        self.assertEqual((d['kind'], d['candidates']), ('joint', ['both']))
        self.assertIn('fractionating', d['explanation'])

    def test_cytotoxic_leader_is_a_finding_not_fallthrough(self):
        d = set_decision([0.6, 0.38, 0.01, 0.01], [0.9, 0.05, 0.0, 0.05], SAMPLES, ['s1'], CFG)
        self.assertEqual((d['kind'], d['candidates'], d['vetoed']), ('cytotoxic', ['A'], ['A']))
        self.assertIn('do not isolate', d['explanation'])

    def test_cytotoxic_nonleader_dropped_leader_kept(self):
        d = set_decision([0.6, 0.38, 0.01, 0.01], [0.05, 0.9, 0.0, 0.05], SAMPLES, ['s1'], CFG)
        self.assertEqual((d['kind'], d['candidates'], d['vetoed']), ('nominate', ['A'], ['B']))

    def test_inseparable_abstains(self):
        s = [{'id': 's1', 'x': [0.05, 0.05]}, {'id': 's2', 'x': [0.0, 0.0]}]
        d = set_decision([0.5, 0.5, 0.0, 0.0], NEUTRAL, s, ['s1', 's2'], CFG)
        self.assertEqual((d['kind'], d['candidates']), ('abstain', []))
        self.assertIsNone(d['next_contrast'])


if __name__ == '__main__':
    unittest.main()
