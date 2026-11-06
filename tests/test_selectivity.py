import unittest

from decouple.model import means
from decouple.selectivity import dual_posterior, selective_decision

CFG = {'prior': [0.4, 0.4, 0.1, 0.1], 'noise_sd': 0.12, 'background': 0.05, 'gain': 50.0,
       'nomination_threshold': 0.9, 'tox_cap': 0.5}
SAMPLES = [{'id': 's1', 'x': [0.05, 0.0]}, {'id': 's2', 'x': [0.0, 0.05]},
           {'id': 's3', 'x': [0.08, 0.0]}, {'id': 's4', 'x': [0.0, 0.0]}]


def channel(hyp):
    return {s['id']: float(means(s['x'], CFG)[hyp]) for s in SAMPLES[:3]}


class SelectivityTests(unittest.TestCase):
    def test_driving_both_channels_not_nominated(self):
        p_par, p_tox = dual_posterior(SAMPLES, channel(0), channel(0), CFG)
        d = selective_decision(p_par, p_tox, SAMPLES, channel(0), CFG)
        self.assertEqual(d['kind'], 'abstain')
        self.assertIn('host cells', d['explanation'])

    def test_parasite_only_is_nominated(self):
        p_par, p_tox = dual_posterior(SAMPLES, channel(0), channel(3), CFG)
        d = selective_decision(p_par, p_tox, SAMPLES, channel(0), CFG)
        self.assertEqual(d['kind'], 'nominate')
        self.assertEqual(d['candidate'], 'A')

    def test_unconfident_parasite_abstains(self):
        p_par, p_tox = dual_posterior(SAMPLES, {}, {}, CFG)
        d = selective_decision(p_par, p_tox, SAMPLES, {}, CFG)
        self.assertEqual(d['kind'], 'abstain')


if __name__ == '__main__':
    unittest.main()
