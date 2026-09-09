import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIError

logger = logging.getLogger(__name__)

settings = get_settings()


async def clone_voice(audio_bytes: bytes, filename: str, title: str) -> str:
    files = {"voices": (filename, audio_bytes)}
    data = {"type": "tts", "title": title, "visibility": "private"}
    headers = {"Authorization": f"Bearer {settings.fish_audio_api_key}"}

    async with httpx.AsyncClient(timeout=settings.fish_audio_timeout_seconds) as client:
        try:
            response = await client.post(
                f"{settings.fish_audio_base_url}/model",
                headers=headers,
                data=data,
                files=files,
            )
        except httpx.HTTPError as exc:
            raise UpstreamAPIError(service="fish_audio", message=f"Network error: {exc}")

    if response.status_code >= 400:
        raise UpstreamAPIError(
            service="fish_audio",
            message=f"Clone failed ({response.status_code}): {response.text}",
        )

    payload = response.json()
    reference_id = payload.get("_id")
    if not reference_id:
        raise UpstreamAPIError(
            service="fish_audio",
            message=f"Clone succeeded but no _id in response: {payload}",
        )

    logger.info("Cloned voice '%s' -> reference_id=%s", title, reference_id)
    return reference_id


async def text_to_speech(text: str, reference_id: str | None = None) -> bytes:
    body: dict = {"text": text, "format": "mp3"}
    if reference_id:
        body["reference_id"] = reference_id

    headers = {
        "Authorization": f"Bearer {settings.fish_audio_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=settings.fish_audio_timeout_seconds) as client:
        try:
            response = await client.post(
                f"{settings.fish_audio_base_url}/v1/tts",
                headers=headers,
                json=body,
            )
        except httpx.HTTPError as exc:
            raise UpstreamAPIError(service="fish_audio", message=f"Network error: {exc}")

    if response.status_code >= 400:
        raise UpstreamAPIError(
            service="fish_audio",
            message=f"TTS failed ({response.status_code}): {response.text}",
        )

    return response.content