# Video production

Two narrated videos, both rendered with [Manim](https://www.manim.community/) and voiced with ElevenLabs:

| Video | Source | Voice | Output |
|---|---|---|---|
| Explainer (~6 min) | `manim/explainer.py` (E1–E7) | George | `output/DECOUPLE_Explainer*.mp4` |
| Product demo (~3.5 min) | `manim/demo.py` (D1–D6) | Alice | `output/DECOUPLE_Product_Demo*.mp4` |

Visual system follows the app (`decouple/static/style.css`): Geist, black & white, one accent (`#1d5fbf`).

## Accuracy

- Narration lives in `narration/*.json` and is checked against `FINDINGS.md` (including Part 5, "Must NOT be claimed").
- The demo does not record the browser. It redraws the workbench from states captured from the real engine
  (`manim_demo/capture_episodes.py` → `manim_demo/episodes.json`), so every number on screen is engine output.

## Rebuild

```sh
# 0. (only if the engine or data changed) recapture episode states
.venv/bin/python -m decouple serve --config config/enpkg.json --port 8089 &
python3 video_production/manim_demo/capture_episodes.py --port=8089

# 1. narration (needs ELEVENLABS_API_KEY in env or .env; cached by text hash)
cd video_production && python3 tts_timed.py all

# 2. render all 13 scenes at 1080p30 (parallel)
./render_all.sh

# 3. assemble: concat, ducked ambient bed, SRT, soft-sub and burned-caption versions
python3 build_videos.py all
```

Edit a narration line → rerun steps 1–3; scenes sync to the new timings automatically
(animations wait on beat keys via `NarratedMixin.at()` / `at_word()` in `manim/common.py`).

`qa_sheet.py <video> <scene_id> <mp4>` writes a contact sheet (one frame per beat) to `build/qa/`.
`build/` is scratch output and can be deleted.

## Unified submission pitch (8 Nov revision)

Use **`output/DECOUPLE_Pitch_captioned.mp4`** for a pitch with always-visible captions,
or `output/DECOUPLE_Pitch.mp4` with toggleable English subtitles. Both are 1920×1080.
Runtime: **8:14.30**. The original two videos remain unchanged.

The edit follows problem → method → guided demonstration → results → traditional-knowledge
context → impact and next experiments. It removes the duplicate worked example and the
rapid tour of additional verdicts. The guided demo now explains each of the three reveals
separately, with four persistent step labels and a narrated transition. It explicitly calls
itself a reconstruction of captured engine states, using archived assay outcomes.

The chapter header and caption strip sit outside the scene area. Transitions fade through
the app's light background. George narrates the original research sections; Alice narrates
the revised walkthrough, transition and closing. The project-generated ambient pad runs
continuously and ducks under speech.

Rebuild from the existing original explainer scene masters:

```sh
# Requires the configured ElevenLabs key only for uncached narration.
.venv/bin/python video_production/tts_timed.py demo_steps
.venv/bin/python video_production/tts_timed.py pitch
.venv/bin/python video_production/render_pitch.py
.venv/bin/python video_production/build_pitch.py
```

If original explainer masters are missing, run `render_all.sh` first. The new edit uses
E1, E2, E4, E5 and the measured-data portion of E6. The historical legal-clearance wording
at the end of E6 is excluded. New scenes live in `manim/step_demo.py` and `manim/pitch.py`.
Narration sources are `narration/demo_steps.json` and `narration/pitch.json`.

`DECOUPLE_Pitch.srt` contains captions, `DECOUPLE_Pitch_chapters.txt` contains timestamps,
and `DECOUPLE_Pitch_manifest.json` records scene inputs, durations and output hashes.
The explanatory and demo models remain research hypotheses, not validated biology.
