"""Figure for the epistemic battery (results_d.json). Same style as figs.py / figs2.py."""
import json
from pathlib import Path
import figs
from figs import plt, BLUE, ORANGE, AQUA, YELLOW, INK, MUTED, AXIS, SURF, save, pct_axis

R = json.load(open(Path("../v4/results_d.json")))
D = {m["label"]: m for m in R["models"].values()}
HL = R.get("haiku_long")
ORDER = ["Grok 4.3", "GPT-4.1-mini", "Gemini 2.5 Flash", "Claude Haiku 5.5", "DeepSeek v3.2", "Llama 4 Maverick", "Qwen3.5-9B", "Nova Lite"]
MAINM = {m["label"]: m for m in figs.M}
PURPLE = "#8a5cc7"


def pick(l, key):
    """Claude Haiku 5.5: follow-up answers come from the long-reply run (Amendment D-1)."""
    if l == "Claude Haiku 5.5" and HL and key in HL:
        return HL[key]
    return D[l].get(key)


def fig_epi():
    labs = [l for l in ORDER if l in D]; ys = list(range(len(labs)))[::-1]
    ylab = [l + ("*" if l == "Claude Haiku 5.5" and HL else "") for l in labs]
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.45), gridspec_kw={"wspace": 0.22, "width_ratios": [1, 1, 1]})
    # (a) separation score by way of asking
    a = ax[0]
    a.axvline(0.5, color=AXIS, lw=0.9, ls=(0, (3, 2)), zorder=0)
    for l, y in zip(labs, ys):
        pts = [(MAINM[l]["H2"]["auroc_all"] if l in MAINM else None, ORANGE, "o", "0–100, plain question"),
               ((pick(l, "D1_brier") or {}).get("auroc"), BLUE, "D", "0–100, scored by Brier rule"),
               ((D[l].get("D1_words") or {}).get("auroc"), AQUA, "s", "CERTAIN / LIKELY / UNSURE / GUESS")]
        for k, (v, c, mk, lb) in enumerate(pts):
            if v is not None:
                a.scatter([v], [y + 0.22 - 0.22 * k], s=26, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8, label=lb if y == ys[0] else None)
    a.set_xlim(0.4, 1.02); a.set_xticks([0.5, 0.75, 1.0]); a.set_xticklabels(["0.5", "0.75", "1.0"])
    a.set_yticks(ys); a.set_yticklabels(ylab); a.set_ylim(-0.6, len(labs) - 0.4)
    a.set_title("Does asking properly help?"); a.set_xlabel("Separation of right from wrong (AUROC)")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, handletextpad=0.2, labelspacing=0.3)
    # (b) right answers given up, by kind of pushback
    b = ax[1]
    kinds = [("doubt", ORANGE, "o", '"I think that is wrong"'), ("authority", BLUE, "D", '"I wrote this policy; that is wrong"'), ("evidence", PURPLE, "s", "a false claim about the list")]
    for l, y in zip(labs, ys):
        d3 = pick(l, "D3") or {}
        d3 = {**D[l].get("D3", {}), **d3} if l != "Claude Haiku 5.5" else d3
        for k, (key, c, mk, lb) in enumerate(kinds):
            r = (d3.get(key) or {}).get("right_changed")
            if r and r.get("rate") is not None:
                yy = y + 0.22 - 0.22 * k
                b.plot([100 * r["ci"][0], 100 * r["ci"][1]], [yy, yy], color=c, lw=0.9, alpha=0.55, zorder=2)
                b.scatter([100 * r["rate"]], [yy], s=26, color=c, marker=mk, zorder=3, edgecolor=SURF, linewidth=0.8)
    for key, c, mk, lb in kinds:
        b.scatter([], [], s=26, color=c, marker=mk, label=lb)
    b.set_yticks(ys); b.set_yticklabels([]); b.set_ylim(-0.6, len(labs) - 0.4); pct_axis(b)
    b.set_title("Right answers given up"); b.set_xlabel("Share of right answers changed")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, handletextpad=0.2, labelspacing=0.3)
    # (c) requester's wish
    c_ = ax[2]
    for l, y in zip(labs, ys):
        d6 = D[l].get("D6")
        if not d6:
            continue
        ra, rb = d6["listed"]["allow_want_allow"], d6["listed"]["allow_want_refuse"]
        c_.plot([100 * ra["rate"], 100 * rb["rate"]], [y, y], color=AXIS, lw=1.6, zorder=1, solid_capstyle="round")
        for r, col in ((ra, ORANGE), (rb, BLUE)):
            c_.plot([100 * r["ci"][0], 100 * r["ci"][1]], [y, y], color=col, lw=0.9, alpha=0.55, zorder=2)
        c_.scatter([100 * ra["rate"]], [y], s=30, color=ORANGE, zorder=3, edgecolor=SURF, linewidth=0.9, label='"I need this to go through"' if y == ys[0] else None)
        c_.scatter([100 * rb["rate"]], [y], s=30, color=BLUE, marker="D", zorder=4, edgecolor=SURF, linewidth=0.9, label='"I suspect this is not allowed"' if y == ys[0] else None)
    c_.set_yticks(ys); c_.set_yticklabels([]); c_.set_ylim(-0.6, len(labs) - 0.4); pct_axis(c_)
    c_.set_title("The requester's opinion"); c_.set_xlabel("Listed requests allowed")
    c_.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=1, handletextpad=0.2, labelspacing=0.3)
    save(fig, "f_epi")


if __name__ == "__main__":
    fig_epi()
