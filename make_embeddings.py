import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# -------------------------
# CONFIG
# -------------------------
VENUES_JSON_PATH = "illinois_business_mapping.json"
EVENTS_CSV_PATH = "chicago_ticketmaster_events.csv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VENUE_BATCH_SIZE = 64
EVENT_BATCH_SIZE = 64

# -------------------------
# HELPERS
# -------------------------
def to_clean_str(x) -> str:
    """Convert lists/dicts/NaN into a clean string."""
    if x is None:
        return ""
    # Handle pandas NaN safely
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass

    if isinstance(x, list):
        return ", ".join([str(i) for i in x if i is not None])
    if isinstance(x, dict):
        # Keep dicts light; they can be huge/noisy
        items = list(x.items())[:10]
        return ", ".join([f"{k}={v}" for k, v in items if v is not None])
    return str(x)

def clean_attributes(attrs: dict, max_keys: int = 8) -> str:
    """Attributes can be large/noisy; keep only a few keys."""
    if not isinstance(attrs, dict) or len(attrs) == 0:
        return ""
    items = list(attrs.items())[:max_keys]
    return ", ".join([f"{k}={v}" for k, v in items if v is not None])

def venue_to_text(v: dict) -> str:
    """Build a meaningful text blob for each venue."""
    business_id = to_clean_str(v.get("business_id"))
    name = to_clean_str(v.get("name"))
    city = to_clean_str(v.get("city"))
    categories = v.get("categories", [])
    categories_str = to_clean_str(categories)
    attrs_str = clean_attributes(v.get("attributes", {}), max_keys=8)

    parts = []
    if name: parts.append(f"Venue: {name}")
    if city: parts.append(f"City: {city}")
    if categories_str: parts.append(f"Categories: {categories_str}")
    if attrs_str: parts.append(f"Attributes: {attrs_str}")
    # business_id is not meaningful text; we keep it separately in dataframe, not in embed text
    return " | ".join(parts)

def event_to_text(row: pd.Series) -> str:
    """Build a meaningful text blob for each event using your provided columns."""
    parts = []

    # High-signal meaning fields
    name = to_clean_str(row.get("name"))
    description = to_clean_str(row.get("description"))
    keywords = to_clean_str(row.get("keywords"))
    categories = to_clean_str(row.get("categories"))
    typ = to_clean_str(row.get("type"))

    # Context fields (still helpful)
    venue_name = to_clean_str(row.get("venue_name"))
    venue_city = to_clean_str(row.get("venue_city"))
    venue_state = to_clean_str(row.get("venue_state"))
    start_date = to_clean_str(row.get("start_date"))
    start_time = to_clean_str(row.get("start_time"))
    timezone = to_clean_str(row.get("timezone"))

    if name: parts.append(f"Event: {name}")
    if typ: parts.append(f"Type: {typ}")
    if categories: parts.append(f"Categories: {categories}")

    # Keywords can be very helpful; include them
    if keywords: parts.append(f"Keywords: {keywords}")

    # Description is usually the best signal
    if description: parts.append(f"Description: {description}")

    # Location + time context
    if venue_name: parts.append(f"Venue: {venue_name}")
    if venue_city or venue_state:
        loc = ", ".join([p for p in [venue_city, venue_state] if p])
        parts.append(f"Location: {loc}")
    if start_date or start_time:
        when = " ".join([p for p in [start_date, start_time] if p])
        parts.append(f"Starts: {when}")
    if timezone: parts.append(f"Timezone: {timezone}")

    return " | ".join(parts)

# -------------------------
# LOAD DATA
# -------------------------
with open(VENUES_JSON_PATH, "r", encoding="utf-8") as f:
    venues = json.load(f)  # list of dicts

events_df = pd.read_csv(EVENTS_CSV_PATH)

print("Loaded venues:", len(venues))
print("Loaded events (raw):", len(events_df))
print("Event columns:", list(events_df.columns))

# Clean events: remove duplicates and fill missing values
if "id" in events_df.columns:
    events_df = events_df.drop_duplicates(subset=["id"])
events_df = events_df.fillna("")

print("Loaded events (deduped):", len(events_df))

# -------------------------
# BUILD TEXT FIELDS
# -------------------------
venues_df = pd.DataFrame({
    "business_id": [v.get("business_id") for v in venues],
    "venue_text": [venue_to_text(v) for v in venues],
}).fillna("")

events_df["event_text"] = events_df.apply(event_to_text, axis=1)

# Safety: if any text accidentally ends up empty, replace with a fallback
venues_df["venue_text"] = venues_df["venue_text"].replace("", "Venue: (missing text)")
events_df["event_text"] = events_df["event_text"].replace("", "Event: (missing text)")

print("\nSample venue text:\n", venues_df["venue_text"].iloc[0])
print("\nSample event text:\n", events_df["event_text"].iloc[0])

# -------------------------
# EMBED
# -------------------------
model = SentenceTransformer(MODEL_NAME)

venue_texts = venues_df["venue_text"].tolist()
event_texts = events_df["event_text"].tolist()

venue_emb = model.encode(
    venue_texts,
    batch_size=VENUE_BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True
)

event_emb = model.encode(
    event_texts,
    batch_size=EVENT_BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("\nVenue embeddings shape:", venue_emb.shape)
print("Event embeddings shape:", event_emb.shape)


np.save("venue_embeddings.npy", venue_emb)
np.save("event_embeddings.npy", event_emb)

venues_df.to_csv("venues_with_text.csv", index=False)
events_df.to_csv("events_with_text.csv", index=False)

print("\nDONE ✅ Saved:")
print("- venue_embeddings.npy")
print("- event_embeddings.npy")
print("- venues_with_text.csv")
print("- events_with_text.csv")