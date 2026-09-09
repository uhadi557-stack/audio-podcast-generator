"""
app/core/logging_config.py

Purpose
-------
Your original JS project's error handling was mostly `console.error()`
inside try/catch blocks scattered across geminiService.ts and App.tsx.
That works for a solo dev staring at DevTools, but it doesn't scale:
there's no severity levels, no consistent format, and nothing is ever
written anywhere persistent.

This module configures Python's built-in `logging` module ONCE, at app
startup, so every other file can just do:

    import logging
    logger = logging.getLogger(__name__)
    logger.info("...")
    logger.error("...")

and have it come out consistently formatted, with the module name and
severity visible, which is exactly what you need when debugging "why did
audio generation fail" three modules deep in a call stack.

Why not print()?
- print() has no severity levels (you can't say "only show me WARNING
  and above in production").
- print() can't easily be redirected to a file or a log aggregation
  service later without changing every call site.
- logging is the standard, interview-expected answer for "how do you
  handle logging in a Python service".
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Third-party libraries (httpx, uvicorn) are chatty at DEBUG/INFO.
    # Keep them at WARNING so your own log lines aren't drowned out.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
