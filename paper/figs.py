"""All paper figures, generated from fig_data.json. Vector SVG, one style, colour-blind-validated palette."""
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
    "font.family": "Inter", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7,
    "ytick.labelsize": 7.5, "legend.fontsize": 7, "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "svg.fonttype": "path", "figure.facecolor": SURF, "axes.facecolor": SURF,
    "legend.frameon": False, "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 6})
LAB = [m["label"] for m in M]
Y = list(range(len(M)))[::-1]
CELL_LAB = {"BOTH": "B", "FWD": "F", "REV": "R", "REV_PATH": "R+C", "NEI_PATH": "C", "NEI_NOPATH": "N"}


def save(fig, name):
    fig.savefig(f"figs/{name}.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(f"figs/{name}.png", bbox_inches="tight", pad_inches=0.03, dpi=110)
    plt.close(fig)


def toplegend(fig, ax, ncol=3, y=1.0):
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, y), ncol=ncol, columnspacing=1.6, handletextpad=0.3)


def pct_axis(ax, lo=0, hi=100, step=25):
    ax.set_xlim(lo, hi)
    ax.set_xticks(range(lo, hi + 1, step))
    ax.set_xticklabels([f"{t}%" for t in range(lo, hi + 1, step)])
    ax.yaxis.grid(False)


def dumbbell(ax, key_a, key_b, metric, col_a, col_b, lab_a, lab_b, title, show_y=True, legend=True):
    for y, m in zip(Y, M):
        a, b = m["rates"][key_a][metric], m["rates"][key_b][metric]
        ax.plot([100 * a["rate"], 100 * b["rate"]], [y, y], color=AXIS, lw=1.6, zorder=1, solid_capstyle="round")
        for r, c, dy in ((a, col_a, 0.0), (b, col_b, 0.0)):
            ax.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y + dy, y + dy], color=c, lw=0.9, alpha=0.55, zorder=2)
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


# ---------------------------------------------------------------- Figure 1: design schematic
def fig_design():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.1))
    P = {"A": (0, 1), "B": (1, 1), "C": (1, 0), "D": (0, 0)}

    def graph(ax, routes, reqs, title, note):
        ax.set_xlim(-0.55, 1.55); ax.set_ylim(-0.62, 1.42); ax.set_aspect("equal"); ax.axis("off")
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
            ax.text(mx, my, lab, ha="center", va="center", fontsize=6.3, color=INK2,
                    bbox=dict(boxstyle="round,pad=0.18", fc=SURF, ec=col, lw=0.7))
        ax.text(0.5, -0.58, note, ha="center", va="center", fontsize=6.6, color=INK2)

    graph(axes[0], [("A", "B"), ("B", "A"), ("B", "C"), ("C", "D")],
          [(("B", "C"), "forward only", True, -0.55, (0.47, 0.0)), (("C", "B"), "reverse only", False, -0.55, (-0.27, 0.2)),
           (("A", "C"), "chain only", False, 0.0, (-0.2, -0.2)), (("D", "A"), "no route", False, -0.5, (-0.36, 0.0))],
          "Mixed policy", "separates every denial type")
    graph(axes[1], [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")],
          [(("B", "A"), "reverse + chain", False, -0.45, (0.0, 0.3)), (("C", "D"), "forward only", True, -0.5, (0.0, -0.33))],
          "Ring policy", "every denial is reverse AND chain")
    graph(axes[2], [("A", "B"), ("B", "A"), ("C", "D"), ("D", "C")],
          [(("A", "B"), "both listed", True, -0.75, (0.0, 0.36)), (("B", "C"), "no route", False, -0.4, (0.36, 0.0))],
          "Reciprocal policy", "no direction to get wrong")
    fig.legend(handles=[plt.Line2D([], [], color="#3a3a38", lw=1.4, label="listed route"),
                        plt.Line2D([], [], color=BLUE, lw=1.1, ls=(0, (3, 2)), label="request, should be allowed"),
                        plt.Line2D([], [], color=ORANGE, lw=1.1, ls=(0, (3, 2)), label="request, should be declined")],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.07), columnspacing=1.6)
    save(fig, "f1_design")


