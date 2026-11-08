"""DECOUPLE product demo — the workbench UI recreated in Manim.

Every value on screen comes from manim_demo/episodes.json, captured from the
live engine by manim_demo/capture_episodes.py. Layout follows
decouple/static/style.css (Geist, 1400px max-width, 8px radii) at 125% zoom.

Render one:  manim -qh demo.py D1Launch
"""
import json

import common
from common import *

common.SCALE = ZOOM = 1.25          # browser zoom: page is laid out in CSS px
U = ZOOM / 135                      # Manim units per CSS px
PAGE_W = 1920 / ZOOM                # 1536 css px
VIEW_H = 1080 / ZOOM                # 864 css px
X0, X1 = 104, 1432                  # main content edges (max-width 1400, padding 36)

DATA = json.loads((VP / "manim_demo" / "episodes.json").read_text())
EPS = DATA["episodes"]
CATALOG = DATA["catalog"]["episodes"]
MAIN = "C383-C5659-r0"
JOINT = "C2843-C9244-r0"
CYTO = "C4183-C7923-r0"


def P(x, y):
    """CSS px page coordinates (origin top-left) -> scene point."""
    return np.array([(x - PAGE_W / 2) * U, (VIEW_H / 2 - y) * U, 0])


def T(s, px, x, y, color=INK, weight=NORMAL, anchor="l", font=FONT, **kw):
    """Single-line text, vertically centred on line-centre y (CSS px)."""
    t = txt(s, px, color, weight, font=font, **kw)
    edge = {"l": LEFT, "r": RIGHT}.get(anchor, ORIGIN)
    return t.move_to(P(x, y), aligned_edge=edge)


def width_px(s, px, weight=NORMAL, font=FONT, **kw):
    return txt(s, px, INK, weight, font=font, **kw).width / U


def wrap(s, px, max_w, weight=NORMAL):
    lines, cur = [], ""
    for w in s.split(" "):
        trial = (cur + " " + w).strip()
        if cur and width_px(trial, px, weight) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def para(s, px, x, y_top, max_w, color=MUTED, lh=1.5, weight=NORMAL):
    """Wrapped paragraph; returns (group, bottom_y)."""
    g = VGroup()
    lines = wrap(s, px, max_w, weight)
    for i, ln in enumerate(lines):
        g.add(T(ln, px, x, y_top + px * lh * (i + 0.5), color, weight))
    return g, y_top + px * lh * len(lines)


def box(x, y, w, h, fill=SURFACE, stroke=LINE, r=8, sw=1.2):
    b = RoundedRectangle(width=w * U, height=h * U, corner_radius=r * U, fill_color=fill, fill_opacity=1,
                         stroke_color=stroke, stroke_width=sw)
    return b.move_to(P(x + w / 2, y + h / 2))


def hline(x, y, w, color=LINE, sw=1.2):
    return Line(P(x, y), P(x + w, y), color=color, stroke_width=sw)


def button(label, x, y, primary=False, disabled=False, px=14, anchor="l", h=38, padx=13):
    w = width_px(label, px, MEDIUM if primary else NORMAL) + 2 * padx + 2
    if anchor == "r":
        x = x - w
    fill = INK if primary else ("#eeeeee" if disabled else SURFACE)
    stroke = INK if primary else BORDER
    col = ON if primary else ("#686868" if disabled else INK)
    b = box(x, y, w, h, fill=fill, stroke=stroke, r=6)
    t = T(label, px, x + w / 2, y + h / 2, col, MEDIUM if primary else NORMAL, anchor="c")
    g = VGroup(b, t)
    g.bounds = (x, y, w, h)
    return g


def pct(v):
    return f"{v * 100:.1f}%"


def logo_mark(size_px=30, color=INK):
    s = size_px / 30 * U
    def pts(seq):
        return [np.array([(x - 15) * s, (15 - y) * s, 0]) for x, y in seq]
    a = VMobject(stroke_color=color, stroke_width=2.4).set_points_as_corners(pts([(3, 7), (13, 7), (18, 23), (27, 23)]))
    b = VMobject(stroke_color=color, stroke_width=2.4).set_points_as_corners(pts([(3, 23), (13, 23), (18, 7), (27, 7)]))
    return VGroup(a, b)


def cursor_mob():
    pts = [(0, 0), (0, -17), (4.2, -13), (7.2, -20), (9.6, -19), (6.8, -12.2), (12, -12.2)]
    poly = Polygon(*[np.array([x * U * 1.15, y * U * 1.15, 0]) for x, y in pts], fill_color=INK, fill_opacity=1,
                   stroke_color=WHITE, stroke_width=1.6)
    return poly


