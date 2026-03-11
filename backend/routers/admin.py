import json
import uuid

from fastapi import APIRouter, HTTPException, Query

from backend.config import CUSTOM_COLLECTIONS_PATH, DEFAULT_COLLECTIONS, YELP_EVENT_LABELS
from backend.models.schemas import (
    Collection,
    CollectionsResponse,
    CreateCollectionRequest,
    CreateSectionRequest,
    CreateSectionResponse,
    GenerateCollectionRequest,
    GenerateCollectionResponse,
    MapSectionEventsRequest,
    MapSectionEventsResponse,
    Section,
    SectionsResponse,
    UserListResponse,
    UserRecommendationsResponse,
    UserSummary,
)
from backend.services import llm_service
from backend.state import app_state

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
def list_users(
    search: str = Query("", description="Filter user IDs by substring"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List all user IDs, optionally filtered by search substring."""
    user_ids = app_state.user_ids
    if search:
        search_lower = search.lower()
        user_ids = [uid for uid in user_ids if search_lower in uid.lower()]

    total = len(user_ids)
    page = user_ids[offset : offset + limit]

    return UserListResponse(
        users=[UserSummary(user_id=uid) for uid in page],
        total=total,
    )


@router.get("/users/{user_id}/recommendations", response_model=UserRecommendationsResponse)
def get_user_recommendations(user_id: str):
    """Get pre-computed event recommendations for a specific user."""
    events = app_state.user_event_recs_by_id.get(user_id)
    if events is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    return UserRecommendationsResponse(
        user_id=user_id,
        recommended_events=events,
    )


def _load_custom_collections() -> list[dict]:
    if CUSTOM_COLLECTIONS_PATH.exists():
        return json.loads(CUSTOM_COLLECTIONS_PATH.read_text())
    return []


@router.get("/collections", response_model=CollectionsResponse)
def get_collections():
    """Return all collections (defaults + custom)."""
    collections = [
        Collection(name=name, labels=labels, is_default=True)
        for name, labels in DEFAULT_COLLECTIONS.items()
    ]
    for c in _load_custom_collections():
        collections.append(Collection(name=c["name"], labels=c["labels"], is_default=False))
    return CollectionsResponse(collections=collections)


@router.post("/collections", response_model=Collection)
def create_collection(req: CreateCollectionRequest):
    """Create a new custom collection."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Collection name is required")
    if not req.labels:
        raise HTTPException(status_code=400, detail="Must select at least one label")

    invalid = [l for l in req.labels if l not in YELP_EVENT_LABELS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid labels: {invalid}")

    custom = _load_custom_collections()

    # Check for duplicate name
    all_names = set(DEFAULT_COLLECTIONS.keys()) | {c["name"] for c in custom}
    if req.name.strip() in all_names:
        raise HTTPException(status_code=409, detail=f"Collection '{req.name.strip()}' already exists")

    entry = {"name": req.name.strip(), "labels": req.labels}
    custom.append(entry)
    CUSTOM_COLLECTIONS_PATH.write_text(json.dumps(custom, indent=2))

    return Collection(name=entry["name"], labels=entry["labels"], is_default=False)


@router.post("/collections/generate", response_model=GenerateCollectionResponse)
async def generate_collection(req: GenerateCollectionRequest):
    """Use LLM to generate a collection name + labels from a freeform description, then save it."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    result = await llm_service.generate_collection(req.description.strip(), YELP_EVENT_LABELS)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="LLM not configured or failed. Set AZURE_OPENAI_KEY in .env",
        )

    # Save the generated collection
    custom = _load_custom_collections()
    all_names = set(DEFAULT_COLLECTIONS.keys()) | {c["name"] for c in custom}

    # If name already exists, append a number
    name = result["name"]
    base_name = name
    counter = 2
    while name in all_names:
        name = f"{base_name} {counter}"
        counter += 1

    entry = {"name": name, "labels": result["labels"]}
    custom.append(entry)
    CUSTOM_COLLECTIONS_PATH.write_text(json.dumps(custom, indent=2))

    collection = Collection(name=name, labels=result["labels"], is_default=False)
    return GenerateCollectionResponse(collection=collection, description=req.description.strip())


# --- Sections (ephemeral, in-memory) ---


@router.get("/sections", response_model=SectionsResponse)
def get_sections():
    """Return all in-memory sections."""
    sections = [Section(**s) for s in app_state.sections]
    return SectionsResponse(sections=sections)


@router.post("/sections", response_model=CreateSectionResponse)
async def create_section(req: CreateSectionRequest):
    """Create a new section: LLM generates a catchy title from the description."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")

    title = await llm_service.generate_section_title(req.description.strip())
    if title is None:
        raise HTTPException(
            status_code=503,
            detail="LLM not configured or failed. Set AZURE_OPENAI_KEY in .env",
        )

    section = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "description": req.description.strip(),
    }
    app_state.sections.append(section)

    return CreateSectionResponse(section=Section(**section))


@router.delete("/sections/{section_id}")
def delete_section(section_id: str):
    """Delete an in-memory section."""
    before = len(app_state.sections)
    app_state.sections = [s for s in app_state.sections if s["id"] != section_id]
    if len(app_state.sections) == before:
        raise HTTPException(status_code=404, detail="Section not found")
    return {"deleted": True}


@router.post("/sections/{section_id}/map", response_model=MapSectionEventsResponse)
async def map_section_events(section_id: str, req: MapSectionEventsRequest):
    """Map a user's events to a section on-the-fly using the LLM."""
    section = next((s for s in app_state.sections if s["id"] == section_id), None)
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")

    events_dicts = [e.model_dump() for e in req.events]

    matched_ids = await llm_service.map_events_to_section(
        section["description"], section["title"], events_dicts
    )

    events_by_id = {e.event_id: e for e in req.events}
    mapped_events = [events_by_id[eid] for eid in matched_ids if eid in events_by_id]

    return MapSectionEventsResponse(
        section_id=section_id,
        title=section["title"],
        events=mapped_events,
    )
