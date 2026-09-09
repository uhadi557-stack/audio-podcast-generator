import asyncio
import logging

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIError

logger = logging.getLogger(__name__)

settings = get_settings()
_client = genai.Client(api_key=settings.gemini_api_key)


async def _generate_with_retry(
    *,
    contents: str,
    tools: list[types.Tool] | None = None,
) -> types.GenerateContentResponse:
    """
    Call the Gemini API with exponential backoff on 429 / RESOURCE_EXHAUSTED.

    Backoff schedule (using gemini_retry_wait_seconds as the base):
        attempt 1 fails → wait  2 s
        attempt 2 fails → wait  4 s
        attempt 3 fails → wait  8 s
        attempt 4 fails → wait 16 s
        attempt 5 fails → wait 32 s  (then raise)
    """
    config = types.GenerateContentConfig(tools=tools) if tools else None
    last_error: Exception | None = None
    delay = settings.gemini_retry_wait_seconds  # Starting backoff (default 2 s)

    for attempt in range(1, settings.gemini_max_retries + 1):
        try:
            return await _client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc).upper()
            if is_rate_limit and attempt < settings.gemini_max_retries:
                logger.warning(
                    "Gemini rate limit hit (attempt %s/%s). "
                    "Waiting %ss before retry... [model=%s]",
                    attempt,
                    settings.gemini_max_retries,
                    delay,
                    settings.gemini_model,
                )
                await asyncio.sleep(delay)
                delay *= 2  # Double the wait: 2→4→8→16→32 s
                continue
            # Non-rate-limit error or final attempt — stop retrying
            logger.error(
                "Gemini call failed permanently (attempt %s/%s): %s",
                attempt, settings.gemini_max_retries, exc,
            )
            break

    raise UpstreamAPIError(
        service="gemini",
        message=str(last_error),
    )


async def research_topic(topic: str) -> tuple[str, list[dict]]:
    """
    Research a topic using Gemini with Google Search grounding.

    The raw response text is truncated to ``settings.gemini_search_max_chars``
    before being returned so that downstream agents (Analyst, Scriptwriter)
    do not receive an oversized payload that would blow the TPM budget.
    """
    try:
        response = await _generate_with_retry(
            contents=f'Research the topic: "{topic}"',
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        sources: list[dict] = []
        candidates = response.candidates or []
        if candidates and candidates[0].grounding_metadata:
            chunks = candidates[0].grounding_metadata.grounding_chunks or []
            for chunk in chunks:
                if chunk.web and chunk.web.uri:
                    sources.append({
                        "title": chunk.web.title or "Web Source",
                        "uri": chunk.web.uri,
                        "type": "website",
                    })

        # Compact the payload to stay within TPM budget for downstream agents
        raw_text = response.text or ""
        if len(raw_text) > settings.gemini_search_max_chars:
            logger.info(
                "research_topic: truncating response from %d → %d chars (gemini_search_max_chars).",
                len(raw_text), settings.gemini_search_max_chars,
            )
            raw_text = raw_text[: settings.gemini_search_max_chars]

        return raw_text, sources
    except UpstreamAPIError as exc:
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc).upper():
            logger.warning("Gemini quota exhausted. Falling back to local Ollama for research...")
            from app.services import ollama_service
            # Provide a fallback via Ollama (no live Google search, but avoids crashing)
            text = await ollama_service._generate_ollama(
                f"Research the topic: '{topic}'. Provide a detailed educational summary."
            )
            return text, [{"title": "Local Ollama Fallback", "uri": "", "type": "fallback"}]
        raise


async def analyze_insights(research_text: str) -> str:
    response = await _generate_with_retry(
        contents=f"Analyze: {research_text[:10000]}",
    )
    return response.text or ""


async def write_podcast_script(
    topic: str,
    insights: str,
    host_name: str = "Host",
    guest_name: str = "Guest",
) -> str:
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
    response = await _generate_with_retry(contents=prompt)
    return response.text or ""


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

    Parameters
    ----------
    research_text : str
        The raw research output from the research phase.
    sources : list[dict]
        Cited sources (each has title, uri, type).
    question : str
        The user's latest question.
    history : list[dict]
        Previous conversation turns, each {"role": "user"|"assistant", "content": "..."}.
    guest_name : str
        The name of the expert persona (e.g. "Sam").

    Returns
    -------
    str
        The expert's answer.
    """
    # Build a source list string so Gemini can cite them
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

    response = await _generate_with_retry(contents=prompt)
    return response.text or ""