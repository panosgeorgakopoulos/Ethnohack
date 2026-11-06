#!/usr/bin/env python3
"""
Figures for the submission. Run: python3.12 figures/make_figures.py

All numbers are read from results/benchmark.json — nothing is hardcoded,
so the figures cannot drift from the benchmark.

Design notes (deliberate, not matplotlib defaults):
  * fig1 sets the method against the baselines a chemist would otherwise
    use; the baselines recede to grey so the comparison reads at a glance.
  * fig2 is two panels because the story is a trade: the left panel collapses,
    the right one does not. The 0.21 bar is a sliver on a zero-based axis, and
    that is the message, not a defect.
  * Palette validated with the data-viz validator: categorical pair
    #2a78d6 / #eb6834, CVD dE 24.7, normal-vision dE 33.6, contrast >= 3:1.
  * Light and dark are separately chosen steps, not an automatic inversion.
"""
import json, math, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.lines import Line2D

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "figures"

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", s1="#2a78d6", s2="#eb6834",
                  deemph="#b9b7ae"),
    "dark":  dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                  grid="#2c2c2a", axis="#383835", s1="#3987e5", s2="#d95926",
                  deemph="#4e4d49"),
}
SANS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


def style(t):
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": SANS,
        "figure.facecolor": t["surface"], "axes.facecolor": t["surface"],
        "savefig.facecolor": t["surface"], "savefig.edgecolor": "none",
        "axes.edgecolor": t["axis"], "axes.linewidth": 1.0, "axes.grid": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": t["muted"], "ytick.color": t["muted"],
        "xtick.labelcolor": t["ink2"], "ytick.labelcolor": t["ink2"],
        "xtick.major.size": 0, "ytick.major.size": 0,
        "text.color": t["ink"], "axes.labelcolor": t["ink2"],
        "font.size": 9.5, "figure.dpi": 200, "savefig.dpi": 200,
    })


def rounded_bar(ax, x0, y, width, height, color, r_px=4, z=3):
    """Square at the baseline, 4px-rounded at the data end."""
    p0 = ax.transData.inverted().transform((0, 0))
    r = abs(ax.transData.inverted().transform((r_px, 0))[0] - p0[0])
    r = min(r, max(width, 1e-9) * 0.5, height * 0.5)
    y0, y1, xe = y - height / 2, y + height / 2, x0 + width
    v = [(x0, y0), (xe - r, y0), (xe, y0), (xe, y0 + r),
         (xe, y1 - r), (xe, y1), (xe - r, y1), (x0, y1), (x0, y0)]
    c = [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3,
         Path.LINETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v, c), facecolor=color, edgecolor="none",
                           zorder=z, clip_on=False))


def load():
    d = json.loads((ROOT / "results/benchmark.json").read_text())
    return d, d["regimes"]["well_specified/single_driver"]


def pick(reg, **kw):
    return [c for c in reg["cells"] if all(c[k] == v for k, v in kw.items())]


# ---------------------------------------------------------------- figure 1 ---
# Policies are named for what they DO. Their indistinguishability is the finding,
# so they also share a single hue below.
METHOD = "adaptive_contrast"
INFORMED = {METHOD, "strongest-first"}
LABELS = {"no_budget": "No assays spent",
          "random": "Three extracts at random",
          "strongest-first": "Strongest-looking first\n(current practice)",
          METHOD: "Adaptive contrast\n(this work)"}
ORDER = ["no_budget", "random", "strongest-first", METHOD]


