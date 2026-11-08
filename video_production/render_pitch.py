"""Render only the revised guided-demo and pitch scenes, with bounded concurrency."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
TASKS=[('step_demo',s) for s in ['D1Launch','D2Recommend','D3Reveal','D4Finalize']]+[('pitch',s) for s in ['PTransition','PClose']]
def render(task):
    module,scene=task
    dest=ROOT/'build'/f'pitch_{scene}'
    log=ROOT/'build'/f'pitch_{scene}.log'
    with log.open('w') as f:
        p=subprocess.run([str(ROOT.parent/'.venv/bin/manim'),'-qh','--fps','30','--media_dir',str(dest),module+'.py',scene],cwd=ROOT/'manim',stdout=f,stderr=subprocess.STDOUT)
    print(scene, 'OK' if p.returncode==0 else 'FAIL '+str(log),flush=True)
    return p.returncode
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        codes=list(pool.map(render,TASKS))
    raise SystemExit(any(codes))