# ======================================================================
class Workbench:
    """Builds the page for one episode state and morphs it to later states."""

    def __init__(self, scene, ep_id, idx=0):
        self.scene = scene
        self.ep_id = ep_id
        self.ep = EPS[ep_id]
        self.idx = idx
        self.s = self.ep["states"][idx]
        self.parts = {}

    # ------------------------------------------------------------ geometry
    LEFT_X, LEFT_W = 104, 439
    RIGHT_X, RIGHT_W = 555, 877
    WS_Y = 304

    def cand_lines(self, i):
        name = self.s["candidates"][i]["name"]
        a, b = name.rsplit(" · ", 1)
        return [a + " ·", b]

    # ------------------------------------------------------------ chrome
    def chrome(self):
        g = VGroup()
        g.add(Rectangle(width=30, height=30, fill_color=GROUND, fill_opacity=1, stroke_width=0).move_to(P(PAGE_W / 2, VIEW_H / 2 + 200)))
        hdr = Rectangle(width=PAGE_W * U + 0.02, height=68 * U, fill_color=SURFACE, fill_opacity=1, stroke_width=0).move_to(P(PAGE_W / 2, 34))
        g.add(hdr, hline(0, 68, PAGE_W))
        lm = logo_mark(30).move_to(P(36 + 15, 34))
        brand = T("DECOUPLE", 14, 78, 34, INK, MEDIUM)
        sub = T("Natural products / T. cruzi", 14, 78 + width_px("DECOUPLE", 14, MEDIUM) + 32, 34, MUTED)
        self.bench_btn = button("Benchmark", PAGE_W - 36, 15, anchor="r")
        g.add(lm, brand, sub, self.bench_btn)
        g.add(T("Which assay breaks the tie?", 28, X0, 106, INK, MEDIUM))
        g.add(T("Reveal up to three assays to distinguish two chemical explanations.", 14, X0, 136, MUTED))
        self.export_btn = button("Export decision trace ↗", X1, 102, anchor="r")
        g.add(self.export_btn)
        # notice
        self.notice = box(X0, 166, X1 - X0, 42, stroke="#d7dce2", r=6)
        tier = T(self.s["tier"], 12, X0 + 16, 187, INK, MEDIUM)
        lim = T(self.s["limitations"][0], 12, X0 + 16 + width_px(self.s["tier"], 12, MEDIUM) + 16, 187, INK)
        g.add(self.notice, tier, lim)
        # toolbar
        g.add(T("Candidate pair", 12, X0, 230, INK))
        self.check = VGroup(box(X0 + 360, 263, 16, 16, r=3, stroke="#767676"),
                            T("Withhold separating specimens", 14, X0 + 384, 271, INK))
        self.start_btn = button("Start new episode", X1, 252, anchor="r")
        g.add(self.check, self.start_btn)
        # section frames
        g.add(box(self.LEFT_X, self.WS_Y, self.LEFT_W, 493))
        g.add(box(self.RIGHT_X, self.WS_Y, self.RIGHT_W, 430))
        g.add(T("Competing explanations", 16, self.LEFT_X + 22, 337, INK, MEDIUM),
              T("Posterior probability", 12, self.LEFT_X + self.LEFT_W - 22, 338, MUTED, anchor="r"))
        g.add(T("Sample profiles", 16, self.RIGHT_X + 22, 337, INK, MEDIUM))
        g.add(T(self.s["limitations"][-1], 12, self.RIGHT_X + 22, 371, MUTED))
        # next + lower frames
        g.add(box(X0, 809, X1 - X0, 98))
        g.add(T("Next experiment", 12, X0 + 22, 830, MUTED))
        lw = (X1 - X0 - 12) / 2
        g.add(box(X0, 919, lw, 166), box(X0 + lw + 12, 919, lw, 166))
        g.add(T("Decision trail", 16, X0 + 22, 945, INK, MEDIUM), T("Saved locally", 12, X0 + lw - 22, 946, MUTED, anchor="r"))
        g.add(T("Same budget, different question", 16, X0 + lw + 34, 945, INK, MEDIUM))
        g.add(T("The comparison uses identical archived outcomes and unlocks after finalization.", 12, X0 + lw + 34, 1066, MUTED))
        g.add(T("DECOUPLE / Research prototype", 12, X0, 1110, MUTED),
              T("Occurrence ≠ abundance. Association ≠ causation.", 12, X1, 1110, MUTED, anchor="r"))
        self.lower_w = lw
        return g

    # ------------------------------------------------------------ dynamic pieces
    def select_box(self):
        s = " / ".join(next(e["names"] for e in CATALOG if e["id"] == self.ep_id))
        while width_px(s, 14) > 290:
            s = s[:-1]
        b = box(X0, 252, 340, 38, stroke=BORDER, r=6)
        t = T(s, 14, X0 + 13, 271, INK)
        chev = VGroup(Line(P(X0 + 316, 268), P(X0 + 321, 274), stroke_width=1.6, color=INK),
                      Line(P(X0 + 321, 274), P(X0 + 326, 268), stroke_width=1.6, color=INK))
        return VGroup(b, t, chev)

    def candidates(self, s):
        g = VGroup()
        self.trackers = getattr(self, "trackers", None) or [ValueTracker(s["posterior"][0]), ValueTracker(s["posterior"][1])]
        y = 360
        x = self.LEFT_X + 22
        w = self.LEFT_W - 44
        for i in range(2):
            letter = VGroup(box(x, y + 12, 24, 24, r=4, stroke=BORDER), T("AB"[i], 12, x + 12, y + 24, INK, anchor="c"))
            l1, l2 = self.cand_lines(i)
            n1 = T(l1, 16, x + 34, y + 12, INK)
            n2 = T(l2, 16, x + 34, y + 36, INK)
            track = Rectangle(width=w * U, height=7 * U, fill_color="#eeeeee", fill_opacity=1, stroke_width=0).move_to(P(x + w / 2, y + 62.5))
            col = ACCENT if i == 0 else SLATE
            vt = self.trackers[i]

            def mk_bar(vt=vt, track=track, col=col):
                ww = max(vt.get_value() * w * U, 0.0005)
                return Rectangle(width=ww, height=7 * U, fill_color=col, fill_opacity=1, stroke_width=0).move_to(track.get_left(), aligned_edge=LEFT)

            def mk_prob(vt=vt, yy=y + 24):
                return T(pct(vt.get_value()), 30, x + w, yy, INK, anchor="r")

            g.add(VGroup(letter, n1, n2, track, always_redraw(mk_bar), always_redraw(mk_prob)))
            y += 80
        return g

    def alternatives(self, s):
        x = self.LEFT_X + 22
        w = self.LEFT_W - 44
        both = VGroup(T("Both", 14, x, 535, INK), T(pct(s["posterior"][2]), 14, x + width_px("Both", 14) + 5, 535, INK, MEDIUM))
        nei_v = T(pct(s["posterior"][3]), 14, x + w, 535, INK, MEDIUM, anchor="r")
        nei = VGroup(T("Neither", 14, nei_v.get_left()[0] / U + PAGE_W / 2 - width_px("Neither", 14) - 5, 535, INK), nei_v)
        line = hline(x, 520, w)
        small, _ = para("The four explanations sum to 100%. Bars show support under the inference model.", 12, x, 556, w)
        return VGroup(line, both, nei, small)

    def verdict(self, s):
        x = self.LEFT_X + 22
        w = self.LEFT_W - 44
        cands = s["candidates"]
        d = s["decision"]
        if d:
            title, text = self.label(d), d["explanation"]
            text = text[0].upper() + text[1:]
        elif s["trace"]:
            best = max(range(4), key=lambda i: s["posterior"][i])
            title = "Leading explanation: " + ["A only", "B only", "both", "neither"][best]
            text = "One response is already visible. Choose a sample profile that distinguishes the explanations. Final nomination requires the configured support threshold."
        else:
            title = "The starting assay cannot separate A and B."
            text = "One response is already visible. Choose a sample profile that distinguishes the explanations. Final nomination requires the configured support threshold."
        tl = wrap(title, 16, w, MEDIUM)
        g = VGroup(hline(x, 600, w))
        y = 612
        for ln in tl:
            g.add(T(ln, 16, x, y + 11, INK, MEDIUM))
            y += 22
        p, _ = para(text, 12, x, y + 4, w)
        g.add(p)
        g.title = title
        return g

    def label(self, d):
        cands = self.s["candidates"]
        nm = lambda k: cands[0]["name"] if k == "A" else cands[1]["name"] if k == "B" else k
        st = d.get("candidates") or ([d["candidate"]] if d.get("candidate") else [])
        k = d["kind"]
        if k == "nominate":
            return f"Nominate {nm(st[0])}"
        if k == "shortlist":
            return "Shortlist: " + " or ".join(nm(c) for c in st)
        if k == "joint":
            return "Both contribute. Do not fractionate."
        if k == "cytotoxic":
            return f"Cytotoxic: do not isolate {nm(st[0])}"
        return "Abstain. Preserve the uncertainty."

    def budget(self, s):
        x = self.LEFT_X + 22
        w = self.LEFT_W - 44
        g = VGroup(T("Assays remaining", 14, x, 756, INK, MEDIUM), T(f"{s['remaining']} / 3", 24, x + w, 756, INK, anchor="r"))
        mw = (w - 12) / 3
        for i in range(3):
            spent = i >= s["remaining"]
            g.add(Rectangle(width=mw * U, height=5 * U, fill_color="#dedede" if spent else INK, fill_opacity=1, stroke_width=0)
                  .move_to(P(x + i * (mw + 6) + mw / 2, 778)))
        return g

    def sample(self, s, sid):
        return next(x for x in s["samples"] if x["id"] == sid)

    def ordered_rows(self, s):
        rec = (s.get("recommendation") or {}).get("sample_id")
        traced = [t["sample_id"] for t in reversed(s["trace"])]
        order = []
        if rec:
            order.append(rec)
        order += [t for t in traced if t not in order]
        order += [x["id"] for x in s["samples"] if x["id"] not in order]
        return order[:6]

    def table(self, s):
        g = VGroup()
        x0 = self.RIGHT_X + 22
        x1 = self.RIGHT_X + self.RIGHT_W - 22
        cols = {"A": x1 - 360, "B": x1 - 290, "P": x1 - 190, "H": x1 - 100}
        hy = 407
        g.add(T("Species", 12, x0, hy, MUTED), T("A", 12, cols["A"], hy, MUTED, anchor="r"), T("B", 12, cols["B"], hy, MUTED, anchor="r"),
              T("Parasite", 12, cols["P"], hy, MUTED, anchor="r"), T("Host tox", 12, cols["H"], hy, MUTED, anchor="r"))
        rec = (s.get("recommendation") or {}).get("sample_id")
        known_ids = set(s["revealed"])
        traced = {t["sample_id"] for t in s["trace"]}
        tox = s.get("revealed_cytotox") or {}
        self.row_y = {}
        y = 426
        for sid in self.ordered_rows(s):
            x = self.sample(s, sid)
            known = sid in known_ids
            sel = sid == rec
            rh = 50
            g.add(hline(x0, y, x1 - x0, "#eeeeee"))
            nx = x0 + (12 if sel else 0)
            if sel:
                g.add(Rectangle(width=3 * U, height=rh * U, fill_color=ACCENT, fill_opacity=1, stroke_width=0).move_to(P(x0 + 1.5, y + rh / 2)))
            g.add(T(x["name"], 14, nx, y + 19, INK, slant=ITALIC))
            subl = "Recommended assay" if sel else ("Assay revealed" if sid in traced else "Starting assay") if known else sid
            g.add(T(subl, 11, nx, y + 36, ACCENT if sel else MUTED, MEDIUM if sel else NORMAL))
            for j, key in enumerate(["A", "B"]):
                v = x["x"][j]
                g.add(T(f"{v:.2f}", 14, cols[key], y + 21, INK, anchor="r"))
                g.add(Rectangle(width=42 * U, height=2 * U, fill_color="#eeeeee", fill_opacity=1, stroke_width=0).move_to(P(cols[key] - 21, y + 34)))
                bw = min(v / 1.5, 1) * 42
                if bw > 0.3:
                    g.add(Rectangle(width=bw * U, height=2 * U, fill_color="#748195", fill_opacity=1, stroke_width=0).move_to(P(cols[key] - 42 + bw / 2, y + 34)))
            g.add(T(f"{s['revealed'][sid]:.3f}" if known else "—", 14, cols["P"], y + 25, INK, MEDIUM, anchor="r"))
            g.add(T(f"{tox[sid]:.3f}" if known and sid in tox else "—", 14, cols["H"], y + 25, INK, MEDIUM, anchor="r"))
            dis = known or s["remaining"] == 0 or bool(s["decision"])
            g.add(button("Revealed" if known else "Reveal", x1, y + 9, disabled=dis, px=12, anchor="r", h=32, padx=10))
            self.row_y[sid] = y
            y += rh
        return g

    def next_section(self, s):
        x = X0 + 22
        d = s["decision"]
        rec = s.get("recommendation")
        if d:
            title = {"nominate": "Nomination", "shortlist": "Shortlist", "joint": "Joint activity", "cytotoxic": "Cytotoxicity veto"}.get(d["kind"], "No justified single-compound choice")
            text = "Export the evidence and decision trace, or compare the baseline on the same episode."
            prim = "Decision finalized"
        elif rec:
            title = self.sample(s, rec["sample_id"])["name"]
            p = rec["predictions"]
            text = f"Expected nomination utility gain {rec['score']:.3f} on a 0–1 scale. Predicted response under A {p['A']:.2f} / B {p['B']:.2f}."
            prim = "Reveal assay"
        else:
            title = "The assay budget is complete."
            text = "Apply the shared nomination threshold, or retain ambiguity."
            prim = "Finalize decision"
        abst = button("Abstain now", X1 - 22, 839, disabled=bool(d), anchor="r")
        pb = button(prim, abst.bounds[0] - 8, 839, primary=not d, disabled=bool(d), anchor="r")
        g = VGroup(T(title, 20, x, 856, INK, MEDIUM), T(text, 14, x, 884, MUTED), pb, abst)
        self.primary_btn, self.abstain_btn = pb, abst
        return g

    def trail(self, s):
        x = X0 + 22
        g = VGroup()
        if not s["trace"]:
            g.add(T("1.  No new assays yet. Your three-assay budget is intact.", 14, x, 980, MUTED))
        for i, t in enumerate(s["trace"]):
            nm = self.sample(s, t["sample_id"])["name"]
            line = f"{i + 1}.  {nm} → parasite {t['response']:.3f}" + (f" · host tox {t['response_cytotox']:.3f}" if t.get("response_cytotox") is not None else "")
            g.add(T(line, 14, x, 980 + i * 31, MUTED))
        return g

    def baseline(self, s):
        x = X0 + self.lower_w + 34
        w = self.lower_w - 44
        if s.get("strongest"):
            st = s["strongest"]
            text = f"Strongest-first would assay {self.sample(s, st['sample_id'])['name']}, maximizing predicted response ({st['score']:.3f}). DECOUPLE maximizes expected nomination utility gain."
        else:
            text = "Compare the complete strongest-first replay against your choices on identical archived outcomes."
        p, yb = para(text, 14, x, 965, w)
        self.compare_btn = button("Compare with strongest-first", x, 1020, disabled=not s["decision"])
        return VGroup(p, self.compare_btn)

    # ------------------------------------------------------------ assemble
    KEYS = ["select", "alts", "verdict", "budget", "table", "next", "trail", "baseline"]

    def build_dynamic(self, s):
        return {"select": self.select_box(), "alts": self.alternatives(s), "verdict": self.verdict(s), "budget": self.budget(s),
                "table": self.table(s), "next": self.next_section(s), "trail": self.trail(s), "baseline": self.baseline(s)}

    def build(self):
        self.chrome_g = self.chrome()
        self.cands = self.candidates(self.s)
        self.parts = self.build_dynamic(self.s)
        return VGroup(self.chrome_g, self.cands, *self.parts.values())

    def goto(self, idx, run_time=0.8, bars_time=1.4, keys=None, bars=True):
        """Animate the page to state idx. `keys` limits which parts change now."""
        self.idx = idx
        self.s = self.ep["states"][idx]
        new = self.build_dynamic(self.s)
        keys = keys or self.KEYS
        anims = [FadeTransform(self.parts[k], new[k]) if k == "table" else ReplacementTransform(self.parts[k], new[k])
                 for k in keys]
        for k in keys:
            self.parts[k] = new[k]
        self.scene.play(*anims, run_time=run_time)
        if bars:
            self.bars(bars_time)

    def bars(self, rt=1.4):
        self.scene.play(self.trackers[0].animate.set_value(self.s["posterior"][0]),
                        self.trackers[1].animate.set_value(self.s["posterior"][1]), run_time=rt, rate_func=smooth)

    def switch_episode(self, ep_id, run_time=0.8):
        """Load another episode (the app re-renders the workbench)."""
        self.ep_id = ep_id
        self.ep = EPS[ep_id]
        self.idx = 0
        self.s = self.ep["states"][0]
        old_c = self.cands
        self.trackers = None
        self.cands = self.candidates(self.s)
        new = self.build_dynamic(self.s)
        self.scene.play(FadeOut(old_c), *[FadeOut(self.parts[k]) for k in self.KEYS], run_time=run_time / 2)
        self.parts = new
        self.scene.play(FadeIn(self.cands), *[FadeIn(new[k]) for k in self.KEYS], run_time=run_time / 2)


