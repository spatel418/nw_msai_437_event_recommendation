import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import EVENT_BATCH_SIZE, SENTENCE_MODEL_NAME

# Module-level model (loaded once, stays resident)
_model: SentenceTransformer | None = None


def load_model() -> None:
    """Load the sentence-transformer model into memory."""
    global _model
    if _model is not None:
        return
    print(f"Loading sentence-transformer: {SENTENCE_MODEL_NAME}")
    _model = SentenceTransformer(SENTENCE_MODEL_NAME)
    print("Sentence-transformer loaded.")


def get_model() -> SentenceTransformer:
    if _model is None:
        load_model()
    return _model


def encode_texts(texts: list[str], batch_size: int = EVENT_BATCH_SIZE) -> np.ndarray:
    """Encode a list of strings into L2-normalized embeddings. Returns (N, 768)."""
    model = get_model()
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )


def get_top_events_for_labels(
    selected_labels: list[str],
    events_df,
    event_embeddings: np.ndarray,
    top_n: int = 10,
) -> list[dict]:
    """
    Build a query embedding from selected labels, compute cosine similarity
    against all event embeddings, return top N events.
    """
    # Build text in the same format as venue/event text
    query_text = "Categories: " + ", ".join(selected_labels)
    query_emb = encode_texts([query_text])[0]  # shape (768,)

    # Cosine similarity (embeddings are already L2-normalized)
    scores = query_emb @ event_embeddings.T  # shape (N_events,)
    top_indices = np.argsort(scores)[-top_n:][::-1]

    results = []
    for idx in top_indices:
        row = events_df.iloc[idx]
        results.append({
            "event_id": str(row.get("url", "")),
            "event_name": str(row.get("name", "")),
            "event_categories": str(row.get("event_text", "")),
            "yelp_labels": str(row.get("yelp_labels", "")),
            "venue_name": str(row.get("venue_name", "")),
            "venue_city": str(row.get("venue_city", "")),
            "start_date": str(row.get("start_date", "")),
            "url": str(row.get("url", "")),
            "score": float(round(scores[idx], 4)),
        })

    return results
