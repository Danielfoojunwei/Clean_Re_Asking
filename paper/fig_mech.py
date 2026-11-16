"""Figure 6 of the paper (Study L, Ministral 8B), drawn from study_local/. Run from paper/."""
import json
from pathlib import Path
import numpy as np
from figs import plt, BLUE, ORANGE, AQUA, INK, INK2, MUTED, AXIS, GRID, save

L = Path("../study_local")
R = json.load(open(L / "results_l_ministral8b.json"))
P = json.load(open(L / "runs" / "ministral8b" / "probe_results.json"))
DEEP = "#b8430f"


def wordings(a):
    pw = R["wordings"]["per_wording"]
    sets = [("Q", "asks", AQUA), ("SO", "hedged\nclaim", AQUA), ("QR", "asks to\nchange", ORANGE), ("A", "asserts", ORANGE), ("D", "tells", ORANGE)]
    rng = np.random.RandomState(3)
    for i, (s_, lab, col) in enumerate(sets):
        v = [100 * x["F"]["v"] for x in pw.values() if x["set"] == s_]
        xs = i + rng.uniform(-0.16, 0.16, len(v))
        a.scatter(xs, v, s=9, color=col, alpha=0.85, edgecolor="white", linewidth=0.3, zorder=3)
        m = 100 * R["wordings"]["per_set"][s_]["F"]["v"]
        a.plot([i - 0.28, i + 0.28], [m, m], color=INK, lw=1.3, zorder=4)
        a.text(i + 0.30, m, f"{m:.0f}%", ha="left", va="center", fontsize=5.9, color=INK, zorder=5, bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none", alpha=0.85))
    qf = [100 * R["qrfree"][k]["F"]["v"] for k in ("QR0", "QR2", "QR5")]
    a.scatter([2.0] * len(qf), qf, s=13, marker="D", facecolor="white", edgecolor=ORANGE, linewidth=0.8, zorder=4)
    a.text(2.0, -13, "◇ free-form", fontsize=5.3, color=INK2, ha="center", va="center")
    a.set_xticks(range(len(sets))); a.set_xticklabels([l for _, l, _ in sets], fontsize=6.0)
    a.set_xlim(-0.5, 4.75); a.set_ylim(-20, 106); a.set_yticks([0, 25, 50, 75, 100]); a.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    a.set_ylabel("right answers given up"); a.xaxis.grid(False)
    a.scatter([], [], s=9, color=AQUA, label="keeps the question open")
    a.scatter([], [], s=9, color=ORANGE, label="replaces it")
    a.legend(loc="upper left", fontsize=5.3, handletextpad=0.1, title="label set before data", title_fontsize=5.3, borderaxespad=0.1)
    a.set_title("a  49 wordings: how the user objects")


def patching(a):
    for key, ls, lab in (("assert/dis", "-", "assertion pair"), ("direct/dis", "--", "directive pair")):
        v = R["patch"][key]
        xs = range(len(v["rebuttal"]["restored"]))
        a.plot(xs, [100 * e["v"] for e in v["rebuttal"]["restored"]], color=ORANGE, ls=ls, lw=1.1, label=f"rebuttal tokens, {lab}")
        a.plot(xs, [100 * e["v"] for e in v["final"]["restored"]], color=BLUE, ls=ls, lw=1.1, label=f"answer position, {lab}")
    a.axvspan(17, 21, color=GRID, alpha=0.6, lw=0, zorder=0)
    a.text(19, 113, "hand-over", fontsize=5.6, color=INK2, ha="center")
    a.set_xlim(0, 33); a.set_ylim(-12, 122); a.set_yticks([0, 50, 100]); a.set_yticklabels(["0%", "50%", "100%"])
    a.set_xlabel("copied after block (of 34)"); a.set_ylabel("ask−tell difference restored")
    a.legend(loc="center left", fontsize=5.2, handlelength=1.8, bbox_to_anchor=(0.0, 0.47))
    a.set_title("b  Copy ask run into tell run")


def probe(a):
    xs = range(-1, len(P["bare_acc"]) - 1)
    g = P["groups"]
    a.axhline(50, color=AXIS, lw=0.7)
    a.plot(xs, [100 * x for x in P["bare_acc"]], color=MUTED, ls=":", lw=1.0, label="bare question (held out)")
    a.plot(xs, [100 * x for x in P["shuffled_acc"]], color="#c9c7bf", lw=0.8, label="shuffled labels")
    k = "Q0/dis/user_wrong/kept"; a.plot(xs, [100 * x for x in g[k]["acc"]], color=AQUA, lw=1.2, label=f"asked, kept (n={g[k]['n']})")
    k = "D0/dis/user_wrong/flipped"; a.plot(xs, [100 * x for x in g[k]["acc"]], color=DEEP, lw=1.2, label=f"told, gave up (n={g[k]['n']})")
    k = "A0/dis/user_wrong/flipped"; a.plot(xs, [100 * x for x in g[k]["acc"]], color=ORANGE, lw=1.0, ls="--", label=f"asserted, gave up (n={g[k]['n']})")
    a.set_xlim(8, 33); a.set_ylim(-3, 104); a.set_yticks([0, 50, 100]); a.set_yticklabels(["0%", "50%", "100%"])
    a.set_xlabel("after block"); a.set_ylabel("probe reads the right answer")
    a.legend(loc="lower left", fontsize=5.2, handlelength=1.6)
    a.set_title("c  Is the right answer still there?")


if __name__ == "__main__":
    fig, ax = plt.subplots(1, 3, figsize=(7.15, 2.05), gridspec_kw={"wspace": 0.36, "width_ratios": [1.4, 1, 1]})
    wordings(ax[0]); patching(ax[1]); probe(ax[2])
    save(fig, "f_mech")