# ---------------------------------------------------------------- Figure 2: chaining and the clause
def fig_clause():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True, gridspec_kw={"wspace": 0.12})
    dumbbell(ax[0], "E1/base", "E1/explicit", "chain_release", ORANGE, BLUE, "original wording", "with no-chaining clause",
             "Direct one-word answer", legend=False)
    dumbbell(ax[1], "E5/base", "E5/explicit", "chain_release", ORANGE, BLUE, "original wording", "with no-chaining clause",
             "After step-by-step reasoning", show_y=False)
    for a in ax:
        a.set_xlabel("Chain-reachable requests wrongly released")
    toplegend(fig, ax[1], 2, 0.97)
    save(fig, "f2_clause")


# ---------------------------------------------------------------- Figure 3: error heat map
def fig_heat():
    panels = [("E1", "base", "Direct, original"), ("E1", "explicit", "Direct, with clause"),
              ("E5", "base", "Reasoning, original"), ("E5", "explicit", "Reasoning, with clause")]
    fig, axes = plt.subplots(1, 4, figsize=(7.0, 2.7), sharey=True, gridspec_kw={"wspace": 0.05})
    for ax, (e, cl, title) in zip(axes, panels):
        grid = []
        for m in M:
            c = m["cells"][e][cl]
            grid.append([100 * (c[k]["wrong_decline"] + c[k]["wrong_execute"]) / c[k]["n"] for k in D["cells"]])
        im = ax.imshow(grid, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
        ax.set_title(title, fontsize=7.4)
        ax.set_xticks(range(6)); ax.set_xticklabels([CELL_LAB[k] for k in D["cells"]], fontsize=6.4, color=INK2)
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
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6, color="#ffffff" if v > 45 else INK)
        ax.text(0.5, len(M) + 0.55, "refused", ha="center", fontsize=6, color=MUTED)
        ax.text(3.5, len(M) + 0.55, "released", ha="center", fontsize=6, color=MUTED)
    cb = fig.colorbar(im, ax=axes, fraction=0.012, pad=0.012)
    cb.set_label("error rate (%)", fontsize=6.5); cb.ax.tick_params(labelsize=6, length=0); cb.outline.set_visible(False)
    save(fig, "f3_heat")


# ---------------------------------------------------------------- Figure 4: over-refusal
def fig_refusal():
    fig = plt.figure(figsize=(7.0, 2.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 1, 1], wspace=0.34)
    ax = fig.add_subplot(gs[0])
    dumbbell(ax, "E1/base", "E1/explicit", "listed_refusal", ORANGE, BLUE, "original wording", "with clause",
             "Listed requests refused (direct answer)")
    for y, m in zip(Y, M):
        lk = m["components"]["lookup"]
        ax.scatter([100 * (1 - lk[0] / lk[1])], [y], marker="|", s=70, color=INK, zorder=5, linewidth=1.1,
                   label="lookup error on the same routes" if y == Y[0] else None)
    ax.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.1, labelspacing=0.3)
    ax.set_xlabel("Share of listed requests")
    series = [("Grok 4.3", BLUE), ("DeepSeek v3.2", ORANGE), ("Llama 4 Maverick", AQUA), ("Qwen3.5-9B", YELLOW)]
    prev = None
    for k, (sf, title) in enumerate((("opaque", "Opaque tokens, arrows"), ("natural", "Departments, sentences"))):
        a = fig.add_subplot(gs[1 + k], sharey=prev) if prev is not None else fig.add_subplot(gs[1 + k])
        prev = a
        for lab, col in series:
            m = next(x for x in M if x["label"] == lab)
            ys = [100 * m["refusal_by_position"][f"{sf}/{p}"][0] / m["refusal_by_position"][f"{sf}/{p}"][1] for p in range(4)]
            a.plot([1, 2, 3, 4], ys, color=col, lw=1.6, marker="o", ms=4.2, mec=SURF, mew=0.8, label=lab, solid_capstyle="round")
        a.set_title(title); a.set_xticks([1, 2, 3, 4]); a.set_xlabel("Line holding the matching route")
        a.set_ylim(0, 100); a.set_yticks([0, 25, 50, 75, 100])
        a.xaxis.grid(False); a.tick_params(axis="y", colors=MUTED)
        if k == 0:
            a.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
            a.yaxis.tick_right(); a.tick_params(axis="y", labelright=False, labelleft=True)
        else:
            a.tick_params(labelleft=False)
            a.legend(loc="upper left", handlelength=1.4, borderaxespad=0.1)
    save(fig, "f4_refusal")


