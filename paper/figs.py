"""Shared figure style: one palette, plain-language labels. Imported by figs6.py."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
plt.rcParams.update({
    "font.family": "Inter", "font.size": 7.5, "axes.titlesize": 8.2, "axes.labelsize": 7.5, "xtick.labelsize": 7,
    "ytick.labelsize": 7.5, "legend.fontsize": 7, "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "svg.fonttype": "path", "figure.facecolor": SURF, "axes.facecolor": SURF,
    "legend.frameon": False, "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 6})
OUT = "figs"


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.svg", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight", pad_inches=0.03, dpi=110)
    plt.close(fig)


def pct_axis(ax, lo=0, hi=100, step=25):
    ax.set_xlim(lo, hi)
    ax.set_xticks(range(lo, hi + 1, step))
    ax.set_xticklabels([f"{t}%" for t in range(lo, hi + 1, step)])
    ax.yaxis.grid(False)
