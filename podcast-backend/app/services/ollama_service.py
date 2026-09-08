"""
app/services/ollama_service.py

Purpose
-------
Local-LLM replacements for the Gemini calls that do NOT need Google
Search grounding.  Calls the Ollama HTTP API running on localhost,
avoiding any cloud API rate limits.

Functions moved here from gemini_service.py:
- analyze_insights()
- write_podcast_script()
- expert_chat()

research_topic() stays in gemini_service.py because it requires
Google Search grounding, which only Gemini can provide.
"""

import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIError

logger = logging.getLogger(__name__)

settings = get_settings()


async def _generate_ollama(prompt: str) -> str:
    """
    Send a prompt to the local Ollama server and return the response text.

    Uses the /api/generate endpoint with stream=false for simplicity.
    No retry loop is needed — Ollama runs locally, so 429 rate limits
    don't apply.  We just handle connection errors clearly.
    """
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=900.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.ConnectError as exc:
        raise UpstreamAPIError(
            service="ollama",
            message=(
                f"Cannot connect to Ollama at {settings.ollama_base_url}. "
                "Is 'ollama serve' running?"
            ),
        ) from exc
    except httpx.ReadTimeout as exc:
        raise UpstreamAPIError(
            service="ollama",
            message=(
                f"Ollama took too long to respond (timed out). "
                f"Your hardware might be struggling to run the '{settings.ollama_model}' model. "
                "Consider changing OLLAMA_MODEL to a smaller model like 'llama3.2:3b' in your .env file."
            ),
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise UpstreamAPIError(
            service="ollama",
            message=f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text[:500]}",
            status_code=exc.response.status_code,
        ) from exc
    except Exception as exc:
        raise UpstreamAPIError(
            service="ollama",
            message=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Public functions — same signatures as the gemini_service originals
# ---------------------------------------------------------------------------


async def analyze_insights(research_text: str) -> str:
    """Analyze research text and extract insights (runs on local Ollama, falls back to Gemini)."""
    try:
        response = await _generate_ollama(f"Analyze: {research_text[:10000]}")
        return response
    except UpstreamAPIError as exc:
        logger.warning(
            "Ollama unavailable or model missing (%s). Falling back to Gemini for analysis...",
            exc,
        )
        from app.services import gemini_service
        return await gemini_service.analyze_insights(research_text)


async def write_podcast_script(
    topic: str,
    insights: str,
    host_name: str = "Host",
    guest_name: str = "Guest",
) -> str:
    """Generate a podcast script (runs on local Ollama, falls back to Gemini)."""
    prompt = f"""
    Write an educational podcast dialogue about "{topic}" based on these insights: {insights}.
    The podcast features two co-hosts:
    - {host_name}: A skeptical, curious host who asks analytical questions.
    - {guest_name}: An authoritative, clear technical expert who explains concepts.

    CRITICAL RULES:
    1. Alternate turns between {host_name} and {guest_name}. Both speakers MUST have multiple speaking turns.
    2. Format EVERY line starting with the exact speaker name followed by a colon and space:
    {host_name}: Spoken dialogue here.
    {guest_name}: Spoken dialogue here.
    3. Do NOT use markdown asterisks or bolding (do NOT write **{host_name}**:).
    4. Do not include any stage directions, parentheticals like (laughs), sound effects, or introductory headers.
    5. Spoken words only. Keep the dialogue concise: 8-12 lines total (4-6 per speaker). Each line should be 1-2 clear sentences.
    """
    try:
        response = await _generate_ollama(prompt)
        return response
    except UpstreamAPIError as exc:
        logger.warning(
            "Ollama unavailable or model missing (%s). Falling back to Gemini for scriptwriting...",
            exc,
        )
        from app.services import gemini_service
        return await gemini_service.write_podcast_script(
            topic=topic,
            insights=insights,
            host_name=host_name,
            guest_name=guest_name,
        )


async def expert_chat(
    research_text: str,
    sources: list[dict],
    question: str,
    history: list[dict],
    guest_name: str = "Guest",
) -> str:
    """
    Answer a follow-up question as the guest persona, grounded in the
    research text and sources already gathered for this episode.
    Runs on local Ollama, with fallback to Gemini if Ollama is unavailable.
    """
    # Build a source list string so the model can cite them
    source_list = "\n".join(
        f"  - {s.get('title', 'Source')} ({s.get('uri', '')})"
        for s in sources
    ) or "  (no sources available)"

    # Build conversation history string
    history_text = ""
    if history:
        history_text = "\n\nPrevious conversation:\n" + "\n".join(
            f"{'User' if turn['role'] == 'user' else guest_name}: {turn['content']}"
            for turn in history
        )

    prompt = f"""You are {guest_name}, a knowledgeable and articulate expert.
You are answering follow-up questions from a listener who just heard your
podcast episode. Stay in character as {guest_name} throughout.

Ground your answers in the following research material and cited sources.
If the question goes beyond what the research covers, say so honestly
rather than making things up.

RESEARCH MATERIAL:
{research_text[:12000]}

CITED SOURCES:
{source_list}
{history_text}

User's new question: {question}

Respond as {guest_name}. Be conversational, helpful, and concise (2-4 paragraphs max).
When relevant, mention which source supports a claim."""

    try:
        response = await _generate_ollama(prompt)
        return response
    except UpstreamAPIError as exc:
        logger.warning(
            "Ollama unavailable or model missing (%s). Falling back to Gemini for expert chat...",
            exc,
        )
        from app.services import gemini_service
        return await gemini_service.expert_chat(
            research_text=research_text,
            sources=sources,
            question=question,
            history=history,
            guest_name=guest_name,
        )