# ---------------------------------------------------------------- Figure 5: confidence and re-check
def fig_conf():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.28})
    a = ax[0]
    for y, m in zip(Y, M):
        def share(kinds):
            tot = sum(sum(m["confidence"].get(k, {}).values()) for k in kinds)
            hi = sum(m["confidence"].get(k, {}).get(b, 0) for k in kinds for b in ("100", "90-99"))
            return 100 * hi / tot if tot else None
        c, w = share(["correct"]), share(["wrong_release", "wrong_refusal"])
        a.plot([c, w], [y, y], color=AXIS, lw=1.6, zorder=1)
        a.scatter([c], [y + 0.13], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9, label="when correct" if y == Y[0] else None)
        a.scatter([w], [y - 0.13], s=30, color=ORANGE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9,
                  label="when wrong" if y == Y[0] else None)
    a.set_yticks(Y); a.set_yticklabels(LAB); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a)
    a.set_title("Decisions given confidence of 90 or more"); a.set_xlabel("Share of direct decisions")
    a.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.2)
    b = ax[1]
    b.plot([0, 100], [0, 100], color=AXIS, lw=0.9, zorder=1)
    b.text(84, 76, "no discrimination", rotation=40, fontsize=6.3, color=MUTED, ha="center", va="center")
    nudge = {"Grok 4.3": (4, -1), "GPT-4.1": (6, 17), "Claude Haiku 5.5": (6, 9), "Gemini 2.5 Flash": (-3, 4), "GPT-4.1-mini": (-3, -4),
             "DeepSeek v3.2": (3, -4), "Llama 4 Maverick": (3, 0), "Qwen3.5-9B": (3, -3), "Nova Lite": (-3, -5)}
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
    b.set_xlabel("Correct decisions changed"); b.set_ylabel("Wrong decisions changed"); b.set_title("Asked to re-check, the model says CHANGE")
    save(fig, "f5_conf")


# ---------------------------------------------------------------- Figure 6: knowing versus doing
def fig_know():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.5), gridspec_kw={"width_ratios": [1.45, 1], "wspace": 0.14}, sharey=True)
    a = ax[0]
    ser = [("roles", "names both roles", BLUE, "o", 0.24), ("lookup", "finds the directed route", AQUA, "s", 0.08),
           ("decision_reasoned", "decides, with reasoning", YELLOW, "^", -0.08), ("decision", "decides, direct answer", ORANGE, "D", -0.24)]
    for y, m in zip(Y, M):
        a.plot([50, 100], [y, y], color=GRID, lw=0.6, zorder=0)
        for key, lab, col, mk, dy in ser:
            v = 100 * m["components"][key][0] / m["components"][key][1]
            a.scatter([v], [y + dy], s=26, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8, label=lab if y == Y[0] else None)
    a.set_yticks(Y); a.set_yticklabels(LAB); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a, 50, 100, 10)
    a.set_title("Accuracy on the parts and on the whole"); a.set_xlabel("Accuracy (both wordings pooled)")
    a.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.2, labelspacing=0.3)
    b = ax[1]
    for y, m in zip(Y, M):
        c = m["components"]
        v = 100 * c["wrong_both_right"] / c["wrong_total"]
        b.barh([y], [v], height=0.42, color=BLUE)
        b.text(v - 2, y, f'{c["wrong_both_right"]}/{c["wrong_total"]}', ha="right", va="center", fontsize=6.4, color="#ffffff")
    pct_axis(b); b.set_title("Wrong decisions with both parts right"); b.set_xlabel("Share of wrong direct decisions")
    save(fig, "f6_know")


