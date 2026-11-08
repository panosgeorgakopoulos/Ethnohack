"""Shared Manim helpers: narration sync, type scale, palette."""
import json
from pathlib import Path

import manimpango
from manim import *

VP = Path(__file__).resolve().parent.parent          # video_production/
for _f in sorted((Path(__file__).parent / "fonts").glob("*.ttf")):
    manimpango.register_font(str(_f))

# The app's type: Geist, weights 400/500 (decouple/static/style.css)
FONT = "Geist"
DISPLAY = "Geist"
MONO = "Geist Mono"

# The app's palette: black & white plus one accent (style.css :root)
GROUND = "#f2f4f7"
SURFACE = "#ffffff"
INK = "#141414"
MUTED = "#60656b"
FAINT = "#8f959c"
LINE = "#e2e4e7"
BORDER = "#bfc4ca"
SLATE = "#727d8e"      # candidate-B track in the app
PALE = "#c9cdd3"
ACCENT = "#1d5fbf"     # the single accent
ON = "#ffffff"

# CSS px -> Manim font_size at 1080p (Inter cap height = 0.727 em; 1 unit = 135 px)
PX_FS = 0.533


def css(px):
    return px * PX_FS


SCALE = 1.0   # per-video type scale (explainer sets this > 1 for legibility)


def _w(weight):
    # the app tops out at 500; keep "bold" restrained at 600
    return SEMIBOLD if weight == BOLD else weight


def txt(s, px=24, color=INK, weight=NORMAL, font=FONT, **kw):
    return Text(s, font=font, font_size=css(px) * SCALE, color=color, weight=_w(weight), **kw)


def mono(s, px=20, color=INK, weight=NORMAL, **kw):
    return Text(s, font=MONO, font_size=css(px) * SCALE, color=color, weight=_w(weight), **kw)


class NarratedMixin:
    """Plays tts/<VIDEO>/<SID>.wav and offers beat-synchronised waits."""
    VIDEO = "explainer"
    SID = ""
    TAIL = 0.8   # seconds held after narration ends

    def start_narration(self):
        d = VP / "tts" / self.VIDEO
        self.timing = json.loads((d / f"{self.SID}.timing.json").read_text())
        self.beats = {b["key"]: b for b in self.timing["beats"]}
        self.add_sound(str(d / f"{self.SID}.wav"))

    @property
    def t(self):
        return self.renderer.time

    def until(self, t):
        dt = t - self.renderer.time
        if dt > 1 / 30:
            self.wait(dt)

    def at(self, key, offset=0.0):
        """Wait until beat `key` starts (+offset seconds)."""
        self.until(self.beats[key]["start"] + offset)

    def left(self, key, end_key=None, reserve=0.0):
        """Seconds from now until beat `end_key` (or end of `key`), minus reserve."""
        end = self.beats[end_key]["start"] if end_key else self.beats[key]["end"]
        return max(0.3, end - self.renderer.time - reserve)

    def word_time(self, word, after_key=None):
        """Start time of the first spoken word containing `word` (after a beat)."""
        t0 = self.beats[after_key]["start"] if after_key else 0
        for w in self.timing["words"]:
            if w["start"] >= t0 - 0.01 and word.lower() in w["w"].lower():
                return w["start"]
        raise KeyError(word)

    def at_word(self, word, after_key=None, offset=0.0):
        self.until(self.word_time(word, after_key) + offset)

    def finish(self, fade=True):
        end = self.timing["duration"] + self.TAIL
        if fade:
            self.until(end - 0.6)
            mobs = [m for m in self.mobjects]
            if mobs:
                self.play(*[FadeOut(m) for m in mobs], run_time=0.5)
        self.until(end)
