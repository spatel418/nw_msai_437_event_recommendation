from fastapi import APIRouter

from backend.models.schemas import LLMRerankerRequest, LLMRerankerResponse
from backend.services import llm_service

router = APIRouter()


@router.post("/rerank", response_model=LLMRerankerResponse)
async def rerank(req: LLMRerankerRequest):
    """
    Rerank/filter events using Azure OpenAI based on a natural language prompt.
    Falls back to returning events unchanged if Azure is not configured.
    """
    events, llm_applied = await llm_service.rerank_events(
        [e.model_dump() for e in req.events],
        req.prompt,
    )

    if llm_applied:
        message = f"Reranked by LLM. {len(events)} events returned."
    else:
        message = "LLM not configured. Set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT in .env"

    return LLMRerankerResponse(
        events=events,
        llm_applied=llm_applied,
        message=message,
    )
