"""DECOUPLE explainer video — seven narrated Manim scenes.

Render one:  manim -qh explainer.py E1Problem
All numbers come from FINDINGS.md / results/benchmark.json, or (E3) from the
live engine capture in manim_demo/episodes.json.
"""
import random

from common import *

import common
common.SCALE = 1.3          # video type scale: UI px sizes read too small full-frame

# black & white + the app's single accent (see common.py)
BG = GROUND
PANEL = SURFACE
PANEL2 = "#f7f8fa"
A_COL = ACCENT         # candidate A: the app's A track is the accent
B_COL = SLATE          # candidate B: the app's B track
BOTH = INK
NEITHER = PALE
GOOD = ACCENT          # emphasis / chosen / selective
BAD = INK              # toxic / rejected: black, never a second hue


# ---------------------------------------------------------------- components
def logo(scale=1.0, color=INK):
    s = 0.06 * scale
    def pts(seq):
        return [np.array([(x - 15) * s, (15 - y) * s, 0]) for x, y in seq]
    a = VMobject(stroke_color=color, stroke_width=4 * scale).set_points_as_corners(pts([(3, 7), (13, 7), (18, 23), (27, 23)]))
    b = VMobject(stroke_color=color, stroke_width=4 * scale).set_points_as_corners(pts([(3, 23), (13, 23), (18, 7), (27, 7)]))
    return VGroup(a, b)


def heading(kicker, title, color=GOOD):
    k = txt(kicker.upper(), 14, color, MEDIUM)
    h = txt(title, 40, INK, MEDIUM, font=DISPLAY)
    g = VGroup(k, h).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    return g.to_corner(UL, buff=0.55)


def card(w, h, stroke=LINE, fill=PANEL, r=0.08):
    # app: white surface, 1px #e2e4e7 border, 8px radius
    return RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=fill, fill_opacity=1,
                            stroke_color=stroke, stroke_width=1.5 if stroke == LINE else 2.2)


def chip(s, color, px=17, fill_op=0.08):
    t = txt(s, px, color, MEDIUM)
    bg = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.26, corner_radius=0.06,
                          fill_color=color if color != INK else SURFACE, fill_opacity=fill_op if color != INK else 1,
                          stroke_color=color if color != INK else BORDER, stroke_width=1.2)
    return VGroup(bg, t.move_to(bg))


class ProbBars(VGroup):
    """Labelled horizontal probability bars driven by ValueTrackers."""

    def __init__(self, labels, colors, values, width=4.6, row_h=0.62, label_w=2.2, px=20):
        super().__init__()
        self.trackers = []
        for i, (lab, col, v) in enumerate(zip(labels, colors, values)):
            vt = ValueTracker(v)
            self.trackers.append(vt)
            y = -i * row_h
            name = txt(lab, px, INK, MEDIUM).move_to([0, y, 0], aligned_edge=LEFT)
            track = Rectangle(width=width, height=0.13, fill_color="#eeeeee",
                              fill_opacity=1, stroke_width=0).move_to([label_w + width / 2, y, 0])

            def mk_fill(vt=vt, col=col, track=track):
                w = max(vt.get_value() * width, 0.001)
                return Rectangle(width=w, height=track.height, fill_color=col, fill_opacity=1,
                                 stroke_width=0).move_to(track.get_left(), aligned_edge=LEFT)

            def mk_num(vt=vt, track=track, col=col):
                return txt(f"{vt.get_value() * 100:.1f}%", px, INK, MEDIUM).next_to(track, RIGHT, buff=0.25)

            self.add(VGroup(name, track, always_redraw(mk_fill), always_redraw(mk_num)))

    def to(self, values, **kw):
        return [vt.animate(**kw).set_value(v) for vt, v in zip(self.trackers, values)]


def trypanosome(color=BAD, scale=1.0):
    body = ParametricFunction(lambda t: np.array([t, 0.12 * np.sin(3 * t) * (1 - (t / 1.3) ** 2), 0]),
                              t_range=[-1.3, 1.3], color=color, stroke_width=0)
    top = [np.array([t, 0.26 * np.sqrt(max(0, 1 - (t / 1.3) ** 2)) + 0.08 * np.sin(3 * t), 0]) for t in np.linspace(-1.3, 1.3, 40)]
    bot = [np.array([t, -0.22 * np.sqrt(max(0, 1 - (t / 1.3) ** 2)) + 0.08 * np.sin(3 * t), 0]) for t in np.linspace(1.3, -1.3, 40)]
    shape = VMobject(fill_color=color, fill_opacity=0.25, stroke_color=color, stroke_width=3)
    shape.set_points_smoothly(top + bot + [top[0]])
    membrane = ParametricFunction(lambda t: np.array([t, 0.26 * np.sqrt(max(0, 1 - (t / 1.3) ** 2)) + 0.08 * np.sin(3 * t) + 0.05 * np.sin(14 * t), 0]),
                                  t_range=[-1.1, 1.2], color=color, stroke_width=2)
    flag = ParametricFunction(lambda t: np.array([1.3 + t, 0.1 * np.sin(7 * t) + 0.08, 0]), t_range=[0, 0.9], color=color, stroke_width=2.5)
    nucleus = Dot([-0.1, 0.03, 0], radius=0.09, color=color)
    kin = Dot([-0.85, 0.02, 0], radius=0.05, color=color)
    return VGroup(shape, membrane, flag, nucleus, kin, body).scale(scale)


def vial(h=2.6, w=1.25, liquid=GOOD):
    glass = RoundedRectangle(width=w, height=h, corner_radius=w / 2.2, stroke_color=INK, stroke_width=2.5, fill_opacity=0)
    rim = Line(glass.get_corner(UL) + LEFT * 0.12, glass.get_corner(UR) + RIGHT * 0.12, color=INK, stroke_width=3)
    liq = RoundedRectangle(width=w - 0.14, height=h * 0.66, corner_radius=(w - 0.14) / 2.2, fill_color=liquid,
                           fill_opacity=0.18, stroke_width=0).align_to(glass, DOWN).shift(UP * 0.07)
    return VGroup(liq, glass, rim)


def column_icon():
    tube = RoundedRectangle(width=0.55, height=2.2, corner_radius=0.08, stroke_color=INK, stroke_width=2, fill_opacity=0)
    bands = VGroup(*[Rectangle(width=0.5, height=0.14, fill_color=c, fill_opacity=0.8, stroke_width=0).move_to(tube).shift(UP * y)
                     for c, y in [(A_COL, 0.55), (B_COL, 0.15), (BOTH, -0.25), (GOOD, -0.6)]])
    drip = Dot(tube.get_bottom() + DOWN * 0.22, radius=0.05, color=GOOD)
    return VGroup(tube, bands, drip)


def vbar_chart(items, ymax, h=3.2, bar_w=0.9, gap=0.75, unit="%"):
    """items: (label, value, lo, hi, color). Returns (group, bars list)."""
    g = VGroup()
    base = Line(LEFT * 0.4, RIGHT * (len(items) * (bar_w + gap)), color=LINE, stroke_width=2)
    g.add(base)
    cols = []
    for i, (lab, v, lo, hi, col) in enumerate(items):
        x = i * (bar_w + gap) + bar_w / 2
        bar = Rectangle(width=bar_w, height=max(v / ymax * h, 0.001), fill_color=col, fill_opacity=0.9,
                        stroke_width=0).move_to([x, 0, 0], aligned_edge=DOWN)
        val = txt(f"{v:.1f}{unit}", 22, INK, BOLD).next_to(bar, UP, buff=0.12)
        name = txt(lab, 16, MUTED, MEDIUM).next_to([x, 0, 0], DOWN, buff=0.2)
        parts = VGroup(bar, val, name)
        if lo is not None:
            whisk = VGroup(Line([x, lo / ymax * h, 0], [x, hi / ymax * h, 0], color=INK, stroke_width=2),
                           Line([x - 0.12, lo / ymax * h, 0], [x + 0.12, lo / ymax * h, 0], color=INK, stroke_width=2),
                           Line([x - 0.12, hi / ymax * h, 0], [x + 0.12, hi / ymax * h, 0], color=INK, stroke_width=2))
            val.next_to(whisk, UP, buff=0.1)
            parts.add(whisk)
        cols.append(parts)
        g.add(parts)
    return g, cols


