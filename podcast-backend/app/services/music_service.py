import numpy as np
from pydub import AudioSegment

SAMPLE_RATE = 44100

_CHORD_FREQS_HZ = [130.81, 164.81, 196.00, 246.94]  # C3, E3, G3, B3

_MUSIC_GAIN_DB = -22
_FADE_MS = 2000


def _generate_pad_samples(duration_ms: int) -> np.ndarray:
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)

    pad = np.zeros(n_samples)
    for i, freq in enumerate(_CHORD_FREQS_HZ):
        lfo_rate = 0.15 + i * 0.05
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * lfo_rate * t + i)
        pad += lfo * np.sin(2 * np.pi * freq * t)

    pad /= len(_CHORD_FREQS_HZ)
    return pad.astype(np.float32)


def generate_lofi_bed(duration_ms: int) -> AudioSegment:
    samples = _generate_pad_samples(duration_ms)
    pcm16 = (samples * 32767).astype(np.int16)

    bed = AudioSegment(
        pcm16.tobytes(),
        frame_rate=SAMPLE_RATE,
        sample_width=2,
        channels=1,
    )
    return bed + _MUSIC_GAIN_DB


def mix_with_music(dialogue: AudioSegment) -> AudioSegment:
    bed = generate_lofi_bed(len(dialogue)).fade_in(_FADE_MS).fade_out(_FADE_MS)
    return dialogue.overlay(bed)