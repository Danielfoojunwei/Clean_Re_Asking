"""Figures for the pushback study on published protocols (v6/results_main.json). Same style as the other figures."""
import json
from pathlib import Path
import numpy as np
import figs
from figs import plt, BLUE, ORANGE, AQUA, INK, MUTED, AXIS, SURF, save, pct_axis
from matplotlib.colors import LinearSegmentedColormap

R = json.load(open(Path("../v6/results_main.json")))
M, ORDER, GR = R["models"], R["order"], R["groups"]
CM = LinearSegmentedColormap.from_list("wo", ["#f7f6f0", "#fbe3c8", "#f3a56f", "#eb6834", "#b8430f"])
PURPLE = "#8a5cc7"
# rows: grouped by where the model comes from
ROWS = [l for l in GR["first8"]] + [l for l in GR["basta"] if l not in GR["first8"]] + [l for l in GR["yang"] if l not in GR["first8"]]
ROWS = [l for l in ROWS if l in M]
SEP = [len(GR["first8"]), len(GR["first8"]) + len([l for l in GR["basta"] if l not in GR["first8"]])]


def heat(ax, cols, getter, title, ylab=True, fs=6.6):
    A = np.array([[np.nan if getter(M[l], c) is None else 100 * getter(M[l], c) for c, _ in cols] for l in ROWS])
    ax.imshow(np.nan_to_num(A, nan=0), cmap=CM, vmin=0, vmax=100, aspect="auto")
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            v = A[i, j]
            ax.text(j, i, "–" if np.isnan(v) else f"{v:.0f}", ha="center", va="center", fontsize=fs, color="#fff" if (not np.isnan(v) and v >= 62) else INK)
    ax.set_xticks(range(len(cols))); ax.xaxis.tick_top(); ax.set_xticklabels([c.replace("-\n", "-").replace("\n", " ") for _, c in cols], fontsize=6.0, rotation=40, ha="left", rotation_mode="anchor"); ax.tick_params(length=0)
    ax.set_yticks(range(len(ROWS))); ax.set_yticklabels(ROWS if ylab else [], fontsize=6.4)
    ax.set_title(title, pad=44, fontsize=7.6, loc="left"); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True); ax.set_yticks(np.arange(-.5, len(ROWS), 1), minor=True)
    ax.grid(which="minor", color=SURF, linewidth=1.2); ax.tick_params(which="minor", length=0)
    for sp in SEP:
        ax.axhline(sp - .5, color=INK, lw=0.9)


def fig_rebuttals():
    """Right answers given up (user wrong), 21 models x published rebuttals, three comparable blocks."""
    A = [("neutral_dis", "double-\ncheck"), ("sure_dis", "Are you\nsure?"), ("doubt_dis", "not right,\nsure?"), ("push_dis", "sure it\nisn't X?"), ("plain_dis", "change\nto X"), ("page_frame_dis", "page +\nchange")]
    B = [("plain", "change\nto X"), ("authority", "+ degree"), ("citation", "+ source"), ("outside_frame", "+ outside\nfact"), ("page_frame", "+ page\nclaim"), ("expert", "expert\n+ fact"), ("expert_page", "expert\n+ page")]
    C = [("neutral", "double-\ncheck"), ("doubt", "not right,\nsure?"), ("citation", "source +\nchange"), ("page_frame", "page +\nchange")]
    fig, ax = plt.subplots(1, 3, figsize=(7.1, 4.6), gridspec_kw={"wspace": 0.05, "width_ratios": [6, 7, 4]})
    heat(ax[0], A, lambda m, c: m["word_F"].get(c), "One word, same closing instruction")
    heat(ax[1], B, lambda m, c: m["word_F"].get(c), "One word, rebuttal as published", ylab=False)
    heat(ax[2], C, lambda m, c: m["free_F"].get(c), "Free-form reply", ylab=False)
    save(fig, "f_rebuttals")


def fig_factorial():
    labs = ROWS; ys = list(range(len(labs)))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.5), gridspec_kw={"wspace": 0.08, "width_ratios": [1.25, 1]})
    a = ax[0]
    acts = [("question", AQUA, "o", "asks"), ("assertion", ORANGE, "s", "asserts"), ("directive", "#b8430f", "D", "tells")]
    for l, y in zip(labs, ys):
        f = M[l].get("fact")
        if not f:
            continue
        xs = [100 * f["by_act"][k] for k, *_ in acts if f["by_act"].get(k) is not None]
        a.plot([min(xs), max(xs)], [y, y], color=AXIS, lw=1.3, zorder=1)
        for k, c, mk, lb in acts:
            if f["by_act"].get(k) is not None:
                a.scatter([100 * f["by_act"][k]], [y], s=22, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.7, label=lb if y == ys[0] else None)
    a.set_yticks(ys); a.set_yticklabels(labs, fontsize=6.4); a.set_ylim(-0.7, len(labs) - 0.3); pct_axis(a)
    a.set_title("Right answers given up, by what the rebuttal does"); a.set_xlabel("Share of right answers changed")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, handletextpad=0.2, columnspacing=1.0, fontsize=6.2)
    for sp in SEP:
        a.axhline(len(labs) - sp - .5, color=INK, lw=0.6, ls=(0, (2, 2)))
    b = ax[1]
    effs = [("act", "#b8430f", "D", "tells − asks"), ("naming", BLUE, "o", "named − unnamed"), ("page", PURPLE, "s", "page claim − none")]
    b.axvline(0, color=AXIS, lw=0.9)
    for l, y in zip(labs, ys):
        f = M[l].get("fact")
        if not f:
            continue
        for k, (key, c, mk, lb) in enumerate(effs):
            e = f.get(key)
            if e:
                yy = y + 0.24 - 0.24 * k
                b.plot([100 * e["ci"][0], 100 * e["ci"][1]], [yy, yy], color=c, lw=0.8, alpha=0.55, zorder=2)
                b.scatter([100 * e["diff"]], [yy], s=17, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.6, label=lb if y == ys[0] else None)
    b.set_yticks(ys); b.set_yticklabels([]); b.set_ylim(-0.7, len(labs) - 0.3); b.set_xlim(-40, 100); b.set_xticks([-25, 0, 25, 50, 75, 100])
    b.set_xticklabels(["-25", "0", "+25", "+50", "+75", "+100"]); b.set_title("Size of each effect (points)"); b.set_xlabel("Difference (points)")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, handletextpad=0.2, columnspacing=0.8, fontsize=6.2)
    for sp in SEP:
        b.axhline(len(labs) - sp - .5, color=INK, lw=0.6, ls=(0, (2, 2)))
    save(fig, "f_factorial")


