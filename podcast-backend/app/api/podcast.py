"""
app/api/podcast.py

All podcast-related API routes.

Endpoints
---------
POST /api/research          — Gemini research with Google Search grounding
POST /api/analyze           — Local Ollama analyst summary
POST /api/script            — Local Ollama podcast script generation
POST /api/voice/clone       — Upload a voice sample for local XTTS-v2 cloning
POST /api/tts               — Text-to-speech for one line
POST /api/generate-episode  — Full blocking pipeline (kept for compatibility)
GET  /api/generate-episode/stream — SSE streaming version of the full pipeline
GET  /api/audio/{filename}  — Serve a generated episode file
POST /api/chat              — Expert follow-up chat (stateless)
"""

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sse_starlette.sse import EventSourceResponse

from app.core.config import get_settings
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    EpisodeRequest,
    EpisodeResponse,
    ResearchRequest,
    ResearchResponse,
    ScriptRequest,
    ScriptResponse,
    Source,
    TTSRequest,
    VoiceCloneResponse,
)
from app.services import (
    audio_pipeline_service,
    gemini_service,
    ollama_service,
    voice_clone_service,
)
from app.services.progress import ProgressTracker

router = APIRouter()
settings = get_settings()


# ---------------------------------------------------------------------------
# Existing endpoints (unchanged logic, just added `insights` to episode)
# ---------------------------------------------------------------------------

