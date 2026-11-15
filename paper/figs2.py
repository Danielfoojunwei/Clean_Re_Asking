"""Figures for Stages 2 and 3, from results_b.json, results_c.json and the open-model results. Same style as figs.py."""
import json, os
from pathlib import Path
import numpy as np
import figs
from figs import plt, BLUE, ORANGE, AQUA, YELLOW, INK, INK2, MUTED, GRID, AXIS, SURF, SEQ, save, pct_axis

V3 = Path("../v3"); MECH = Path("../mech/out_qwen15")
B = {m["label"]: m for m in json.load(open(V3 / "results_b.json"))["models"]}
C = {m["label"]: m for m in json.load(open(V3 / "results_c.json"))["models"].values()}
MAINM = {m["label"]: m for m in figs.M}
ORDER = ["Grok 4.3", "Gemini 2.5 Flash", "Claude Haiku 5.5", "DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B", "Nova Lite"]
P = lambda x: 100 * x["rate"]


def rows(have):
    labs = [l for l in ORDER if have(l)]
    return labs, list(range(len(labs)))[::-1]


def bell(ax, labs, ys, a, b, la, lb, title, xlabel, show_y=True, ca=ORANGE, cb=BLUE):
    for l, y in zip(labs, ys):
        ra, rb = a(l), b(l)
        ax.plot([P(ra), P(rb)], [y, y], color=AXIS, lw=1.6, zorder=1, solid_capstyle="round")
        for r, c in ((ra, ca), (rb, cb)):
            ax.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y, y], color=c, lw=0.9, alpha=0.55, zorder=2)
        ax.scatter([P(ra)], [y], s=34, color=ca, zorder=3, edgecolor=SURF, linewidth=0.9, label=la if y == ys[0] else None)
        ax.scatter([P(rb)], [y], s=34, color=cb, zorder=4, edgecolor=SURF, linewidth=0.9, marker="D", label=lb if y == ys[0] else None)
    ax.set_yticks(ys); ax.set_yticklabels(labs if show_y else []); ax.set_ylim(-0.6, len(labs) - 0.4); pct_axis(ax)
    ax.set_title(title); ax.set_xlabel(xlabel)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, handletextpad=0.2, labelspacing=0.3)


COL = {"Grok 4.3": "#0d366b", "Gemini 2.5 Flash": BLUE, "DeepSeek v3.2": ORANGE, "Llama 4 Maverick": AQUA, "Qwen3.5-9B": YELLOW, "Nova Lite": "#8a5cc7"}


def size_lines(ax, key, title, ylabel, legend=False):
    for l in ORDER:
        if l in C and "X1" in C[l]:
            d = C[l]["X1"][key]
            ax.plot(range(4), [P(d[str(K)]) for K in (4, 8, 16, 32)], color=COL[l], lw=1.5, marker="o", ms=3.8, mec=SURF, mew=0.7, label=l)
    ax.set_xticks(range(4)); ax.set_xticklabels(["4", "8", "16", "32"]); ax.set_xlabel("Rules in the rulebook")
    ax.set_ylim(0, 100); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); ax.xaxis.grid(False)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.tick_params(axis="y", colors=MUTED)
    if legend:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=2, handlelength=1.2, columnspacing=0.8, labelspacing=0.25, fontsize=6.1)


# ---------------------------------------------------------------- why models chain
def fig_why_chain():
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.3), gridspec_kw={"wspace": 0.95, "width_ratios": [1, 1.05, 1]})
    labs, ys = rows(lambda l: l in C and "X4" in C[l])
    bell(ax[0], labs, ys, lambda l: C[l]["X4"]["E5"]["chain_route"], lambda l: C[l]["X4"]["E5"]["chain_entry"], 'rule says "route"', 'rule says "entry"',
         "A different word", "Chain requests allowed (step-by-step)")
    size_lines(ax[1], "chain_release", "A longer rulebook", "Chain requests allowed (quick)", legend=True)
    labs, ys = rows(lambda l: l in C and "X6" in C[l])
    bell(ax[2], labs, ys, lambda l: C[l]["X6"]["base"]["chain_off"], lambda l: C[l]["X6"]["base"]["chain_on"], "hidden reasoning off", "hidden reasoning on",
         "Hidden reasoning", "Chain requests allowed (quick)")
    save(fig, "f_why_chain")


