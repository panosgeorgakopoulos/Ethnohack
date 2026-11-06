"""Local web app with transactional, restart-safe episode sessions."""
import copy
import json
import re
import sqlite3
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .engine import start, visible, reveal, finalize, export, run, evidence
from .policies import recommend


class SessionStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'episodes.sqlite3'
        with sqlite3.connect(self.path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT NOT NULL)')

    def _read(self, connection, session_id):
        if not isinstance(session_id, str) or not re.fullmatch('[a-f0-9]{32}', session_id):
            raise ValueError('Invalid session')
        row = connection.execute('SELECT state FROM sessions WHERE id = ?', (session_id,)).fetchone()
        if row is not None:
            return json.loads(row[0])
        # Preserve sessions created by the original JSON-backed server.
        legacy = self.directory / f'{session_id}.json'
        if legacy.is_file():
            state = json.loads(legacy.read_text())
            connection.execute('INSERT INTO sessions VALUES (?, ?)', (session_id, json.dumps(state, allow_nan=False)))
            return state
        raise ValueError('Unknown session')

    def create(self, state):
        session_id = uuid.uuid4().hex
        with sqlite3.connect(self.path) as connection:
            connection.execute('INSERT INTO sessions VALUES (?, ?)',
                               (session_id, json.dumps(state, allow_nan=False)))
        return session_id

    def load(self, session_id):
        with sqlite3.connect(self.path, timeout=10) as connection:
            connection.execute('BEGIN IMMEDIATE')
            return self._read(connection, session_id)

    def update(self, session_id, transition):
        with sqlite3.connect(self.path, timeout=10) as connection:
            connection.execute('BEGIN IMMEDIATE')
            state = self._read(connection, session_id)
            transition(state)
            connection.execute('UPDATE sessions SET state = ? WHERE id = ?',
                               (json.dumps(state, allow_nan=False), session_id))
            return state


def create_server(cfg, port):
    episodes = json.loads((Path(cfg['data_dir']) / 'episodes.json').read_text())
    by_id = {episode['id']: episode for episode in episodes}
    store = SessionStore(Path(cfg['data_dir']) / 'sessions')
    static = Path(__file__).parent / 'static'

    def episode_for(state):
        episode = copy.deepcopy(by_id[state['episode_id']])
        if state.get('diagnostic'):
            episode['samples'] = [s for s in episode['samples'] if s['x'][0] == s['x'][1]]
            episode['tier'] = 'Diagnostic · reconstructed, contrasts withheld'
        return episode

    def present(session_id, episode, state):
        view = visible(episode, state, cfg)
        view.update(session_id=session_id, recommendation=recommend(view, 'decouple', cfg),
                    strongest=recommend(view, 'strongest-first', cfg))
        view['evidence'] = evidence(episode, state)
        view['limitations'] = episode['limitations']
        return view

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, obj, code=200):
            payload = json.dumps(obj, allow_nan=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            try:
                url = urlparse(self.path)
                query = parse_qs(url.query)
                if url.path == '/api/catalog':
                    self.send({'episodes': [
                        {'id': e['id'], 'names': [c['name'] for c in e['candidates']]}
                        for e in episodes if e['provenance']['replicate'] == 0],
                        'audit': json.loads((Path(cfg['data_dir']) / 'audit.json').read_text())})
                    return
                if url.path == '/api/results':
                    result = json.loads(Path(cfg['results_file']).read_text())
                    result.pop('rows', None)
                    self.send(result)
                    return
                if url.path in ('/api/state', '/api/export', '/api/compare'):
                    session_id = query.get('session', [''])[0]
                    state = store.load(session_id)
                    episode = episode_for(state)
                    if url.path == '/api/state':
                        self.send(present(session_id, episode, state))
                    elif url.path == '/api/export':
                        self.send(export(episode, state, cfg))
                    else:
                        if state['decision'] is None:
                            raise ValueError('Finalize this episode before comparing the full baseline replay')
                        baseline = run(episode, 'strongest-first', cfg)
                        self.send({'you': visible(episode, state, cfg), 'baseline': visible(episode, baseline, cfg)})
                    return
                name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css',
                        '/geist.woff2': 'geist.woff2'}.get(url.path)
                if name is None:
                    self.send({'error': 'Not found'}, 404)
                    return
                data = (static / name).read_bytes()
                mime = {'html': 'text/html', 'js': 'text/javascript', 'css': 'text/css',
                        'woff2': 'font/woff2'}[name.rsplit('.', 1)[1]]
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
                self.send({'error': str(exc)}, 400)

        def do_POST(self):
            try:
                origin = self.headers.get('Origin')
                if origin and origin != f'http://127.0.0.1:{self.server.server_port}':
                    raise ValueError('Local origin required')
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 10000:
                    raise ValueError('Request body must be between 1 and 10000 bytes')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError('JSON object required')
                if self.path == '/api/start':
                    template = {'episode_id': body['episode_id'], 'diagnostic': bool(body.get('diagnostic'))}
                    episode = episode_for(template)
                    state = start(episode, cfg)
                    state['diagnostic'] = template['diagnostic']
                    session_id = store.create(state)
                else:
                    session_id = body['session']

                    def transition(state):
                        episode = episode_for(state)
                        options = {'request_id': body.get('request_id'),
                                   'expected_revision': body.get('expected_revision')}
                        if self.path == '/api/reveal':
                            reveal(episode, state, body['sample_id'], cfg, **options)
                        elif self.path in ('/api/finalize', '/api/abstain'):
                            finalize(episode, state, cfg, abstain=self.path == '/api/abstain', **options)
                        else:
                            raise ValueError('Unknown operation')

                    state = store.update(session_id, transition)
                    episode = episode_for(state)
                self.send(present(session_id, episode, state))
            except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
                self.send({'error': str(exc)}, 400)

    return HTTPServer(('127.0.0.1', port), Handler)


def serve(cfg, port):
    with create_server(cfg, port) as server:
        server.serve_forever()
