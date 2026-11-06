"""Descriptive paired simulation evaluation; biological inference is unavailable."""
import copy
import json
from pathlib import Path
import numpy as np
from .engine import run, visible, save
from .model import HYPOTHESES
from .policies import POLICIES
from .ingest import digest


def summary(rows):
    nom = [r for r in rows if r['nominate']]
    single = [r for r in rows if r['truth'] in ('A','B')]
    reached = [r['first_correct_step'] for r in single if r['first_correct_step'] is not None]
    return {'correct_nomination_rate': sum(r['correct_nomination'] for r in rows)/len(rows),
            'single_driver_recovery': sum(r['correct_nomination'] for r in single)/len(single) if single else None,
            'abstention_rate': 1-len(nom)/len(rows),
            'precision_when_nominating': sum(r['correct_nomination'] for r in nom)/len(nom) if nom else None,
            'hypothesis_accuracy': sum(r['predicted_hypothesis']==r['truth'] for r in rows)/len(rows),
            'mean_assays_to_correct_threshold_among_recovered': float(np.mean(reached)) if reached else None,
            'unrecovered_single_driver_rate': 1-len(reached)/len(single) if single else None}


def evaluate(cfg):
    path = Path(cfg['data_dir'])/'episodes.json'
    episodes = json.loads(path.read_text())
    rows = []
    for episode in episodes:
        for policy in POLICIES:
            state = run(episode, policy, cfg)
            v = visible(episode, state, cfg)
            truth = episode['hidden']['truth']
            first = None
            if truth in ('A','B'):
                idx = HYPOTHESES.index(truth)
                for event in state['trace']:
                    if event['posterior'][idx] >= cfg['nomination_threshold']:
                        first = event['step']; break
            rows.append({'episode_id': episode['id'], 'pair_id': episode['pair_id'], 'policy': policy, 'truth': truth,
                'nominate': state['decision']['kind']=='nominate', 'correct_nomination': state['decision']['candidate']==truth,
                'predicted_hypothesis': HYPOTHESES[int(np.argmax(v['posterior']))], 'first_correct_step': first,
                'decision': state['decision'], 'trace': state['trace']})
    pair_ids = sorted({r['pair_id'] for r in rows})
    by_policy = {p: [r for r in rows if r['policy']==p] for p in POLICIES}
    estimates = {p: summary(rs) for p,rs in by_policy.items()}
    # Noise replicates and pairs sharing a source do not provide independent
    # biological validation. Report diagnostic estimates without inferential CIs.
    document_ids = sorted({
        record['document_chembl_id']
        for episode in episodes for candidate in episode['candidates']
        for record in candidate['activity_records']
    })
    table = {
        policy: {name: {'estimate': value, 'ci95': None} for name, value in values.items()}
        for policy, values in estimates.items()
    }
    # A separately labelled diagnostic: withhold every contrast specimen.
    diagnostic = []
    for e in episodes:
        co = [s for s in e['samples'] if s['x'][0]==s['x'][1]]
        if len(co) < cfg['budget']+1:continue
        d=copy.deepcopy(e); d['samples']=co
        diagnostic.append(run(d,'decouple',cfg)['decision']['kind']=='abstain')
    diagnostic_pair_count=len({e['pair_id'] for e in episodes if sum(s['x'][0]==s['x'][1] for s in e['samples'])>=cfg['budget']+1})
    result = {'schema_version':2,'tier':'Simulation diagnostic','config':cfg,'episodes_sha256':digest(path),
        'manifest_sha256':digest(Path(cfg['data_dir'])/'manifest.json'), 'episodes':len(episodes),'unique_pairs':len(pair_ids),
        'unique_source_documents': len(document_ids),
        'source_documents': document_ids,
        'uncertainty': 'Descriptive simulation results only. Confidence intervals are withheld because noise replicates and shared-source chemical pairs do not provide independent biological validation.',
        'measured_extract_replay': False,
        'acquisition_objective': 'Expected gain in threshold-aware single-driver nomination utility; unitless.',
        'policies':table,'paired_difference_vs_strongest':{'metric':'correct_nomination_rate','estimate':estimates['decouple']['correct_nomination_rate']-estimates['strongest-first']['correct_nomination_rate'],
                'ci95':None},
        'indistinguishable_diagnostic':{'label':'Contrast-withheld reconstructed diagnostic, excluded from main results',
            'episodes':len(diagnostic),'unique_pairs':diagnostic_pair_count,'abstentions':sum(diagnostic),
            'rate':sum(diagnostic)/len(diagnostic) if diagnostic else None,
            'ci95':None,
            'note':'Structural rule under simulated profiles; no biological safety estimate.'},'rows':rows}
    save(cfg['results_file'], result)
    return result
