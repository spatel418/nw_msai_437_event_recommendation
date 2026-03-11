"""
Evaluate BART zero-shot classification on Illinois Yelp venues.

For each venue, BART classifies it against the 35 labels using only the
venue's name + attributes text (NOT the actual Yelp categories).
We then compare BART's predictions to the venue's real Yelp categories.

This validates that BART's zero-shot classification is meaningful for
the event labeling pipeline.
"""

import json
import sys
import time
from pathlib import Path

import torch
from transformers import pipeline

# --- Config ---
DATA_DIR = Path(__file__).parent / "data"
BUSINESS_MAP_PATH = DATA_DIR / "illinois_business_mapping.json"
OUTPUT_PATH = DATA_DIR / "bart_venue_evaluation.json"

CLASSIFIER_MODEL = "facebook/bart-large-mnli"
THRESHOLD = 0.30
TOP_N = 3

YELP_EVENT_LABELS = [
    "Restaurants", "Bars", "Nightlife", "Coffee & Tea", "Beer",
    "Wine & Spirits", "Sports Bars", "Breweries", "Specialty Food", "Barbeque",
    "Arts & Entertainment", "Music Venues", "Jazz & Blues", "Comedy Clubs",
    "Performing Arts", "Theaters", "Art Galleries", "Museums",
    "Active Life", "Fitness & Instruction", "Yoga", "Bowling", "Golf", "Sports Clubs",
    "Kids Activities", "Arcades", "Amusement Parks", "Aquariums",
    "Shopping", "Fashion", "Beauty & Spas",
    "Venues & Event Spaces", "Event Planning & Services", "Hotels & Travel", "Education",
]

SKIP_ATTRS = {
    "businessacceptscreditcards", "businessacceptsbitcoin",
    "restaurantspricerange2", "businessparking", "ambience",
    "goodformeal", "dietaryrestrictions", "music", "beststatus",
    "open24hours", "restaurantsattire", "restaurantsreservations",
    "byappointmentonly",
}


def build_venue_text(venue: dict) -> str:
    """Build classification text from venue name + attributes (NOT categories)."""
    parts = [venue["name"]]

    if venue.get("attributes"):
        for key, val in venue["attributes"].items():
            if key.lower() not in SKIP_ATTRS and val and str(val).lower() not in ("none", "false"):
                parts.append(key)

    return " | ".join(parts)


def get_ground_truth_labels(venue: dict) -> set[str]:
    """Get the venue's actual Yelp categories that overlap with our 35 labels."""
    label_set = set(YELP_EVENT_LABELS)
    return {cat for cat in venue.get("categories", []) if cat in label_set}


