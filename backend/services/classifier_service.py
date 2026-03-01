"""Zero-shot classification service — extracted from eventbrite_scrape_and_classify.ipynb."""

import pandas as pd

from backend.config import CLASSIFIER_MODEL_NAME, CLASSIFIER_THRESHOLD, CLASSIFIER_TOP_N, YELP_EVENT_LABELS

# Lazily loaded — only when pipeline runs
_classifier = None


def load_classifier() -> None:
    """Load the zero-shot classification model. Call only when needed."""
    global _classifier
    if _classifier is not None:
        return
    from transformers import pipeline

    print(f"Loading zero-shot classifier: {CLASSIFIER_MODEL_NAME}")
    _classifier = pipeline(
        "zero-shot-classification",
        model=CLASSIFIER_MODEL_NAME,
        device=-1,  # CPU — safest for 4GB VRAM GPU
    )
    print("Classifier loaded.")


def unload_classifier() -> None:
    """Free classifier memory after pipeline completes."""
    global _classifier
    if _classifier is not None:
        del _classifier
        _classifier = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        print("Classifier unloaded.")


def classify_event(
    text: str,
    threshold: float = CLASSIFIER_THRESHOLD,
    top_n: int = CLASSIFIER_TOP_N,
) -> tuple[list[str], list[float]]:
    """Run zero-shot classification on a single event text."""
    if _classifier is None:
        load_classifier()

    result = _classifier(text, YELP_EVENT_LABELS, multi_label=True)
    labels = [
        label
        for label, score in zip(result["labels"], result["scores"])
        if score >= threshold
    ][:top_n]
    scores = [
        round(score, 3)
        for score in result["scores"]
        if score >= threshold
    ][:top_n]
    return labels, scores


def classify_events_batch(events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify all events, adding yelp_labels, yelp_scores, and event_text columns.
    Drops events with no labels passing threshold.
    """
    load_classifier()

    yelp_labels_list = []
    yelp_scores_list = []

    total = len(events_df)
    print(f"Classifying {total} events...")

    for i, (_, row) in enumerate(events_df.iterrows()):
        text = str(row.get("classifier_input", row.get("name", ""))).strip()[:512]
        labels, scores = classify_event(text)
        yelp_labels_list.append(labels)
        yelp_scores_list.append(scores)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{total} classified")

    events_df = events_df.copy()
    events_df["yelp_labels"] = yelp_labels_list
    events_df["yelp_scores"] = yelp_scores_list

    # Build event_text from labels
    def event_to_text(row):
        labels = row["yelp_labels"]
        if not labels:
            return ""
        return "Categories: " + ", ".join(labels)

    events_df["event_text"] = events_df.apply(event_to_text, axis=1)

    # Drop events with no labels
    before = len(events_df)
    events_df = events_df[events_df["event_text"].str.strip() != ""].reset_index(
        drop=True
    )
    print(f"Dropped {before - len(events_df)} events with no labels")
    print(f"Classification complete: {len(events_df)} events")

    return events_df