# ======================================================================
class DemoScene(NarratedMixin, MovingCameraScene):
    VIDEO = "demo"

    def setup(self):
        MovingCameraScene.setup(self)
        self.camera.background_color = GROUND
        self.cur = cursor_mob().move_to(P(900, 600), aligned_edge=UL)
        self.cur.set_z_index(100)

    # page + cursor
    def page(self, ep_id=MAIN, idx=0, fade=False):
        self.wb = Workbench(self, ep_id, idx)
        g = self.wb.build()
        if fade:
            self.play(FadeIn(g), run_time=0.8)
        else:
            self.add(g)
        self.add(self.cur)
        return g

    def move(self, x, y, rt=0.7):
        self.play(self.cur.animate.move_to(P(x, y), aligned_edge=UL), run_time=rt, rate_func=smooth)

    def click(self, x, y, rt=0.6):
        self.move(x, y, rt)
        ring = Circle(radius=4 * U, color=ACCENT, stroke_width=3).move_to(P(x, y)).set_z_index(99)
        self.play(self.cur.animate.scale(0.85, about_point=P(x, y)), FadeIn(ring), run_time=0.12)
        self.play(self.cur.animate.scale(1 / 0.85, about_point=P(x, y)), ring.animate.scale(5).set_stroke(opacity=0), run_time=0.3)
        self.remove(ring)

    def click_btn(self, btn, rt=0.6):
        x, y, w, h = btn.bounds
        self.click(x + w * 0.55, y + h * 0.6, rt)

    # camera
    def focus(self, x, y, w, rt=0.9):
        """Zoom so that the css-px region of width w centred on (x, y) fills the frame."""
        self.play(self.camera.frame.animate.set_width(w * U).move_to(P(x, y)), run_time=rt, rate_func=smooth)

    def unfocus(self, rt=0.8, scroll=0):
        self.play(self.camera.frame.animate.set_width(config.frame_width).move_to(P(PAGE_W / 2, VIEW_H / 2 + scroll)), run_time=rt, rate_func=smooth)

    # annotation bubble (video callout, not part of the app)
    def callout(self, s, x, y, anchor="l", px=14, w_max=None):
        t = txt(s, px, ON, MEDIUM)
        bg = RoundedRectangle(width=t.width + 28 * U, height=t.height + 22 * U, corner_radius=6 * U, fill_color=INK, fill_opacity=0.94, stroke_width=0)
        dot = Dot(radius=4 * U, color=ACCENT)
        g = VGroup(bg, t.move_to(bg).shift(RIGHT * 6 * U), dot.move_to(bg.get_left() + RIGHT * 12 * U))
        if anchor == "l":
            g.move_to(P(x, y), aligned_edge=LEFT)
        elif anchor == "r":
            g.move_to(P(x, y), aligned_edge=RIGHT)
        else:
            g.move_to(P(x, y))
        g.set_z_index(90)
        return g

    def show(self, *m, rt=0.4):
        self.play(*[FadeIn(x, shift=UP * 0.05) for x in m], run_time=rt)

    def hide(self, *m, rt=0.3):
        self.play(*[FadeOut(x) for x in m], run_time=rt)

    # dropdown for the candidate-pair select
    def pick_episode(self, ep_id, rt_open=0.4):
        self.click(X0 + 200, 272)
        y0 = 292
        rows = VGroup()
        items = VGroup()
        bg = box(X0, y0, 460, 12 * 26 + 10, stroke=BORDER, r=6).set_z_index(80)
        target_y = None
        for i, e in enumerate(CATALOG):
            yy = y0 + 5 + i * 26
            label = " / ".join(e["names"])
            while width_px(label, 13) > 430:
                label = label[:-1]
            t = T(label, 13, X0 + 12, yy + 13, INK).set_z_index(82)
            items.add(t)
            if e["id"] == ep_id:
                target_y = yy
        self.play(FadeIn(bg), FadeIn(items), run_time=rt_open)
        hl = Rectangle(width=450 * U, height=24 * U, fill_color=ACCENT, fill_opacity=1, stroke_width=0).move_to(P(X0 + 230, target_y + 13)).set_z_index(81)
        self.move(X0 + 160, target_y + 14, 0.6)
        idx = [e["id"] for e in CATALOG].index(ep_id)
        self.add(hl)
        items[idx].set_color(ON)
        self.wait(0.25)
        self.click(X0 + 160, target_y + 14, 0.1)
        self.play(FadeOut(bg), FadeOut(items), FadeOut(hl), run_time=0.2)
        self.wb.switch_episode(ep_id)

    # modal dialog
    def modal(self, title, body_fn, width=900, scroll=0):
        """Centred <dialog>; `scroll` is the current page scroll in css px."""
        x = PAGE_W / 2 - width / 2
        top = 40 + scroll
        content, bottom = body_fn(x + 24, top + 24 + 30 + 20, width - 48)
        dlg = box(x, top, width, bottom + 24 - top, r=8)
        head = T(title, 22, x + 24, top + 24 + 15, INK, MEDIUM)
        close = button("Close", x + width - 24, top + 20, anchor="r")
        g = VGroup(dlg, head, close, content)
        for m in g.get_family():
            m.set_z_index(70)
        backdrop = Rectangle(width=60, height=60, fill_color=BLACK, fill_opacity=0.3, stroke_width=0).set_z_index(60)
        backdrop.move_to(self.camera.frame.get_center())
        self.play(FadeIn(backdrop), FadeIn(g, shift=UP * 0.08), run_time=0.45)
        self.dialog = (backdrop, g, close)
        return g

    def close_modal(self):
        backdrop, g, close = self.dialog
        self.click_btn(close, 0.5)
        self.play(FadeOut(backdrop), FadeOut(g), run_time=0.3)


