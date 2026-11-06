import copy
import json
from pathlib import Path
import numpy as np
import pytest
from decouple.engine import start, visible, reveal, finalize, run, save, export
from decouple.model import information_gain, update, decision
from decouple.policies import recommend, POLICIES

CFG=json.loads(Path('config/default.json').read_text())
EPISODES=json.loads(Path('data/episodes.json').read_text())


def test_hidden_outcomes_and_labels_cannot_change_actions():
    e=copy.deepcopy(EPISODES[0]);state=start(e,CFG)
    before=visible(e,state,CFG)
    for c in e['candidates']:
        c['activity_records']=[]
    e['hidden']['truth']='neither'
    e['hidden']['outcomes']={sid:999 for sid in e['hidden']['outcomes']}
    after=visible(e,state,CFG)
    assert before==after
    for p in POLICIES:assert recommend(before,p,CFG)==recommend(after,p,CFG)


def test_budget_repeat_and_finalization():
    e=EPISODES[0];s=start(e,CFG)
    for _ in range(3):
        rec=recommend(visible(e,s,CFG),'decouple',CFG)
        reveal(e,s,rec['sample_id'],CFG)
        snapshot = copy.deepcopy(s)
        reveal(e,s,rec['sample_id'],CFG)
        assert s == snapshot
    unrevealed = next(sm['id'] for sm in e['samples'] if sm['id'] not in s['revealed'])
    with pytest.raises(ValueError, match='budget'):
        reveal(e, s, unrevealed, CFG)
    finalize(e,s,CFG)
    with pytest.raises(ValueError):finalize(e,s,CFG)


def test_resume_preserves_posterior_and_next_action(tmp_path):
    e=EPISODES[0];s=start(e,CFG)
    reveal(e,s,recommend(visible(e,s,CFG),'decouple',CFG)['sample_id'],CFG)
    path=tmp_path/'session.json';save(path,s)
    resumed=json.loads(path.read_text())
    assert visible(e,s,CFG)==visible(e,resumed,CFG)
    assert recommend(visible(e,s,CFG),'decouple',CFG)==recommend(visible(e,resumed,CFG),'decouple',CFG)


@pytest.mark.parametrize('policy',POLICIES)
def test_perfect_cooccurrence_always_abstains(policy):
    for original in EPISODES:
        co = [s for s in original['samples'] if s['x'][0] == s['x'][1]]
        if len(co) < CFG['budget'] + 1:
            continue
        e = copy.deepcopy(original)
        e['samples'] = co
        result=run(e,policy,CFG)
        assert result['decision']['kind']=='abstain'
        assert 'identical profiles' in result['decision']['explanation']


def test_both_and_neither_do_not_nominate_a_single_driver():
    e=EPISODES[0];v=visible(e,start(e,CFG),CFG)
    for p in ([.01,.01,.97,.01],[.01,.01,.01,.97]):
        v['posterior']=p
        assert decision(v,CFG)['kind']=='abstain'


def test_model_symmetry_and_information_gain():
    p=np.array([.45,.45,.05,.05])
    assert np.isclose(update(p,[1,1],.8,CFG)[0],update(p,[1,1],.8,CFG)[1])
    assert information_gain(p,[1,0],CFG,9)>information_gain(p,[1,1],CFG,9)
    assert information_gain(p,[0,0],CFG,9)<1e-10
    a=update(p,[1,0],.9,CFG);b=update(p,[0,1],.9,CFG)
    assert np.allclose(a,b[[1,0,2,3]])


def test_policies_share_inputs_and_complete_same_budget():
    for e in EPISODES:
        frozen=copy.deepcopy(e)
        views=[visible(e,start(e,CFG),CFG) for _ in POLICIES]
        assert all(v==views[0] for v in views)
        for policy in POLICIES:
            state=run(e,policy,CFG)
            assert len(state['trace'])==CFG['budget']
        assert e==frozen


def test_export_preserves_source_units_qualifiers_identity_tiers():
    e=EPISODES[0];out=export(e,run(e,'decouple',CFG),CFG)
    assert out['evidence']==e['candidates']
    for c in out['evidence']:
        assert c['identity_match_tier']=='exact-full-InChIKey'
        assert c['activity_records'][0]['standard_units']=='nM'
        assert c['activity_records'][0]['standard_relation']=='='
        assert 'units' in c['activity_records'][0]
    assert all('occurrence_status' in s for s in out['visible']['samples'])


def test_frozen_results_reproduce(tmp_path):
    from decouple.evaluate import evaluate
    cfg=copy.deepcopy(CFG);cfg['results_file']=str(tmp_path/'results.json')
    result=evaluate(cfg);frozen=json.loads(Path(CFG['results_file']).read_text())
    result['config']['results_file']=CFG['results_file']
    assert result==frozen


