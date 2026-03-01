from fastapi import APIRouter, HTTPException

from backend.config import LABEL_GROUPS, YELP_EVENT_LABELS
from backend.models.schemas import LabelsResponse, NewUserRequest, NewUserResponse
from backend.services import embedding_service
from backend.state import app_state

router = APIRouter()


@router.get("/labels", response_model=LabelsResponse)
def get_labels():
    """Return the 35 Yelp-style labels grouped by category."""
    return LabelsResponse(labels=YELP_EVENT_LABELS, groups=LABEL_GROUPS)


@router.post("/events", response_model=NewUserResponse)
def recommend_events_for_labels(req: NewUserRequest):
    """
    Accept selected labels, embed them, compute cosine similarity
    against all event embeddings, return top N events.
    """
    # Validate that at least one label was selected
    if not req.selected_labels:
        raise HTTPException(status_code=400, detail="Must select at least one label")

    # Validate labels are from the known set
    invalid = [l for l in req.selected_labels if l not in YELP_EVENT_LABELS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid labels: {invalid}",
        )

    results = embedding_service.get_top_events_for_labels(
        selected_labels=req.selected_labels,
        events_df=app_state.events_df,
        event_embeddings=app_state.event_embeddings,
        top_n=req.top_n,
    )

    return NewUserResponse(
        selected_labels=req.selected_labels,
        recommended_events=results,
    )
