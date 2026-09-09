"""
app/core/exceptions.py

Purpose
-------
Defines our own exception classes instead of raising bare `Exception` or
generic `ValueError` everywhere. This is the Python equivalent of your JS
code doing `throw new Error("Fish Audio API error (...)")`, but structured
so that FastAPI's exception handlers (wired up in main.py) can catch
*specific* exception types and turn them into the right HTTP status code
automatically, instead of every route handler needing its own try/except.

Why a class hierarchy instead of one generic error?
- `except UpstreamAPIError:` can catch Gemini AND Fish Audio failures
  the same way, while still letting you branch on the specific subclass
  when you need to (e.g. show a different message for a 401 vs. a 429).
- It documents, in the type system, every way this backend can fail.
"""


class PodcastGenerationError(Exception):
    """Base class for all expected/handled errors in this app."""


class UpstreamAPIError(PodcastGenerationError):
    """
    Raised when a call to an external API (Gemini, Fish Audio) fails.

    status_code: the HTTP status the *upstream* API returned (or None if
                 the request never got a response at all, e.g. timeout).
    """

    def __init__(self, service: str, message: str, status_code: int | None = None):
        self.service = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")


class ConfigurationError(PodcastGenerationError):
    """Raised when required configuration (e.g. an API key) is missing or invalid."""


class ScriptParsingError(PodcastGenerationError):
    """Raised when a generated podcast script can't be parsed into dialogue lines."""
