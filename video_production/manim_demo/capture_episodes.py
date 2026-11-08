"""Drive the live DECOUPLE server and capture real episode trajectories as JSON.

The Manim demo renders the UI from these captured states, so every number on
screen comes from the engine, not from the script.
Usage: python capture_episodes.py [--port 8089]
"""
import json, sys, uuid, urllib.request
from pathlib import Path

PORT = 8089
for a in sys.argv[1:]:
    if a.startswith('--port='):
        PORT = int(a.split('=', 1)[1])
BASE = f'http://localhost:{PORT}'
OUT = Path(__file__).parent / 'episodes.json'


def api(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={'Content-Type': 'application/json'} if data else {})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def mutate(state, path, **extra):
    return api(path, {'session': state['session_id'], 'expected_revision': state['revision'],
                      'request_id': str(uuid.uuid4()), **extra})


def run(ep_id):
    s = api('/api/start', {'episode_id': ep_id, 'diagnostic': False})
    states = [s]
    while s['remaining'] and s.get('recommendation'):
        s = mutate(s, '/api/reveal', sample_id=s['recommendation']['sample_id'])
        states.append(s)
    s = mutate(s, '/api/finalize')
    states.append(s)
    compare = api('/api/compare?session=' + s['session_id'])
    return {'id': ep_id, 'states': states, 'compare': compare}


def main():
    cat = api('/api/catalog')
    out = {'catalog': cat, 'results': api('/api/results'), 'episodes': {}}
    for e in cat['episodes']:
        r = run(e['id'])
        out['episodes'][e['id']] = r
        d = r['states'][-1]['decision']
        print(e['id'], d['kind'], d.get('candidates') or d.get('candidate'),
              [round(p, 3) for p in r['states'][0]['posterior']], '->',
              [round(p, 3) for p in r['states'][-1]['posterior']])
    OUT.write_text(json.dumps(out, indent=1))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
