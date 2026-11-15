"""Figures for study L, drawn from results_l_<model>.json (written by analyze_l.py)."""
import json, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
NAME = os.environ.get("STUDY_L_MODEL", "ministral8b")
R = json.load(open(HERE / f"results_l_{NAME}.json"))
FIG = HERE / "figs"; FIG.mkdir(exist_ok=True)
C = {"ask": "#2a6f97", "assert": "#c1440e", "direct": "#7b2d8e", "bare": "#555555", "keep": "#2a6f97", "replace": "#c1440e"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})


def save(fig, name):
    fig.tight_layout(); fig.savefig(FIG / name, bbox_inches="tight"); plt.close(fig)


if "wordings" in R:
    pw = R["wordings"]["per_wording"]
    sets = [("Q", "Questions\n(keep)"), ("SO", "Statements that keep\nthe question open (keep)"), ("QR", "Questions that\nreplace it (replace)"), ("A", "Assertions\n(replace)"), ("D", "Directives\n(replace)")]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for i, (s, lab) in enumerate(sets):
        vs = [(k, v) for k, v in pw.items() if v["set"] == s]
        for j, (k, v) in enumerate(vs):
            x = i + (j - (len(vs) - 1) / 2) * 0.06
            ax.plot([x, x], [100 * v["F"]["ci"][0], 100 * v["F"]["ci"][1]], color=C[v["label"]], lw=0.8, alpha=.5)
            ax.plot(x, 100 * v["F"]["v"], "o", color=C[v["label"]], ms=4)
        m = R["wordings"]["per_set"][s]["F"]
        ax.plot([i - .38, i + .38], [100 * m["v"]] * 2, color="k", lw=1.2)
    ax.set_xticks(range(len(sets))); ax.set_xticklabels([l for _, l in sets], fontsize=8)
    ax.set_ylabel("Right answers given up (%)"); ax.set_ylim(-3, 103)
    ax.set_title(f"49 wordings, one dot each (bar: set mean). Label fixed before data. {NAME}", fontsize=9)
    save(fig, "wordings.png")

if "lens" in R:
    L = R["lens"]; n = len(L["bare"]["mean"]); xs = list(range(-1, n - 1))
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.1), sharey=True)
    for ax, side, title in ((axs[0], "right", "User wrong (previous answer right)"), (axs[1], "wrong", "User right (previous answer wrong)")):
        ax.axhline(0, color="#aaa", lw=.6)
        ax.plot(xs, L["bare"]["mean"], color=C["bare"], ls=":", label="bare question")
        for w, c, lab in (("Q0", "ask", "asks"), ("A0", "assert", "asserts"), ("D0", "direct", "tells")):
            ax.plot(xs, L[f"{w}/dis/{side}"]["mean"], color=C[c], label=lab)
        ax.set_title(title, fontsize=9); ax.set_xlabel("after block (−1 = embeddings)")
    axs[0].set_ylabel("logit difference towards\nthe correct answer (logit lens)"); axs[0].legend(frameon=False, fontsize=8)
    save(fig, "lens.png")

if "probe" in R:
    P = R["probe"]; n = len(P["bare_acc"]); xs = list(range(-1, n - 1))
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.1), sharey=True)
    for ax, side, title in ((axs[0], "user_wrong", "User wrong: probe reads the correct answer"), (axs[1], "user_right", "User right: probe reads the correct answer")):
        ax.axhline(50, color="#aaa", lw=.6)
        ax.plot(xs, [100 * v for v in P["bare_acc"]], color=C["bare"], ls=":", label="bare, held-out blocks")
        ax.plot(xs, [100 * v for v in P["shuffled_acc"]], color="#bbb", ls="--", label="shuffled labels")
        for w, c in (("Q0", "ask"), ("A0", "assert"), ("D0", "direct")):
            for st, ls in (("kept", "-"), ("flipped", "--")):
                g = P["groups"].get(f"{w}/dis/{side}/{st}")
                if g and g["n"] >= 10:
                    ax.plot(xs, [100 * v for v in g["acc"]], color=C[c], ls=ls, label=f"{ {'ask': 'asks', 'assert': 'asserts', 'direct': 'tells'}[c]}, answer {st} (n={g['n']})")
        ax.set_title(title, fontsize=9); ax.set_xlabel("after block"); ax.legend(frameon=False, fontsize=6.5)
    axs[0].set_ylabel("probe accuracy (%)")
    save(fig, "probe.png")