def table_rows(rows, x, y, widths, px=14, header_px=12, aligns=None):
    """rows[0] is the header. Returns (group, bottom_y)."""
    g = VGroup()
    aligns = aligns or ["l"] + ["r"] * (len(widths) - 1)
    total = sum(widths)
    for r, row in enumerate(rows):
        rh = 38 if r == 0 else 43
        if r:
            g.add(hline(x, y, total, "#eeeeee"))
        cx = x
        for c, (cell, w) in enumerate(zip(row, widths)):
            if aligns[c] == "l":
                g.add(T(cell, header_px if r == 0 else px, cx, y + rh / 2, MUTED if r == 0 else INK))
            else:
                g.add(T(cell, header_px if r == 0 else px, cx + w, y + rh / 2, MUTED if r == 0 else INK, anchor="r"))
            cx += w
        y += rh
    return g, y


# ====================================================================== scenes
class D1Launch(DemoScene):
    SID = "d1_launch"

    def construct(self):
        self.start_narration()
        self.page(CATALOG[0]["id"], 0, fade=True)
        self.move(760, 520, 1.0)

        self.at("tier")
        self.focus(560, 187, 900)
        c = self.callout("Measured ENPKG values · nothing simulated", 560, 232, anchor="c")
        self.show(c)
        self.at_word("real", "tier", 0.6)
        self.hide(c)
        self.unfocus()

        self.at("pair")
        self.pick_episode(MAIN)
        self.focus(323, 420, 620)
        c2 = self.callout("MS annotation candidates, not confirmed structures", 323, 302, anchor="c", px=12)
        self.show(c2)

        self.at("post")
        self.hide(c2)
        self.focus(323, 520, 560, rt=0.6)
        hl = SurroundingRectangle(VGroup(self.wb.cands[1], self.wb.parts["alts"][1]), color=ACCENT, buff=6 * U, stroke_width=2.5, corner_radius=4 * U)
        self.play(Create(hl), run_time=0.6)
        self.at_word("can't", "post", -0.3)
        self.play(FadeOut(hl), run_time=0.3)
        self.unfocus()
        self.finish(fade=False)