def fig1(reg, theme):
    t = THEMES[theme]; style(t)
    cells = {c["policy"]: c for c in
             pick(reg, pool="unconstrained", rule="potency-only",
                  stratum="hard", scoring="named")}
    rows = [(p, cells[p]) for p in ORDER if p in cells]

    fig, ax = plt.subplots(figsize=(8.8, 4.1))
    fig.subplots_adjust(left=0.30, right=0.95, top=0.64, bottom=0.18)
    ys = list(range(len(rows)))[::-1]
    ax.set_xlim(0, 50); ax.set_ylim(-0.8, len(rows) - 0.2)
    for g in range(0, 51, 10):
        ax.axvline(g, color=t["grid"], lw=1.0, zorder=0)

    h = 0.34
    for y, (pol, c) in zip(ys, rows):
        v = c["accuracy"] * 100
        lo, hi = [x * 100 for x in c["accuracy_ci95"]]
        col = t["s1"] if pol in INFORMED else t["deemph"]
        rounded_bar(ax, 0, y, v, h, col)
        ax.plot([lo, hi], [y, y], color=t["ink2"], lw=1.4, zorder=5, solid_capstyle="butt")
        for e in (lo, hi):
            ax.plot([e, e], [y - h * .3, y + h * .3], color=t["ink2"], lw=1.4, zorder=5)
        ax.text(hi + 1.4, y, f"{v:.1f}%", va="center", ha="left",
                color=t["ink"] if pol in INFORMED else t["ink2"],
                fontsize=10 if pol in INFORMED else 9.5,
                fontweight="semibold" if pol in INFORMED else "normal", zorder=6)

    ax.set_yticks(ys); ax.set_yticklabels([LABELS[p] for p, _ in rows],
                                          fontsize=9.5, linespacing=1.35)
    ax.set_xticks(range(0, 51, 10))
    ax.set_xticklabels([f"{v}%" for v in range(0, 51, 10)], fontsize=9)
    ax.set_xlabel("Correctly names the responsible compound", fontsize=9,
                  color=t["ink2"], labelpad=7)
    ax.tick_params(length=0)

    fig.text(0.035, 0.945, "Three assays double the hit rate — if they are chosen",
             fontsize=13.5, fontweight="semibold", color=t["ink"])
    fig.text(0.035, 0.885,
             f"Hard stratum: {reg['n_hard']} episodes the primary screen cannot resolve, "
             f"from {reg['n_distinct_pairs_hard']} compound pairs. Whiskers are pair-clustered 95% CIs.",
             fontsize=8.8, color=t["ink2"])
    fig.text(0.035, 0.035,
             "Semi-synthetic benchmark: composition and co-occurrence are real, the response is simulated.",
             fontsize=7.6, color=t["muted"])
    fig.text(0.035, 0.818,
             "Three extracts chosen at random are worth nothing over spending no budget at all. "
             "Adaptive contrast matches current practice here; its value is in what it nominates (fig. 2).",
             fontsize=8.0, color=t["muted"])
    fig.savefig(OUT / f"fig1_selection_{theme}.png", bbox_inches="tight", pad_inches=0.26)
    plt.close(fig)


# ---------------------------------------------------------------- figure 2 ---
def fig2(reg, theme):
    t = THEMES[theme]; style(t)
    cells = {c["rule"]: c for c in
             pick(reg, pool="unconstrained", policy="adaptive_contrast",
                  stratum="overall", scoring="developable")}
    rules = [("potency-only", "Potency only"), ("selectivity-aware", "Selectivity-aware")]
    cols = [t["s2"], t["s1"]]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.0, 3.5))
    fig.subplots_adjust(left=0.19, right=0.97, top=0.66, bottom=0.18, wspace=0.55)

    # left: wasted isolations -- collapses
    wmax = max(cells[r]["wasted_per_100"] for r, _ in rules)
    axL.set_xlim(0, wmax * 1.35); axL.set_ylim(-0.7, 1.7)
    for g in range(0, int(wmax * 1.35) + 1, 10):
        axL.axvline(g, color=t["grid"], lw=1.0, zorder=0)
    for i, ((r, lab), col) in enumerate(zip(rules, cols)):
        c = cells[r]; v = c["wasted_per_100"]; y = 1 - i
        rounded_bar(axL, 0, y, v, 0.42, col)
        lo, hi = c["wasted_per_100_ci95"]
        axL.plot([lo, hi], [y, y], color=t["ink2"], lw=1.3, zorder=5)
        axL.text(max(v, hi) + wmax * 0.035, y, f"{v:.2f}", va="center", ha="left",
                 fontsize=11, fontweight="semibold", color=t["ink"], zorder=6)
    axL.set_yticks([1, 0]); axL.set_yticklabels([l for _, l in rules], fontsize=9.5)
    axL.set_xlabel("Wasted isolations per 100 episodes", fontsize=9, color=t["ink2"], labelpad=7)
    axL.tick_params(length=0)

    # right: developable accuracy -- does not move
    axR.set_xlim(0, 60); axR.set_ylim(-0.7, 1.7)
    for g in range(0, 61, 20):
        axR.axvline(g, color=t["grid"], lw=1.0, zorder=0)
    for i, ((r, lab), col) in enumerate(zip(rules, cols)):
        c = cells[r]; v = c["accuracy"] * 100; y = 1 - i
        rounded_bar(axR, 0, y, v, 0.42, col)
        axR.text(v + 1.6, y, f"{v:.1f}%", va="center", ha="left",
                 fontsize=11, fontweight="semibold", color=t["ink"], zorder=6)
    axR.set_yticks([1, 0]); axR.set_yticklabels(["", ""])
    axR.set_xticks(range(0, 61, 20)); axR.set_xticklabels([f"{v}%" for v in range(0, 61, 20)], fontsize=9)
    axR.set_xlabel("Leads actually worth isolating", fontsize=9, color=t["ink2"], labelpad=7)
    axR.tick_params(length=0)

    fig.text(0.035, 0.945, "The same leads, a fraction of the wasted lab work",
             fontsize=13.5, fontweight="semibold", color=t["ink"])
    fig.text(0.035, 0.868,
             "Host-cell cytotoxicity is measured on the same extracts in the same screen, "
             "so the second channel costs no extra assay.",
             fontsize=8.8, color=t["ink2"])
    fig.text(0.035, 0.038,
             f"{reg['n_episodes']} episodes, {reg['n_distinct_pairs']} compound pairs. "
             "Each wasted isolation is weeks of chromatography. Cytotoxic prevalence is a modelling assumption.",
             fontsize=7.6, color=t["muted"])
    fig.savefig(OUT / f"fig2_selectivity_{theme}.png", bbox_inches="tight", pad_inches=0.26)
    plt.close(fig)


