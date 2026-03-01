"""Azure OpenAI LLM reranker — scaffold for future implementation."""


async def rerank_events(events: list[dict], user_prompt: str) -> list[dict]:
    """
    Future: Call Azure OpenAI to rerank/filter events based on user_prompt.

    Example prompts:
      - "only events after 8pm"
      - "prefer outdoor events"
      - "nothing too expensive"

    To implement:
      1. Set up Azure OpenAI resource
      2. Set env vars: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT
      3. Use openai SDK to call the deployment with events + prompt
      4. Parse LLM response to reorder/filter the events list

    For now, returns events unchanged.
    """
    # TODO: Implement Azure OpenAI call
    # import os
    # from openai import AzureOpenAI
    # client = AzureOpenAI(
    #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    #     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    #     api_version="2024-02-01",
    # )
    # response = client.chat.completions.create(
    #     model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    #     messages=[
    #         {"role": "system", "content": "You are an event recommendation assistant..."},
    #         {"role": "user", "content": f"Events: {events}\n\nFilter: {user_prompt}"},
    #     ],
    # )
    return events