class D2Recommend(DemoScene):
    SID = "d2_recommend"

    def construct(self):
        self.start_narration()
        self.page(MAIN, 0)
        self.focus(993, 560, 1000)
        self.move(1000, 600, 0.8)

        self.at("strong")
        self.unfocus(scroll=260)
        bl = self.wb.parts["baseline"][0]
        self.move(1000, 990, 0.6)
        hl = SurroundingRectangle(bl, color=ACCENT, buff=6 * U, stroke_width=2.5, corner_radius=4 * U)
        self.play(Create(hl), run_time=0.6)

        self.at("rec")
        self.play(FadeOut(hl), run_time=0.3)
        self.unfocus(scroll=120)
        rid = self.ep_rec()
        y = self.wb.row_y[rid]
        rowhl = SurroundingRectangle(VGroup(*[m for m in self.wb.parts["table"] if abs(m.get_center()[1] - P(0, y + 25)[1]) < 25 * U]),
                                     color=ACCENT, buff=4 * U, stroke_width=2.5, corner_radius=4 * U)
        self.move(700, y + 20, 0.7)
        self.play(Create(rowhl), run_time=0.6)
        self.at_word("xanthone", "rec", -0.2)
        c = self.callout("A 0.10 · B 0.00  — xanthone without the rotenoid", 1000, y - 22, anchor="c", px=13)
        self.show(c)

        self.at("pred")
        self.hide(c, rowhl)
        self.focus(560, 868, 900)
        self.move(560, 890, 0.6)
        u = Underline(self.wb.parts["next"][1], color=ACCENT, buff=3 * U, stroke_width=3)
        self.play(Create(u), run_time=0.6)
        self.at_word("gap", "pred", -0.3)
        self.play(FadeOut(u), run_time=0.3)
        self.unfocus()
        self.finish(fade=False)

    def ep_rec(self):
        return self.wb.s["recommendation"]["sample_id"]


