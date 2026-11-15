"""Figure for the harness-side fixes (results_e.json). Same style as the other figures."""
import json
from pathlib import Path
import figs
from figs import plt, BLUE, ORANGE, AQUA, AXIS, SURF, save, pct_axis

R = json.load(open(Path("../v4/results_e.json")))
E = {m["label"]: m for m in R["models"].values()}
ORDER = ["Grok 4.3", "GPT-4.1-mini", "Gemini 2.5 Flash", "Claude Haiku 5.5", "DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B", "Nova Lite"]


def fig_fix():
    labs = [l for l in ORDER if l in E]; ys = list(range(len(labs)))[::-1]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.0), gridspec_kw={"wspace": 0.12})
    arms = [("base", ORANGE, "o", "no fix"), ("E1", AQUA, "s", "model checks the claim first"), ("E2", BLUE, "D", "harness checks the claim and says so")]
    for a, key, title, xl in ((ax[0], "right_changed", "False claim: right answers given up", "Share of right answers changed (lower is better)"),
                              (ax[1], "wrong_changed", "True claim: wrong answers corrected", "Share of wrong answers changed (higher is better)")):
        for l, y in zip(labs, ys):
            xs = [100 * E[l][arm][key]["rate"] for arm, *_ in arms]
            a.plot([min(xs), max(xs)], [y, y], color=AXIS, lw=1.4, zorder=1, solid_capstyle="round")
            for (arm, c, mk, lb), x in zip(arms, xs):
                a.scatter([x], [y], s=30, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8, label=lb if y == ys[0] else None)
        a.set_yticks(ys); a.set_yticklabels([l + ("*" if l == "Claude Haiku 5.5" else "") for l in labs] if a is ax[0] else [])
        a.set_ylim(-0.6, len(labs) - 0.4); pct_axis(a); a.set_title(title); a.set_xlabel(xl)
    ax[0].legend(loc="upper center", bbox_to_anchor=(1.06, -0.3), ncol=3, handletextpad=0.2, columnspacing=1.2)
    save(fig, "f_fix")


if __name__ == "__main__":
    fig_fix()