class ExplainerScene(NarratedMixin, Scene):
    VIDEO = "explainer"

    def setup(self):
        self.camera.background_color = BG

    def swap(self, old, new, rt=0.6):
        self.play(FadeOut(old, shift=UP * 0.2), FadeIn(new, shift=UP * 0.2), run_time=rt)


# ====================================================================== E1
class E1Problem(ExplainerScene):
    SID = "e1_problem"

    def construct(self):
        self.start_narration()
        brand = VGroup(logo(0.7), txt("DECOUPLE", 18, MUTED, BOLD)).arrange(RIGHT, buff=0.18).to_corner(UR, buff=0.5)
        head = heading("The problem", "Which molecule did it?")
        self.play(FadeIn(brand), FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)

        # --- hit: extract kills parasite
        v = vial().move_to(LEFT * 3.6 + DOWN * 0.3)
        vlab = txt("Plant extract", 20, MUTED, MEDIUM).next_to(v, DOWN, buff=0.25)
        par = trypanosome(BAD, 1.15).move_to(RIGHT * 3.3 + DOWN * 0.1)
        plab = VGroup(txt("Trypanosoma cruzi", 22, INK, BOLD, slant=ITALIC),
                      txt("parasite behind Chagas disease", 17, MUTED)).arrange(DOWN, buff=0.1).next_to(par, DOWN, buff=0.45)
        arr = Arrow(v.get_right() + RIGHT * 0.2, par.get_left() + LEFT * 0.25, color=GOOD, stroke_width=5, buff=0)
        self.play(FadeIn(v, shift=UP * 0.2), FadeIn(vlab), run_time=0.8)
        self.play(GrowArrow(arr), FadeIn(par, shift=LEFT * 0.2), FadeIn(plab), run_time=1.0)
        x = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(BAD, 6).scale(0.35).move_to(par).shift(UP * 0.05)
        self.play(par.animate.set_opacity(0.35), Create(x), run_time=0.8)

        # --- mixture
        self.at("mixture")
        random.seed(3)
        cols = [INK, SLATE, PALE, "#9aa1a9", MUTED, ACCENT]
        liq = v[0]
        dots = VGroup(*[Dot(liq.get_center() + np.array([random.uniform(-0.42, 0.42), random.uniform(-0.75, 0.75), 0]),
                            radius=0.045, color=random.choice(cols)) for _ in range(70)])
        q = txt("?", 120, INK, BOLD, font=DISPLAY).next_to(v, RIGHT, buff=0.35).shift(UP * 0.9)
        lbl2 = txt("hundreds of compounds", 18, MUTED).next_to(v, UP, buff=0.3)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.02), FadeIn(lbl2), run_time=1.6)
        self.play(FadeIn(q, scale=0.6), run_time=0.6)

        # --- cost
        self.at("cost")
        col = column_icon().move_to(RIGHT * 0.2 + DOWN * 0.2)
        one = dots[5]
        clock = VGroup(Circle(radius=0.32, color=A_COL, stroke_width=3),
                       Line(ORIGIN, UP * 0.22, color=A_COL, stroke_width=3), Line(ORIGIN, RIGHT * 0.16, color=A_COL, stroke_width=3))
        weeks = VGroup(clock, txt("weeks of chromatography\nper molecule", 19, A_COL, BOLD)).arrange(RIGHT, buff=0.25)
        weeks.next_to(col, DOWN, buff=0.35)
        self.play(FadeOut(q), FadeOut(arr), FadeOut(x), par.animate.set_opacity(0.15),
                  FadeIn(col, shift=UP * 0.2), run_time=0.7)
        self.play(one.animate.scale(2.2).move_to(col.get_top() + UP * 0.25), run_time=0.8)
        self.play(FadeIn(weeks, shift=UP * 0.15), run_time=0.6)

        # --- rho
        self.at("rho")
        scene1 = VGroup(v, vlab, par, plab, dots, lbl2, col, weeks)
        self.play(FadeOut(scene1, shift=DOWN * 0.2), run_time=0.6)
        c = card(6.0, 3.6).move_to(LEFT * 3.2 + DOWN * 0.45)
        cap = txt("Rotenoid share vs. T. cruzi activity", 19, MUTED, MEDIUM).next_to(c.get_top(), DOWN, buff=0.35)
        rho = txt("ρ = 0.095", 76, INK, BOLD, font=DISPLAY).move_to(c).shift(UP * 0.05)
        sub = txt("Spearman, 1,600 ENPKG extracts", 17, FAINT).next_to(rho, DOWN, buff=0.3)
        self.play(FadeIn(c), FadeIn(cap), run_time=0.5)
        self.at_word("tracks", "rho", -0.2)
        self.play(Write(rho), FadeIn(sub), run_time=1.0)

        # --- clitoria
        self.at("clitoria")
        c2 = card(5.8, 3.6, stroke=BAD).move_to(RIGHT * 3.25 + DOWN * 0.45)
        name = txt("Clitoria macrophylla · roots", 21, INK, BOLD, slant=ITALIC)
        rows = VGroup(*[VGroup(txt(a, 18, MUTED), txt(b, 20, cc, BOLD)).arrange(RIGHT, buff=0.3)
                        for a, b, cc in [("rotenoid share", "91.4%", B_COL), ("T. cruzi inhibition", "71.8%", INK),
                                         ("host cytotoxicity", "46.8%", BAD)]]).arrange(DOWN, aligned_edge=RIGHT, buff=0.2)
        verdict = chip("not a selective active", BAD, 17)
        grp = VGroup(name, rows, verdict).arrange(DOWN, buff=0.3).move_to(c2)
        tag = txt("most rotenoid-rich extract in the library", 15, FAINT).next_to(c2, UP, buff=0.12)
        self.play(FadeIn(c2, shift=LEFT * 0.2), FadeIn(name), FadeIn(tag), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rows], lag_ratio=0.3), run_time=1.2)
        self.play(FadeIn(verdict, scale=0.8), run_time=0.5)

        # --- alibi
        self.at("alibi")
        self.play(FadeOut(VGroup(c, cap, rho, sub, c2, name, rows, verdict, tag)), run_time=0.5)
        ext_names = ["extract 1", "extract 2", "extract 3", "extract 4", "extract 5"]
        grid = VGroup()
        for i, n in enumerate(ext_names):
            box = card(2.1, 1.7, fill=PANEL).move_to(RIGHT * (i - 2) * 2.4 + DOWN * 0.2)
            da = Dot(box.get_center() + LEFT * 0.4 + UP * 0.05, radius=0.22, color=A_COL)
            db = Dot(box.get_center() + RIGHT * 0.4 + UP * 0.05, radius=0.22, color=B_COL)
            la = txt("A", 16, ON, BOLD).move_to(da)
            lb = txt("B", 16, ON, BOLD).move_to(db)
            act = chip("active", GOOD, 13).next_to(box.get_bottom(), UP, buff=0.12)
            grid.add(VGroup(box, da, db, la, lb, act))
        stat = VGroup(txt("486", 54, INK, BOLD, font=DISPLAY),
                      txt("rotenoid pairs co-occur in ≥ 3 extracts", 21, MUTED)).arrange(RIGHT, buff=0.3).next_to(grid, DOWN, buff=0.55)
        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.2) for g in grid], lag_ratio=0.15), run_time=1.4)
        self.play(FadeIn(stat, shift=UP * 0.1), run_time=0.6)
        self.at_word("alibi", "alibi", -0.4)
        links = VGroup(*[CurvedDoubleArrow(g[1].get_top(), g[2].get_top(), angle=-PI / 2, color=INK, stroke_width=2, tip_length=0.12)
                         for g in grid])
        alibi = txt("each gives the other an alibi", 20, A_COL, BOLD).next_to(grid, UP, buff=0.35)
        self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.1), FadeIn(alibi), run_time=1.0)

        # --- pools
        self.at("pools")
        self.play(FadeOut(VGroup(grid, stat, links, alibi)), run_time=0.5)

        def pool_grid(pattern, title, sub, col):
            cells = VGroup()
            for r, (a, b) in enumerate(pattern):
                for cidx, val, cc in [(0, a, A_COL), (1, b, B_COL)]:
                    sq = Square(0.42, fill_color=cc, fill_opacity=0.12 + 0.8 * val, stroke_color=LINE, stroke_width=1)
                    sq.move_to([cidx * 0.5, -r * 0.5, 0])
                    cells.add(sq)
            hd = VGroup(txt("A", 16, A_COL, BOLD).next_to(cells[0], UP, buff=0.12),
                        txt("B", 16, B_COL, BOLD).next_to(cells[1], UP, buff=0.12))
            t = VGroup(txt(title, 22, col, BOLD), txt(sub, 16, MUTED)).arrange(DOWN, buff=0.1)
            body = VGroup(cells, hd)
            return VGroup(t, body).arrange(DOWN, buff=0.3)

        designed = pool_grid([(1, 0), (0, 1), (1, 1), (0, 0), (1, 0), (0, 1)], "Pooled screening", "you design the pools", MUTED)
        nature = pool_grid([(0.9, 0.85), (0.6, 0.65), (0.95, 0.9), (0.3, 0.35), (0.8, 0.75), (0.15, 0.6)], "Natural products", "nature composed them", GOOD)
        pools = VGroup(designed, nature).arrange(RIGHT, buff=2.6).shift(DOWN * 0.15 + LEFT * 1.2)
        self.play(FadeIn(designed, shift=UP * 0.2), run_time=0.7)
        self.at_word("nature", "pools", -0.2)
        self.play(FadeIn(nature, shift=UP * 0.2), run_time=0.7)
        hint = nature[1][0][-2:]  # last row: B without much A
        ring = SurroundingRectangle(hint, color=A_COL, buff=0.06, corner_radius=0.06)
        free = VGroup(txt("Our only freedom:", 20, MUTED),
                      txt("which extract to assay next", 28, INK, BOLD, font=DISPLAY)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        free.next_to(pools, RIGHT, buff=0.9)
        self.at_word("freedom", "pools", -0.2)
        self.play(Create(ring), FadeIn(free, shift=LEFT * 0.2), run_time=0.8)
        self.finish()


# ====================================================================== E2
class E2Method(ExplainerScene):
    SID = "e2_method"

    def construct(self):
        self.start_narration()
        head = heading("The method", "Three assays. Choose them well.")
        pips = VGroup(*[RoundedRectangle(width=0.7, height=0.07, corner_radius=0.0, fill_color=INK, fill_opacity=1, stroke_width=0)
                        for _ in range(3)]).arrange(RIGHT, buff=0.12)
        budget = VGroup(txt("assay budget", 16, MUTED, MEDIUM), pips).arrange(RIGHT, buff=0.3).to_corner(UR, buff=0.6)
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.7)
        self.play(LaggedStart(*[GrowFromEdge(p, LEFT) for p in pips], lag_ratio=0.2), FadeIn(budget[0]), run_time=0.9)
        hero = VGroup(logo(1.4, INK), txt("DECOUPLE", 44, INK, MEDIUM)).arrange(RIGHT, buff=0.3)
        hero_sub = txt("one decision per assay, under a fixed budget", 20, MUTED).next_to(hero, DOWN, buff=0.3)
        hero_g = VGroup(hero, hero_sub).move_to(DOWN * 0.3)
        self.play(FadeIn(hero_g, shift=UP * 0.15), run_time=0.8)

        # --- 1. continuous attribution
        self.at("continuous")
        self.play(FadeOut(hero_g), run_time=0.4)
        n1 = chip("1 · continuous attribution", GOOD, 16).next_to(head, DOWN, aligned_edge=LEFT, buff=0.35)
        ax = Axes(x_range=[0, 4, 1], y_range=[0, 1.1, 0.5], x_length=6.4, y_length=3.0,
                  axis_config={"color": FAINT, "include_tip": False, "stroke_width": 2}).move_to(LEFT * 2.2 + DOWN * 0.95)
        xl = txt("log abundance of compound", 16, MUTED).next_to(ax.x_axis, DOWN, buff=0.2)
        yl = txt("predicted inhibition", 16, MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        curve = ax.plot(lambda x: 0.05 + 0.95 / (1 + np.exp(-3.2 * (x - 2.1))), x_range=[0, 4], color=GOOD, stroke_width=4)
        self.play(FadeIn(n1), Create(ax), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(Create(curve), run_time=1.2)
        random.seed(7)
        pts = [(0.4, 0.07), (0.7, 0.04), (1.0, 0.10), (1.6, 0.18), (2.0, 0.45), (2.3, 0.62), (2.7, 0.83), (3.1, 0.95), (3.5, 1.0), (3.8, 0.97)]
        sdots = VGroup(*[Dot(ax.c2p(x, y), radius=0.07, color=INK) for x, y in pts])
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in sdots], lag_ratio=0.08), run_time=1.0)
        side = VGroup(txt("not present / absent", 18, FAINT), txt("but how much", 26, INK, BOLD, font=DISPLAY)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        side.next_to(ax, RIGHT, buff=0.8).shift(UP * 0.6)
        strike = Line(side[0].get_left(), side[0].get_right(), color=BAD, stroke_width=3)
        self.at_word("presence", "continuous", -0.3)
        self.play(FadeIn(side), run_time=0.5)
        self.play(Create(strike), run_time=0.4)

        # --- floor
        self.at("floor")
        fx = 1.3
        zone = Rectangle(width=ax.c2p(fx, 0)[0] - ax.c2p(0, 0)[0], height=3.0, fill_color=PALE, fill_opacity=0.35, stroke_width=0)
        zone.move_to(ax.c2p(0, 0), aligned_edge=DL)
        fl = DashedLine(ax.c2p(fx, 0), ax.c2p(fx, 1.1), color=A_COL, dash_length=0.1)
        fltxt = txt("detection floor", 15, A_COL, BOLD).next_to(fl, UP, buff=0.1)
        unin = txt("uninformative,\nnot negative", 17, INK, BOLD).move_to(zone).shift(UP * 0.55)
        low = VGroup(*sdots[:3])
        self.play(FadeIn(zone), Create(fl), FadeIn(fltxt), run_time=0.7)
        self.play(low.animate.set_fill(opacity=0).set_stroke(FAINT, 2), FadeIn(unin), run_time=0.7)

        # --- 2. hypotheses
        self.at("hyp")
        part1 = VGroup(n1, ax, xl, yl, curve, sdots, side, strike, zone, fl, fltxt, unin)
        self.play(FadeOut(part1, shift=LEFT * 0.3), run_time=0.6)
        n2 = chip("2 · four competing explanations", BOTH, 16).next_to(head, DOWN, aligned_edge=LEFT, buff=0.35)
        bars = ProbBars(["A alone", "B alone", "Both", "Neither"], [A_COL, B_COL, BOTH, NEITHER], [0.25, 0.25, 0.25, 0.25],
                        width=5.2, row_h=0.75, label_w=2.0, px=22).move_to(DOWN * 0.7 + LEFT * 0.6)
        self.play(FadeIn(n2), FadeIn(bars, shift=UP * 0.2), run_time=0.8)
        tray = VGroup()
        self.at_word("Every", "hyp", -0.1)
        for vals in ([0.08, 0.42, 0.45, 0.05], [0.01, 0.86, 0.12, 0.01]):
            tk = chip("assay", GOOD, 14).next_to(bars, RIGHT, buff=0.9).shift(UP * (0.6 - 0.7 * len(tray)))
            tray.add(tk)
            self.play(FadeIn(tk, shift=LEFT * 0.3), *bars.to(vals), run_time=1.3)
            self.wait(0.4)

        # --- 3. adaptive contrast
        self.at("contrast")
        self.play(FadeOut(VGroup(n2, bars, tray), shift=LEFT * 0.3), run_time=0.6)
        n3 = chip("3 · adaptive contrast", B_COL, 16).next_to(head, DOWN, aligned_edge=LEFT, buff=0.35)
        specs = [(0.8, 0.75), (0.5, 0.55), (0.0, 0.7), (0.65, 0.05), (0.1, 0.15), (0.62, 0.08)]
        scores = [0.06, 0.04, 0.55, 0.92, 0.10, 0.88]
        cards = VGroup()
        for i, (a, b) in enumerate(specs):
            cc = card(1.85, 2.5, fill=PANEL).move_to(RIGHT * (i - 2.5) * 2.08 + DOWN * 0.55)
            ba = Rectangle(width=0.36, height=max(a * 1.1, 0.02), fill_color=A_COL, fill_opacity=0.9, stroke_width=0)
            bb = Rectangle(width=0.36, height=max(b * 1.1, 0.02), fill_color=B_COL, fill_opacity=0.9, stroke_width=0)
            base = cc.get_center() + UP * -0.05
            ba.move_to(base + LEFT * 0.3, aligned_edge=DOWN)
            bb.move_to(base + RIGHT * 0.3, aligned_edge=DOWN)
            la = txt("A", 13, A_COL, BOLD).next_to(ba, DOWN, buff=0.08).set_y(base[1] - 0.15)
            lb = txt("B", 13, B_COL, BOLD).next_to(bb, DOWN, buff=0.08).set_y(base[1] - 0.15)
            nm = txt(f"extract {i + 1}", 14, MUTED).next_to(cc.get_top(), DOWN, buff=0.15)
            meter_bg = RoundedRectangle(width=1.45, height=0.13, corner_radius=0.06, fill_color=LINE, fill_opacity=1, stroke_width=0)
            meter_bg.next_to(cc.get_bottom(), UP, buff=0.32)
            cards.add(VGroup(cc, ba, bb, la, lb, nm, meter_bg))
        sch = txt("schematic", 14, FAINT, slant=ITALIC).next_to(cards, DOWN, aligned_edge=RIGHT, buff=0.15)
        self.play(FadeIn(n3), LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cards], lag_ratio=0.08), FadeIn(sch), run_time=1.2)
        lab = txt("how far would this pull the explanations apart?", 18, MUTED).next_to(cards, UP, buff=0.3)
        self.play(FadeIn(lab), run_time=0.5)
        meters = VGroup()
        for c, s in zip(cards, scores):
            mbg = c[6]
            m = RoundedRectangle(width=max(1.45 * s, 0.02), height=0.13, corner_radius=0.06, fill_color=B_COL, fill_opacity=1,
                                 stroke_width=0).move_to(mbg, aligned_edge=LEFT)
            meters.add(m)
        self.play(LaggedStart(*[GrowFromEdge(m, LEFT) for m in meters], lag_ratio=0.15), run_time=1.6)
        best = SurroundingRectangle(cards[3], color=GOOD, buff=0.06, corner_radius=0.2, stroke_width=3)
        self.play(Create(best), run_time=0.5)

        # --- recompute
        self.at("recompute")
        picked = chip("assayed", GOOD, 13).next_to(cards[3], DOWN, buff=0.1)
        self.play(cards[3].animate.set_opacity(0.35), meters[3].animate.set_opacity(0.2), FadeOut(best), FadeIn(picked), run_time=0.6)
        red = chip("redundant", BAD, 13).next_to(cards[5], DOWN, buff=0.1)
        new = [0.12, 0.08, 0.81, 0.0, 0.18, 0.09]
        anims = [m.animate.stretch_to_fit_width(max(1.45 * s, 0.02), about_edge=LEFT) for m, s in zip(meters, new) if True]
        self.play(*anims, FadeIn(red), run_time=1.2)
        best2 = SurroundingRectangle(cards[2], color=GOOD, buff=0.06, corner_radius=0.2, stroke_width=3)
        self.play(Create(best2), run_time=0.5)
        goal = txt("Find the extract where the suspects come apart.", 26, INK, BOLD, font=DISPLAY).to_edge(DOWN, buff=1.05)
        self.at_word("goal", "recompute", -0.2)
        self.play(FadeOut(sch), FadeIn(goal, shift=UP * 0.15), run_time=0.7)
        self.finish()