class D3Reveal(DemoScene):
    SID = "d3_reveal"

    def construct(self):
        self.start_narration()
        self.page(MAIN, 0)
        self.unfocus(rt=0.3, scroll=40)
        self.click_btn(self.wb.primary_btn, 0.8)

        self.at("both")
        # values land first; the posterior moves on "jump"
        self.wb.goto(1, run_time=0.6, keys=["table", "next", "trail", "budget", "baseline"], bars=False)
        rid = "VGF153_F10"
        y = self.wb.row_y[rid]
        self.focus(1180, y + 25, 640)
        c = self.callout("one reveal · parasite + host-cell toxicity", 1180, y - 12, anchor="c", px=12)
        self.show(c)
        self.at_word("Inactive", "both", -0.2)
        self.hide(c)

        self.at("jump")
        self.focus(323, 450, 560)
        self.wb.goto(1, run_time=0.4, keys=["alts", "verdict"], bars=False)
        self.wb.bars(1.6)
        self.focus(323, 730, 560, rt=0.6)
        self.unfocus(scroll=40)

        self.at("more")
        self.click_btn(self.wb.primary_btn, 0.6)
        self.wb.goto(2, run_time=0.5, bars_time=0.6)
        self.click_btn(self.wb.primary_btn, 0.5)
        self.wb.goto(3, run_time=0.5, bars_time=0.6)
        self.unfocus(scroll=200)
        self.wait(0.8)
        self.unfocus(scroll=40)
        self.finish(fade=False)