# ---------------------------------------------------------------- Figure 7: mitigations
def fig_mitig():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True, gridspec_kw={"wspace": 0.1})
    ser = [("E4", "restate the route first", BLUE, "o", 0.24), ("E4p", "placebo line first", YELLOW, "s", 0.0), ("E5", "step-by-step reasoning", AQUA, "^", -0.24)]
    for a, metric, title, lim in ((ax[0], "chain_release", "Change in chain-reachable requests released", (-60, 80)),
                                  (ax[1], "listed_kept", "Change in listed requests allowed", (-25, 60))):
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
        a.set_xlim(*lim); a.set_title(title); a.set_xlabel("Percentage points versus direct answer")
    ax[0].text(-58, -0.52, "← fewer wrong releases", fontsize=6.2, color=MUTED, va="center")
    ax[1].text(58, -0.52, "more authorized requests allowed →", fontsize=6.2, color=MUTED, va="center", ha="right")
    toplegend(fig, ax[0], 3, 0.97)
    save(fig, "f7_mitig")


# ---------------------------------------------------------------- Figure 8: role order
def fig_order():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.4), gridspec_kw={"width_ratios": [1, 1.2], "wspace": 0.6})
    g = next(m for m in M if m["label"] == "GPT-4.1")
    a = ax[0]
    cells = ["FWD", "BOTH", "REV", "REV_PATH"]
    for i, c in enumerate(cells):
        for k, (rec, col, lab) in enumerate((("d_first", BLUE, "document scope printed first"), ("a_first", ORANGE, "active scope printed first"))):
            w, n = g["wrong_by_role_order"][f"{c}/{rec}"]
            a.bar([i + (k - 0.5) * 0.34], [100 * w / n], width=0.3, color=col, label=lab if i == 0 else None)
            a.text(i + (k - 0.5) * 0.34, 100 * w / n + 0.8, f"{w}/{n}", ha="center", va="bottom", fontsize=6, color=INK2)
    a.set_xticks(range(4)); a.set_xticklabels(["Forward\nonly", "Both\nlisted", "Reverse\nonly", "Reverse\n+ chain"], color=INK2)
    a.set_ylim(0, 30); a.set_yticks([0, 10, 20, 30]); a.set_yticklabels(["0%", "10%", "20%", "30%"]); a.tick_params(axis="y", colors=MUTED)
    a.xaxis.grid(False); a.set_title("GPT-4.1: wrong direct decisions"); a.legend(loc="upper left", borderaxespad=0.1)
    b = ax[1]
    for y, m in zip(Y, M):
        tot = {rec: [sum(v[0] for k, v in m["wrong_by_role_order"].items() if k.endswith(rec)),
                     sum(v[1] for k, v in m["wrong_by_role_order"].items() if k.endswith(rec))] for rec in ("d_first", "a_first")}
        d, av = 100 * tot["d_first"][0] / tot["d_first"][1], 100 * tot["a_first"][0] / tot["a_first"][1]
        b.plot([d, av], [y, y], color=AXIS, lw=1.6, zorder=1)
        b.scatter([d], [y], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9, label="document scope first" if y == Y[0] else None)
        b.scatter([av], [y], s=30, color=ORANGE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9, label="active scope first" if y == Y[0] else None)
    b.set_yticks(Y); b.set_yticklabels(LAB); b.set_ylim(-0.6, len(M) - 0.4); pct_axis(b, 0, 50, 10)
    b.set_title("All models: wrong direct decisions by role order"); b.set_xlabel("Share of direct decisions")
    b.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.2)
    save(fig, "f8_order")


