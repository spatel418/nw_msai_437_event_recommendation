from pydantic import BaseModel


class EventRecommendation(BaseModel):
    event_id: str
    event_name: str
    event_categories: str
    yelp_labels: str
    venue_name: str
    venue_city: str
    start_date: str
    url: str
    score: float
    matched_via_venue: str | None = None
    venue_profile: str | None = None
    venue_rank: int | None = None
    venue_cosine_similarity: float | None = None


# --- Admin ---
class UserSummary(BaseModel):
    user_id: str


class UserListResponse(BaseModel):
    users: list[UserSummary]
    total: int


class UserRecommendationsResponse(BaseModel):
    user_id: str
    recommended_events: list[EventRecommendation]


# --- New User ---
class NewUserRequest(BaseModel):
    selected_labels: list[str]
    top_n: int = 10


class NewUserResponse(BaseModel):
    selected_labels: list[str]
    recommended_events: list[EventRecommendation]


class SaveNewUserRequest(BaseModel):
    name: str
    selected_labels: list[str]
    recommended_events: list[EventRecommendation]


class SaveNewUserResponse(BaseModel):
    saved: bool
    name: str
    message: str


class LabelsResponse(BaseModel):
    labels: list[str]
    groups: dict[str, list[str]]


# --- Collections ---
class Collection(BaseModel):
    name: str
    labels: list[str]
    is_default: bool = False


class CollectionsResponse(BaseModel):
    collections: list[Collection]


class CreateCollectionRequest(BaseModel):
    name: str
    labels: list[str]


class GenerateCollectionRequest(BaseModel):
    description: str


class GenerateCollectionResponse(BaseModel):
    collection: Collection
    description: str


# --- Pipeline ---
class PipelineStatusResponse(BaseModel):
    is_running: bool
    stage: str
    last_updated: str | None
    last_error: str | None


# --- Sections (ephemeral, in-memory) ---
class Section(BaseModel):
    id: str
    title: str
    description: str


class SectionsResponse(BaseModel):
    sections: list[Section]


class CreateSectionRequest(BaseModel):
    description: str


class CreateSectionResponse(BaseModel):
    section: Section


class MapSectionEventsRequest(BaseModel):
    events: list[EventRecommendation]


class MapSectionEventsResponse(BaseModel):
    section_id: str
    title: str
    events: list[EventRecommendation]


# --- LLM Reranker (scaffold) ---
class LLMRerankerRequest(BaseModel):
    events: list[EventRecommendation]
    prompt: str


class LLMRerankerResponse(BaseModel):
    events: list[EventRecommendation]
    llm_applied: bool
    message: str