# ====================================================================== E3
class E3Example(ExplainerScene):
    SID = "e3_example"

    def construct(self):
        self.start_narration()
        head = heading("Measured ENPKG data", "One episode, three assays")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.7)
        ca = VGroup(txt("A", 18, ON, BOLD), txt("methyl xanthone · m/z 353.102", 18, A_COL, BOLD))
        cb = VGroup(txt("B", 18, ON, BOLD), txt("rotenoid · m/z 393.133", 18, B_COL, BOLD))
        chips = VGroup()
        for g, col in [(ca, A_COL), (cb, B_COL)]:
            badge = Circle(radius=0.2, fill_color=col, fill_opacity=1, stroke_width=0)
            g[0].move_to(badge)
            chips.add(VGroup(VGroup(badge, g[0]), g[1]).arrange(RIGHT, buff=0.2))
        chips.arrange(RIGHT, buff=0.8).next_to(head, DOWN, aligned_edge=LEFT, buff=0.35)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in chips], lag_ratio=0.4), run_time=1.0)

        # table of extracts (left)
        tab_x = -6.55
        hdr = VGroup(txt("extract", 15, FAINT, BOLD), txt("A", 15, A_COL, BOLD), txt("B", 15, B_COL, BOLD),
                     txt("T. cruzi", 15, FAINT, BOLD))
        col_x = [0, 3.9, 5.1, 6.35]
        y0 = 0.85
        for h, cx in zip(hdr, col_x):
            h.move_to([tab_x + cx, y0, 0], aligned_edge=LEFT)
        self.rows = []

        def row(name, a, b, resp, i, note=None):
            y = y0 - 0.5 - i * 0.48
            nm = txt(name, 17, INK, MEDIUM, slant=ITALIC).move_to([tab_x, y, 0], aligned_edge=LEFT)
            va = mono(f"{a:.3f}", 16, A_COL if a > 0 else FAINT).move_to([tab_x + col_x[1], y, 0], aligned_edge=LEFT)
            vb = mono(f"{b:.3f}", 16, B_COL if b > 0 else FAINT).move_to([tab_x + col_x[2], y, 0], aligned_edge=LEFT)
            vr = mono("—" if resp is None else f"{resp:.3f}", 16, INK).move_to([tab_x + col_x[3], y, 0], aligned_edge=LEFT)
            return VGroup(nm, va, vb, vr)

        seeds = [("Desmodium heterophyllum", 0.0, 0.197, 1.174), ("Cnestis palala · roots", 0.0, 0.463, 1.121),
                 ("Pachyrhizus erosus · leaves", 0.003, 0.0, 1.122)]
        self.at("seeds")
        srows = VGroup(*[row(*s, i) for i, s in enumerate(seeds)])
        stag = txt("starting hits", 14, GOOD, BOLD).next_to(hdr, UP, aligned_edge=LEFT, buff=0.2)
        self.play(FadeIn(hdr), FadeIn(stag), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in srows[:2]], lag_ratio=0.3), run_time=1.2)
        self.at_word("third", "seeds", -0.2)
        self.play(FadeIn(srows[2], shift=RIGHT * 0.2), run_time=0.6)
        hl = SurroundingRectangle(srows[2], color=A_COL, buff=0.1, corner_radius=0.08)
        self.play(Create(hl), Indicate(srows[2][1], color=A_COL, scale_factor=1.3), run_time=0.9)

        # posterior bars (right)
        self.at("tie")
        pc = card(5.3, 3.3).move_to(RIGHT * 4.0 + DOWN * 0.55)
        ptitle = txt("posterior", 15, FAINT, BOLD).next_to(pc.get_corner(UL), DR, buff=0.25)
        bars = ProbBars(["A alone", "B alone", "Both", "Neither"], [A_COL, B_COL, BOTH, NEITHER], [0.0, 0.397, 0.603, 0.0],
                        width=2.3, row_h=0.62, label_w=1.45, px=17).move_to(pc).shift(DOWN * 0.15 + LEFT * 0.15)
        self.play(FadeIn(pc), FadeIn(ptitle), FadeIn(bars), FadeOut(hl), run_time=0.8)

        # pick
        self.at("pick")
        pick = row("Uncarina decaryi · green stems", 0.102, 0.0, None, 3)
        ptag = chip("adaptive contrast pick", GOOD, 13).next_to(pick, DOWN, aligned_edge=LEFT, buff=0.12)
        self.play(FadeIn(pick, shift=RIGHT * 0.2), FadeIn(ptag), run_time=0.7)
        self.at_word("thirty", "pick", -0.1)
        x36 = txt("≈ 36×", 17, A_COL, BOLD).next_to(pick[1], UP, buff=0.08).shift(RIGHT * 0.25)
        arrow36 = Arrow(srows[2][1].get_bottom(), pick[1].get_top(), color=A_COL, buff=0.05, stroke_width=2, max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(arrow36), Indicate(pick[1], color=A_COL, scale_factor=1.3), run_time=0.8)

        # reveal: predicted vs observed
        self.at("reveal")
        pred = VGroup(txt("if A acts:  ≈ 0.99", 16, A_COL, MEDIUM), txt("if B acts:  ≈ 0.05", 16, B_COL, MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        pred.next_to(ptag, RIGHT, buff=0.5)
        self.play(FadeOut(arrow36), FadeIn(pred, shift=LEFT * 0.1), run_time=0.6)
        self.at_word("inactive", "reveal", -0.3)
        obs = mono("0.001", 16, INK, BOLD).move_to(pick[3], aligned_edge=LEFT)
        self.play(Transform(pick[3], obs), Flash(pick[3].get_center(), color=GOOD, flash_radius=0.4), run_time=0.6)
        inact = chip("inactive", MUTED, 13).next_to(pick[3], RIGHT, buff=0.15)
        self.play(FadeIn(inact), run_time=0.3)

        # jump
        self.at("jump")
        self.play(*bars.to([0.0, 0.999, 0.001, 0.0]), run_time=1.8, rate_func=smooth)
        self.play(Circumscribe(bars[1], color=B_COL), run_time=0.9)

        # verdict
        self.at("verdict")
        r2 = row("Uncarina decaryi · bark", 0.075, 0.0, 0.0, 4)
        r3 = row("Carya kweichowensis · leaves", 0.056, 0.0, 0.0, 5)
        self.play(FadeOut(ptag), FadeOut(pred), FadeOut(inact), FadeIn(r2, shift=RIGHT * 0.2), run_time=0.6)
        self.play(FadeIn(r3, shift=RIGHT * 0.2), *bars.to([0.0, 1.0, 0.0, 0.0]), run_time=0.6)
        ver = VGroup(txt("Nominate B · rotenoid", 22, B_COL, BOLD),
                     txt("not the host-toxicity driver", 16, GOOD, MEDIUM)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        vbg = card(ver.width + 0.5, ver.height + 0.4, stroke=B_COL, fill=PANEL2)
        verdict = VGroup(vbg, ver.move_to(vbg)).next_to(pc, DOWN, buff=0.2).align_to(pc, LEFT)
        self.at_word("nominates", "verdict", -0.2)
        self.play(FadeIn(verdict, shift=UP * 0.15), run_time=0.6)

        # baseline
        self.at("baseline")
        base = VGroup(txt("strongest-first, same budget:", 15, MUTED), txt("shortlist · both or B", 17, INK, BOLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        base.next_to(verdict, RIGHT, buff=0.3).shift(LEFT * 0.0)
        if base.get_right()[0] > 6.9:
            base.next_to(verdict, DOWN, aligned_edge=LEFT, buff=0.15)
        self.play(FadeIn(base, shift=LEFT * 0.15), run_time=0.6)
        self.finish()


# ====================================================================== E4
class E4Selectivity(ExplainerScene):
    SID = "e4_selectivity"

    def construct(self):
        self.start_narration()
        head = heading("The contribution", "Selectivity, not potency")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)
        lead = VGroup(txt("most potent", 40, INK, MEDIUM), txt("≠", 40, ACCENT, MEDIUM),
                      txt("best candidate", 40, INK, MEDIUM)).arrange(RIGHT, buff=0.35).move_to(DOWN * 0.3)
        self.play(FadeIn(lead[0], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(lead[1:], shift=UP * 0.1), run_time=0.6)

        # --- SI chart (log scale)
        self.at("si")
        self.play(FadeOut(lead), run_time=0.4)
        L = 6.0
        x0 = -3.2
        axis = Line([x0, -2.0, 0], [x0 + L, -2.0, 0], color=LINE, stroke_width=2)
        ticks = VGroup()
        for p in range(0, 5):
            x = x0 + L * p / 4
            ticks.add(Line([x, -2.0, 0], [x, -2.1, 0], color=FAINT, stroke_width=2),
                      txt(f"{10 ** p:,}", 14, FAINT).move_to([x, -2.35, 0]))
        axt = txt("selectivity index  (host toxicity ÷ parasite potency, log scale)", 15, MUTED).next_to(axis, DOWN, buff=0.55)
        data = [("rotenone", 51.7, BAD), ("deguelin", 1148.5, GOOD), ("tephrosin", 1937.0, GOOD)]
        rows = VGroup()
        for i, (n, v, col) in enumerate(data):
            y = 0.2 - i * 0.8
            bar = Rectangle(width=L * np.log10(v) / 4, height=0.42, fill_color=col, fill_opacity=0.85, stroke_width=0)
            bar.move_to([x0, y, 0], aligned_edge=LEFT)
            nm = txt(n, 20, INK, BOLD).next_to([x0, y, 0], LEFT, buff=0.3)
            val = txt(f"{v:,.1f}", 20, col, BOLD).next_to(bar, RIGHT, buff=0.2)
            rows.add(VGroup(bar, nm, val))
        self.play(Create(axis), FadeIn(ticks), FadeIn(axt), run_time=0.6)
        self.play(GrowFromEdge(rows[0][0], LEFT), FadeIn(rows[0][1:]), run_time=0.8)
        potent = chip("most potent · least selective", BAD, 14).next_to(rows[0][2], RIGHT, buff=0.3)
        self.play(FadeIn(potent), run_time=0.4)
        self.at_word("against", "si", -0.2)
        self.play(*[GrowFromEdge(r[0], LEFT) for r in rows[1:]], *[FadeIn(r[1:]) for r in rows[1:]], run_time=1.0)

        # --- decoys
        self.at("decoys")
        self.play(FadeOut(VGroup(axis, ticks, axt, rows, potent)), run_time=0.5)
        sub = txt("ENPKG extracts with > 80% T. cruzi inhibition", 19, MUTED).move_to(UP * 1.05)
        dots = VGroup(*[Circle(radius=0.3, fill_color=INK, fill_opacity=0.85, stroke_width=0) for _ in range(15)])
        dots.arrange_in_grid(3, 5, buff=0.35).move_to(LEFT * 2.2 + DOWN * 0.75)
        self.play(FadeIn(sub), LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.04), run_time=1.0)
        tox = [1, 3, 4, 7, 9, 12, 13]
        self.at_word("toxic", "decoys", -0.3)
        self.play(*[dots[i].animate.set_fill(BAD) for i in tox],
                  *[dots[i].animate.set_fill(GOOD) for i in range(15) if i not in tox], run_time=0.9)
        leg = VGroup(VGroup(txt("7", 46, BAD, BOLD, font=DISPLAY), txt("also toxic to host cells", 19, INK)).arrange(RIGHT, buff=0.25),
                     VGroup(txt("8", 46, GOOD, BOLD, font=DISPLAY), txt("selective", 19, INK)).arrange(RIGHT, buff=0.25)).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        leg.next_to(dots, RIGHT, buff=1.0)
        real = txt("real screen data", 14, FAINT, slant=ITALIC).next_to(leg, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(FadeIn(leg, shift=LEFT * 0.2), FadeIn(real), run_time=0.6)

        # --- free second channel
        self.at("free")
        self.play(FadeOut(VGroup(sub, dots, leg, real)), run_time=0.5)
        v = vial(2.0, 1.0).move_to(LEFT * 4.2 + DOWN * 0.6)
        rv = chip("1 reveal", GOOD, 16).next_to(v, DOWN, buff=0.3)
        o1 = card(4.3, 1.0, stroke=B_COL).move_to(RIGHT * 1.6 + UP * 0.2)
        o2 = card(4.3, 1.0, stroke=BAD).move_to(RIGHT * 1.6 + DOWN * 1.4)
        t1 = txt("T. cruzi inhibition", 20, INK, BOLD).move_to(o1)
        t2 = txt("L6 host-cell toxicity", 20, INK, BOLD).move_to(o2)
        a1 = Arrow(v.get_right(), o1.get_left(), color=B_COL, buff=0.2, stroke_width=4)
        a2 = Arrow(v.get_right(), o2.get_left(), color=BAD, buff=0.2, stroke_width=4)
        self.play(FadeIn(v), FadeIn(rv), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(o1), FadeIn(t1), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(o2), FadeIn(t2), run_time=0.6)
        zero = VGroup(txt("+0", 60, GOOD, BOLD, font=DISPLAY), txt("extra assays", 18, MUTED)).arrange(DOWN, buff=0.05).next_to(VGroup(o1, o2), RIGHT, buff=0.7)
        self.at_word("no", "free", -0.2)
        self.play(FadeIn(zero, scale=0.8), run_time=0.6)

        # --- benchmark bars
        self.at("bench")
        self.play(FadeOut(VGroup(v, rv, o1, o2, t1, t2, a1, a2, zero)), run_time=0.5)
        legend = VGroup(VGroup(Square(0.22, fill_color=NEITHER, fill_opacity=1, stroke_width=0), txt("potency-only", 17, INK)).arrange(RIGHT, buff=0.15),
                        VGroup(Square(0.22, fill_color=GOOD, fill_opacity=1, stroke_width=0), txt("selectivity-aware (2 channels)", 17, INK)).arrange(RIGHT, buff=0.15)
                        ).arrange(RIGHT, buff=0.6).next_to(head, DOWN, aligned_edge=LEFT, buff=0.4)
        semi = txt("semi-synthetic benchmark · 952 episodes · 238 pairs", 15, FAINT).next_to(legend, RIGHT, buff=0.6)

        def panel(title, vals, ymax, fmt, cx):
            h = 2.6
            bars = VGroup()
            for j, (vv, col) in enumerate(zip(vals, [NEITHER, GOOD])):
                b = Rectangle(width=1.1, height=max(vv / ymax * h, 0.02), fill_color=col, fill_opacity=0.95, stroke_width=0)
                b.move_to([cx - 0.75 + j * 1.5, -2.25, 0], aligned_edge=DOWN)
                lab = txt(fmt(vv), 22, INK, BOLD).next_to(b, UP, buff=0.12)
                bars.add(VGroup(b, lab))
            base = Line([cx - 1.6, -2.25, 0], [cx + 1.6, -2.25, 0], color=LINE, stroke_width=2)
            t = txt(title, 19, MUTED, MEDIUM).move_to([cx, 0.85, 0])
            return VGroup(t, base, bars)

        p1 = panel("developable accuracy", [32.7, 32.7], 40, lambda v: f"{v:.1f}%", -3.3)
        p2 = panel("wasted isolations / 100 episodes", [32.35, 0.21], 40, lambda v: f"{v:.2f}", 2.6)
        self.play(FadeIn(legend), FadeIn(semi), FadeIn(p1[:2]), run_time=0.6)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in p1[2]], *[FadeIn(b[1]) for b in p1[2]], run_time=0.9)
        same = chip("identical", INK, 14).next_to(p1[2], RIGHT, buff=0.3).shift(UP * 0.9)
        self.play(FadeIn(same), run_time=0.4)
        self.at("wasted")
        self.play(FadeIn(p2[:2]), GrowFromEdge(p2[2][0][0], DOWN), FadeIn(p2[2][0][1]), run_time=0.8)
        self.at_word("0.21", "wasted", -0.2)
        self.play(GrowFromEdge(p2[2][1][0], DOWN), FadeIn(p2[2][1][1]), run_time=0.6)
        big = txt("154× fewer", 40, GOOD, BOLD, font=DISPLAY).next_to(p2[2], RIGHT, buff=0.35).shift(UP * 0.6)
        if big.get_right()[0] > 6.9:
            big.next_to(p2[0], UP, buff=0.3)
        self.at_word("154", "wasted", -0.2)
        self.play(FadeIn(big, scale=0.8), run_time=0.6)

        # --- caveat
        self.at("caveat")
        cav = VGroup(chip("assumed 50% cytotoxic prevalence", A_COL, 15), chip("supported in simulation · not validated", A_COL, 15)).arrange(RIGHT, buff=0.3)
        cav.to_edge(DOWN, buff=0.95)
        self.play(FadeIn(cav, shift=UP * 0.15), run_time=0.6)
        self.finish()


# ====================================================================== E5
class E5Benchmark(ExplainerScene):
    SID = "e5_benchmark"

    def construct(self):
        self.start_narration()
        head = heading("Evaluation", "What the benchmark shows")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)
        stats = VGroup(*[VGroup(txt(a, 50, INK, BOLD, font=DISPLAY), txt(b, 17, MUTED)).arrange(DOWN, buff=0.08)
                         for a, b in [("952", "semi-synthetic episodes"), ("238", "real compound pairs")]]).arrange(RIGHT, buff=1.2)
        stats.move_to(UP * 0.6)
        rr = VGroup(chip("real · abundances, co-occurrence", GOOD, 16), chip("simulated · response", A_COL, 16)).arrange(RIGHT, buff=0.4).next_to(stats, DOWN, buff=0.6)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in stats], lag_ratio=0.3), run_time=1.0)
        self.at_word("abundances", "setup", -0.3)
        self.play(FadeIn(rr[0]), run_time=0.4)
        self.at_word("simulated", "setup", -0.3)
        self.play(FadeIn(rr[1]), run_time=0.4)

        # --- hard stratum chart
        self.at("hard")
        self.play(FadeOut(VGroup(stats, rr)), run_time=0.5)
        items = [("no assays", 8.6, 0.0, 24.1, NEITHER), ("random 3", 8.6, 0.0, 24.1, NEITHER),
                 ("strongest-first", 19.0, 6.9, 34.4, MUTED), ("adaptive contrast", 19.0, 6.9, 34.4, ACCENT)]
        chart, cols = vbar_chart(items, 40, h=3.3, bar_w=1.15, gap=0.85)
        chart.move_to(LEFT * 1.7 + DOWN * 0.55)
        sub = txt("hard stratum · 16 pairs · correct nominations, 95% CI", 16, MUTED).next_to(chart, UP, buff=0.35).align_to(chart, LEFT)
        self.play(FadeIn(chart[0]), FadeIn(sub), run_time=0.4)
        for c in cols:
            c.save_state()
        self.play(GrowFromEdge(cols[0][0], DOWN), FadeIn(cols[0][1:]), run_time=0.7)
        self.at_word("random", "hard", -0.2)
        self.play(GrowFromEdge(cols[1][0], DOWN), FadeIn(cols[1][1:]), run_time=0.7)

        self.at("choose")
        self.play(GrowFromEdge(cols[3][0], DOWN), FadeIn(cols[3][1:]), run_time=0.8)
        dbl = txt("≈ 2×", 30, ACCENT, BOLD, font=DISPLAY).next_to(cols[3], RIGHT, buff=0.3)
        self.play(FadeIn(dbl), run_time=0.4)

        self.at("tie")
        self.play(FadeOut(dbl), GrowFromEdge(cols[2][0], DOWN), FadeIn(cols[2][1:]), run_time=0.8)
        brace = BraceBetweenPoints(cols[2][0].get_corner(UL) + UP * 1.45, cols[3][0].get_corner(UR) + UP * 1.45, UP, color=INK)
        tie = VGroup(txt("tie", 24, INK, BOLD), txt("margin +0.0 [0.0, 0.0]", 15, MUTED)).arrange(DOWN, buff=0.05).next_to(brace, UP, buff=0.1)
        self.play(GrowFromCenter(brace), FadeIn(tie), run_time=0.7)
        claim = VGroup(txt("we do not claim to beat", 19, MUTED), txt("current practice", 19, MUTED),
                       txt("value is in what", 24, INK, BOLD), txt("it nominates", 24, INK, BOLD)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        claim.to_edge(RIGHT, buff=0.6).shift(DOWN * 0.3)
        self.at_word("claim", "tie", -0.2)
        self.play(FadeIn(claim[:2], shift=LEFT * 0.2), run_time=0.5)
        self.at_word("value", "tie", -0.2)
        self.play(FadeIn(claim[2:], shift=LEFT * 0.2), run_time=0.5)

        # --- abstain
        self.at("abstain")
        self.play(FadeOut(VGroup(chart, sub, brace, tie, claim)), run_time=0.5)
        c1 = card(5.4, 2.6, stroke=GOOD).move_to(LEFT * 3.1 + DOWN * 0.4)
        c1t = VGroup(txt("100%", 64, GOOD, BOLD, font=DISPLAY), txt("precision when it nominates", 18, INK),
                     txt("semi-synthetic benchmark", 14, FAINT)).arrange(DOWN, buff=0.12).move_to(c1)
        c2 = card(5.4, 2.6, stroke=A_COL).move_to(RIGHT * 3.1 + DOWN * 0.4)
        c2t = VGroup(txt("abstains", 50, A_COL, BOLD, font=DISPLAY), txt("on the full real library", 18, INK),
                     txt("top score 0.468, below the 0.6 bar", 14, FAINT)).arrange(DOWN, buff=0.14).move_to(c2)
        self.play(FadeIn(c1), FadeIn(c1t, shift=UP * 0.1), run_time=0.7)
        self.at_word("library", "abstain", -0.6)
        self.play(FadeIn(c2), FadeIn(c2t, shift=UP * 0.1), run_time=0.7)

        # --- gaudry
        self.at("gaudry")
        cite = VGroup(txt("Rotenoid finding: Gaudry et al., RSC Advances 2025", 21, INK, BOLD),
                      txt("reproduced as a pipeline check, not claimed as ours", 17, MUTED)).arrange(DOWN, buff=0.1)
        cbg = card(cite.width + 0.7, cite.height + 0.5, stroke=LINE, fill=PANEL2)
        g = VGroup(cbg, cite.move_to(cbg)).to_edge(DOWN, buff=0.9)
        self.play(VGroup(c1, c1t, c2, c2t).animate.shift(UP * 0.5), FadeIn(g, shift=UP * 0.15), run_time=0.7)
        self.finish()


# ====================================================================== E6
class E6Ethno(ExplainerScene):
    SID = "e6_ethno"

    def construct(self):
        self.start_narration()
        head = heading("Ethnobotany", "Grounded in traditional knowledge")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)

        # --- jicama plant
        ground = Line(LEFT * 2.2, RIGHT * 2.2, color=FAINT, stroke_width=2).move_to(LEFT * 3.3 + DOWN * 0.6)
        stem = CubicBezier(ground.get_center(), ground.get_center() + UP * 0.8 + RIGHT * 0.2,
                           ground.get_center() + UP * 1.4 + LEFT * 0.2, ground.get_center() + UP * 2.1, color=INK, stroke_width=3)
        leaves = VGroup(*[Ellipse(width=0.9, height=0.38, fill_color=PALE, fill_opacity=1, stroke_color=INK, stroke_width=2).rotate(a).move_to(stem.point_from_proportion(p) + off)
                          for a, p, off in [(0.5, 0.45, RIGHT * 0.45), (-0.5, 0.6, LEFT * 0.45), (0.4, 0.85, RIGHT * 0.4), (-0.4, 0.95, LEFT * 0.35)]])
        pod = VGroup(*[Dot(radius=0.07, color=INK) for _ in range(4)]).arrange(RIGHT, buff=0.04).move_to(stem.get_end() + RIGHT * 0.65 + UP * 0.05)
        tuber = Ellipse(width=1.4, height=1.1, fill_color=SURFACE, fill_opacity=1, stroke_color=INK, stroke_width=2.5).move_to(ground.get_center() + DOWN * 0.75)
        root = VGroup(tuber, Line(tuber.get_bottom(), tuber.get_bottom() + DOWN * 0.3, color=INK, stroke_width=2.5))
        plant = VGroup(ground, stem, leaves, pod, root)
        name = VGroup(txt("Pachyrhizus erosus", 22, INK, BOLD, slant=ITALIC), txt("jicama", 17, MUTED)).arrange(DOWN, buff=0.06).next_to(ground, UP, buff=2.6)
        self.play(Create(ground), Create(stem), FadeIn(root), run_time=0.8)
        self.play(LaggedStart(*[GrowFromCenter(l) for l in leaves], lag_ratio=0.15), FadeIn(pod), FadeIn(name), run_time=0.8)
        food = chip("root · eaten as food", GOOD, 16).next_to(tuber, RIGHT, buff=0.6)
        poison = chip("seeds & leaves · insecticide, fish poison", BAD, 16).next_to(leaves, RIGHT, buff=0.5).shift(UP * 0.2)
        self.at_word("root", "jicama", -0.2)
        self.play(FadeIn(food, shift=LEFT * 0.2), run_time=0.5)
        self.at_word("seeds", "jicama", -0.2)
        self.play(FadeIn(poison, shift=LEFT * 0.2), run_time=0.5)

        # --- gradient table
        self.at("gradient")
        self.play(VGroup(plant, name).animate.scale(0.75).to_edge(LEFT, buff=0.7).shift(DOWN * 0.3), FadeOut(food), FadeOut(poison), run_time=0.7)
        organs = [("leaves", 65.5, 112.2), ("woody stems", 11.6, 53.7), ("roots", 4.0, 0.0)]
        tx0 = -1.6
        hdr = VGroup(txt("organ", 15, FAINT, BOLD).move_to([tx0, 1.05, 0], aligned_edge=LEFT),
                     txt("rotenoid share", 15, B_COL, BOLD).move_to([tx0 + 2.4, 1.05, 0], aligned_edge=LEFT),
                     txt("T. cruzi inhibition", 15, BAD, BOLD).move_to([tx0 + 5.4, 1.05, 0], aligned_edge=LEFT))
        self.play(FadeIn(hdr), run_time=0.4)
        rows = VGroup()
        for i, (o, s, inh) in enumerate(organs):
            y = 0.3 - i * 0.95
            nm = txt(o, 20, INK, BOLD).move_to([tx0, y, 0], aligned_edge=LEFT)
            b1 = Rectangle(width=max(s / 100 * 2.2, 0.02), height=0.36, fill_color=B_COL, fill_opacity=0.9, stroke_width=0).move_to([tx0 + 2.4, y, 0], aligned_edge=LEFT)
            v1 = txt(f"{s:.1f}%", 17, INK, BOLD).next_to(b1, RIGHT, buff=0.12)
            b2 = Rectangle(width=max(min(inh, 112.2) / 112.2 * 2.0, 0.02), height=0.36, fill_color=BAD, fill_opacity=0.9, stroke_width=0).move_to([tx0 + 5.4, y, 0], aligned_edge=LEFT)
            v2 = txt(f"{inh:.1f}%", 17, INK, BOLD).next_to(b2, RIGHT, buff=0.12)
            rows.add(VGroup(nm, b1, v1, b2, v2))
        for i, o in enumerate(["leaves", "woody", "roots"]):
            self.at_word(o, "gradient", -0.25)
            r = rows[i]
            self.play(FadeIn(r[0]), GrowFromEdge(r[1], LEFT), GrowFromEdge(r[3], LEFT), FadeIn(r[2]), FadeIn(r[4]), run_time=0.7)
        note = txt("one plant · monotonic under both annotation tools", 15, FAINT).next_to(rows, DOWN, aligned_edge=LEFT, buff=0.35)
        self.play(FadeIn(note), run_time=0.4)

        # --- melochia
        self.at("melochia")
        self.play(FadeOut(VGroup(plant, name, hdr, rows, note)), run_time=0.5)
        sp = VGroup(*[Circle(radius=0.32, fill_color=A_COL if i < 3 else PANEL2, fill_opacity=1, stroke_color=A_COL if i < 3 else LINE, stroke_width=2)
                      for i in range(6)]).arrange(RIGHT, buff=0.25)
        spl = txt("3 of 6 active species carry relevant traditional use", 19, INK, MEDIUM).next_to(sp, DOWN, buff=0.3)
        sgrp = VGroup(sp, spl).move_to(UP * 0.65)
        self.play(LaggedStart(*[GrowFromCenter(s) for s in sp], lag_ratio=0.1), FadeIn(spl), run_time=1.0)
        mc = card(8.2, 1.8, stroke=A_COL).next_to(sgrp, DOWN, buff=0.45)
        mt = VGroup(VGroup(txt("Melochia umbellata", 22, INK, BOLD, slant=ITALIC), txt("Cameroonian antimalarial", 17, MUTED)).arrange(RIGHT, buff=0.35),
                    VGroup(chip("0 rotenoids", B_COL, 14), chip("89.9% inhibition", BAD, 14), chip("a lead, not an identification", A_COL, 14)).arrange(RIGHT, buff=0.2)
                    ).arrange(DOWN, buff=0.3).move_to(mc)
        self.at_word("Melochia", "melochia", -0.2)
        self.play(FadeIn(mc), FadeIn(mt, shift=UP * 0.1), run_time=0.7)

        # --- ethics
        self.at("ethics")
        self.play(FadeOut(VGroup(sgrp, mc, mt)), run_time=0.5)
        items = VGroup(
            VGroup(txt("✕", 26, BAD, BOLD), txt("Rejected an unsupported traditional-use claim (malaria, P. pulcher)", 20, INK)).arrange(RIGHT, buff=0.35),
            VGroup(txt("◆", 22, A_COL, BOLD), txt("No claim of ownership over traditional knowledge", 20, INK)).arrange(RIGHT, buff=0.35),
            VGroup(txt("◆", 22, A_COL, BOLD), txt("Nagoya / ABS obligations attach to collection and any commercial use", 20, INK)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to(DOWN * 0.3)
        for i, it in enumerate(items):
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.5)
            if i == 0:
                self.at_word("ownership", "ethics", -0.4)
        self.finish()


# ====================================================================== E7
class E7Close(ExplainerScene):
    SID = "e7_close"
    TAIL = 2.0

    def construct(self):
        self.start_narration()
        l1 = txt("Occurrence is not abundance.", 50, INK, BOLD, font=DISPLAY)
        l2 = txt("Association is not causation.", 50, MUTED, BOLD, font=DISPLAY)
        motto = VGroup(l1, l2).arrange(DOWN, buff=0.25).move_to(UP * 0.6)
        self.play(FadeIn(l1, shift=UP * 0.2), run_time=0.8)
        self.at_word("Association", "motto", -0.2)
        self.play(FadeIn(l2, shift=UP * 0.2), run_time=0.8)

        self.at("summary")
        self.play(motto.animate.scale(0.6).to_edge(UP, buff=0.8), run_time=0.6)
        pts = VGroup(*[VGroup(Dot(radius=0.08, color=c), txt(s, 24, INK, MEDIUM)).arrange(RIGHT, buff=0.3)
                       for c, s in [(B_COL, "chooses the assays that pull candidates apart"),
                                    (BOTH, "says “both” or “neither” when that is the honest answer"),
                                    (BAD, "vetoes cytotoxic decoys before weeks at the bench")]]).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        pts.move_to(DOWN * 0.2)
        for key, p in zip(["pull", "both", "vetoes"], pts):
            self.at_word(key, "summary", -0.3)
            self.play(FadeIn(p, shift=RIGHT * 0.2), run_time=0.5)

        self.at("thanks", -0.4)
        self.play(FadeOut(VGroup(motto, pts)), run_time=0.5)
        brand = VGroup(logo(1.6), txt("DECOUPLE", 54, INK, BOLD, font=DISPLAY)).arrange(RIGHT, buff=0.35)
        tag = txt("Budget-constrained experiment selection for natural-product dereplication", 19, MUTED).next_to(brand, DOWN, buff=0.35)
        foot = txt("EthnoHack 2026 · research prototype · not clinically validated", 15, FAINT).next_to(tag, DOWN, buff=0.6)
        self.play(FadeIn(brand, scale=0.9), FadeIn(tag), FadeIn(foot), run_time=0.9)
        self.finish(fade=False)


SCENES = ["E1Problem", "E2Method", "E3Example", "E4Selectivity", "E5Benchmark", "E6Ethno", "E7Close"]