# ---------------------------------------------------------------- why models refuse allowed requests
CONDS = [("base", "as\nwritten"), ("placebo", "filler\nsentence"), ("exact", '"exact\nline"'), ("norev", '"no re-\nversing"'), ("nochain", '"no\nchaining"'),
         ("explicit", "full\nsentence"), ("balanced", "balanced\nsentence")]


def fig_why_refuse():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.25), gridspec_kw={"wspace": 0.5, "width_ratios": [1.9, 1]})
    labs = [l for l in ORDER if l in B]
    Z = np.array([[P(B[l]["E1"][c]["listed_refusal"]) for c, _ in CONDS] for l in labs])
    a = ax[0]; a.imshow(Z, cmap=SEQ, vmin=0, vmax=70, aspect="auto"); a.grid(False)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            a.text(j, i, f"{Z[i, j]:.0f}", ha="center", va="center", fontsize=6.8, color="#ffffff" if Z[i, j] > 42 else INK)
    a.set_xticks(range(len(CONDS))); a.set_xticklabels([c for _, c in CONDS], fontsize=6.2); a.set_yticks(range(len(labs))); a.set_yticklabels(labs)
    a.set_title("Allowed requests refused (%), by the sentence added to the rule"); a.axvline(0.5, color=SURF, lw=2.5)
    for sp in a.spines.values():
        sp.set_visible(False)
    labs, ys = rows(lambda l: l in C and "X3" in C[l])
    bell(ax[1], labs, ys, lambda l: C[l]["X3"]["listed_refusal_quick"], lambda l: C[l]["X3"]["listed_refusal_scaffold"], "quick answer", 'first answers "is the rule listed?"',
         "Stating the rule first", "Allowed requests refused")
    save(fig, "f_why_refuse")