def main():
    print("=" * 70)
    print("BART Zero-Shot Classification Evaluation on Illinois Yelp Venues")
    print("=" * 70)

    # Load venues
    print(f"\nLoading venues from {BUSINESS_MAP_PATH}...")
    with open(BUSINESS_MAP_PATH) as f:
        venues = json.load(f)
    print(f"Total venues: {len(venues)}")

    # Filter to venues that have at least one ground truth label
    venues_with_labels = [v for v in venues if get_ground_truth_labels(v)]
    print(f"Venues with ground truth labels (overlap with 35 labels): {len(venues_with_labels)}")
    venues_without = len(venues) - len(venues_with_labels)
    print(f"Venues with no overlapping labels (skipped): {venues_without}")

    # Load BART
    print(f"\nLoading {CLASSIFIER_MODEL}...")
    device = 0 if torch.cuda.is_available() else -1
    device_name = "GPU" if device == 0 else "CPU"
    print(f"Using device: {device_name}")

    classifier = pipeline(
        "zero-shot-classification",
        model=CLASSIFIER_MODEL,
        device=device,
    )
    print("Model loaded.\n")

    # Run classification
    total = len(venues_with_labels)
    results = []
    tp_total = 0  # true positives
    fp_total = 0  # false positives
    fn_total = 0  # false negatives
    exact_matches = 0
    partial_matches = 0

    start_time = time.time()

    for i, venue in enumerate(venues_with_labels):
        text = build_venue_text(venue)
        ground_truth = get_ground_truth_labels(venue)

        # Classify
        output = classifier(text, YELP_EVENT_LABELS, multi_label=True)

        # Get predictions above threshold, max TOP_N
        predicted = set()
        for label, score in zip(output["labels"], output["scores"]):
            if score >= THRESHOLD and len(predicted) < TOP_N:
                predicted.add(label)

        # Compute metrics for this venue
        tp = len(predicted & ground_truth)
        fp = len(predicted - ground_truth)
        fn = len(ground_truth - predicted)

        tp_total += tp
        fp_total += fp
        fn_total += fn

        if predicted == ground_truth:
            exact_matches += 1
        if tp > 0:
            partial_matches += 1

        results.append({
            "business_id": venue["business_id"],
            "name": venue["name"],
            "text_used": text,
            "ground_truth": sorted(ground_truth),
            "predicted": sorted(predicted),
            "scores": {l: round(s, 4) for l, s in zip(output["labels"][:10], output["scores"][:10])},
            "tp": tp, "fp": fp, "fn": fn,
        })

        # Progress display
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (total - i - 1) / rate if rate > 0 else 0

        if (i + 1) % 10 == 0 or i == 0 or (i + 1) == total:
            precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0
            recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            sys.stdout.write(
                f"\r[{i+1:>4}/{total}] "
                f"P={precision:.3f} R={recall:.3f} F1={f1:.3f} "
                f"| Exact={exact_matches} Partial={partial_matches}/{i+1} "
                f"| {rate:.1f} venues/sec | ETA {eta/60:.1f}min"
            )
            sys.stdout.flush()

    elapsed_total = time.time() - start_time
    print("\n")

    # --- Final Metrics ---
    precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0
    recall = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Venues evaluated:      {total}")
    print(f"Time elapsed:          {elapsed_total/60:.1f} minutes")
    print(f"Speed:                 {total/elapsed_total:.1f} venues/sec")
    print()
    print(f"Threshold:             {THRESHOLD}")
    print(f"Max labels per venue:  {TOP_N}")
    print()
    print(f"Precision:             {precision:.4f}  (of predicted labels, how many were correct)")
    print(f"Recall:                {recall:.4f}  (of true labels, how many were found)")
    print(f"F1 Score:              {f1:.4f}")
    print()
    print(f"Exact matches:         {exact_matches}/{total} ({100*exact_matches/total:.1f}%)")
    print(f"Partial matches:       {partial_matches}/{total} ({100*partial_matches/total:.1f}%)  (at least 1 correct)")
    print()
    print(f"True positives:        {tp_total}")
    print(f"False positives:       {fp_total}")
    print(f"False negatives:       {fn_total}")

    # --- Per-label analysis ---
    print("\n" + "=" * 70)
    print("PER-LABEL ANALYSIS")
    print("=" * 70)
    print(f"{'Label':<30} {'TP':>5} {'FP':>5} {'FN':>5} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Support':>8}")
    print("-" * 70)

    for label in YELP_EVENT_LABELS:
        l_tp = sum(1 for r in results if label in r["predicted"] and label in r["ground_truth"])
        l_fp = sum(1 for r in results if label in r["predicted"] and label not in r["ground_truth"])
        l_fn = sum(1 for r in results if label not in r["predicted"] and label in r["ground_truth"])
        support = l_tp + l_fn

        l_prec = l_tp / (l_tp + l_fp) if (l_tp + l_fp) > 0 else 0
        l_rec = l_tp / (l_tp + l_fn) if (l_tp + l_fn) > 0 else 0
        l_f1 = 2 * l_prec * l_rec / (l_prec + l_rec) if (l_prec + l_rec) > 0 else 0

        if support > 0 or l_fp > 0:
            print(f"{label:<30} {l_tp:>5} {l_fp:>5} {l_fn:>5} {l_prec:>7.3f} {l_rec:>7.3f} {l_f1:>7.3f} {support:>8}")

    # --- Save detailed results ---
    output_data = {
        "config": {
            "model": CLASSIFIER_MODEL,
            "threshold": THRESHOLD,
            "top_n": TOP_N,
            "total_venues": len(venues),
            "evaluated_venues": total,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "exact_match_rate": round(exact_matches / total, 4),
            "partial_match_rate": round(partial_matches / total, 4),
        },
        "venue_results": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed results saved to {OUTPUT_PATH}")

    # Auto-generate plots
    print("\nGenerating evaluation plots...")
    try:
        from visualize_evaluation import main as viz_main
        viz_main()
    except ImportError:
        print("(matplotlib not installed — run: poetry add matplotlib, then poetry run python visualize_evaluation.py)")


if __name__ == "__main__":
    main()
