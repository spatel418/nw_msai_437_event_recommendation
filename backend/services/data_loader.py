import json

import numpy as np
import pandas as pd

from backend.config import (
    BUSINESS_MAP_PATH,
    EVENT_EMB_PATH,
    EVENTS_TEXT_CSV_PATH,
    USER_EVENT_RECS_PATH,
    USER_RECS_PATH,
    VENUE_EMB_PATH,
    VENUES_TEXT_CSV_PATH,
)
from backend.state import AppState


def load_all(state: AppState) -> None:
    """Load all data files into AppState on server startup."""
    print("Loading data files...")

    # Business mapping: business_id -> venue dict
    with open(BUSINESS_MAP_PATH, "r", encoding="utf-8") as f:
        businesses = json.load(f)
    state.business_map = {v["business_id"]: v for v in businesses}
    print(f"  Business map: {len(state.business_map)} venues")

    # Collaborative filtering user -> venue recommendations
    with open(USER_RECS_PATH, "r", encoding="utf-8") as f:
        state.user_recs = json.load(f)
    print(f"  User recs: {len(state.user_recs)} users")

    # Pre-computed user -> event recommendations
    with open(USER_EVENT_RECS_PATH, "r", encoding="utf-8") as f:
        state.user_event_recs = json.load(f)

    # Build O(1) lookup by user_id
    state.user_event_recs_by_id = {
        u["user_id"]: u["recommended_events"]
        for u in state.user_event_recs
    }
    state.user_ids = sorted(state.user_event_recs_by_id.keys())
    print(f"  User event recs: {len(state.user_event_recs)} users")

    # Embeddings
    state.venue_embeddings = np.load(VENUE_EMB_PATH)
    state.event_embeddings = np.load(EVENT_EMB_PATH)
    print(f"  Venue embeddings: {state.venue_embeddings.shape}")
    print(f"  Event embeddings: {state.event_embeddings.shape}")

    # Text CSVs (for metadata lookup when returning results)
    state.venues_df = pd.read_csv(VENUES_TEXT_CSV_PATH)
    state.events_df = pd.read_csv(EVENTS_TEXT_CSV_PATH).fillna("")
    print(f"  Venues CSV: {len(state.venues_df)} rows")
    print(f"  Events CSV: {len(state.events_df)} rows")

    print("Data loading complete.")
