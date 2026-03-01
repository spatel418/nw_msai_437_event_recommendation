from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.models.schemas import PipelineStatusResponse
from backend.services import pipeline_service
from backend.state import app_state

router = APIRouter()


@router.post("/update", response_model=PipelineStatusResponse)
def trigger_update(background_tasks: BackgroundTasks):
    """Trigger the full update pipeline as a background task."""
    if app_state.pipeline.is_running:
        raise HTTPException(
            status_code=409,
            detail=f"Pipeline already running (stage: {app_state.pipeline.stage})",
        )

    app_state.pipeline.is_running = True
    app_state.pipeline.stage = "starting"
    app_state.pipeline.last_error = None

    background_tasks.add_task(pipeline_service.run_full_pipeline, app_state)

    return PipelineStatusResponse(
        is_running=True,
        stage="starting",
        last_updated=app_state.pipeline.last_updated,
        last_error=None,
    )


@router.get("/status", response_model=PipelineStatusResponse)
def get_status():
    """Check current pipeline status."""
    return PipelineStatusResponse(
        is_running=app_state.pipeline.is_running,
        stage=app_state.pipeline.stage,
        last_updated=app_state.pipeline.last_updated,
        last_error=app_state.pipeline.last_error,
    )
