"""Contact sheet: one frame at the end of each narration beat. python qa_sheet.py <video> <SID> <mp4>"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image
video, sid, mp4 = sys.argv[1:4]
here = Path(__file__).parent
t = json.loads((here / 'tts' / video / f'{sid}.timing.json').read_text())
out = here / 'build' / 'qa'
frames = []
for i, b in enumerate(t['beats']):
    ts = max(0.1, b['end'] - 0.15) if i + 1 == len(t['beats']) else t['beats'][i + 1]['start'] - 0.1
    p = out / f'{sid}_{i}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ts:.2f}', '-i', mp4, '-frames:v', '1', str(p)], check=True)
    frames.append(Image.open(p))
w, h = frames[0].size
cols = 2
rows = (len(frames) + 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows), 'white')
for i, f in enumerate(frames):
    sheet.paste(f, ((i % cols) * w, (i // cols) * h))
sheet.save(out / f'{sid}_sheet.png')
print(out / f'{sid}_sheet.png')
