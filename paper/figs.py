"""All paper figures, generated from fig_data.json. Plain-language labels, one style, colour-blind-validated palette."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Circle

D = json.load(open("fig_data.json"))
M = D["models"]
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
SEQ = LinearSegmentedColormap.from_list("seq", ["#f4f8fe", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
plt.rcParams.update({
    "font.family": "Inter", "font.size": 7.5, "axes.titlesize": 8.2, "axes.labelsize": 7.5, "xtick.labelsize": 7,
    "ytick.labelsize": 7.5, "legend.fontsize": 7, "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "svg.fonttype": "path", "figure.facecolor": SURF, "axes.facecolor": SURF,
    "legend.frameon": False, "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 6})
LAB = [m["label"] for m in M]
Y = list(range(len(M)))[::-1]
CELL_LAB = {"BOTH": "listed\nboth\nways", "FWD": "listed\none\nway", "REV": "wrong\nway\nround", "REV_PATH": "wrong\nway +\nchain",
            "NEI_PATH": "needs\na\nchain", "NEI_NOPATH": "not\ncon-\nnected"}
OUT = "figs"


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight", pad_inches=0.03, dpi=110)
    plt.close(fig)


def toplegend(fig, ax, ncol=3, y=1.0):
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, y), ncol=ncol, columnspacing=1.6, handletextpad=0.3)


def pct_axis(ax, lo=0, hi=100, step=25):
    ax.set_xlim(lo, hi)
    ax.set_xticks(range(lo, hi + 1, step))
    ax.set_xticklabels([f"{t}%" for t in range(lo, hi + 1, step)])
    ax.yaxis.grid(False)


def better(ax, text="← better", x=0.01, ha="left"):
    return None


def dumbbell(ax, key_a, key_b, metric, col_a, col_b, lab_a, lab_b, title, show_y=True):
    for y, m in zip(Y, M):
        a, b = m["rates"][key_a][metric], m["rates"][key_b][metric]
        ax.plot([100 * a["rate"], 100 * b["rate"]], [y, y], color=AXIS, lw=1.6, zorder=1, solid_capstyle="round")
        for r, c in ((a, col_a), (b, col_b)):
            ax.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y, y], color=c, lw=0.9, alpha=0.55, zorder=2)
        ax.scatter([100 * a["rate"]], [y], s=34, color=col_a, zorder=3, edgecolor=SURF, linewidth=0.9, label=lab_a if y == Y[0] else None)
        ax.scatter([100 * b["rate"]], [y], s=34, color=col_b, zorder=4, edgecolor=SURF, linewidth=0.9, label=lab_b if y == Y[0] else None,
                   marker="D")
    if show_y:
        ax.set_yticks(Y)
        ax.set_yticklabels(LAB)
    else:
        ax.tick_params(labelleft=False)
    ax.set_ylim(-0.6, len(M) - 0.4)
    pct_axis(ax)
    ax.set_title(title)


# ---------------------------------------------------------------- design schematic
def fig_design():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.1))
    P = {"A": (0, 1), "B": (1, 1), "C": (1, 0), "D": (0, 0)}

    def graph(ax, routes, reqs, title, note):
        ax.set_xlim(-0.6, 1.6); ax.set_ylim(-0.62, 1.42); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, fontsize=8)
        for s, t in routes:
            rad = 0.18 if (t, s) in routes else 0.0
            ax.add_patch(FancyArrowPatch(P[s], P[t], arrowstyle="-|>", mutation_scale=9, lw=1.4, color="#3a3a38",
                                         shrinkA=11, shrinkB=11, connectionstyle=f"arc3,rad={rad}", zorder=2))
        for n, (x, y) in P.items():
            ax.add_patch(Circle((x, y), 0.13, facecolor=SURF, edgecolor="#3a3a38", lw=1.1, zorder=3))
            ax.text(x, y, n, ha="center", va="center", fontsize=8, fontweight="semibold", zorder=4)
        for (s, t), lab, ok, rad, off in reqs:
            col = BLUE if ok else ORANGE
            ax.add_patch(FancyArrowPatch(P[s], P[t], arrowstyle="-|>", mutation_scale=8, lw=1.1, color=col, linestyle=(0, (3, 2)),
                                         shrinkA=13, shrinkB=13, connectionstyle=f"arc3,rad={rad}", zorder=1))
            mx, my = (P[s][0] + P[t][0]) / 2 + off[0], (P[s][1] + P[t][1]) / 2 + off[1]
            ax.text(mx, my, lab, ha="center", va="center", fontsize=6.2, color=INK2,
                    bbox=dict(boxstyle="round,pad=0.18", fc=SURF, ec=col, lw=0.7))
        ax.text(0.5, -0.58, note, ha="center", va="center", fontsize=6.6, color=INK2)

    graph(axes[0], [("A", "B"), ("B", "A"), ("B", "C"), ("C", "D")],
          [(("B", "C"), "listed one way", True, -0.55, (0.5, 0.0)), (("C", "B"), "wrong way round", False, -0.55, (-0.3, 0.22)),
           (("A", "C"), "needs a chain", False, 0.0, (-0.22, -0.2)), (("D", "A"), "not connected", False, -0.5, (-0.42, 0.0))],
          "Mixed rulebook (this study)", "each mistake has its own request")
    graph(axes[1], [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")],
          [(("B", "A"), "wrong way + chain", False, -0.45, (0.0, 0.3)), (("C", "D"), "listed one way", True, -0.5, (0.0, -0.33))],
          "Ring rulebook (common)", "two mistakes look identical")
    graph(axes[2], [("A", "B"), ("B", "A"), ("C", "D"), ("D", "C")],
          [(("A", "B"), "listed both ways", True, -0.75, (0.0, 0.36)), (("B", "C"), "not connected", False, -0.4, (0.42, 0.0))],
          "Two-way rulebook", "no direction to get wrong")
    fig.legend(handles=[plt.Line2D([], [], color="#3a3a38", lw=1.4, label="rule in the rulebook"),
                        plt.Line2D([], [], color=BLUE, lw=1.1, ls=(0, (3, 2)), label="request that should be allowed"),
                        plt.Line2D([], [], color=ORANGE, lw=1.1, ls=(0, (3, 2)), label="request that should be refused")],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.07), columnspacing=1.6)
    save(fig, "f_design")


# ---------------------------------------------------------------- chaining and the extra sentence
def fig_clause():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.3), sharey=True, gridspec_kw={"wspace": 0.12})
    dumbbell(ax[0], "E1/base", "E1/explicit", "chain_release", ORANGE, BLUE, "rule as first written", "plus \"routes cannot be chained\"",
             "Quick one-word answer")
    dumbbell(ax[1], "E5/base", "E5/explicit", "chain_release", ORANGE, BLUE, "rule as first written", "plus \"routes cannot be chained\"",
             "Step-by-step answer", show_y=False)
    for a in ax:
        a.set_xlabel("Chain requests wrongly allowed (lower is better)")
        better(a)
    toplegend(fig, ax[1], 2, 0.99)
    save(fig, "f_clause")


# ---------------------------------------------------------------- error map
def fig_heat():
    panels = [("E1", "base", "Quick answer · rule as first written"), ("E1", "explicit", "Quick answer · with the extra sentence"),
              ("E5", "base", "Step-by-step · rule as first written"), ("E5", "explicit", "Step-by-step · with the extra sentence")]
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.6), sharey=True, sharex=True, gridspec_kw={"wspace": 0.04, "hspace": 0.26})
    for ax, (e, cl, title) in zip(axes.flat, panels):
        grid = []
        for m in M:
            c = m["cells"][e][cl]
            grid.append([100 * (c[k]["wrong_decline"] + c[k]["wrong_execute"]) / c[k]["n"] for k in D["cells"]])
        im = ax.imshow(grid, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
        ax.set_title(title, fontsize=7.8)
        ax.set_xticks(range(6)); ax.set_xticklabels([CELL_LAB[k] for k in D["cells"]], fontsize=6, color=INK2)
        ax.set_yticks(range(len(M))); ax.set_yticklabels(LAB)
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks([x - 0.5 for x in range(1, 6)], minor=True); ax.set_yticks([y - 0.5 for y in range(1, len(M))], minor=True)
        ax.grid(which="minor", color=SURF, linewidth=1.6); ax.tick_params(which="minor", length=0)
        ax.axvline(1.5, color=INK, lw=0.9)
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                if v >= 4.5:
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6.2, color="#ffffff" if v > 45 else INK)
    for ax in axes[1]:
        ax.text(0.5, len(M) + 1.75, "should be allowed:\nerror = refused", ha="center", va="top", fontsize=6, color=MUTED)
        ax.text(3.5, len(M) + 1.75, "should be refused:\nerror = allowed", ha="center", va="top", fontsize=6, color=MUTED)
    cb = fig.colorbar(im, ax=axes, fraction=0.014, pad=0.012)
    cb.set_label("share of answers that are wrong (%)", fontsize=6.5); cb.ax.tick_params(labelsize=6, length=0); cb.outline.set_visible(False)
    save(fig, "f_heat")


# ---------------------------------------------------------------- refusing what is allowed
def fig_refusal():
    fig = plt.figure(figsize=(7.0, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1, 1], wspace=0.34)
    ax = fig.add_subplot(gs[0])
    dumbbell(ax, "E1/base", "E1/explicit", "listed_refusal", ORANGE, BLUE, "as first written", "with extra sentence",
             "Allowed requests refused")
    for y, m in zip(Y, M):
        lk = m["components"]["lookup"]
        ax.scatter([100 * (1 - lk[0] / lk[1])], [y], marker="|", s=70, color=INK, zorder=5, linewidth=1.1,
                   label="can't find the rule when asked" if y == Y[0] else None)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.02, 0.99), ncol=3, columnspacing=1.2, handletextpad=0.2)
    ax.set_xlabel("Share of allowed requests (lower is better)")
    series = [("Grok 4.3", BLUE), ("DeepSeek v3.2", ORANGE), ("Llama 4 Maverick", AQUA), ("Qwen3.5-9B", YELLOW)]
    for k, (sf, title) in enumerate((("opaque", "Code-word names"), ("natural", "Department names"))):
        a = fig.add_subplot(gs[1 + k])
        for lab, col in series:
            m = next(x for x in M if x["label"] == lab)
            ys = [100 * m["refusal_by_position"][f"{sf}/{p}"][0] / m["refusal_by_position"][f"{sf}/{p}"][1] for p in range(4)]
            a.plot([1, 2, 3, 4], ys, color=col, lw=1.6, marker="o", ms=4.2, mec=SURF, mew=0.8, label=lab, solid_capstyle="round")
        a.set_title(title); a.set_xticks([1, 2, 3, 4]); a.set_xticklabels(["1st", "2nd", "3rd", "4th"])
        a.set_xlabel("Position of the matching rule")
        a.set_ylim(0, 100); a.set_yticks([0, 25, 50, 75, 100]); a.xaxis.grid(False); a.tick_params(axis="y", colors=MUTED)
        if k == 0:
            a.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); a.set_ylabel("Allowed requests refused")
        else:
            a.tick_params(labelleft=False)
            a.legend(loc="upper left", handlelength=1.4, borderaxespad=0.1)
    save(fig, "f_refusal")


# ---------------------------------------------------------------- confidence and double-checking
def fig_conf():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={"width_ratios": [1.2, 1], "wspace": 0.3})
    a = ax[0]
    for y, m in zip(Y, M):
        def share(kinds):
            tot = sum(sum(m["confidence"].get(k, {}).values()) for k in kinds)
            hi = sum(m["confidence"].get(k, {}).get(b, 0) for k in kinds for b in ("100", "90-99"))
            return 100 * hi / tot if tot else None
        c, w = share(["correct"]), share(["wrong_release", "wrong_refusal"])
        a.plot([c, w], [y, y], color=AXIS, lw=1.6, zorder=1)
        a.scatter([c], [y + 0.13], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9, label="when its answer was right" if y == Y[0] else None)
        a.scatter([w], [y - 0.13], s=30, color=ORANGE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9,
                  label="when its answer was wrong" if y == Y[0] else None)
    a.set_yticks(Y); a.set_yticklabels(LAB); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a)
    a.set_title("\"I am at least 90% sure\""); a.set_xlabel("Share of answers given 90+ confidence")
    a.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.2)
    a.text(0.42, 0.55, "a useful signal would\nput the orange diamonds\nfar to the left", transform=a.transAxes, fontsize=6.3, color=MUTED,
           ha="center", va="center")
    b = ax[1]
    b.plot([0, 100], [0, 100], color=AXIS, lw=0.9, zorder=1)
    b.text(90, 97, "coin flip", rotation=40, fontsize=6.3, color=MUTED, ha="center", va="center")
    b.text(1, 100, "↖ ideal", fontsize=6.4, color=MUTED, ha="left", va="top")
    b.text(97, 6, "rubber stamp:\nnever changes", fontsize=6.2, color=MUTED, ha="right", va="bottom")
    nudge = {"Grok 4.3": (5, -1.5), "GPT-4.1": (5, 5), "Claude Haiku 5.5": (5, 6), "Gemini 2.5 Flash": (4, 3), "GPT-4.1-mini": (-4, 0),
             "DeepSeek v3.2": (4, -3), "Llama 4 Maverick": (4, -3), "Qwen3.5-9B": (4, -3), "Nova Lite": (4, -3)}
    for m in M:
        def ch(kinds):
            tot = sum(sum(m["recheck"].get(k, {}).values()) for k in kinds)
            return 100 * sum(m["recheck"].get(k, {}).get("CHANGE", 0) for k in kinds) / tot if tot else 0
        x, yv = ch(["correct"]), ch(["wrong_release", "wrong_refusal"])
        b.scatter([x], [yv], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9)
        dx, dy = nudge[m["label"]]
        b.annotate(m["label"], (x, yv), xytext=(x + dx, yv + dy), fontsize=6.2, color=INK2, ha="left" if dx > 0 else "right", va="center")
    b.set_xlim(-3, 103); b.set_ylim(-3, 103); b.set_xticks([0, 25, 50, 75, 100]); b.set_yticks([0, 25, 50, 75, 100])
    b.set_xticklabels(["0%", "25%", "50%", "75%", "100%"]); b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); b.tick_params(axis="y", colors=MUTED)
    b.set_xlabel("Right answers it changed"); b.set_ylabel("Wrong answers it changed"); b.set_title("Asked to double-check")
    save(fig, "f_conf")


# ---------------------------------------------------------------- knowing versus doing
def fig_know():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1.45, 1], "wspace": 0.14}, sharey=True)
    a = ax[0]
    ser = [("roles", "says who is sender and receiver", BLUE, "o", 0.24), ("lookup", "finds the rule in the list", AQUA, "s", 0.08),
           ("decision_reasoned", "final decision, step-by-step", YELLOW, "^", -0.08), ("decision", "final decision, quick answer", ORANGE, "D", -0.24)]
    for y, m in zip(Y, M):
        a.plot([50, 100], [y, y], color=GRID, lw=0.6, zorder=0)
        for key, lab, col, mk, dy in ser:
            vv = 100 * m["components"][key][0] / m["components"][key][1]
            a.scatter([vv], [y + dy], s=26, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8, label=lab if y == Y[0] else None)
    a.set_yticks(Y); a.set_yticklabels(LAB); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a, 50, 100, 10)
    a.set_title("Each step is easy; the decision is not"); a.set_xlabel("Share answered correctly (higher is better)")
    toplegend(fig, a, 4, 0.99)
    b = ax[1]
    for y, m in zip(Y, M):
        c = m["components"]
        vv = 100 * c["wrong_both_right"] / c["wrong_total"]
        b.barh([y], [vv], height=0.42, color=BLUE)
        b.text(vv - 2, y, f'{c["wrong_both_right"]}/{c["wrong_total"]}', ha="right", va="center", fontsize=6.4, color="#ffffff")
    pct_axis(b); b.set_title("Wrong decisions where both steps were right"); b.set_xlabel("Share of wrong quick decisions")
    save(fig, "f_know")


# ---------------------------------------------------------------- fixes
def fig_mitig():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.75), sharey=True, gridspec_kw={"wspace": 0.1})
    ser = [("E4", "say the rule to look up first", BLUE, "o", 0.24), ("E4p", "write a filler line first", YELLOW, "s", 0.0),
           ("E5", "think step by step", AQUA, "^", -0.24)]
    for a, metric, title, lim in ((ax[0], "chain_release", "Chained requests wrongly allowed", (-60, 80)),
                                  (ax[1], "listed_kept", "Allowed requests correctly allowed", (-25, 60))):
        a.axvline(0, color=INK2, lw=0.8, zorder=1)
        for y, m in zip(Y, M):
            for e, lab, col, mk, dy in ser:
                r = m["effects"][f"{e}/base"][metric]
                a.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y + dy, y + dy], color=col, lw=1.0, alpha=0.6, zorder=2)
                a.scatter([100 * r["diff"]], [y + dy], s=22, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.7,
                          label=lab if y == Y[0] else None)
        a.set_yticks(Y); a.set_ylim(-0.6, len(M) - 0.4); a.yaxis.grid(False)
        if a is ax[0]:
            a.set_yticklabels(LAB)
        a.set_xlim(*lim); a.set_title(title)
    ax[0].set_xlabel("Change vs quick answer, points (left of 0 is better)")
    ax[1].set_xlabel("Change vs quick answer, points (right of 0 is better)")
    toplegend(fig, ax[0], 3, 0.99)
    save(fig, "f_mitig")


# ---------------------------------------------------------------- appendix
def fig_order():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.4), gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.6})
    g = next(m for m in M if m["label"] == "GPT-4.1")
    a = ax[0]
    cells = ["FWD", "BOTH", "REV", "REV_PATH"]
    for i, c in enumerate(cells):
        for k, (rec, col, lab) in enumerate((("d_first", BLUE, "sender line printed first"), ("a_first", ORANGE, "receiver line printed first"))):
            w, n = g["wrong_by_role_order"][f"{c}/{rec}"]
            a.bar([i + (k - 0.5) * 0.34], [100 * w / n], width=0.3, color=col, label=lab if i == 0 else None)
            a.text(i + (k - 0.5) * 0.34, 100 * w / n + 0.8, f"{w}/{n}", ha="center", va="bottom", fontsize=6, color=INK2)
    a.set_xticks(range(4)); a.set_xticklabels([CELL_LAB[c] for c in cells], color=INK2, fontsize=6.5)
    a.set_ylim(0, 30); a.set_yticks([0, 10, 20, 30]); a.set_yticklabels(["0%", "10%", "20%", "30%"]); a.tick_params(axis="y", colors=MUTED)
    a.xaxis.grid(False); a.set_title("GPT-4.1: wrong quick decisions"); a.legend(loc="upper left", borderaxespad=0.1)
    b = ax[1]
    for y, m in zip(Y, M):
        tot = {rec: [sum(v[0] for k, v in m["wrong_by_role_order"].items() if k.endswith(rec)),
                     sum(v[1] for k, v in m["wrong_by_role_order"].items() if k.endswith(rec))] for rec in ("d_first", "a_first")}
        d, av = 100 * tot["d_first"][0] / tot["d_first"][1], 100 * tot["a_first"][0] / tot["a_first"][1]
        b.plot([d, av], [y, y], color=AXIS, lw=1.6, zorder=1)
        b.scatter([d], [y], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9, label="sender line first" if y == Y[0] else None)
        b.scatter([av], [y], s=30, color=ORANGE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9, label="receiver line first" if y == Y[0] else None)
    b.set_yticks(Y); b.set_yticklabels(LAB); b.set_ylim(-0.6, len(M) - 0.4); pct_axis(b, 0, 50, 10)
    b.set_title("All models: wrong quick decisions"); b.set_xlabel("Share of quick decisions")
    b.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.2)
    save(fig, "a_order")


def fig_banks():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True, gridspec_kw={"wspace": 0.12})
    for a, key, metric, title in ((ax[0], "E5", "chain_release", "Chained requests wrongly allowed (step-by-step)"),
                                  (ax[1], "E1", "listed_refusal", "Allowed requests refused (quick answer)")):
        for y, m in zip(Y, M):
            for cl, col, dy in (("base", ORANGE, 0.17), ("explicit", BLUE, -0.17)):
                vals = sorted(m["rates"][f"{key}/{cl}"][metric]["per_bank"].values())
                a.scatter([100 * v for v in vals], [y + dy + ((i % 3) - 1) * 0.045 for i in range(len(vals))], s=9, color=col, alpha=0.75,
                          linewidth=0, zorder=3, label=("rule as first written" if cl == "base" else "with the extra sentence") if y == Y[0] else None)
        a.set_yticks(Y); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a); a.set_title(title)
        if a is ax[0]:
            a.set_yticklabels(LAB)
        a.set_xlabel("Rate within one name set (each dot is one set)")
    toplegend(fig, ax[1], 2, 0.97)
    save(fig, "a_banks")


def fig_rank():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), gridspec_kw={"wspace": 0.62})
    a = ax[0]
    a.plot([50, 100], [50, 100], color=AXIS, lw=0.9)
    nudge = {"Grok 4.3": (1.2, -1.5), "Nova Lite": (1.2, -2.2), "Qwen3.5-9B": (-1.2, -1.5), "DeepSeek v3.2": (1.2, 1.2), "Llama 4 Maverick": (-1.2, 1.5),
             "GPT-4.1": (-1.4, -0.3), "GPT-4.1-mini": (-1.4, 4.2), "Gemini 2.5 Flash": (-1.6, 1.3), "Claude Haiku 5.5": (-1.2, -3.6)}
    for m in M:
        x, y = 100 * m["H7"]["symmetric_subset_acc"], 100 * m["H7"]["oneway_subset_acc"]
        a.scatter([x], [y], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9)
        dx, dy = nudge[m["label"]]
        a.annotate(m["label"], (x, y), xytext=(x + dx, y + dy), fontsize=6.2, color=INK2, ha="left" if dx > 0 else "right", va="center")
    a.set_xlim(55, 101); a.set_ylim(55, 104); a.set_xlabel("Correct on two-way and unconnected requests (%)")
    a.set_ylabel("Correct on one-way requests (%)"); a.set_title("Model ranking barely changes (ρ = 0.91)"); a.tick_params(axis="y", colors=MUTED)
    b = ax[1]
    for y, m in zip(Y, M):
        for sf, col, mk in (("opaque", BLUE, "o"), ("natural", ORANGE, "D")):
            pos = m["refusal_by_position"]
            k = sum(pos[f"{sf}/{p}"][0] for p in range(4)); n = sum(pos[f"{sf}/{p}"][1] for p in range(4))
            b.scatter([100 * k / n], [y], s=30, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.9,
                      label=("code-word names" if sf == "opaque" else "department names") if y == Y[0] else None)
    b.set_yticks(Y); b.set_yticklabels(LAB); b.set_ylim(-0.6, len(M) - 0.4); pct_axis(b)
    b.set_title("Allowed requests refused, by naming style"); b.set_xlabel("Share of allowed requests (quick answer)")
    b.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.2)
    save(fig, "a_rank")


if __name__ == "__main__":
    for f in (fig_design, fig_clause, fig_heat, fig_refusal, fig_conf, fig_know, fig_mitig, fig_order, fig_banks, fig_rank):
        f()
    print("figures written")
