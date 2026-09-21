"""Render evaluation charts into docs/images/.

Produces:
    docs/images/eval_metrics.png       — accuracy / precision / recall / F1
    docs/images/score_distribution.png — score histogram, true match vs. not

Run:
    python scripts/plot_results.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.dataset import generate_dataset  # noqa: E402
from backend.evaluate import evaluate, _score_pairs  # noqa: E402

IMAGES = REPO_ROOT / "docs" / "images"
ACCENT = "#3b82f6"
GOOD = "#22c55e"
BAD = "#ef4444"
TEXT = "#111827"
GRID = "#e5e7eb"


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=TEXT)


def plot_metrics(result):
    labels = ["Accuracy", "Precision", "Recall", "F1"]
    values = [result.accuracy, result.precision, result.recall, result.f1]
    fig, ax = plt.subplots(figsize=(7, 4), dpi=140)
    bars = ax.bar(labels, values, color=ACCENT)
    ax.set_ylim(0, 1)
    ax.set_title("Ranking performance on held-out test set", color=TEXT,
                 fontsize=13, fontweight="bold")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.2f}",
                ha="center", color=TEXT, fontweight="bold")
    _style(ax)
    fig.tight_layout()
    out = IMAGES / "eval_metrics.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


def plot_score_distribution():
    pairs = generate_dataset(n=1000, seed=42)
    scored = _score_pairs(pairs)
    pos = [s for s, y in scored if y == 1]
    neg = [s for s, y in scored if y == 0]
    fig, ax = plt.subplots(figsize=(7, 4), dpi=140)
    ax.hist(neg, bins=25, alpha=0.7, color=BAD, label="Not a match (label 0)")
    ax.hist(pos, bins=25, alpha=0.7, color=GOOD, label="True match (label 1)")
    ax.axvline(0.60, color=TEXT, linestyle="--", linewidth=1, label="Decision threshold (0.60)")
    ax.set_xlabel("Ranker score", color=TEXT)
    ax.set_ylabel("Candidates", color=TEXT)
    ax.set_title("Score distribution by true label", color=TEXT, fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    _style(ax)
    fig.tight_layout()
    out = IMAGES / "score_distribution.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


def main():
    IMAGES.mkdir(parents=True, exist_ok=True)
    result = evaluate(n=1000, seed=42, verbose=False)
    plot_metrics(result)
    plot_score_distribution()


if __name__ == "__main__":
    main()