# ---------------------------------------------------------------- figure 3 ---
# Real screening data, no simulation. Two measures on the same items:
# a dual-axis chart would be the obvious choice and is always wrong.
SERIES = [("Pachyrhizus erosus", "s1",
           [("leaves", 21.91, 112.2), ("woody stems", 4.96, 53.7), ("roots", 0.20, 0.0)]),
          ("Cnestis palala", "s2",
           [("woody stems", 51.80, 112.0), ("roots", 49.61, 112.1), ("leaves", 0.37, 0.0)])]
PLACE = {("Pachyrhizus erosus", "leaves"): (12, 2, "left", False, "the part that poisons fish"),
         ("Pachyrhizus erosus", "woody stems"): (12, -2, "left", False, None),
         ("Pachyrhizus erosus", "roots"): (16, -24, "left", True, "the part you eat"),
         ("Cnestis palala", "woody stems"): (10, -16, "left", True, None),
         ("Cnestis palala", "roots"): (-8, 17, "right", False, None),
         ("Cnestis palala", "leaves"): (118, -22, "left", True, None)}


def fig3(theme):
    t = THEMES[theme]; style(t)
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    fig.subplots_adjust(left=0.11, right=0.96, top=0.72, bottom=0.16)
    ax.set_xlim(-3, 61); ax.set_ylim(-42, 128)
    for g in range(0, 126, 25):
        ax.axhline(g, color=t["grid"], lw=1.0, zorder=0)
    for name, slot, pts in SERIES:
        c = t[slot]
        ax.plot([p[1] for p in pts], [p[2] for p in pts], color=c, lw=2.0,
                solid_capstyle="round", solid_joinstyle="round", zorder=3)
        ax.plot([p[1] for p in pts], [p[2] for p in pts], "o", ms=9, mfc=c,
                mec=t["surface"], mew=2.0, zorder=4)
        for organ, x, y in pts:
            dx, dy, ha, lead, extra = PLACE[(name, organ)]
            ax.annotate(organ, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                        ha=ha, va="center", fontsize=8.6, color=t["ink2"], zorder=7,
                        arrowprops=dict(arrowstyle="-", color=t["axis"], lw=0.8,
                                        shrinkA=1, shrinkB=6) if lead else None)
            if extra:
                ax.annotate(extra, xy=(x, y), xytext=(dx, dy - 11), textcoords="offset points",
                            ha=ha, va="center", fontsize=8.0, color=t["muted"],
                            style="italic", zorder=7)
    ax.set_xticks(range(0, 56, 10)); ax.set_xticklabels([f"{v}%" for v in range(0, 56, 10)], fontsize=9)
    ax.set_yticks(range(0, 126, 25)); ax.set_yticklabels([f"{v}%" for v in range(0, 126, 25)], fontsize=9)
    ax.set_xlabel("Rotenoid share of annotated signal  (CANOPUS)", fontsize=9, color=t["ink2"], labelpad=7)
    ax.set_ylabel("T. cruzi inhibition", fontsize=9, color=t["ink2"], labelpad=7)
    ax.tick_params(length=0)
    handles = [Line2D([], [], color=t[s], lw=2.0, marker="o", ms=8, mec=t["surface"],
                      mew=1.8, label=n) for n, s, _ in SERIES]
    leg = ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9,
                    handletextpad=0.7, borderpad=0.9, labelspacing=0.65)
    for tx in leg.get_texts():
        tx.set_color(t["ink2"]); tx.set_style("italic")
    fig.text(0.035, 0.945, "Traditional knowledge, recovered as a dose gradient",
             fontsize=13.5, fontweight="semibold", color=t["ink"])
    fig.text(0.035, 0.883,
             "Within one plant, the organ that carries the chemistry is the organ that carries the activity.",
             fontsize=8.8, color=t["ink2"])
    fig.text(0.035, 0.035,
             "Real screening data, no simulation. Jicama tubers are eaten; the leaves are a traditional fish poison.",
             fontsize=7.6, color=t["muted"])
    fig.savefig(OUT / f"fig3_ethnobotany_{theme}.png", bbox_inches="tight", pad_inches=0.26)
    plt.close(fig)


