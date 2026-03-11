"""
Generate evaluation graphs from BART venue classification results.

Run after evaluate_bart.py:
    poetry run python visualize_evaluation.py

Generates 4 plots saved to data/evaluation_plots/
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

DATA_DIR = Path(__file__).parent / "data"
EVAL_PATH = DATA_DIR / "bart_venue_evaluation.json"
PLOT_DIR = DATA_DIR / "evaluation_plots"

# Northwestern purple palette
NU_PURPLE = "#4E2A84"
NU_PURPLE_LIGHT = "#7B5EA7"
NU_PURPLE_FAINT = "#B6A0C9"
NU_WHITE = "#FFFFFF"
GRAY = "#888888"
GREEN = "#2E7D32"
RED = "#C62828"


def load_results():
    with open(EVAL_PATH) as f:
        return json.load(f)


def compute_per_label_stats(results: list[dict], labels: list[str]):
    """Compute per-label precision, recall, F1, and support."""
    stats = {}
    for label in labels:
        tp = sum(1 for r in results if label in r["predicted"] and label in r["ground_truth"])
        fp = sum(1 for r in results if label in r["predicted"] and label not in r["ground_truth"])
        fn = sum(1 for r in results if label not in r["predicted"] and label in r["ground_truth"])
        support = tp + fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

        if support > 0 or fp > 0:
            stats[label] = {"tp": tp, "fp": fp, "fn": fn, "support": support,
                            "precision": prec, "recall": rec, "f1": f1}
    return stats


def plot_1_per_label_f1(stats: dict, save_path: Path):
    """Horizontal bar chart of F1 score per label, sorted by F1."""
    sorted_labels = sorted(stats.keys(), key=lambda l: stats[l]["f1"])
    f1_scores = [stats[l]["f1"] for l in sorted_labels]

    fig, ax = plt.subplots(figsize=(10, max(8, len(sorted_labels) * 0.35)))

    colors = [NU_PURPLE if f >= 0.3 else NU_PURPLE_FAINT for f in f1_scores]
    bars = ax.barh(sorted_labels, f1_scores, color=colors, edgecolor="white", linewidth=0.5)

    ax.set_xlabel("F1 Score", fontsize=12)
    ax.set_title("BART Zero-Shot F1 Score per Label", fontsize=14, fontweight="bold", color=NU_PURPLE)
    ax.set_xlim(0, 1.0)
    ax.axvline(x=0.5, color=GRAY, linestyle="--", alpha=0.5, label="F1 = 0.5")

    # Add value labels
    for bar, val in zip(bars, f1_scores):
        ax.text(val + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9, color="#333")

    ax.legend(loc="lower right", fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_2_precision_vs_recall(stats: dict, save_path: Path):
    """Scatter plot of precision vs recall per label, sized by support."""
    fig, ax = plt.subplots(figsize=(9, 7))

    labels_list = list(stats.keys())
    precisions = [stats[l]["precision"] for l in labels_list]
    recalls = [stats[l]["recall"] for l in labels_list]
    supports = [stats[l]["support"] for l in labels_list]

    # Scale marker size by support
    max_support = max(supports) if supports else 1
    sizes = [max(30, (s / max_support) * 300) for s in supports]

    scatter = ax.scatter(recalls, precisions, s=sizes, c=NU_PURPLE,
                         alpha=0.7, edgecolors="white", linewidth=1)

    # Label each point
    for i, label in enumerate(labels_list):
        ax.annotate(label, (recalls[i], precisions[i]),
                    fontsize=7, ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points", color="#333")

    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title("Precision vs Recall per Label\n(bubble size = # venues with that label)",
                 fontsize=13, fontweight="bold", color=NU_PURPLE)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)

    # Diagonal reference lines
    ax.plot([0, 1], [0, 1], "--", color=GRAY, alpha=0.3, label="P = R")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_3_confusion_summary(results: list[dict], save_path: Path):
    """Stacked bar showing TP/FP/FN distribution per venue."""
    fig, ax = plt.subplots(figsize=(10, 5))

    # Bin venues by match quality
    bins = {"Exact Match": 0, "Partial Match\n(≥1 correct)": 0,
            "No Match\n(all wrong)": 0, "No Prediction\n(below threshold)": 0}

    for r in results:
        if set(r["predicted"]) == set(r["ground_truth"]):
            bins["Exact Match"] += 1
        elif r["tp"] > 0:
            bins["Partial Match\n(≥1 correct)"] += 1
        elif len(r["predicted"]) > 0:
            bins["No Match\n(all wrong)"] += 1
        else:
            bins["No Prediction\n(below threshold)"] += 1

    categories = list(bins.keys())
    values = list(bins.values())
    total = sum(values)
    colors_list = [GREEN, NU_PURPLE, RED, GRAY]

    bars = ax.bar(categories, values, color=colors_list, edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, values):
        pct = 100 * val / total if total > 0 else 0
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                f"{val}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylabel("Number of Venues", fontsize=12)
    ax.set_title("BART Classification Match Quality Across All Venues",
                 fontsize=14, fontweight="bold", color=NU_PURPLE)
    ax.set_ylim(0, max(values) * 1.25)
    ax.tick_params(axis="x", labelsize=10)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def plot_4_overall_metrics(metrics: dict, config: dict, save_path: Path):
    """Summary dashboard with overall metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    # Plot 1: P / R / F1 bar chart
    ax = axes[0]
    metric_names = ["Precision", "Recall", "F1"]
    metric_vals = [metrics["precision"], metrics["recall"], metrics["f1"]]
    bars = ax.bar(metric_names, metric_vals, color=[NU_PURPLE_LIGHT, NU_PURPLE, NU_PURPLE],
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, metric_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.3f}", ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.set_title("Overall Metrics", fontsize=12, fontweight="bold", color=NU_PURPLE)
    ax.grid(axis="y", alpha=0.2)

    # Plot 2: Match rates
    ax = axes[1]
    match_names = ["Exact\nMatch", "Partial\nMatch"]
    match_vals = [metrics["exact_match_rate"], metrics["partial_match_rate"]]
    bars = ax.bar(match_names, match_vals, color=[GREEN, NU_PURPLE],
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, match_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.1%}", ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.set_title("Match Rates", fontsize=12, fontweight="bold", color=NU_PURPLE)
    ax.grid(axis="y", alpha=0.2)

    # Plot 3: Config info as text
    ax = axes[2]
    ax.axis("off")
    info_text = (
        f"Model: BART-large-MNLI\n"
        f"Threshold: {config['threshold']}\n"
        f"Max labels/venue: {config['top_n']}\n"
        f"Total venues: {config['total_venues']}\n"
        f"Evaluated: {config['evaluated_venues']}\n"
        f"Labels: 35 Yelp categories"
    )
    ax.text(0.1, 0.5, info_text, transform=ax.transAxes,
            fontsize=11, verticalalignment="center", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=NU_PURPLE_FAINT, alpha=0.3))
    ax.set_title("Configuration", fontsize=12, fontweight="bold", color=NU_PURPLE)

    fig.suptitle("BART Zero-Shot Venue Classification Evaluation",
                 fontsize=15, fontweight="bold", color=NU_PURPLE, y=1.02)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {save_path.name}")


def main():
    if not EVAL_PATH.exists():
        print(f"Error: {EVAL_PATH} not found. Run evaluate_bart.py first.")
        return

    data = load_results()
    results = data["venue_results"]
    metrics = data["metrics"]
    config = data["config"]

    # Get unique labels from results
    all_labels = set()
    for r in results:
        all_labels.update(r["ground_truth"])
        all_labels.update(r["predicted"])
    labels = sorted(all_labels)

    stats = compute_per_label_stats(results, labels)

    PLOT_DIR.mkdir(exist_ok=True)
    print(f"\nGenerating evaluation plots to {PLOT_DIR}/\n")

    plot_1_per_label_f1(stats, PLOT_DIR / "1_per_label_f1.png")
    plot_2_precision_vs_recall(stats, PLOT_DIR / "2_precision_vs_recall.png")
    plot_3_confusion_summary(results, PLOT_DIR / "3_match_quality.png")
    plot_4_overall_metrics(metrics, config, PLOT_DIR / "4_overall_summary.png")

    print(f"\nDone! {len(list(PLOT_DIR.glob('*.png')))} plots generated.")
    print(f"Open {PLOT_DIR} to view them.")


if __name__ == "__main__":
    main()
