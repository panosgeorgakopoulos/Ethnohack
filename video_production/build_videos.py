"""Assemble the rendered Manim scenes into the two final videos.

Pipeline (run after tts_timed.py and render_all.sh):
  1. concatenate each video's 1080p30 scenes (narration is already muxed by Manim)
  2. mix a quiet ambient pad, side-chain ducked under the narration
  3. build SRT captions from the ElevenLabs word timings
  4. write  output/<name>.mp4            (soft, toggleable subtitles)
            output/<name>_captioned.mp4  (captions burned in, for muted playback)
            output/<name>.srt

Usage: python build_videos.py [explainer|demo|all] [--no-music]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
OUT = HERE / "output"
FONT = HERE / "manim" / "fonts" / "Geist-Medium.ttf"

VIDEOS = {
    "explainer": {"name": "DECOUPLE_Explainer", "module": "explainer",
                  "scenes": [("E1Problem", "e1_problem"), ("E2Method", "e2_method"), ("E3Example", "e3_example"),
                             ("E4Selectivity", "e4_selectivity"), ("E5Benchmark", "e5_benchmark"),
                             ("E6Ethno", "e6_ethno"), ("E7Close", "e7_close")]},
    "demo": {"name": "DECOUPLE_Product_Demo", "module": "demo",
             "scenes": [("D1Launch", "d1_launch"), ("D2Recommend", "d2_recommend"), ("D3Reveal", "d3_reveal"),
                        ("D4Finalize", "d4_finalize"), ("D5Verdicts", "d5_verdicts"), ("D6Benchmark", "d6_benchmark")]},
}


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cues_for(words, offset):
    """Group words into readable caption cues (<= ~46 chars, break on punctuation/pauses)."""
    cues, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["start"] - w["end"]) if nxt else 9
        punct = re.search(r"[.?!;:]$", w["w"]) or (re.search(r",$", w["w"]) and len(text) > 24)
        too_long = nxt and len(text) + 1 + len(nxt["w"]) > 46
        if punct or too_long or gap > 0.45 or not nxt:
            cues.append([cur[0]["start"] + offset, w["end"] + offset + 0.12, text])
            cur = []
    for a, b in zip(cues, cues[1:]):
        a[1] = min(a[1], b[0] - 0.02)
    return cues


def caption_png(text, path, W=1920, H=1080):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if text:
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype(str(FONT), 38)
        l, t, r, b = d.textbbox((0, 0), text, font=f)
        tw, th = r - l, b - t
        px, py = 26, 16
        x0, y1 = (W - tw) // 2 - px, H - 70
        y0 = y1 - th - 2 * py
        d.rounded_rectangle((x0, y0, x0 + tw + 2 * px, y1), radius=10, fill=(20, 20, 20, 225))
        d.text((x0 + px - l, y0 + py - t), text, font=f, fill=(255, 255, 255, 255))
    img.save(path)


def ambient(total, path):
    sys.path.insert(0, str(HERE))
    cwd = os.getcwd()
    os.chdir(HERE.parent)                 # make_ambient writes to a workspace-relative path
    try:
        from make_ambient import create_ambient_track
        create_ambient_track(total + 2)
    finally:
        os.chdir(cwd)
    (HERE / "audio" / "ambient_track.wav").replace(path)


def build(key, music=True):
    v = VIDEOS[key]
    work = BUILD / f"assemble_{key}"
    work.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)

    clips, offset, cues = [], 0.0, []
    for scene, sid in v["scenes"]:
        mp4 = BUILD / f"hq_{scene}" / "videos" / v["module"] / "1080p30" / f"{scene}.mp4"
        if not mp4.exists():
            sys.exit(f"missing render: {mp4} (run render_all.sh)")
        timing = json.loads((HERE / "tts" / key / f"{sid}.timing.json").read_text())
        cues += cues_for(timing["words"], offset)
        # pad audio to the exact video length so concatenation can never drift the narration
        vdur = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                                     "-of", "csv=p=0", str(mp4)], capture_output=True, text=True, check=True).stdout)
        padded = work / f"{scene}.mp4"
        run(["ffmpeg", "-y", "-i", mp4, "-af", f"apad=whole_dur={vdur:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-ar", "48000", "-t", f"{vdur:.3f}", padded])
        clips.append(padded)
        offset += vdur
    print(f"[{key}] {len(clips)} scenes, {offset:.1f}s, {len(cues)} caption cues")

    lst = work / "scenes.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    raw = work / "raw.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw])

    mixed = work / "mixed.mp4"
    if music:
        amb = work / "ambient.wav"
        ambient(offset, amb)
        run(["ffmpeg", "-y", "-i", raw, "-i", amb, "-filter_complex",
             "[0:a]asplit=2[nar][key];[1:a]volume=0.55[m];"
             "[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[duck];"
             "[nar][duck]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", mixed])
    else:
        run(["ffmpeg", "-y", "-i", raw, "-c", "copy", mixed])

    srt = OUT / f"{v['name']}.srt"
    srt.write_text("".join(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues)))

    final = OUT / f"{v['name']}.mp4"
    run(["ffmpeg", "-y", "-i", mixed, "-i", srt, "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=eng", "-movflags", "+faststart", final])

    # burned captions: one transparent PNG per cue (blank between cues), fed as a single overlay stream
    capdir = work / "captions"
    capdir.mkdir(exist_ok=True)
    blank = capdir / "blank.png"
    caption_png("", blank)
    entries, t = [], 0.0
    for i, (a, b, text) in enumerate(cues):
        if a > t + 0.01:
            entries.append((blank, a - t))
        p = capdir / f"c{i:04d}.png"
        caption_png(text, p)
        entries.append((p, b - a))
        t = b
    entries.append((blank, max(0.5, offset - t)))
    clist = work / "captions.txt"
    clist.write_text("".join(f"file '{p}'\nduration {d:.3f}\n" for p, d in entries) + f"file '{blank}'\n")
    capd = OUT / f"{v['name']}_captioned.mp4"
    run(["ffmpeg", "-y", "-i", mixed, "-f", "concat", "-safe", "0", "-i", clist, "-filter_complex",
         "[1:v]fps=30,format=rgba[c];[0:v][c]overlay=0:0:shortest=1:format=auto[v]", "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy",
         "-movflags", "+faststart", capd])
    for f in (final, capd, srt):
        print(f"  {f.relative_to(HERE)}  ({f.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    for k in (VIDEOS if target == "all" else [target]):
        build(k, music="--no-music" not in sys.argv)
