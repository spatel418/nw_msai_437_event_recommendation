from fastapi import APIRouter

from backend.models.schemas import LLMRerankerRequest, LLMRerankerResponse
from backend.services import llm_service

router = APIRouter()


@router.post("/rerank", response_model=LLMRerankerResponse)
async def rerank(req: LLMRerankerRequest):
    """
    Scaffold: accepts events + natural language prompt for LLM reranking.
    Currently returns events unchanged.
    """
    events = await llm_service.rerank_events(
        [e.model_dump() for e in req.events],
        req.prompt,
    )

    return LLMRerankerResponse(
        events=events,
        llm_applied=False,
        message="LLM reranker not yet configured. Set up Azure OpenAI resource.",
    )
