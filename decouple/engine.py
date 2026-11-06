"""Episode transitions with a visible projection that excludes hidden outcomes."""
import copy
import json
import os
import tempfile
from pathlib import Path

from .model import update, decision
from .policies import recommend
from .setvalued import set_decision

PUBLIC_CANDIDATE_FIELDS = ('id', 'name', 'inchikey', 'smiles', 'identity_match_tier', 'source_url')
PUBLIC_SAMPLE_FIELDS = ('id', 'name', 'x', 'units', 'occurrence_status', 'evidence')


def start(episode, cfg):
    state = {'episode_id': episode['id'], 'revealed': {}, 'revealed_cytotox': {}, 'trace': [],
             'decision': None, 'revision': 0, 'requests': {}}
    tox = episode['hidden'].get('outcomes_cytotox') or {}
    for sample_id in episode.get('initial', []):
        state['revealed'][sample_id] = episode['hidden']['outcomes'][sample_id]
        if sample_id in tox:
            state['revealed_cytotox'][sample_id] = tox[sample_id]
    return state


def revision(state):
    return state.get('revision', len(state['trace']) + int(state['decision'] is not None))


def _posterior(episode, revealed, cfg):
    posterior = cfg['prior']
    for sample_id, response in revealed.items():
        sample = next(s for s in episode['samples'] if s['id'] == sample_id)
        posterior = update(posterior, sample['x'], response, cfg).tolist()
    return list(posterior)


def visible(episode, state, cfg):
    posterior = _posterior(episode, state['revealed'], cfg)
    cytotox = state.get('revealed_cytotox') or {}
    return {
        'id': episode['id'], 'tier': episode['tier'], 'target': cfg['target'],
        'candidates': [{key: candidate[key] for key in ('id', 'name')} for candidate in episode['candidates']],
        'samples': [{key: copy.deepcopy(sample[key]) for key in PUBLIC_SAMPLE_FIELDS if key in sample}
                    for sample in episode['samples']],
        'posterior': posterior, 'revealed': dict(state['revealed']),
        'revealed_cytotox': dict(cytotox),
        'posterior_cytotox': _posterior(episode, cytotox, cfg) if cytotox else None,
        'remaining': cfg['budget'] - len(state['trace']),
        'decision': copy.deepcopy(state['decision']), 'trace': copy.deepcopy(state['trace']),
        'revision': revision(state),
    }


def _request_replayed(state, request_id, operation, expected_revision):
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
            raise ValueError('Request ID must be a nonempty string of at most 128 characters')
        previous = state.get('requests', {}).get(request_id)
        if previous is not None:
            if previous != operation:
                raise ValueError('Request ID was already used for a different operation')
            return True
    if expected_revision is not None:
        if type(expected_revision) is not int or expected_revision != revision(state):
            raise ValueError('Stale state revision; reload the episode before continuing')
    return False


def _complete_request(state, request_id, operation):
    state['revision'] = revision(state) + 1
    if request_id is not None:
        state.setdefault('requests', {})[request_id] = operation


def reveal(episode, state, sample_id, cfg, policy='manual', request_id=None, expected_revision=None):
    operation = ['reveal', sample_id]
    if _request_replayed(state, request_id, operation, expected_revision):
        return state
    # A sample can be charged only once, including callers that do not send a request ID.
    if sample_id in state['revealed']:
        if request_id is not None:
            state.setdefault('requests', {})[request_id] = operation
        return state
    if state['decision'] is not None:
        raise ValueError('This episode is already finalized')
    if len(state['trace']) >= cfg['budget']:
        raise ValueError('The three-assay budget has been exhausted')
    if sample_id not in {sample['id'] for sample in episode['samples']}:
        raise ValueError('Unknown specimen')
    response = episode['hidden']['outcomes'][sample_id]
    # Store the revision before mutating legacy states that predate explicit revisions.
    state['revision'] = revision(state)
    state['revealed'][sample_id] = response
    cytotox_response = (episode['hidden'].get('outcomes_cytotox') or {}).get(sample_id)
    if cytotox_response is not None:
        state.setdefault('revealed_cytotox', {})[sample_id] = cytotox_response
    event = {'step': len(state['trace']) + 1, 'sample_id': sample_id,
             'response': response, 'policy': policy}
    if cytotox_response is not None:
        event['response_cytotox'] = cytotox_response
    state['trace'].append(event)
    event['posterior'] = visible(episode, state, cfg)['posterior']
    _complete_request(state, request_id, operation)
    return state


def finalize(episode, state, cfg, request_id=None, expected_revision=None, abstain=False):
    operation = ['abstain' if abstain else 'finalize']
    if _request_replayed(state, request_id, operation, expected_revision):
        return state
    if state['decision'] is not None:
        raise ValueError('This episode is already finalized')
    if not abstain and len(state['trace']) < cfg['budget']:
        raise ValueError('Complete the assay budget before finalizing, or abstain')
    state['revision'] = revision(state)
    view = visible(episode, state, cfg)
    if view['posterior_cytotox'] is not None:
        names = tuple(candidate['name'] for candidate in view['candidates'])
        result = set_decision(view['posterior'], view['posterior_cytotox'], view['samples'],
                              view['revealed'], cfg, mass=cfg.get('set_mass', 0.95), names=names)
        # keep the single-candidate field the pre-set-valued clients read
        candidates = result['candidates']
        result['candidate'] = candidates[0] if len(candidates) == 1 and candidates[0] in ('A', 'B') else None
    else:
        result = decision(view, cfg)
    if abstain:
        result = {'kind': 'abstain', 'candidate': None, 'probability': result['probability'],
                  'explanation': 'The user ended this episode without an isolation nomination.'}
    state['decision'] = result
    _complete_request(state, request_id, operation)
    return state


def run(episode, policy, cfg):
    state = start(episode, cfg)
    for _ in range(cfg['budget']):
        recommendation = recommend(visible(episode, state, cfg), policy, cfg)
        if recommendation is None:
            raise ValueError('Insufficient eligible specimens for budget')
        reveal(episode, state, recommendation['sample_id'], cfg, policy)
    return finalize(episode, state, cfg)


def save(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix=path.name + '.',
                                         suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(state, handle, indent=2, allow_nan=False)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def evidence(episode, state):
    if state['decision'] is not None:
        return copy.deepcopy(episode['candidates'])
    return [{key: copy.deepcopy(candidate[key]) for key in PUBLIC_CANDIDATE_FIELDS if key in candidate}
            for candidate in episode['candidates']]


def export(episode, state, cfg):
    return {'schema_version': 2, 'config': copy.deepcopy(cfg), 'visible': visible(episode, state, cfg),
            'evidence': evidence(episode, state), 'provenance': copy.deepcopy(episode['provenance']),
            'limitations': copy.deepcopy(episode['limitations'])}
