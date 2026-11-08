"""ElevenLabs narration with character timestamps.

For every scene in narration/<video>.json this writes
  tts/<video>/<scene>.mp3          raw ElevenLabs audio
  tts/<video>/<scene>.wav          mastered narration (what Manim plays)
  tts/<video>/<scene>.timing.json  beat start/end times + word timings

Scenes are cached by a hash of (voice, model, settings, text), so re-running only
re-synthesises scenes whose text changed.

Usage: python tts_timed.py explainer|demo|all [--force]
"""
import base64
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from elevenlabs_tts import load_api_key

HERE = Path(__file__).parent
MODEL = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True}
LEAD_IN = 0.35  # seconds of silence before speech so the scene can open first
# gentle mastering: rumble cut, light compression, loudness to -16 LUFS
MASTER = "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=15:release=200,loudnorm=I=-16:TP=-1.5:LRA=11"


def synth(text, voice_id, key):
    body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": SETTINGS}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.loads(r.read())
    return base64.b64decode(j["audio_base64"]), j["alignment"]


def words_from_alignment(al):
    words, cur, start = [], "", None
    for ch, t0, t1 in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append({"w": cur, "start": start, "end": prev_end})
            cur, start = "", None
        else:
            if not cur:
                start = t0
            cur += ch
            prev_end = t1
    if cur:
        words.append({"w": cur, "start": start, "end": prev_end})
    return words


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def build_scene(scene, voice_id, key, out_dir, force=False):
    text = " ".join(b["text"] for b in scene["beats"])
    digest = hashlib.sha256(json.dumps([voice_id, MODEL, SETTINGS, LEAD_IN, text]).encode()).hexdigest()[:16]
    timing_path = out_dir / f"{scene['id']}.timing.json"
    wav = out_dir / f"{scene['id']}.wav"
    if not force and timing_path.exists() and wav.exists():
        if json.loads(timing_path.read_text()).get("hash") == digest:
            print(f"  cached  {scene['id']}")
            return
    print(f"  synth   {scene['id']} ({len(text)} chars)")
    audio, al = synth(text, voice_id, key)
    mp3 = out_dir / f"{scene['id']}.mp3"
    mp3.write_bytes(audio)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af",
                    f"adelay={int(LEAD_IN * 1000)}:all=1,{MASTER}", "-ar", "48000", "-ac", "2", str(wav)], check=True)

    # beat offsets: beats were joined with single spaces, so char offsets are exact
    starts = al["character_start_times_seconds"]
    ends = al["character_end_times_seconds"]
    beats, pos = [], 0
    for b in scene["beats"]:
        i0, i1 = pos, pos + len(b["text"]) - 1
        beats.append({"key": b["key"], "text": b["text"],
                      "start": round(starts[i0] + LEAD_IN, 3), "end": round(ends[i1] + LEAD_IN, 3)})
        pos += len(b["text"]) + 1
    words = [{**w, "start": round(w["start"] + LEAD_IN, 3), "end": round(w["end"] + LEAD_IN, 3)}
             for w in words_from_alignment(al)]
    timing_path.write_text(json.dumps({"hash": digest, "id": scene["id"], "title": scene["title"],
                                       "duration": round(duration(wav), 3), "beats": beats, "words": words}, indent=1))


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    force = "--force" in sys.argv
    key = load_api_key()
    if not key:
        sys.exit("ELEVENLABS_API_KEY not found (env or .env)")
    for video in (["explainer", "demo"] if target == "all" else [target]):
        spec = json.loads((HERE / "narration" / f"{video}.json").read_text())
        out_dir = HERE / "tts" / video
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{video}] voice {spec['voice_name']}")
        for scene in spec["scenes"]:
            build_scene(scene, spec["voice_id"], key, out_dir, force)


if __name__ == "__main__":
    main()