def test_idempotent_requests_and_revision_conflicts():
    episode = EPISODES[0]
    state = start(episode, CFG)
    sample_id = recommend(visible(episode, state, CFG), 'decouple', CFG)['sample_id']
    reveal(episode, state, sample_id, CFG, request_id='first', expected_revision=0)
    committed = copy.deepcopy(state)
    reveal(episode, state, sample_id, CFG, request_id='first', expected_revision=0)
    assert state == committed
    next_sample = recommend(visible(episode, state, CFG), 'decouple', CFG)['sample_id']
    with pytest.raises(ValueError, match='different operation'):
        reveal(episode, state, next_sample, CFG, request_id='first')
    with pytest.raises(ValueError, match='Stale state'):
        reveal(episode, state, next_sample, CFG, request_id='second', expected_revision=0)
    assert state == committed
    finalize(episode, state, CFG, abstain=True, request_id='stop', expected_revision=1)
    stopped = copy.deepcopy(state)
    finalize(episode, state, CFG, abstain=True, request_id='stop', expected_revision=1)
    assert state == stopped
    with pytest.raises(ValueError, match='finalized'):
        reveal(episode, state, next_sample, CFG)
    assert state['decision']['kind'] == 'abstain'
    assert len(state['trace']) == 1


def test_unfinished_export_and_visible_state_exclude_future_evidence():
    episode = copy.deepcopy(EPISODES[0])
    episode['candidates'][0]['private_new_label'] = 'secret'
    episode['samples'][0]['future_assay'] = 'secret'
    state = start(episode, CFG)
    output = export(episode, state, CFG)
    for candidate in output['evidence']:
        assert 'activity_records' not in candidate
        assert 'private_new_label' not in candidate
    assert 'future_assay' not in output['visible']['samples'][0]
    assert 'hidden' not in output
    output['visible']['revealed'].clear()
    assert state['revealed']


def test_legacy_session_import_and_concurrent_idempotency(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from decouple.server import SessionStore

    episode = EPISODES[0]
    state = start(episode, CFG)
    state.pop('revision')
    state.pop('requests')
    session_id = 'a' * 32
    (tmp_path / f'{session_id}.json').write_text(json.dumps(state))
    store = SessionStore(tmp_path)
    assert store.load(session_id) == state
    sample_id = recommend(visible(episode, state, CFG), 'decouple', CFG)['sample_id']

    def apply_request(_):
        return store.update(session_id, lambda loaded: reveal(
            episode, loaded, sample_id, CFG, request_id='concurrent', expected_revision=0))

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(apply_request, range(8)))
    assert all(result == results[0] for result in results)
    resumed = SessionStore(tmp_path).load(session_id)
    assert len(resumed['trace']) == 1
    assert resumed['revision'] == 1
    assert visible(episode, resumed, CFG)['remaining'] == 2

    def failing_transition(loaded):
        loaded['revealed'].clear()
        raise ValueError('Interrupted transaction')

    with pytest.raises(ValueError, match='Interrupted'):
        store.update(session_id, failing_transition)
    assert store.load(session_id) == resumed


def test_second_concurrent_action_cannot_use_stale_revision(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from decouple.server import SessionStore

    episode = EPISODES[0]
    store = SessionStore(tmp_path)
    state = start(episode, CFG)
    session_id = store.create(state)
    eligible = [sample['id'] for sample in episode['samples'] if sample['id'] not in state['revealed']]

    def apply_request(sample_id):
        try:
            store.update(session_id, lambda loaded: reveal(
                episode, loaded, sample_id, CFG, request_id=sample_id, expected_revision=0))
            return 'committed'
        except ValueError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(apply_request, eligible[:2]))
    assert results.count('committed') == 1
    assert sum('Stale state' in result for result in results) == 1
    assert len(store.load(session_id)['trace']) == 1


def test_structure_svg_rendering():
    from decouple.server import render_svg
    svg = render_svg('COc1ccc(cc1)C2OCC3C2COC3c4ccc(cc4)OC', width=200, height=100)
    assert '<svg' in svg
    assert '</svg>' in svg
    fallback = render_svg('INVALID_SMILES', width=200, height=100)
    assert '<svg' in fallback
    assert 'unavailable' in fallback


def test_terminal_demo_runs(capsys):
    from decouple.__main__ import run_demo
    run_demo(CFG)
    captured = capsys.readouterr()
    assert 'Live Terminal Demo' in captured.out
    assert 'FINAL DECISION' in captured.out
    assert 'Nomination' in captured.out