def fig_fixes():
    labs = [l for l in ROWS if M[l].get("H")]; ys = list(range(len(labs)))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), gridspec_kw={"wspace": 0.14})
    def panel(a, arms, title, ylab):
        for l, y in zip(labs, ys):
            xs = [v for v in (arm[0](M[l]["H"]) for arm in arms) if v is not None]
            if not xs:
                continue
            a.plot([100 * min(xs), 100 * max(xs)], [y, y], color=AXIS, lw=1.3, zorder=1)
            for get, c, mk, lb in arms:
                v = get(M[l]["H"])
                if v is not None:
                    a.scatter([100 * v], [y], s=24, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.7, label=lb if y == ys[0] else None)
        a.set_yticks(ys); a.set_yticklabels(labs if ylab else [], fontsize=6.4); a.set_ylim(-0.6, len(labs) - 0.4); pct_axis(a); a.set_title(title)
        a.set_xlabel("Share of right answers changed (lower is better)")
        a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=1, handletextpad=0.2, labelspacing=0.25, fontsize=6.2)
    panel(ax[0], [(lambda h: h["base"]["page_word"]["F"], ORANGE, "o", "no fix"), (lambda h: h["fix"]["quote_page"]["F"], AQUA, "s", "model quotes the deciding line first"),
                  (lambda h: h["fix"]["note_page"]["F"], BLUE, "D", "fact computed outside the model, attached")], "One-word format", True)
    panel(ax[1], [(lambda h: h["base"]["page_free"]["F"], ORANGE, "o", "no fix"), (lambda h: h["fix"]["warn_page"]["F"], AQUA, "s", "warning prompt of Basta et al."),
                  (lambda h: h["fix"]["gate_page"]["F"], BLUE, "D", "evidence-gated prompt of Basta et al.")], "Free-form replies", False)
    save(fig, "f_fixes")


def fig_trade():
    """What telling adds over asking: right answers lost (cost) against wrong answers additionally corrected (gain)."""
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.75), gridspec_kw={"wspace": 0.3, "width_ratios": [1, 1.05]})
    a = ax[0]
    for l in ROWS:
        f = M[l].get("fact")
        if not f:
            continue
        x0, y0 = 100 * f["by_act"]["question"], 100 * f["H_by_act"]["question"]; x1, y1 = 100 * f["by_act"]["directive"], 100 * f["H_by_act"]["directive"]
        a.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.9))
        a.scatter([x0], [y0], s=18, color=AQUA, zorder=3, edgecolor=SURF, linewidth=0.6, label="asked" if l == ROWS[0] else None)
        a.scatter([x1], [y1], s=20, color="#b8430f", marker="D", zorder=3, edgecolor=SURF, linewidth=0.6, label="told" if l == ROWS[0] else None)
    a.scatter([0], [100], s=90, facecolor="none", edgecolor=INK, linewidth=0.9, zorder=2); a.text(4, 101.2, "ideal", fontsize=6.4, color=INK, va="bottom")
    a.set_xlim(-4, 100); a.set_ylim(78, 103); a.set_xticks([0, 25, 50, 75, 100]); a.set_xticklabels(["0%", "25%", "50%", "75%", "100%"]); a.set_yticks([80, 90, 100]); a.set_yticklabels(["80%", "90%", "100%"])
    a.set_xlabel("Right answers given up when the user is wrong"); a.set_ylabel("Wrong answers corrected\nwhen the user is right"); a.set_title("Each model, asked and told")
    a.legend(loc="lower right", fontsize=6.4, handletextpad=0.2)
    b = ax[1]
    order = sorted([l for l in ROWS if M[l].get("fact")], key=lambda l: M[l]["fact"]["by_act"]["directive"] - M[l]["fact"]["by_act"]["question"])
    ys = range(len(order))
    cost = [100 * (M[l]["fact"]["by_act"]["directive"] - M[l]["fact"]["by_act"]["question"]) for l in order]
    gain = [100 * (M[l]["fact"]["H_by_act"]["directive"] - M[l]["fact"]["H_by_act"]["question"]) for l in order]
    b.barh([y + 0.2 for y in ys], cost, height=0.38, color="#eb6834", label="right answers lost by telling")
    b.barh([y - 0.2 for y in ys], gain, height=0.38, color=BLUE, label="wrong answers gained by telling")
    b.axvline(0, color=AXIS, lw=0.8); b.set_yticks(list(ys)); b.set_yticklabels(order, fontsize=5.6); b.set_xlabel("Points (told minus asked)"); b.set_title("What telling adds over asking")
    b.set_xlim(-10, 80); b.legend(loc="lower right", fontsize=6.2, handletextpad=0.3)
    save(fig, "f_trade")


if __name__ == "__main__":
    fig_rebuttals(); fig_factorial(); fig_fixes(); fig_trade()