class D4Finalize(DemoScene):
    SID = "d4_finalize"

    def construct(self):
        self.start_narration()
        self.page(MAIN, 3)
        self.unfocus(rt=0.01, scroll=40)
        self.click_btn(self.wb.primary_btn, 0.8)
        self.wb.goto(4, run_time=0.6, bars_time=0.1)

        self.at("nominate")
        self.focus(323, 670, 540)
        self.at_word("purified", "nominate", -0.4)
        self.unfocus(scroll=260)

        self.at("compare")
        self.click_btn(self.wb.compare_btn, 0.7)
        cmp = EPS[MAIN]["compare"]

        def body(x, y, w):
            g = VGroup()
            colw = (w - 24) / 2
            bottom = y
            for j, (name, v) in enumerate([("Your choices", cmp["you"]), ("Strongest-first", cmp["baseline"])]):
                cx = x + j * (colw + 24)
                yy = y
                g.add(T(name, 16, cx, yy + 11, INK, MEDIUM))
                yy += 34
                samples = {s["id"]: s for s in v["samples"]}
                for i, t in enumerate(v["trace"]):
                    g.add(T(f"{i + 1}.  {samples[t['sample_id']]['name']}", 14, cx, yy + 10, MUTED))
                    g.add(T(f"parasite {t['response']:.3f}", 14, cx + 22, yy + 31, MUTED))
                    g.add(T(f"host tox {t['response_cytotox']:.3f}", 14, cx + 22, yy + 52, MUTED))
                    yy += 72
                wb = Workbench(self, MAIN, 4)
                lab = wb.label(v["decision"])
                for ln in wrap(lab, 16, colw, MEDIUM):
                    g.add(T(ln, 16, cx, yy + 11, INK, MEDIUM))
                    yy += 22
                ex = v["decision"]["explanation"]
                p, yy = para(ex[0].upper() + ex[1:], 14, cx, yy + 6, colw)
                g.add(p)
                bottom = max(bottom, yy)
                if j == 1:
                    self.base_col = g[-1]
            return g, bottom

        dlg = self.modal("One episode. Equal assay budgets.", body, scroll=260)
        self.at_word("shortlist", "compare", -0.4)
        self.wait(1.0)

        self.at("export")
        self.close_modal()
        self.unfocus(scroll=0, rt=0.6)
        self.click_btn(self.wb.export_btn, 0.6)
        c = self.callout("decouple-decision-trace.json", X1, 152, anchor="r", px=13)
        self.show(c)
        self.wait(1.0)
        self.hide(c)
        self.finish(fade=False)


