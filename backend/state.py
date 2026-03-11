import threading
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class PipelineStatus:
    is_running: bool = False
    last_updated: Optional[str] = None   # ISO timestamp
    last_error: Optional[str] = None
    stage: str = "idle"  # idle | scraping | classifying | embedding | recommending


@dataclass
class AppState:
    # Core data (loaded on startup)
    business_map: dict = field(default_factory=dict)           # business_id -> venue dict
    user_recs: list = field(default_factory=list)              # raw CF user recommendations
    user_event_recs: list = field(default_factory=list)        # full user_event_recommendations list
    user_event_recs_by_id: dict = field(default_factory=dict)  # user_id -> recommended_events
    user_ids: list = field(default_factory=list)               # sorted list of all user_ids

    # Embedding data
    event_embeddings: Optional[np.ndarray] = None   # (N_events, 768)
    venue_embeddings: Optional[np.ndarray] = None   # (N_venues, 768)
    events_df: Optional[pd.DataFrame] = None
    venues_df: Optional[pd.DataFrame] = None

    # Pipeline status
    pipeline: PipelineStatus = field(default_factory=PipelineStatus)
    lock: threading.Lock = field(default_factory=threading.Lock)

    # Ephemeral sections (in-memory only, cleared on restart)
    sections: list = field(default_factory=list)  # list of {id, title, description}


# Singleton instance
app_state = AppState()
