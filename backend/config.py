from pathlib import Path

# Resolve relative to project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ----- Data file paths -----
BUSINESS_MAP_PATH = DATA_DIR / "illinois_business_mapping.json"
USER_RECS_PATH = DATA_DIR / "illinois_user_recommendations.json"
EVENTS_CSV_PATH = DATA_DIR / "chicago_eventbrite_scraped.csv"
EVENTS_TEXT_CSV_PATH = DATA_DIR / "events_with_text_v3.csv"
VENUES_TEXT_CSV_PATH = DATA_DIR / "venues_with_text_v3.csv"
VENUE_EMB_PATH = DATA_DIR / "venue_embeddings_v3.npy"
EVENT_EMB_PATH = DATA_DIR / "event_embeddings_v3.npy"
VENUE_EVENT_MAP_PATH = DATA_DIR / "venue_event_map_v3.json"
USER_EVENT_RECS_PATH = DATA_DIR / "user_event_recommendations_v3.json"
NEW_USERS_PATH = DATA_DIR / "new_user_recommendations.json"
CUSTOM_COLLECTIONS_PATH = DATA_DIR / "custom_collections.json"

# ----- Model names -----
SENTENCE_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
CLASSIFIER_MODEL_NAME = "facebook/bart-large-mnli"

# ----- Pipeline parameters -----
VENUE_BATCH_SIZE = 64
EVENT_BATCH_SIZE = 64
MIN_CATEGORIES = 2
TOP_EVENTS_PER_VENUE = 5
TOP_EVENTS_PER_USER = 10
CLASSIFIER_THRESHOLD = 0.30
CLASSIFIER_TOP_N = 3

# ----- Scraper parameters -----
SCRAPER_CITY = "il--chicago"
SCRAPER_MAX_PAGES = 25
SCRAPER_DAYS_AHEAD = 14
SCRAPER_SLEEP_BETWEEN = 1.5

# ----- Attributes to skip in venue profile -----
SKIP_ATTRS = {
    "businessacceptscreditcards", "businessacceptsbitcoin",
    "restaurantspricerange2", "businessparking", "ambience",
    "goodformeal", "dietaryrestrictions", "music", "beststatus",
    "open24hours", "restaurantsattire", "restaurantsreservations",
    "byappointmentonly",
}

# ----- The 35 Yelp-style labels for zero-shot classification -----
YELP_EVENT_LABELS = [
    # Food & Drink
    "Restaurants", "Bars", "Nightlife", "Coffee & Tea", "Beer",
    "Wine & Spirits", "Sports Bars", "Breweries", "Specialty Food", "Barbeque",
    # Arts & Entertainment
    "Arts & Entertainment", "Music Venues", "Jazz & Blues", "Comedy Clubs",
    "Performing Arts", "Theaters", "Art Galleries", "Museums",
    # Active Life & Sports
    "Active Life", "Fitness & Instruction", "Yoga", "Bowling", "Golf", "Sports Clubs",
    # Family & Kids
    "Kids Activities", "Arcades", "Amusement Parks", "Aquariums",
    # Shopping & Lifestyle
    "Shopping", "Fashion", "Beauty & Spas",
    # Community & Events
    "Venues & Event Spaces", "Event Planning & Services", "Hotels & Travel", "Education",
]

# Label groups for frontend display
LABEL_GROUPS = {
    "Food & Drink": [
        "Restaurants", "Bars", "Nightlife", "Coffee & Tea", "Beer",
        "Wine & Spirits", "Sports Bars", "Breweries", "Specialty Food", "Barbeque",
    ],
    "Arts & Entertainment": [
        "Arts & Entertainment", "Music Venues", "Jazz & Blues", "Comedy Clubs",
        "Performing Arts", "Theaters", "Art Galleries", "Museums",
    ],
    "Active Life & Sports": [
        "Active Life", "Fitness & Instruction", "Yoga", "Bowling", "Golf", "Sports Clubs",
    ],
    "Family & Kids": [
        "Kids Activities", "Arcades", "Amusement Parks", "Aquariums",
    ],
    "Shopping & Lifestyle": [
        "Shopping", "Fashion", "Beauty & Spas",
    ],
    "Community & Events": [
        "Venues & Event Spaces", "Event Planning & Services", "Hotels & Travel", "Education",
    ],
}

# ----- Default collections (Netflix-style groupings) -----
DEFAULT_COLLECTIONS = {
    "Friday Night Out": ["Bars", "Nightlife", "Music Venues", "Comedy Clubs"],
    "Family Weekend": ["Kids Activities", "Amusement Parks", "Aquariums", "Museums"],
}
