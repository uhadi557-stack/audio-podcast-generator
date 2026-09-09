from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="The podcast topic to research")


class Source(BaseModel):
    title: str
    uri: str
    type: str = "website"


class ResearchResponse(BaseModel):
    text: str
    sources: list[Source]


class AnalyzeRequest(BaseModel):
    research_text: str = Field(..., min_length=1)


class AnalyzeResponse(BaseModel):
    insights: str


class ScriptRequest(BaseModel):
    topic: str
    insights: str
    host_name: str = "Host"
    guest_name: str = "Guest"


class ScriptResponse(BaseModel):
    script: str


class VoiceCloneResponse(BaseModel):
    reference_id: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    reference_id: str | None = Field(
        default=None,
        description="Voice sample reference_id from /api/voice/clone. Omit to use a default voice.",
    )


class EpisodeRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    host_name: str = "Host"
    guest_name: str = "Guest"
    host_reference_id: str | None = Field(
        default=None, description="From /api/voice/clone, or omit for a default voice."
    )
    guest_reference_id: str | None = Field(
        default=None, description="From /api/voice/clone, or omit for a default voice."
    )
    include_music: bool = Field(
        default=True, description="Layer a soft ambient background bed under the dialogue."
    )


class EpisodeResponse(BaseModel):
    filename: str
    script: str
    sources: list[Source]
    insights: str = ""  # analyst summary — was computed but not returned before


# ---------------------------------------------------------------------------
# Expert follow-up chat models
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """One turn in the conversation history (user question or assistant answer)."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """
    Stateless chat request.  The frontend sends the full history every time
    so the backend doesn't need to manage sessions.
    """
    research_text: str = Field(..., min_length=1, description="The raw research text to ground answers in")
    sources: list[Source] = Field(default_factory=list, description="Cited sources from the research phase")
    question: str = Field(..., min_length=1, description="The user's new question")
    history: list[ChatMessage] = Field(default_factory=list, description="Previous Q&A turns")
    guest_name: str = Field(default="Guest", description="Name of the expert persona to impersonate")


class ChatResponse(BaseModel):
    answer: str