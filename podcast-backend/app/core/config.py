"""
app/core/config.py

Purpose
-------
This is the ONLY place in the whole backend that is allowed to read
environment variables directly with os.environ / os.getenv. Every other
file imports the `settings` object defined here instead of touching
os.environ itself.

Why centralize this?
- Single source of truth: if you rename an env var, you change it in one
  place, not in every file that used it.
- Validation: Pydantic's BaseSettings checks types and required fields
  at *startup* (app crashes immediately with a clear error), instead of
  at request time deep inside some function (which is how your original
  JS project failed: fishApiKey was silently `undefined` and the error
  only surfaced 5 network calls later).
- Testability: tests can override `settings` without touching real
  environment variables.

Library used: pydantic-settings
- BaseSettings is a normal Pydantic model, except its values are
  auto-populated from environment variables (and a .env file) instead of
  from a JSON body. Field names are matched case-insensitively to env
  var names by default.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Gemini ---
    gemini_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"

    # --- Fish Audio (no longer used - kept optional so an old .env doesn't crash startup) ---
    fish_audio_api_key: str = ""
    fish_audio_base_url: str = "https://api.fish.audio"

    # --- XTTS-v2 (local, free voice cloning) ---
    xtts_language: str = "en"

    # --- Ollama (local LLM for analyze / script / chat) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # --- App behaviour ---
    app_env: str = "development"          # "development" | "production"
    cors_allow_origins: str = "http://localhost:3000"  # comma-separated
    audio_output_dir: str = "audio_output"
    log_level: str = "INFO"

    # --- Retry / rate limiting knobs ---
    gemini_max_retries: int = 5
    gemini_retry_wait_seconds: int = 2
    gemini_inter_agent_delay: int = 5
    gemini_search_max_chars: int = 8000

    fish_audio_timeout_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Turns 'http://a.com,http://b.com' into ['http://a.com', 'http://b.com']."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()