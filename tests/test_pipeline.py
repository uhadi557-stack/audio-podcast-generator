import os
from pathlib import Path
from pydub import AudioSegment
import pytest

from app.services.audio_pipeline_service import parse_script_lines
from app.services import music_service
from app.services.voice_clone_service import DEFAULT_VOICE_SAMPLE


def test_bundled_default_voice_exists():
    """Verify that the bundled default voice sample exists and is valid WAV."""
    assert DEFAULT_VOICE_SAMPLE.exists(), f"Missing default voice at {DEFAULT_VOICE_SAMPLE}"
    audio = AudioSegment.from_file(str(DEFAULT_VOICE_SAMPLE), format="wav")
    assert len(audio) > 1000, "Default voice sample is too short (<1s)"
    assert audio.frame_rate > 0


def test_parse_script_lines_standard():
    script = """
    Alex: Hello and welcome everyone.
    Sam: Thanks for having me Alex.
    Alex: Today we are discussing quantum physics.
    Sam: It is a fascinating topic.
    """
    lines = parse_script_lines(script, "Alex", "Sam")
    assert len(lines) == 4
    assert lines[0] == ("Alex", "Hello and welcome everyone.")
    assert lines[1] == ("Sam", "Thanks for having me Alex.")
    assert lines[2] == ("Alex", "Today we are discussing quantum physics.")
    assert lines[3] == ("Sam", "It is a fascinating topic.")


def test_parse_script_lines_markdown_and_stage_directions():
    script = """
    **Alex**: (laughs) Welcome back to the show! [intro music]
    **Sam**: "Thanks, Alex! (smiles) Glad to be here."
    **Alex (Host)**: Let's jump right in.
    **Host**: Here is our first question.
    **Guest**: That is an important question.
    """
    lines = parse_script_lines(script, "Alex", "Sam")
    assert len(lines) == 5
    assert lines[0] == ("Alex", "Welcome back to the show!")
    assert lines[1] == ("Sam", "Thanks, Alex!  Glad to be here.")
    assert lines[2] == ("Alex", "Let's jump right in.")
    assert lines[3] == ("Alex", "Here is our first question.")
    assert lines[4] == ("Sam", "That is an important question.")


def test_music_service_generation_and_mixing():
    dialogue = AudioSegment.silent(duration=2000, frame_rate=44100)
    mixed = music_service.mix_with_music(dialogue)
    assert len(mixed) == len(dialogue)
    assert mixed.frame_rate == 44100