# ---------------------------------------------------------------- Appendix figures
def fig_banks():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True, gridspec_kw={"wspace": 0.12})
    for a, key, metric, title in ((ax[0], "E5", "chain_release", "Chain-reachable requests released, with reasoning"),
                                  (ax[1], "E1", "listed_refusal", "Listed requests refused, direct answer")):
        for y, m in zip(Y, M):
            for cl, col, dy in (("base", ORANGE, 0.17), ("explicit", BLUE, -0.17)):
                vals = sorted(m["rates"][f"{key}/{cl}"][metric]["per_bank"].values())
                a.scatter([100 * v for v in vals], [y + dy + ((i % 3) - 1) * 0.045 for i in range(len(vals))], s=9, color=col, alpha=0.75,
                          linewidth=0, zorder=3, label=("original wording" if cl == "base" else "with clause") if y == Y[0] else None)
        a.set_yticks(Y); a.set_ylim(-0.6, len(M) - 0.4); pct_axis(a); a.set_title(title)
        if a is ax[0]:
            a.set_yticklabels(LAB)
        a.set_xlabel("Rate within one bank (each dot is one bank)")
    toplegend(fig, ax[1], 2, 0.97)
    save(fig, "a2_banks")


def fig_rank():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.7), gridspec_kw={"wspace": 0.62})
    a = ax[0]
    a.plot([50, 100], [50, 100], color=AXIS, lw=0.9)
    nudge = {"Grok 4.3": (1.2, -1.5), "Nova Lite": (1.2, -2.2), "Qwen3.5-9B": (-1.2, -1.5), "DeepSeek v3.2": (1.2, 1.2), "Llama 4 Maverick": (-1.2, 1.5),
             "GPT-4.1": (-1.2, 2.2), "GPT-4.1-mini": (-1.2, -0.5), "Gemini 2.5 Flash": (1.2, -2.5), "Claude Haiku 5.5": (-1.2, -3.2)}
    for m in M:
        x, y = 100 * m["H7"]["symmetric_subset_acc"], 100 * m["H7"]["oneway_subset_acc"]
        a.scatter([x], [y], s=30, color=BLUE, zorder=3, edgecolor=SURF, linewidth=0.9)
        dx, dy = nudge[m["label"]]
        a.annotate(m["label"], (x, y), xytext=(x + dx, y + dy), fontsize=6.2, color=INK2, ha="left" if dx > 0 else "right", va="center")
    a.set_xlim(55, 101); a.set_ylim(55, 101); a.set_xlabel("Accuracy, symmetric requests (both listed, no route)")
    a.set_ylabel("Accuracy, one-way requests"); a.set_title("Model ranking barely changes (ρ = 0.91)"); a.tick_params(axis="y", colors=MUTED)
    b = ax[1]
    for y, m in zip(Y, M):
        for sf, col, mk in (("opaque", BLUE, "o"), ("natural", ORANGE, "D")):
            pos = m["refusal_by_position"]
            k = sum(pos[f"{sf}/{p}"][0] for p in range(4)); n = sum(pos[f"{sf}/{p}"][1] for p in range(4))
            b.scatter([100 * k / n], [y], s=30, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.9,
                      label=("opaque tokens" if sf == "opaque" else "department sentences") if y == Y[0] else None)
    b.set_yticks(Y); b.set_yticklabels(LAB); b.set_ylim(-0.6, len(M) - 0.4); pct_axis(b)
    b.set_title("Listed requests refused, by surface"); b.set_xlabel("Share of listed requests (direct answer)")
    b.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.2)
    save(fig, "a3_rank")


for f in (fig_design, fig_clause, fig_heat, fig_refusal, fig_conf, fig_know, fig_mitig, fig_order, fig_banks, fig_rank):
    f()
print("figures written")
