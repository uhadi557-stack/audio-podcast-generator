"""
app/services/audio_pipeline_service.py

Purpose
-------
Assembles a full podcast episode from a script:
1. Parses the script into dialogue lines.
2. Generates TTS audio for each line (with optional voice cloning).
3. Concatenates clips with pauses between them.
4. Optionally mixes in a lo-fi ambient music bed.

The optional `tracker` parameter lets us push real-time progress events
to the frontend via SSE.  When tracker is None (e.g. the old blocking
endpoint still calls this), progress is simply logged and nothing breaks.
"""

import io
import logging
import re

import os
from pathlib import Path
from pydub import AudioSegment

from app.services import music_service, voice_clone_service
from app.services.progress import ProgressTracker

logger = logging.getLogger(__name__)

# Register local FFmpeg if available
_ffmpeg_dir = Path(__file__).resolve().parent.parent.parent.parent / "ffmpeg-8.1.2-essentials_build" / "bin"
if _ffmpeg_dir.exists():
    os.environ["PATH"] = f"{_ffmpeg_dir};{os.environ.get('PATH', '')}"
    _ffmpeg_exe = _ffmpeg_dir / "ffmpeg.exe"
    if _ffmpeg_exe.exists():
        AudioSegment.converter = str(_ffmpeg_exe)

_LINE_PATTERN = re.compile(r"^\s*([^:\n]+):\s*(.+)$", re.MULTILINE)
_PAUSE_MS = 400


def parse_script_lines(script: str, host_name: str, guest_name: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    host_lower = host_name.strip().lower()
    guest_lower = guest_name.strip().lower()

    for match in _LINE_PATTERN.finditer(script):
        raw_speaker = match.group(1).strip()
        raw_text = match.group(2).strip()

        # Clean markdown formatting, quotes, and asterisks from speaker
        clean_speaker = re.sub(r"[*_`]", "", raw_speaker).strip()

        # Clean dialogue text: remove bracketed/parenthetical stage directions and extra quotes
        clean_text = re.sub(r"\[.*?\]", "", raw_text)
        clean_text = re.sub(r"\(.*?\)", "", clean_text)
        clean_text = clean_text.strip().strip('"\'')
        if not clean_text:
            continue

        sp_lower = clean_speaker.lower()

        # Determine speaker identity
        if (
            sp_lower == host_lower
            or sp_lower.startswith(f"{host_lower} ")
            or f"({host_lower})" in sp_lower
            or sp_lower == "host"
            or sp_lower.startswith("host ")
        ):
            canonical_speaker = host_name
        elif (
            sp_lower == guest_lower
            or sp_lower.startswith(f"{guest_lower} ")
            or f"({guest_lower})" in sp_lower
            or sp_lower == "guest"
            or sp_lower.startswith("guest ")
        ):
            canonical_speaker = guest_name
        else:
            continue

        lines.append((canonical_speaker, clean_text))

    host_count = sum(1 for sp, _ in lines if sp == host_name)
    guest_count = sum(1 for sp, _ in lines if sp == guest_name)
    logger.info(
        "Parsed %d lines from script (Host '%s': %d lines, Guest '%s': %d lines)",
        len(lines), host_name, host_count, guest_name, guest_count,
    )

    if not lines:
        logger.warning(
            "No lines matched host_name=%r / guest_name=%r in script. "
            "Raw script preview: %s",
            host_name, guest_name, script[:300],
        )
    return lines


async def generate_episode_audio(
    script: str,
    host_name: str,
    guest_name: str,
    host_reference_id: str | None,
    guest_reference_id: str | None,
    include_music: bool = True,
    tracker: ProgressTracker | None = None,
) -> bytes:
    """
    Generate episode audio from a script.

    Parameters
    ----------
    tracker : ProgressTracker | None
        If provided, progress events are pushed to this tracker so the
        SSE endpoint can stream them to the browser.  If None, we just
        log normally (backwards-compatible with the blocking endpoint).
    """
    async def progress(stage: str, message: str) -> None:
        logger.info("[%s] %s", stage, message)
        if tracker:
            await tracker.emit(stage, message)

    await progress("Audio Director", f"Parsing script for {host_name} and {guest_name}...")
    lines = parse_script_lines(script, host_name, guest_name)
    if not lines:
        raise ValueError(
            "Could not find any dialogue lines matching the given host/guest names in the script."
        )

    await progress("Audio Director", f"Found {len(lines)} dialogue lines. Starting TTS generation...")
    episode = AudioSegment.empty()
    pause = AudioSegment.silent(duration=_PAUSE_MS)

    for i, (speaker, text) in enumerate(lines, start=1):
        reference_id = host_reference_id if speaker == host_name else guest_reference_id
        await progress(
            "Audio Director",
            f"Generating voice {i}/{len(lines)} for {speaker}...",
        )

        # XTTS-v2 (voice_clone_service) returns WAV bytes, not MP3.
        wav_bytes = await voice_clone_service.text_to_speech(text=text, reference_id=reference_id)
        clip = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")

        episode += clip
        if i < len(lines):
            episode += pause

    if include_music:
        await progress("Audio Engineer", "Generating lo-fi ambient music bed...")
        episode = music_service.mix_with_music(episode)
        await progress("Audio Engineer", "Mixed music bed with dialogue.")

    await progress("Audio Engineer", "Exporting final audio file...")
    buffer = io.BytesIO()
    episode.export(buffer, format="wav")
    return buffer.getvalue()