"""Recommendation logic — extracted from recommend_events_v3.py."""

import json
import re

import numpy as np
import pandas as pd

from backend.config import (
    SKIP_ATTRS,
    TOP_EVENTS_PER_USER,
    TOP_EVENTS_PER_VENUE,
    USER_EVENT_RECS_PATH,
    VENUE_EVENT_MAP_PATH,
)
from backend.state import AppState


def _camel_to_words(s: str) -> str:
    s = re.sub(r"([A-Z])", r" \1", s).strip()
    for prefix in ("Restaurants ", "Business ", "Good For "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip()


def build_venue_profile(venue_info: dict) -> str:
    """Build 'Title - Categories - Keywords' string for a venue."""
    name = venue_info.get("name", "")
    categories = venue_info.get("categories", [])
    attributes = venue_info.get("attributes", {})

    seen_cats = set()
    deduped_cats = []
    for c in categories:
        if c.lower() not in seen_cats:
            seen_cats.add(c.lower())
            deduped_cats.append(c)

    keywords = []
    for k, v in attributes.items():
        if k.lower() in SKIP_ATTRS:
            continue
        if str(v).strip().lower() == "true":
            word = _camel_to_words(k)
            if word.lower() not in seen_cats and word not in keywords:
                keywords.append(word)

    parts = [name]
    if deduped_cats:
        parts.append(", ".join(deduped_cats))
    if keywords:
        parts.append(", ".join(keywords))
    return " - ".join(parts)


def build_venue_event_map(
    venues_df: pd.DataFrame,
    events_df: pd.DataFrame,
    venue_emb: np.ndarray,
    event_emb: np.ndarray,
    top_per_venue: int = TOP_EVENTS_PER_VENUE,
) -> dict:
    """For each venue, find the top N most similar events by embedding cosine similarity."""
    venue_event_map = {}

    for i, row in venues_df.iterrows():
        business_id = row["business_id"]
        scores = venue_emb[i] @ event_emb.T
        top_indices = np.argsort(scores)[-top_per_venue:][::-1]

        top_events = []
        for idx in top_indices:
            event_row = events_df.iloc[idx]
            top_events.append({
                "event_id": str(event_row.get("url", "")),
                "event_name": str(event_row.get("name", "")),
                "event_categories": str(event_row.get("event_text", "")),
                "yelp_labels": str(event_row.get("yelp_labels", "")),
                "venue_name": str(event_row.get("venue_name", "")),
                "venue_city": str(event_row.get("venue_city", "")),
                "start_date": str(event_row.get("start_date", "")),
                "url": str(event_row.get("url", "")),
                "score": float(round(scores[idx], 4)),
            })

        venue_event_map[business_id] = top_events

    return venue_event_map


def build_user_event_recommendations(
    user_recs: list,
    venue_event_map: dict,
    business_map: dict,
    top_per_user: int = TOP_EVENTS_PER_USER,
) -> list:
    """For each user, collect top 1 event per recommended venue, return ranked list."""
    user_event_recommendations = []

    for user in user_recs:
        user_id = user["user_id"]
        event_pool = {}

        for rec in user["recommendations"]:
            business_id = rec["business_id"]
            business_name = rec["business_name"]

            if business_id not in venue_event_map:
                continue

            events_for_venue = venue_event_map[business_id]
            if not events_for_venue:
                continue

            best_event = events_for_venue[0]
            event_id = best_event["event_id"]

            if event_id not in event_pool or best_event["score"] > event_pool[event_id]["score"]:
                venue_info = business_map.get(business_id, {})
                venue_profile = build_venue_profile(venue_info) if venue_info else business_name
                event_pool[event_id] = {
                    **best_event,
                    "matched_via_venue": business_name,
                    "venue_profile": venue_profile,
                    "venue_rank": rec["rank"],
                    "venue_cosine_similarity": rec["cosine_similarity"],
                }

        ranked_events = sorted(event_pool.values(), key=lambda x: x["venue_rank"])
        ranked_events = ranked_events[:top_per_user]

        user_event_recommendations.append({
            "user_id": user_id,
            "recommended_events": ranked_events,
        })

    return user_event_recommendations


def rebuild_all(state: AppState) -> None:
    """Recompute venue→event map and user→event recommendations, save to disk and update state."""
    print("Rebuilding venue→event map...")
    venue_event_map = build_venue_event_map(
        state.venues_df, state.events_df,
        state.venue_embeddings, state.event_embeddings,
    )

    with open(VENUE_EVENT_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(venue_event_map, f, indent=2)
    print(f"  Saved venue_event_map: {len(venue_event_map)} venues")

    print("Rebuilding user→event recommendations...")
    user_event_recs = build_user_event_recommendations(
        state.user_recs, venue_event_map, state.business_map,
    )

    with open(USER_EVENT_RECS_PATH, "w", encoding="utf-8") as f:
        json.dump(user_event_recs, f, indent=2)
    print(f"  Saved user_event_recs: {len(user_event_recs)} users")

    # Update state under lock
    with state.lock:
        state.user_event_recs = user_event_recs
        state.user_event_recs_by_id = {
            u["user_id"]: u["recommended_events"]
            for u in user_event_recs
        }
        state.user_ids = sorted(state.user_event_recs_by_id.keys())

    print("Rebuild complete.")