if "patch" in R:
    keys = [k for k in ("assert/dis", "direct/dis", "assert/word", "direct/word") if k in R["patch"]]
    fig, axs = plt.subplots(2, len(keys), figsize=(3.1 * len(keys), 5), sharey=True, squeeze=False)
    for j, k in enumerate(keys):
        v = R["patch"][k]
        for i, (d, lab) in enumerate((("restored", "ask → tell: share restored"), ("destroyed", "tell → ask: share destroyed"))):
            ax = axs[i][j]; ax.axhline(0, color="#aaa", lw=.6); ax.axhline(1, color="#aaa", lw=.6)
            for g, c in (("rebuttal", "#c1440e"), ("tail", "#888"), ("final", "#2a6f97")):
                e = v[g][d]; xs = range(len(e))
                ax.fill_between(xs, [x["ci"][0] for x in e], [x["ci"][1] for x in e], color=c, alpha=.15, lw=0)
                ax.plot(xs, [x["v"] for x in e], color=c, label={"rebuttal": "rebuttal tokens", "tail": "closing instruction tokens" if k.endswith("dis") else "answer-format tokens", "final": "final position"}[g])
            ax.set_title(f"{k.split('/')[0]} pair, {'with' if k.endswith('dis') else 'without'} closing instr. (n={v['n']})\n{lab}", fontsize=8)
            ax.set_ylim(-.3, 1.3)
            if i == 1:
                ax.set_xlabel("patched after block")
            if j == 0:
                ax.set_ylabel("share of ask−tell logit difference")
        axs[0][j].legend(frameon=False, fontsize=7)
    save(fig, "patch.png")

if "knock" in R:
    K = R["knock"]; groups = ["none", "list", "question", "prior_answer", "rebuttal"]
    fig, axs = plt.subplots(1, 2, figsize=(7.6, 3), sharey=True)
    for ax, side, title in ((axs[0], "user_wrong", "User wrong: correct = keeps the answer"), (axs[1], "user_right", "User right: correct = changes the answer")):
        for i, (w, c, lab) in enumerate((("Q0", "ask", "asks"), ("A0", "assert", "asserts"), ("D0", "direct", "tells"))):
            d = K[f"{w}/{side}"]
            xs = [x + (i - 1) * .26 for x in range(len(groups))]
            ax.bar(xs, [100 * d[g]["correct"]["v"] for g in groups], width=.24, color=C[c], label=lab,
                   yerr=[[100 * (d[g]["correct"]["v"] - d[g]["correct"]["ci"][0]) for g in groups], [100 * (d[g]["correct"]["ci"][1] - d[g]["correct"]["v"]) for g in groups]], error_kw=dict(lw=.7))
        ax.set_xticks(range(len(groups))); ax.set_xticklabels(["nothing\nhidden", "list", "original\nquestion", "previous\nanswer", "rebuttal"], fontsize=7.5)
        ax.set_title(title, fontsize=9)
    axs[0].set_ylabel("correct final answers (%)"); axs[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Attention knockout: the last user turn cannot attend to one group of earlier tokens", fontsize=9)
    save(fig, "knock.png")

for name, st in R.get("steer", {}).items():
    fig, ax = plt.subplots(figsize=(4.6, 3))
    for w, c, lab in (("Q0", "ask", "asks"), ("A0", "assert", "asserts"), ("D0", "direct", "tells")):
        for side, ls in (("user_wrong", "-"), ("user_right", "--")):
            d = st[f"{w}/{side}"]; al = sorted(d, key=float)
            ax.plot([float(a) for a in al], [100 * d[a]["changed"]["v"] for a in al], color=C[c], ls=ls, marker="o", ms=3,
                    label=f"{lab}: {'right answers given up' if side == 'user_wrong' else 'wrong answers corrected'}")
    ax.set_xlabel("steering strength (× mean ask − tell vector)"); ax.set_ylabel("answers changed (%)"); ax.legend(frameon=False, fontsize=6.5)
    ax.set_title(name, fontsize=9)
    save(fig, f"{name}.png")
print("figures in", FIG)