# ---------------------------------------------------------------- is there a usable signal
def fig_signal():
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.2), gridspec_kw={"wspace": 0.22, "width_ratios": [1.05, 1, 1]})
    a = ax[0]
    labs = [l for l in ORDER if l in B and "token_prob" in B[l]]
    probe = None
    names = labs + (["Qwen2.5-1.5B\n(run locally)"] if probe else []); ys = list(range(len(names)))[::-1]
    for l, y in zip(labs, ys):
        s = MAINM[l]["H2"]["auroc_all"]; t = B[l]["token_prob"]["all"]
        a.scatter([s], [y], s=34, color=ORANGE, zorder=3, edgecolor=SURF, linewidth=0.9, label="what the model says (0-100)" if y == ys[0] else None)
        a.plot(t["ci"], [y, y], color=BLUE, lw=0.9, alpha=0.55); a.scatter([t["auroc"]], [y], s=34, color=BLUE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9,
                                                                    label="its answer-word probabilities" if y == ys[0] else None)
    if probe:
        y = ys[-1]; bc = probe["best_correct"]
        a.plot(bc["margin_auroc_ci"], [y, y], color=BLUE, lw=0.9, alpha=0.55); a.scatter([bc["margin_auroc"]], [y], s=34, color=BLUE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9)
        a.plot(bc["probe_auroc_ci"], [y - .001, y - .001], color=AQUA, lw=0.9, alpha=0.55)
        a.scatter([bc["probe_auroc"]], [y], s=34, color=AQUA, marker="s", zorder=5, edgecolor=SURF, linewidth=0.9, label="a probe on its activations")
    a.axvline(0.5, color=INK, lw=0.8); a.text(0.505, len(names) - 0.55, "chance", fontsize=6, color=MUTED, va="top")
    a.set_xlim(0.4, 1.0); a.set_yticks(ys); a.set_yticklabels(names); a.set_ylim(-0.6, len(names) - 0.4); a.yaxis.grid(False)
    a.set_title("Telling right from wrong"); a.set_xlabel("Separation score (1.0 is perfect)")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, handletextpad=0.2, labelspacing=0.3)
    labs, ys = rows(lambda l: l in C and "X2" in C[l])
    for k, (key, title) in enumerate((("changed_right", "Right answers changed"), ("changed_wrong", "Wrong answers changed"))):
        b = ax[1 + k]
        for l, y in zip(labs, ys):
            for v, col, mk, dy in (("neutral", MUTED, "o", 0.2), ("affirm", AQUA, "s", 0.0), ("doubt", ORANGE, "D", -0.2)):
                r = C[l]["X2"][v][key]
                b.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y + dy, y + dy], color=col, lw=0.9, alpha=0.55)
                b.scatter([P(r)], [y + dy], s=26, color=col, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8,
                          label={"neutral": '"state your final decision"', "affirm": '"I think that is right"', "doubt": '"I think that is wrong"'}[v] if y == ys[0] else None)
        b.set_yticks(ys); b.set_yticklabels(labs if k == 0 else []); b.set_ylim(-0.6, len(labs) - 0.4); pct_axis(b); b.set_title(title)
        b.set_xlabel("Share changed when asked again")
    ax[1].legend(loc="upper left", bbox_to_anchor=(0.0, -0.27), ncol=3, columnspacing=1.0, handletextpad=0.2)
    pos = ax[0].get_position(); ax[0].set_position([pos.x0 - 0.02, pos.y0, pos.width - 0.07, pos.height])
    save(fig, "f_signal")


# ---------------------------------------------------------------- acting instead of answering
def fig_act():
    labs, ys = rows(lambda l: l in C and "X7" in C[l] and l != "Llama 4 Maverick")
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.0), sharey=True, gridspec_kw={"wspace": 0.2})
    for k, (w, act, title) in enumerate((("refusal_words", "refusal_action", "Allowed requests not carried out"), ("chain_words", "chain_action", "Chain requests carried out"),
                                         (None, "none_action", "Unconnected requests carried out"))):
        a = ax[k]
        for l, y in zip(labs, ys):
            x = C[l]["X7"]["base"]
            if w:
                a.plot([P(x[w]), P(x[act])], [y, y], color=AXIS, lw=1.6, zorder=1)
                a.scatter([P(x[w])], [y], s=34, color=ORANGE, zorder=3, edgecolor=SURF, linewidth=0.9, label="answers in words" if y == ys[0] else None)
            else:
                a.scatter([100 * MAINM[l]["rates"]["E1/base"]["none_release"]["rate"]], [y], s=34, color=ORANGE, zorder=3, edgecolor=SURF, linewidth=0.9)
                a.plot([100 * MAINM[l]["rates"]["E1/base"]["none_release"]["rate"], P(x[act])], [y, y], color=AXIS, lw=1.6, zorder=1)
            a.plot([100 * x[act]["ci"][0], 100 * x[act]["ci"][1]], [y, y], color=BLUE, lw=0.9, alpha=0.55)
            a.scatter([P(x[act])], [y], s=34, color=BLUE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9, label="acts with a tool" if y == ys[0] else None)
        a.set_ylim(-0.6, len(labs) - 0.4); pct_axis(a); a.set_title(title); a.set_xlabel("Share of requests")
        if k == 0:
            a.set_yticks(ys); a.set_yticklabels(labs)
    figs.toplegend(fig, ax[0], 2, 0.99)
    save(fig, "f_act")


