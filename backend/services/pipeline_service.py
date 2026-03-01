"""Full update pipeline: scrape → classify → embed → recommend."""

from datetime import datetime, timezone

import numpy as np

from backend.config import EVENTS_CSV_PATH, EVENTS_TEXT_CSV_PATH, EVENT_EMB_PATH
from backend.services import classifier_service, embedding_service, recommendation_service, scraper_service
from backend.state import AppState


def run_full_pipeline(state: AppState) -> None:
    """
    Run the complete update pipeline. This is designed to be called as a
    BackgroundTask from FastAPI — it takes 20-30 minutes to complete.
    """
    try:
        # Stage 1: Scrape
        state.pipeline.stage = "scraping"
        print("\n=== PIPELINE STAGE 1: SCRAPING ===")
        events_df = scraper_service.scrape_all_events()

        # Stage 2: Classify
        state.pipeline.stage = "classifying"
        print("\n=== PIPELINE STAGE 2: CLASSIFYING ===")
        events_df = classifier_service.classify_events_batch(events_df)

        # Save scraped + classified CSV
        events_df.to_csv(str(EVENTS_CSV_PATH), index=False)
        print(f"Saved {len(events_df)} classified events to {EVENTS_CSV_PATH}")

        # Stage 3: Embed
        state.pipeline.stage = "embedding"
        print("\n=== PIPELINE STAGE 3: EMBEDDING ===")
        event_texts = events_df["event_text"].tolist()
        event_embeddings = embedding_service.encode_texts(event_texts)
        print(f"Event embeddings shape: {event_embeddings.shape}")

        # Save embeddings and text CSV
        np.save(str(EVENT_EMB_PATH), event_embeddings)
        events_df.to_csv(str(EVENTS_TEXT_CSV_PATH), index=False)

        # Update state with new event data
        with state.lock:
            state.event_embeddings = event_embeddings
            state.events_df = events_df

        # Stage 4: Rebuild recommendations
        state.pipeline.stage = "recommending"
        print("\n=== PIPELINE STAGE 4: RECOMMENDING ===")
        recommendation_service.rebuild_all(state)

        # Stage 5: Cleanup
        print("\n=== PIPELINE STAGE 5: CLEANUP ===")
        classifier_service.unload_classifier()

        state.pipeline.stage = "idle"
        state.pipeline.is_running = False
        state.pipeline.last_updated = datetime.now(timezone.utc).isoformat()
        state.pipeline.last_error = None
        print("\n=== PIPELINE COMPLETE ===")

    except Exception as ex:
        state.pipeline.last_error = str(ex)
        state.pipeline.is_running = False
        state.pipeline.stage = "idle"
        classifier_service.unload_classifier()
        print(f"\n=== PIPELINE FAILED: {ex} ===")
        raise
