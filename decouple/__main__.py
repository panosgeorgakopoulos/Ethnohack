import argparse
import json
import sys
from pathlib import Path
from .engine import start, visible, reveal, finalize, run, export, save
from .policies import recommend
from .ingest import prepare, digest
from .evaluate import evaluate


def run_demo(cfg, episode_id=None):
    es = json.loads((Path(cfg['data_dir']) / 'episodes.json').read_text())
    e = next((ep for ep in es if ep['id'] == episode_id), None) if episode_id else es[0]
    c_a, c_b = e['candidates']
    print("=" * 70)
    print("  DECOUPLE: Three Assays, One Isolation (Live Terminal Demo)")
    print("=" * 70)
    print(f"Episode: {e['id']}")
    print(f"Target : {cfg['target']} (ChEMBL ID: {cfg['target_chembl_id']})")
    print(f"Paper  : {c_a['activity_records'][0].get('document_chembl_id', 'N/A')}")
    print(f"Candidate A: {c_a['name']} ({c_a['id']})")
    print(f"Candidate B: {c_b['name']} ({c_b['id']})")
    print(f"Shared Botanical Species: {e['provenance']['shared_species']} (Jaccard: {e['provenance']['jaccard']:.2f})")
    print("-" * 70)
    print("Initial State (1 Starting Assay Visible):")
    state = start(e, cfg)
    v = visible(e, state, cfg)
    print(f"  P(A only) = {v['posterior'][0]:.1%} | P(B only) = {v['posterior'][1]:.1%} | P(both) = {v['posterior'][2]:.1%} | P(neither) = {v['posterior'][3]:.1%}")
    print("  Status: Starting assay cannot separate A and B (confounded co-occurrence).")
    print("-" * 70)
    print("Beginning 3-Assay Active Deconvolution Budget:")
    for step in range(cfg['budget']):
        rec_dec = recommend(visible(e, state, cfg), 'decouple', cfg)
        rec_str = recommend(visible(e, state, cfg), 'strongest-first', cfg)
        sample_dec = next(s for s in e['samples'] if s['id'] == rec_dec['sample_id'])
        sample_str = next(s for s in e['samples'] if s['id'] == rec_str['sample_id'])
        print(f"\n[Assay Reveal {step + 1} / 3]")
        print(f"  * Greedy (strongest-first) would pick: {sample_str['name']} (predicted activity: {rec_str['score']:.2f})")
        print(f"  * DECOUPLE policy selects            : {sample_dec['name']} (utility gain: {rec_dec['score']:.3f})")
        print(f"    -> Profile: [A: {sample_dec['x'][0]:.2f}, B: {sample_dec['x'][1]:.2f}] (Diagnostic contrast!)")
        reveal(e, state, rec_dec['sample_id'], cfg, policy='decouple')
        v = visible(e, state, cfg)
        print(f"    -> Revealed Response: {state['revealed'][rec_dec['sample_id']]:.3f}")
        print(f"    -> Updated Belief: P(A) = {v['posterior'][0]:.1%} | P(B) = {v['posterior'][1]:.1%} | P(both) = {v['posterior'][2]:.1%}")
    finalize(e, state, cfg)
    print("\n" + "=" * 70)
    print("FINAL DECISION:")
    dec = state['decision']
    print(f"  Decision   : {dec['kind'].upper()}")
    if dec['candidate']:
        winner = c_a['name'] if dec['candidate'] == 'A' else c_b['name']
        print(f"  Nomination : Candidate {dec['candidate']} -> {winner}")
        print(f"  Confidence : {dec['probability']:.4%}")
    print(f"  Explanation: {dec['explanation']}")
    print("=" * 70)


def main():
    parser=argparse.ArgumentParser(prog='python -m decouple')
    parser.add_argument('command',choices=['prepare','audit','replay','evaluate','serve','demo'])
    parser.add_argument('--config',required=True)
    parser.add_argument('--policy',default='decouple')
    parser.add_argument('--episode',default=None)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    try:
        cfg=json.loads(Path(args.config).read_text())
        if cfg['noise_sd']<=0 or cfg['budget']!=3 or len(cfg['prior'])!=4 or abs(sum(cfg['prior'])-1)>1e-8 or min(cfg['prior'])<=0:
            raise ValueError('Invalid response model or budget configuration')
        if args.command=='demo':
            run_demo(cfg,args.episode);return
        elif args.command=='prepare': result=prepare(cfg)
        elif args.command=='audit':
            result=json.loads((Path(cfg['data_dir'])/'audit.json').read_text())
            manifest=json.loads((Path(cfg['data_dir'])/'manifest.json').read_text())
            result['source_hashes_verified']=all(Path(s['file']).exists() and digest(s['file'])==s['sha256'] for s in manifest['sources'])
            if not result['source_hashes_verified']:raise ValueError('Source snapshot missing or changed; run prepare or restore frozen data')
        elif args.command=='evaluate':
            r=evaluate(cfg);result={k:v for k,v in r.items() if k!='rows'}
        elif args.command=='replay':
            es=json.loads((Path(cfg['data_dir'])/'episodes.json').read_text())
            e=next((e for e in es if e['id']==args.episode), None) if args.episode else es[0]
            if e is None:raise ValueError('Unknown episode')
            state=run(e,args.policy,cfg)
            save('results/replay.json',export(e,state,cfg))
            result={'episode':e['id'],'decision':state['decision'],'trace_file':'results/replay.json'}
        else:
            from .server import serve
            print(json.dumps({'ok':True,'url':f'http://127.0.0.1:{args.port}'}),flush=True)
            serve(cfg,args.port);return
        print(json.dumps({'ok':True,'result':result},indent=2,allow_nan=False))
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr)
        sys.exit(1)

if __name__=='__main__':main()
