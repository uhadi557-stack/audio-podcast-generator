"""
app/services/progress.py

Purpose
-------
Lightweight in-memory progress tracker for the episode generation pipeline.

Each generation job gets its own ProgressTracker instance.  The pipeline
pushes events into the tracker's asyncio.Queue, and the SSE endpoint
reads from that queue and streams them to the browser in real time.

Why asyncio.Queue instead of (say) a list + polling?
- Queue.get() is *awaitable*, so the SSE endpoint can sleep efficiently
  until the next event arrives — no busy-waiting / polling loops needed.
- It's built into Python's asyncio — zero external dependencies.
"""

import asyncio
import time
from dataclasses import dataclass, field

# The five pipeline stages, in order, matching the frontend's card labels.
STAGES = ["Researcher", "Analyst", "Scriptwriter", "Audio Director", "Audio Engineer"]


@dataclass
class ProgressEvent:
    """One progress update pushed by the pipeline."""
    stage: str           # Which of the 5 agent stages this belongs to
    message: str         # Human-readable log line, e.g. "Generating voice 3/8 for Sam..."
    timestamp: float = field(default_factory=time.time)  # Unix epoch seconds
    is_complete: bool = False   # True only for the final "done" event
    is_error: bool = False      # True if the pipeline failed
    data: dict | None = None    # Optional payload (e.g. the EpisodeResponse on completion)


class ProgressTracker:
    """
    Accumulates progress events from the pipeline into an asyncio.Queue.
    The SSE endpoint awaits events from this queue.
    """

    def __init__(self) -> None:
        # maxsize=0 means unlimited — we never want the pipeline to block
        # just because the SSE consumer is a few events behind.
        self.queue: asyncio.Queue[ProgressEvent] = asyncio.Queue(maxsize=0)

    async def emit(self, stage: str, message: str, **kwargs) -> None:
        """Push a progress event.  Called by the pipeline code."""
        event = ProgressEvent(stage=stage, message=message, **kwargs)
        await self.queue.put(event)

    async def complete(self, data: dict | None = None) -> None:
        """Signal that the pipeline finished successfully."""
        await self.queue.put(ProgressEvent(
            stage="done",
            message="Episode generation complete!",
            is_complete=True,
            data=data,
        ))

    async def error(self, message: str) -> None:
        """Signal that the pipeline failed."""
        await self.queue.put(ProgressEvent(
            stage="error",
            message=message,
            is_error=True,
        ))

    async def get_event(self) -> ProgressEvent:
        """
        Wait for the next event.  This is what the SSE endpoint calls
        in a loop — it blocks (yields control to the event loop) until
        the pipeline pushes something.
        """
        return await self.queue.get()