# ---------------------------------------------------------------- inside an open model
def fig_inside():
    if not (MECH / "probe_results.json").exists():
        return
    pr = json.load(open(MECH / "probe_results.json"))
    st = [json.load(open(p)) for p in sorted(MECH.glob("steer_L*.json"))]
    fig, ax = plt.subplots(1, 2 if st else 1, figsize=(7.0 if st else 3.6, 2.4), gridspec_kw={"wspace": 0.3} if st else None)
    a = ax[0] if st else ax
    L = [r["layer"] for r in pr["layers_listed"]]
    a.plot(L, [100 * r["acc"] for r in pr["layers_listed"]], color=BLUE, lw=1.6, label='probe: "is the rule listed?"')
    a.plot(L, [100 * r["shuffled_acc"] for r in pr["layers_listed"]], color=MUTED, lw=1.1, ls=(0, (3, 2)), label="same probe, shuffled labels")
    a.plot(L, [100 * r["acc_on_wrong_refusals"] for r in pr["layers_listed"]], color=ORANGE, lw=1.4, label="probe, on requests the model wrongly refused")
    a.axhline(100 * pr["model_accuracy"], color=INK, lw=0.9); a.text(0.3, 100 * pr["model_accuracy"] + 1.5, "the model's own decisions", fontsize=6.2, color=INK2)
    a.set_ylim(0, 100); a.set_yticks([0, 25, 50, 75, 100]); a.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); a.set_xlabel("Layer"); a.set_ylabel("Correct on unseen name sets")
    a.set_title("What the activations hold"); a.legend(loc="lower right", handlelength=1.4, borderaxespad=0.2, labelspacing=0.25, fontsize=6.3); a.tick_params(axis="y", colors=MUTED)
    if st:
        b = ax[1]; s = st[0]
        import collections
        base = {r["id"]: r["margin"] for r in s["rows"] if r["dir"] == "none"}
        def flip(group, name, alpha, to_allow):
            rs = [r for r in s["rows"] if r["group"] == group and r["dir"] == name and abs(r["alpha"] - alpha) < 1e-9]
            return 100 * sum((r["margin"] > 0) == to_allow for r in rs) / max(1, len(rs))
        alphas = sorted({r["alpha"] for r in s["rows"] if r["dir"] == "listed"})
        rnd = sorted({r["dir"] for r in s["rows"] if r["dir"].startswith("random")})
        ra = sorted({r["alpha"] for r in s["rows"] if r["dir"].startswith("random")})
        b.plot([0] + [x for x in alphas if x > 0], [flip("wrong_refusal", "none", 0, True)] + [flip("wrong_refusal", "listed", x, True) for x in alphas if x > 0],
               color=BLUE, lw=1.6, marker="o", ms=4, mec=SURF, label="wrong refusals turned into allows")
        b.plot([0] + [x for x in alphas if x > 0], [flip("right_refusal", "none", 0, True)] + [flip("right_refusal", "listed", x, True) for x in alphas if x > 0],
               color=ORANGE, lw=1.6, marker="D", ms=4, mec=SURF, label="correct refusals turned into allows (harm)")
        b.plot([0] + ra, [flip("wrong_refusal", "none", 0, True)] + [np.mean([flip("wrong_refusal", n, x, True) for n in rnd]) for x in ra],
               color=MUTED, lw=1.1, ls=(0, (3, 2)), marker="s", ms=3.5, mec=SURF, label="wrong refusals, random direction")
        b.set_ylim(0, 100); b.set_yticks([0, 25, 50, 75, 100]); b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"]); b.set_xlabel('Strength of the added "rule is listed" direction')
        b.set_ylabel("Share now allowed"); b.set_title(f"Pushing the activations (layer {s['layer']})"); b.legend(loc="upper left", handlelength=1.4, borderaxespad=0.2, labelspacing=0.25, fontsize=6.3)
        b.tick_params(axis="y", colors=MUTED)
    save(fig, "f_inside")


if __name__ == "__main__":
    for f in (fig_why_chain, fig_why_refuse, fig_signal, fig_act):
        f()
    print("stage 2-3 figures written")
