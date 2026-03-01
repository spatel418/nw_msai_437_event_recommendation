from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import UserListResponse, UserRecommendationsResponse, UserSummary
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
