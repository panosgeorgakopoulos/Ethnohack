import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

def load_api_key():
    # Check env var
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("XI_API_KEY")
    if key:
        return key.strip()

    # Check local .env
    for env_path in [WORKSPACE / ".env", Path.home() / ".env"]:
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("XI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def get_available_voices(api_key):
    url = "https://api.elevenlabs.io/v1/voices"
    req = urllib.request.Request(url, headers={"xi-api-key": api_key})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("voices", [])
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []

def generate_tts(text, voice_id, api_key, out_path, model_id="eleven_multilingual_v2"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.80,
            "style": 0.15,
            "use_speaker_boost": True
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
    )

    mp3_path = out_path.with_suffix(".mp3")
    with urllib.request.urlopen(req) as resp:
        mp3_path.write_bytes(resp.read())

    # Convert MP3 to enhanced WAV using ffmpeg
    af = "highpass=f=60, lowpass=f=12000, compand=attacks=0.02:decays=0.2:points=-60/-60|-24/-18|0/-4:gain=1.5, volume=1.1"
    subprocess.run([
        "ffmpeg", "-i", str(mp3_path),
        "-af", af,
        "-ar", "44100", "-ac", "2",
        "-y", str(out_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Remove temp mp3
    if mp3_path.exists():
        mp3_path.unlink()

    # Get duration
    res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out_path)
    ], capture_output=True, text=True, check=True)
    dur = float(res.stdout.strip())
    return dur

def main():
    api_key = load_api_key()
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found in environment or .env file.")
        sys.exit(1)

    print("ElevenLabs API key successfully detected.")

    # Check if user requested listing voices
    if "--list-voices" in sys.argv:
        voices = get_available_voices(api_key)
        print(f"\nAvailable voices ({len(voices)}):")
        for v in voices:
            print(f"  - {v['name']} (ID: {v['voice_id']}) · {v.get('category', '')} · {v.get('labels', {})}")
        return

    # Default voice: Rachel (21m00Tcm4TlvDq8ikWAM) or Adam (pNInz6obpgDQGcFmaJgB)
    voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel
    for arg in sys.argv:
        if arg.startswith("--voice="):
            voice_id = arg.split("=", 1)[1]

    print(f"Using Voice ID: {voice_id}")

    # Target: "demo" or "pitch" or "all"
    target = "all"
    for arg in sys.argv:
        if arg.startswith("--target="):
            target = arg.split("=", 1)[1]

    if target in ("demo", "all"):
        print("\n--- Generating Audio for App Demo Walkthrough ---")
        demo_json_path = WORKSPACE / "video_production/demo_audio/parts.json"
        parts = json.loads(demo_json_path.read_text())
        out_dir = WORKSPACE / "video_production/demo_audio"
        out_dir.mkdir(parents=True, exist_ok=True)

        for p in parts:
            pid = p["id"]
            wav_file = out_dir / f"{pid}.wav"
            print(f"Synthesizing [{pid}] '{p['title']}'...")
            dur = generate_tts(p["text"], voice_id, api_key, wav_file)
            p["duration"] = dur
            print(f"  -> Generated: {dur:.2f}s")

        demo_json_path.write_text(json.dumps(parts, indent=2))
        print("Updated parts.json with new durations.")

    if target in ("pitch", "all"):
        print("\n--- Generating Audio for Pitch Video ---")
        pitch_json_path = WORKSPACE / "video_production/audio/scenes.json"
        scenes = json.loads(pitch_json_path.read_text())
        out_dir = WORKSPACE / "video_production/audio"
        out_dir.mkdir(parents=True, exist_ok=True)

        for s in scenes:
            sid = s["id"]
            wav_file = out_dir / f"{sid}.wav"
            print(f"Synthesizing [{sid}] '{s['title']}'...")
            dur = generate_tts(s["text"], voice_id, api_key, wav_file)
            s["duration"] = dur
            print(f"  -> Generated: {dur:.2f}s")

        pitch_json_path.write_text(json.dumps(scenes, indent=2))
        print("Updated scenes.json with new durations.")

    print("\nAll audio tracks successfully synthesized with ElevenLabs!")

if __name__ == '__main__':
    main()
