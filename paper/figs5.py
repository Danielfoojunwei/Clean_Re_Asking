"""Cross-task figure: reads / re-reads when contradicted / keeps, for three open-book tasks."""
import json
from pathlib import Path
import numpy as np
import figs
from figs import plt, INK, MUTED, SURF, save
from matplotlib.colors import LinearSegmentedColormap

L = json.load(open(Path("../v5/results_ladder.json")))
ORDER = ["Claude Haiku 5.5", "Gemini 2.5 Flash", "GPT-4.1-mini", "Grok 4.3", "DeepSeek v3.2", "Llama 4 Maverick", "Nova Lite", "Qwen3.5-9B"]
TASKS = [("permission", "Permission rules"), ("stock", "Stock list"), ("rooms", "Room bookings")]
COLS = [("reads", "reads the\nlist"), ("rereads", "re-reads it\nwhen told\nit is wrong"), ("keeps", "keeps its\nright\nanswer")]
CM = LinearSegmentedColormap.from_list("gy", ["#eb6834", "#fbe3c8", "#f7f6f0", "#cfe9da", "#2f9e6b"])


def fig_ladder():
    labs = [l for l in ORDER if l in L]
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.55), gridspec_kw={"wspace": 0.06})
    for a, (t, title) in zip(ax, TASKS):
        M = np.array([[100 * L[l][t][c] for c, _ in COLS] for l in labs])
        a.imshow(M, cmap=CM, vmin=0, vmax=100, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                a.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7.4, color=INK, fontweight="bold" if M[i, j] < 60 else "normal")
        a.set_xticks(range(3)); a.set_xticklabels([c for _, c in COLS], fontsize=6.3); a.xaxis.tick_top(); a.tick_params(length=0)
        a.set_yticks(range(len(labs))); a.set_yticklabels(labs if a is ax[0] else [])
        a.set_title(title, pad=30); a.grid(False)
        for s in a.spines.values():
            s.set_visible(False)
        a.set_xticks(np.arange(-.5, 3, 1), minor=True); a.set_yticks(np.arange(-.5, len(labs), 1), minor=True)
        a.grid(which="minor", color=SURF, linewidth=1.6); a.tick_params(which="minor", length=0)
    save(fig, "f_ladder")


if __name__ == "__main__":
    fig_ladder()
