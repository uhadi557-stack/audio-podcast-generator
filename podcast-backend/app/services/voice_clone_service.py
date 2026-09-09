"""
app/services/voice_clone_service.py

Local, free, self-hosted voice cloning + TTS using XTTS-v2 (via the
coqui-tts package). No network call, no per-request cost - the model
runs inside this process.

"Cloning" simplification
-------------------------
XTTS-v2 is zero-shot: no training step. We just save the uploaded
reference .wav and pass it as speaker_wav at generation time.

Threading note
---------------
tts_to_file(...) is a blocking, CPU-heavy call. asyncio.to_thread runs
it in a background thread so uvicorn can keep serving other requests
while one line of audio is being generated.
"""

import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path

# Must be set before importing TTS, or the library prompts (y/n) for
# interactive license agreement on first run - which hangs forever in a
# server process with no terminal attached.
os.environ.setdefault("COQUI_TOS_AGREED", "1")

from app.core.config import get_settings
from app.core.exceptions import UpstreamAPIError

logger = logging.getLogger(__name__)
settings = get_settings()

VOICE_SAMPLES_DIR = Path(settings.audio_output_dir).parent / "voice_samples"
VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE_SAMPLE = Path(__file__).resolve().parent.parent / "assets" / "default_voice.wav"

_tts_model = None


def _get_model():
    global _tts_model
    if _tts_model is None:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        model_path = Path(local_appdata) / "tts" / "tts_models--multilingual--multi-dataset--xtts_v2" / "model.pth"
        expected_size = 1867929118
        if model_path.exists():
            current_size = model_path.stat().st_size
            if current_size < expected_size:
                current_mb = current_size / (1024 * 1024)
                total_mb = expected_size / (1024 * 1024)
                pct = (current_size / expected_size) * 100
                raise UpstreamAPIError(
                    service="xtts",
                    message=(
                        f"XTTS-v2 weights are currently downloading in background "
                        f"({current_mb:.1f} MB / {total_mb:.1f} MB, {pct:.1f}%). "
                        f"Please allow the download to complete before synthesizing audio."
                    ),
                )

        logger.info("Loading XTTS-v2 model (first call only - this can take a while)...")
        import torch
        from TTS.api import TTS

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cpu":
            # Restrict thread allocation on CPU to avoid massive memory pool buffers
            num_threads = min(4, os.cpu_count() or 4)
            torch.set_num_threads(num_threads)
            logger.info("Configured torch num_threads=%d for CPU", num_threads)

        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        logger.info("XTTS-v2 loaded on device=%s", device)
    return _tts_model


async def clone_voice(audio_bytes: bytes, filename: str, title: str) -> str:
    """
    Saves the uploaded voice sample to disk and returns a reference_id
    (the saved filename) to reuse in text_to_speech(). No model
    inference happens here - this is deliberately instant.
    """
    suffix = Path(filename).suffix or ".wav"
    reference_id = f"{title}_{uuid.uuid4().hex[:8]}{suffix}"
    dest = VOICE_SAMPLES_DIR / reference_id
    dest.write_bytes(audio_bytes)
    logger.info("Saved voice sample '%s' -> %s", title, dest)
    return reference_id


def _synthesize_sync(text: str, speaker_wav_path: str | None) -> bytes:
    """The actual blocking model call, run off the event loop via to_thread."""
    import gc
    import torch

    model = _get_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # If no custom voice sample is provided, use the bundled clean default voice sample
        speaker_wav = speaker_wav_path
        if not speaker_wav or not Path(speaker_wav).exists():
            speaker_wav = str(DEFAULT_VOICE_SAMPLE)

        with torch.inference_mode():
            model.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language=settings.xtts_language,
                file_path=tmp_path,
            )
        return Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        gc.collect()


async def text_to_speech(
    text: str,
    reference_id: str | None = None,
    **kwargs,
) -> bytes:
    """
    Generates speech for one line of text, optionally in a previously
    cloned voice. Returns raw WAV bytes using local XTTS-v2.
    """
    speaker_wav_path: str | None = None
    if reference_id:
        candidate = VOICE_SAMPLES_DIR / reference_id
        if not candidate.exists():
            raise UpstreamAPIError(
                service="xtts",
                message=f"Unknown reference_id '{reference_id}' - no such voice sample on disk.",
            )
        speaker_wav_path = str(candidate)

    try:
        return await asyncio.to_thread(_synthesize_sync, text, speaker_wav_path)
    except UpstreamAPIError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise UpstreamAPIError(service="xtts", message=str(exc))