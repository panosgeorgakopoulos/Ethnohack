"""The live episode loop runs both readouts when the data carries them."""
import json
from pathlib import Path

from decouple.engine import start, visible, reveal, finalize

CFG = json.loads(Path('config/enpkg.json').read_text())
REAL = json.loads((Path(CFG['data_dir']) / 'episodes.json').read_text())
TIER_A = json.loads(Path('data/episodes.json').read_text())


def _play(episode, cfg):
    state = start(episode, cfg)
    for sample in episode['samples']:
        if len(state['trace']) >= cfg['budget']:
            break
        if sample['id'] not in state['revealed']:
            reveal(episode, state, sample['id'], cfg)
    return finalize(episode, state, cfg)


def test_one_reveal_yields_both_readouts():
    episode = REAL[0]
    state = start(episode, CFG)
    assert state['revealed_cytotox'], 'the starting assay should carry its host-cell readout'
    sample_id = next(s['id'] for s in episode['samples'] if s['id'] not in state['revealed'])
    reveal(episode, state, sample_id, CFG)
    assert sample_id in state['revealed'] and sample_id in state['revealed_cytotox']
    assert state['trace'][-1]['response_cytotox'] == state['revealed_cytotox'][sample_id]
    view = visible(episode, state, CFG)
    assert view['posterior_cytotox'] is not None and len(view['posterior_cytotox']) == 4


def test_real_episodes_return_set_valued_verdicts():
    kinds = {_play(json.loads(json.dumps(e)), CFG)['decision']['kind'] for e in REAL}
    assert kinds <= {'nominate', 'shortlist', 'joint', 'cytotoxic', 'abstain'}
    for episode in REAL:
        decision = _play(json.loads(json.dumps(episode)), CFG)['decision']
        assert 'candidates' in decision and 'mass' in decision
        # the field pre-set-valued clients read stays single-valued or null
        assert decision['candidate'] in ('A', 'B', None)
        if decision['kind'] == 'nominate':
            assert decision['candidate'] == decision['candidates'][0]


def test_single_channel_data_keeps_the_scalar_rule():
    episode = json.loads(json.dumps(TIER_A[0]))
    cfg = json.loads(Path('config/default.json').read_text())
    assert 'outcomes_cytotox' not in episode['hidden']
    state = _play(episode, cfg)
    assert state['decision']['kind'] in ('nominate', 'abstain')
    assert 'candidates' not in state['decision']
    assert visible(episode, state, cfg)['posterior_cytotox'] is None
    assert all('response_cytotox' not in e for e in state['trace'])
