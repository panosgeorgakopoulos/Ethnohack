"""Assemble one coherent, caption-safe submission pitch from Manim scene masters.

Preserves original exports. Outputs soft-captioned MP4, burned-caption MP4,
SRT, chapter timestamps and a reproducibility manifest. No paid API calls.
"""
from pathlib import Path
import json, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from build_videos import cues_for, ts, ambient
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build'/'unified_pitch'
OUT=ROOT/'output'
BUILD.mkdir(parents=True,exist_ok=True)
FONT=ROOT/'manim/fonts/Geist-Medium.ttf'
# module, class, narration directory, timing ID, chapter label
SCENES=[
('explainer','E1Problem','explainer','e1_problem','THE PROBLEM'),
('explainer','E2Method','explainer','e2_method','THE METHOD'),
('pitch','PTransition','pitch','p_transition','GUIDED DEMONSTRATION'),
('step_demo','D1Launch','demo_steps','d1_launch','STEP 01  /  CHOOSE THE PAIR'),
('step_demo','D2Recommend','demo_steps','d2_recommend','STEP 02  /  INSPECT THE CONTRAST'),
('step_demo','D3Reveal','demo_steps','d3_reveal','STEP 03  /  REVEAL EACH ASSAY'),
('step_demo','D4Finalize','demo_steps','d4_finalize','STEP 04  /  REVIEW, COMPARE, EXPORT'),
('explainer','E4Selectivity','explainer','e4_selectivity','RESULTS  /  SELECTIVITY'),
('explainer','E5Benchmark','explainer','e5_benchmark','RESULTS  /  SELECTION'),
('explainer','E6Ethno','explainer','e6_ethno','DATA  /  TRADITIONAL-KNOWLEDGE CONTEXT'),
('pitch','PClose','pitch','p_close','IMPACT  /  THE NEXT EXPERIMENT'),
]
def run(args):
    p=subprocess.run([str(a) for a in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:raise RuntimeError(p.stderr.decode()[-5000:])
def dur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration','-of','csv=p=0',str(p)]))
def text_png(path,text,header=False):
    im=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(im)
    f=ImageFont.truetype(str(FONT),30 if header else 40)
    if header:
        d.text((64,22),text,font=f,fill='#1d5fbf')
        f2=ImageFont.truetype(str(FONT),25)
        d.text((1690,25),'DECOUPLE',font=f2,fill='#141414')
        d.line((64,66,1856,66),fill='#e2e4e7',width=1)
    elif text:
        bb=d.textbbox((0,0),text,font=f);w=bb[2]-bb[0]
        d.text(((1920-w)/2,990),text,font=f,fill='#141414')
    im.save(path)

def prepare(item):
    i,(module,cls,video,sid,label)=item
    prefix='hq_' if module=='explainer' else 'pitch_'
    source=ROOT/'build'/f'{prefix}{cls}'/'videos'/module/'1080p30'/f'{cls}.mp4'
    timing=json.loads((ROOT/'tts'/video/f'{sid}.timing.json').read_text())
    length=dur(source)
    # Retain measured organ contrast, ending before the historical legal-clearance wording.
    if sid=='e6_ethno':length=next(b['start'] for b in timing['beats'] if b['key']=='ethics')-.1
    header=BUILD/f'{i:02d}_header.png';text_png(header,label,True)
    target=BUILD/f'{i:02d}_{cls}.mp4'
    fc=f'[0:v]trim=duration={length},setpts=PTS-STARTPTS,scale=1536:864,pad=1920:1080:192:80:color=0xf2f4f7,setsar=1,fade=t=in:st=0:d=0.25:color=0xf2f4f7,fade=t=out:st={length-.25}:d=0.25:color=0xf2f4f7[v];[v][1:v]overlay=0:0:format=auto[out]'
    run(['ffmpeg','-y','-i',source,'-i',header,'-filter_complex',fc,'-map','[out]','-map','0:a:0','-af',f'apad,atrim=duration={length},asetpts=PTS-STARTPTS','-t',f'{length:.6f}','-r','30','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000',target])
    actual=dur(target)
    cues=[(a,min(b,actual),t) for a,b,t in cues_for(timing['words'],0) if a<actual and b<=length+.2]
    print(f'Prepared {cls}: {actual:.2f}s',flush=True)
    return dict(path=str(target),source=str(source),duration=actual,cues=cues,label=label)

def main():
    with ThreadPoolExecutor(max_workers=2) as pool:clips=list(pool.map(prepare,enumerate(SCENES)))
    offset=0;cues=[];chapters=[]
    for c in clips:
        chapters.append({'start':round(offset,3),'title':c['label']})
        cues.extend((a+offset,b+offset,t) for a,b,t in c['cues']);offset+=c['duration']
    if offset>600:raise RuntimeError(f'Pitch exceeds 10 minutes: {offset}')
    lst=BUILD/'concat.txt';lst.write_text(''.join(f"file '{c['path']}'\n" for c in clips))
    raw=BUILD/'joined.mp4';run(['ffmpeg','-y','-f','concat','-safe','0','-i',lst,'-c','copy',raw])
    # Use project-generated pad with continuous ducking across the whole pitch.
    amb=BUILD/'ambient.wav';ambient(offset,amb)
    mixed=BUILD/'mixed.mp4'
    run(['ffmpeg','-y','-i',raw,'-i',amb,'-filter_complex','[0:a]asplit=2[nar][key];[1:a]volume=0.45[m];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[duck];[nar][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t',str(offset),mixed])
    srt=OUT/'DECOUPLE_Pitch.srt';srt.write_text(''.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n\n' for i,(a,b,t) in enumerate(cues)))
    meta=BUILD/'chapters.ffmetadata';lines=[';FFMETADATA1','title=DECOUPLE — Which molecule did it?']
    for i,c in enumerate(chapters):
        end=chapters[i+1]['start'] if i+1<len(chapters) else offset
        lines+=['[CHAPTER]','TIMEBASE=1/1000',f"START={round(c['start']*1000)}",f'END={round(end*1000)}',f"title={c['title']}"]
    meta.write_text('\n'.join(lines)+'\n')
    plain=OUT/'DECOUPLE_Pitch.mp4'
    run(['ffmpeg','-y','-i',mixed,'-i',srt,'-i',meta,'-map','0:v','-map','0:a','-map','1:0','-map_metadata','2','-map_chapters','2','-c','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-movflags','+faststart',plain])
    capdir=BUILD/'captions';capdir.mkdir(exist_ok=True)
    blank=capdir/'blank.png';text_png(blank,'');entries=[];now=0
    for i,(a,b,t) in enumerate(cues):
        if a>now:entries.append((blank,a-now))
        img=capdir/f'{i:04d}.png';text_png(img,t);entries.append((img,b-a));now=b
    entries.append((blank,max(.1,offset-now)))
    caplist=BUILD/'captions.txt';caplist.write_text(''.join(f"file '{p}'\nduration {d:.6f}\n" for p,d in entries)+f"file '{blank}'\n")
    burned=OUT/'DECOUPLE_Pitch_captioned.mp4'
    run(['ffmpeg','-y','-i',mixed,'-f','concat','-safe','0','-i',caplist,'-i',meta,'-filter_complex','[1:v]fps=30,format=rgba[c];[0:v][c]overlay=0:0:format=auto[v]','-map','[v]','-map','0:a','-map_metadata','2','-map_chapters','2','-t',str(offset),'-c:v','libx264','-preset','fast','-crf','18','-threads','6','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',burned])
    (OUT/'DECOUPLE_Pitch_chapters.txt').write_text('\n'.join(f"{int(c['start'])//60:02d}:{int(c['start'])%60:02d} {c['title']}" for c in chapters)+'\n')
    manifest={'duration_seconds':offset,'chapters':chapters,'scenes':[{k:v for k,v in c.items() if k!='cues'} for c in clips],'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [plain,burned,srt]}}
    for scene in manifest['scenes']:
        for key in ('path', 'source'):
            scene[key] = str(Path(scene[key]).relative_to(ROOT.parent))
    (OUT/'DECOUPLE_Pitch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'FINISHED: {offset:.2f}s',flush=True)
if __name__=='__main__':main()