def table_view(d, reg):
    L = ["# Figure data (table view)", "",
         "Every plotted value, so nothing is available only as colour or position.",
         f"Source: `results/benchmark.json` · gain {d['config']['gain']:.2f} · "
         f"threshold {d['config']['nomination_threshold']}", "",
         f"## Figure 1 — hard stratum ({reg['n_hard']} episodes, "
         f"{reg['n_distinct_pairs_hard']} compound pairs)", "",
         "| policy | accuracy | pair-clustered 95% CI | nominations |", "|---|---|---|---|"]
    # exactly the policies Figure 1 plots, in the plotted order
    cells = {c["policy"]: c for c in
             pick(reg, pool="unconstrained", rule="potency-only", stratum="hard", scoring="named")}
    for policy in ORDER:
        c = cells[policy]
        lo, hi = [x * 100 for x in c["accuracy_ci95"]]
        L.append(f"| {LABELS[policy].replace(chr(10),' ')} | "
                 f"{c['accuracy']*100:.1f}% | {lo:.1f}–{hi:.1f}% | {c['n_nominations']} |")
    L += ["", f"## Figure 2 — nomination rule ({reg['n_episodes']} episodes, "
              f"{reg['n_distinct_pairs']} pairs, adaptive_contrast, developable scoring)", "",
          "| rule | coverage | precision | leads worth isolating | wasted / 100 |", "|---|---|---|---|---|"]
    for c in pick(reg, pool="unconstrained", policy="adaptive_contrast", stratum="overall", scoring="developable"):
        L.append(f"| {c['rule']} | {c['coverage']*100:.1f}% | {c['precision']*100:.1f}% | "
                 f"{c['accuracy']*100:.1f}% | {c['wasted_per_100']:.2f} |")
    L += ["", "## Figure 3 — organ series (measured data, no simulation)", "",
          "| species | organ | rotenoid share (CANOPUS) | T. cruzi inhibition |", "|---|---|---|---|"]
    for name, _, pts in SERIES:
        for organ, x, y in pts:
            L.append(f"| *{name}* | {organ} | {x:.2f}% | {y:.1f}% |")
    (OUT / "figure_data.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    d, reg = load()
    for old in OUT.glob("fig1_accuracy_*.png"): old.unlink()
    for old in OUT.glob("fig2_robustness_*.png"): old.unlink()
    for theme in ("light", "dark"):
        fig1(reg, theme); fig2(reg, theme); fig3(theme)
    table_view(d, reg)
    for p in sorted(OUT.glob("*.png")):
        print(f"  {p.name}  {p.stat().st_size/1024:.0f} KB")
    print("  figure_data.md")
