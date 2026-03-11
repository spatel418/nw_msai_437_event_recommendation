"""Azure OpenAI LLM reranker for event recommendations."""

import json
import os

from openai import AzureOpenAI

SYSTEM_PROMPT = """You are an event recommendation assistant. The user has been shown a list of events. They want to refine this list using natural language.

You will receive a list of events (as JSON) and a user prompt describing what they want.

Your job: return a JSON array of event_id strings, ordered from most relevant to least relevant, based on the user's prompt. Only include events that match the user's criteria. If an event clearly doesn't match, exclude it.

IMPORTANT: Return ONLY a valid JSON array of event_id strings. No explanation, no markdown, no extra text.

Example output:
["evt_123", "evt_456", "evt_789"]"""


def _get_client() -> AzureOpenAI | None:
    key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not key or not endpoint or key == "your-api-key-here":
        return None
    return AzureOpenAI(
        api_key=key,
        azure_endpoint=endpoint,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def rerank_events(events: list[dict], user_prompt: str) -> tuple[list[dict], bool]:
    """
    Call Azure OpenAI to rerank/filter events based on user_prompt.

    Returns (events, llm_applied). If Azure is not configured, returns original events unchanged.
    """
    client = _get_client()
    if client is None:
        return events, False

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    # Build a compact event summary for the LLM
    event_summaries = []
    for e in events:
        summary = {
            "event_id": e["event_id"],
            "event_name": e["event_name"],
            "categories": e.get("event_categories", ""),
            "labels": e.get("yelp_labels", ""),
            "venue": e.get("venue_name", ""),
            "date": e.get("start_date", ""),
        }
        event_summaries.append(summary)

    user_message = f"Events:\n{json.dumps(event_summaries, indent=2)}\n\nUser request: {user_prompt}"

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    # Parse the LLM response — expect a JSON array of event_id strings
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    ranked_ids: list[str] = json.loads(raw)

    # Rebuild the event list in the LLM's order, keeping only those returned
    events_by_id = {e["event_id"]: e for e in events}
    reranked = [events_by_id[eid] for eid in ranked_ids if eid in events_by_id]

    return reranked, True


COLLECTION_SYSTEM_PROMPT = """You are a creative event collection curator, like Netflix's quirky category names.

The user will describe a mood, vibe, or scenario. Your job:
1. Pick a short, catchy collection name (Netflix-style, creative, fun — e.g. "When Reality Needs an Upgrade", "Sunday Scaries Antidote")
2. Select the most relevant labels from the available list

Available labels:
{labels}

Return ONLY valid JSON with this exact structure:
{{"name": "Your Creative Name", "labels": ["Label1", "Label2", ...]}}

Rules:
- The name should be creative and match the vibe, NOT just list the categories
- Pick 2-6 labels that best match the description
- Only use labels from the available list above
- No explanation, no markdown, just the JSON object"""


async def generate_collection(description: str, available_labels: list[str]) -> dict | None:
    """
    Use LLM to generate a collection name + labels from a freeform description.

    Returns {"name": "...", "labels": [...]} or None if Azure is not configured.
    """
    client = _get_client()
    if client is None:
        return None

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    system = COLLECTION_SYSTEM_PROMPT.format(labels=", ".join(available_labels))

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": description},
        ],
        temperature=0.8,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    result = json.loads(raw)

    # Validate labels are from the known set
    valid_labels = [l for l in result.get("labels", []) if l in available_labels]
    if not valid_labels:
        return None

    return {"name": result["name"], "labels": valid_labels}


SECTION_TITLE_PROMPT = """You are a creative event curator, like Netflix's quirky category names.

The user will describe a mood, vibe, or scenario (e.g. "when I'm bored on a Friday night").
Generate a single short, catchy section title for this vibe.

Rules:
- Be creative and fun, NOT generic (e.g. "Reality Called, I Declined" not "Fun Friday Night")
- Keep it under 8 words
- Return ONLY the title text, nothing else. No quotes, no explanation."""


async def generate_section_title(description: str) -> str | None:
    """Generate a catchy Netflix-style section title from a description."""
    client = _get_client()
    if client is None:
        return None

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SECTION_TITLE_PROMPT},
            {"role": "user", "content": description},
        ],
        temperature=0.9,
        max_tokens=50,
    )

    title = response.choices[0].message.content.strip().strip('"\'')
    return title if title else None


MAP_EVENTS_PROMPT = """You are an event recommendation assistant. You will receive:
1. A section theme/vibe description
2. A list of events (as JSON)

Your job: pick the events that fit this section's vibe. Return a JSON array of event_id strings for events that match. Order them from best fit to weakest fit. Pick 3-8 events that genuinely fit — don't force events that don't match.

If no events fit at all, return an empty array [].

IMPORTANT: Return ONLY a valid JSON array of event_id strings. No explanation, no markdown."""


async def map_events_to_section(
    section_description: str, section_title: str, events: list[dict]
) -> list[str]:
    """Use LLM to pick which events fit a section's vibe. Returns list of event_ids."""
    client = _get_client()
    if client is None:
        return []

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    event_summaries = []
    for e in events:
        summary = {
            "event_id": e["event_id"],
            "event_name": e["event_name"],
            "categories": e.get("event_categories", ""),
            "labels": e.get("yelp_labels", ""),
            "venue": e.get("venue_name", ""),
            "date": e.get("start_date", ""),
        }
        event_summaries.append(summary)

    user_message = (
        f"Section: \"{section_title}\" (vibe: {section_description})\n\n"
        f"Events:\n{json.dumps(event_summaries, indent=2)}"
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": MAP_EVENTS_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    return json.loads(raw)