@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    text, sources = await gemini_service.research_topic(request.topic)
    return ResearchResponse(
        text=text,
        sources=[Source(**s) for s in sources],
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    insights = await ollama_service.analyze_insights(request.research_text)
    return AnalyzeResponse(insights=insights)


@router.post("/script", response_model=ScriptResponse)
async def script(request: ScriptRequest) -> ScriptResponse:
    script_text = await ollama_service.write_podcast_script(
        topic=request.topic,
        insights=request.insights,
        host_name=request.host_name,
        guest_name=request.guest_name,
    )
    return ScriptResponse(script=script_text)


@router.post("/voice/clone", response_model=VoiceCloneResponse)
async def voice_clone(
    audio: UploadFile = File(..., description="A short (~10-30s) clean voice sample"),
    title: str = Form(..., description="A name for this cloned voice, e.g. the host's name"),
) -> VoiceCloneResponse:
    audio_bytes = await audio.read()
    reference_id = await voice_clone_service.clone_voice(
        audio_bytes=audio_bytes,
        filename=audio.filename or "voice_sample.wav",
        title=title,
    )
    return VoiceCloneResponse(reference_id=reference_id)


@router.post("/tts")
async def tts(request: TTSRequest) -> Response:
    audio_bytes = await voice_clone_service.text_to_speech(
        text=request.text,
        reference_id=request.reference_id,
    )
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/generate-episode", response_model=EpisodeResponse)
async def generate_episode(request: EpisodeRequest) -> EpisodeResponse:
    """Original blocking endpoint — kept for backwards compatibility."""
    research_text, sources = await gemini_service.research_topic(request.topic)
    # Pace sequential Gemini calls to stay within the free-tier RPM limit
    await asyncio.sleep(settings.gemini_inter_agent_delay)
    insights = await ollama_service.analyze_insights(research_text)
    script_text = await ollama_service.write_podcast_script(
        topic=request.topic,
        insights=insights,
        host_name=request.host_name,
        guest_name=request.guest_name,
    )

    try:
        audio_bytes = await audio_pipeline_service.generate_episode_audio(
            script=script_text,
            host_name=request.host_name,
            guest_name=request.guest_name,
            host_reference_id=request.host_reference_id,
            guest_reference_id=request.guest_reference_id,
            include_music=request.include_music,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    output_dir = Path(settings.audio_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"episode_{uuid.uuid4().hex[:10]}.wav"
    (output_dir / filename).write_bytes(audio_bytes)

    return EpisodeResponse(
        filename=filename,
        script=script_text,
        sources=[Source(**s) for s in sources],
        insights=insights,
    )


@router.get("/audio/{filename}")
@router.head("/audio/{filename}")
async def get_audio(filename: str) -> FileResponse:
    path = Path(settings.audio_output_dir) / filename
    if not path.exists() or path.parent.resolve() != Path(settings.audio_output_dir).resolve():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/wav", filename=filename)


# ---------------------------------------------------------------------------
# Expert follow-up chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Stateless expert chat.  The frontend sends the full conversation
    history with each request, so no server-side session state is needed.
    """
    answer = await ollama_service.expert_chat(
        research_text=request.research_text,
        sources=[s.model_dump() for s in request.sources],
        question=request.question,
        history=[m.model_dump() for m in request.history],
        guest_name=request.guest_name,
    )
    return ChatResponse(answer=answer)


# ---------------------------------------------------------------------------
# SSE streaming endpoint for episode generation with real-time progress
# ---------------------------------------------------------------------------

@router.get("/generate-episode/stream")
async def generate_episode_stream(
    topic: str = Query(..., min_length=1),
    host_name: str = Query(default="Host"),
    guest_name: str = Query(default="Guest"),
    host_reference_id: str | None = Query(default=None),
    guest_reference_id: str | None = Query(default=None),
    include_music: bool = Query(default=True),
):
    """
    Server-Sent Events endpoint that runs the full pipeline and streams
    progress updates to the browser in real time.
    """
    tracker = ProgressTracker()

    async def _run_pipeline() -> None:
        try:
            # Stage 1: Research (Gemini + Google Search)
            await tracker.emit("Researcher", f'Researching "{topic}"...')
            research_text, sources = await gemini_service.research_topic(topic)
            await tracker.emit("Researcher", f"Research complete — found {len(sources)} sources.")

            await tracker.emit("Researcher", f"Pacing {settings.gemini_inter_agent_delay}s to respect API rate limits...")
            await asyncio.sleep(settings.gemini_inter_agent_delay)

            # Stage 2: Analysis (local Ollama — no Gemini quota consumed)
            await tracker.emit("Analyst", "Analyzing research and extracting insights...")
            insights = await ollama_service.analyze_insights(research_text)
            await tracker.emit("Analyst", "Analysis complete.")

            # Stage 3: Script
            await tracker.emit("Scriptwriter", f"Writing podcast script for {host_name} and {guest_name}...")
            script_text = await ollama_service.write_podcast_script(
                topic=topic,
                insights=insights,
                host_name=host_name,
                guest_name=guest_name,
            )
            await tracker.emit("Scriptwriter", "Script generation complete.")

            # Stages 4 & 5: Audio Director + Audio Engineer
            audio_bytes = await audio_pipeline_service.generate_episode_audio(
                script=script_text,
                host_name=host_name,
                guest_name=guest_name,
                host_reference_id=host_reference_id,
                guest_reference_id=guest_reference_id,
                include_music=include_music,
                tracker=tracker,
            )

            output_dir = Path(settings.audio_output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"episode_{uuid.uuid4().hex[:10]}.wav"
            (output_dir / filename).write_bytes(audio_bytes)

            await tracker.complete(data={
                "filename": filename,
                "script": script_text,
                "sources": [{"title": s.get("title", ""), "uri": s.get("uri", ""), "type": s.get("type", "website")} for s in sources],
                "insights": insights,
                "research_text": research_text,
            })
        except Exception as exc:
            await tracker.error(str(exc))

    async def _event_generator():
        asyncio.create_task(_run_pipeline())

        while True:
            event = await tracker.get_event()

            payload = {
                "stage": event.stage,
                "message": event.message,
                "timestamp": event.timestamp,
            }

            if event.is_complete:
                payload["data"] = event.data
                yield {"event": "complete", "data": json.dumps(payload)}
                break
            elif event.is_error:
                yield {"event": "error", "data": json.dumps(payload)}
                break
            else:
                yield {"event": "progress", "data": json.dumps(payload)}

    return EventSourceResponse(_event_generator())