class D5Verdicts(DemoScene):
    SID = "d5_verdicts"

    def run_episode(self, ep_id, verdict_word, key):
        self.pick_episode(ep_id)
        for i in range(1, 4):
            self.click_btn(self.wb.primary_btn, 0.3)
            self.wb.goto(i, run_time=0.25, bars_time=0.3)
        self.click_btn(self.wb.primary_btn, 0.3)
        self.wb.goto(4, run_time=0.35, bars_time=0.1)
        self.focus(323, 665, 560)

    def construct(self):
        self.start_narration()
        self.page(MAIN, 4)
        self.at("joint")
        self.run_episode(JOINT, "both", "joint")
        self.at("cyto", -1.2)
        self.unfocus(rt=0.4)
        self.run_episode(CYTO, "toxicity", "cyto")
        self.at_word("veto", "cyto", 0.4)
        self.wait(0.5)
        self.unfocus()
        self.finish(fade=False)


class D6Benchmark(DemoScene):
    SID = "d6_benchmark"
    TAIL = 1.5

    def construct(self):
        self.start_narration()
        self.page(CYTO, 4)
        self.click_btn(self.wb.bench_btn, 0.9)
        r = DATA["results"]

        def fmt(o):
            if o["estimate"] is None:
                return "—"
            s = pct(o["estimate"])
            if o.get("ci95"):
                s += f" [{pct(o['ci95'][0])}–{pct(o['ci95'][1])}]"
            return s

        def body(x, y, w):
            g = VGroup()
            p, y = para(f"{r['episodes']} simulated episodes across {r['unique_pairs']} chemical pairs. The current pairs share a compound and a source assay. Repeats vary simulated noise; they provide no additional biological validation.", 14, x, y, w)
            g.add(p)
            rows = [["Policy", "Correct nomination / all episodes", "Abstention", "Precision / nominated"]]
            for k, m in r["policies"].items():
                rows.append([k, fmt(m["correct_nomination_rate"]), fmt(m["abstention_rate"]), fmt(m["precision_when_nominating"])])
            t, y = table_rows(rows, x, y + 10, [190, 260, 130, w - 580])
            g.add(t)
            self.policy_table = t
            p2, y = para(r["uncertainty"], 14, x, y + 10, w)
            g.add(p2)
            self.unc = p2
            sv = r["set_valued"]
            g.add(T(sv["label"], 16, x, y + 24, INK, MEDIUM))
            y += 40
            t2, y = table_rows([["Answered", "Contains the true driver", "Mean set size", "Vetoed as cytotoxic"],
                                [pct(sv["coverage"]), pct(sv["containment"]), f"{sv['mean_size']:.2f}", pct(sv["cytotoxic_rate"])]],
                               x, y, [190, 260, 130, w - 580], aligns=["l", "r", "r", "r"])
            g.add(t2)
            self.sv_table = t2
            g.add(T(" · ".join(f"{k} {n}" for k, n in sv["kind_counts"].items()), 14, x, y + 22, MUTED))
            return g, y + 34

        self.modal(r["tier"], body)
        self.move(900, 700, 0.6)

        self.at("rates")
        self.focus(PAGE_W / 2, self.center_y(self.policy_table), 1000)
        rows = self.policy_table
        self.at_word("32.2", "rates", -0.5)
        self.at_word("99.4", "rates", -0.3)

        self.at("set")
        self.focus(PAGE_W / 2, self.center_y(self.sv_table) + 10, 1000)

        self.at("caveat")
        self.unfocus(rt=0.7)
        hl = SurroundingRectangle(self.unc, color=ACCENT, buff=6 * U, stroke_width=2.5, corner_radius=4 * U).set_z_index(95)
        self.play(Create(hl), run_time=0.6)
        self.wait(1.5)
        self.play(FadeOut(hl), run_time=0.3)
        self.until(self.timing["duration"] - 0.2)
        everything = [m for m in self.mobjects]
        end = VGroup(logo_mark(90), txt("DECOUPLE", 40, INK, MEDIUM)).arrange(RIGHT, buff=0.35).move_to(self.camera.frame.get_center())
        self.play(*[FadeOut(m) for m in everything], run_time=0.6)
        self.play(FadeIn(end), run_time=0.6)
        self.until(self.timing["duration"] + self.TAIL)

    def center_y(self, mob):
        return VIEW_H / 2 - mob.get_center()[1] / U


SCENES = ["D1Launch", "D2Recommend", "D3Reveal", "D4Finalize", "D5Verdicts", "D6Benchmark"]
