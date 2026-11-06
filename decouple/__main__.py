import argparse
import json
import sys
from pathlib import Path
from .engine import run, export, save
from .ingest import prepare, digest
from .evaluate import evaluate


def main():
    parser=argparse.ArgumentParser(prog='python -m decouple')
    parser.add_argument('command',choices=['prepare','audit','replay','evaluate','serve'])
    parser.add_argument('--config',required=True)
    parser.add_argument('--policy',default='decouple')
    parser.add_argument('--episode',default=None)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    try:
        cfg=json.loads(Path(args.config).read_text())
        if cfg['noise_sd']<=0 or cfg['budget']!=3 or len(cfg['prior'])!=4 or abs(sum(cfg['prior'])-1)>1e-8 or min(cfg['prior'])<=0:
            raise ValueError('Invalid response model or budget configuration')
        if args.command=='prepare': result=prepare(cfg)
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
