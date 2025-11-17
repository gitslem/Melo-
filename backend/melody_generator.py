from pathlib import Path
from typing import List, Dict

import numpy as np
import mido
import wave
import struct
import math


# Instrument definitions using harmonic profiles
INSTRUMENTS = {
    "piano": {
        "harmonics": [(1.0, 1.0), (2.0, 0.4), (3.0, 0.2), (4.0, 0.15), (5.0, 0.1)],
        "attack": 0.01,
        "decay": 0.05,
        "sustain": 0.7,
        "release": 0.15,
        "brightness": 1.2,
    },
    "guitar": {
        "harmonics": [(1.0, 1.0), (2.0, 0.6), (3.0, 0.4), (4.0, 0.25), (5.0, 0.15), (6.0, 0.1)],
        "attack": 0.005,
        "decay": 0.1,
        "sustain": 0.6,
        "release": 0.2,
        "brightness": 1.5,
    },
    "strings": {
        "harmonics": [(1.0, 1.0), (2.0, 0.5), (3.0, 0.35), (4.0, 0.25), (5.0, 0.2), (6.0, 0.15)],
        "attack": 0.15,
        "decay": 0.1,
        "sustain": 0.85,
        "release": 0.3,
        "brightness": 0.9,
    },
    "bells": {
        "harmonics": [(1.0, 1.0), (2.7, 0.7), (4.1, 0.5), (5.8, 0.3), (7.2, 0.2)],
        "attack": 0.001,
        "decay": 0.3,
        "sustain": 0.3,
        "release": 0.8,
        "brightness": 2.0,
    },
    "synth": {
        "harmonics": [(1.0, 1.0), (2.0, 0.8), (3.0, 0.6), (4.0, 0.4), (5.0, 0.2)],
        "attack": 0.02,
        "decay": 0.05,
        "sustain": 0.8,
        "release": 0.1,
        "brightness": 1.8,
    },
    "pads": {
        "harmonics": [(1.0, 1.0), (2.0, 0.7), (3.0, 0.5), (4.0, 0.4), (5.0, 0.3), (6.0, 0.2)],
        "attack": 0.3,
        "decay": 0.2,
        "sustain": 0.9,
        "release": 0.5,
        "brightness": 0.7,
    },
}


def notes_to_midi(notes: List[Dict], out_path: Path, tempo_bpm: int = 120) -> None:
    """
    Convert list of notes ({midi, start, end}) to a simple monophonic MIDI file.
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    tempo = mido.bpm2tempo(tempo_bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo))

    ticks_per_beat = mid.ticks_per_beat
    seconds_per_beat = 60.0 / tempo_bpm
    ticks_per_second = ticks_per_beat / seconds_per_beat

    # sort by start time
    notes_sorted = sorted(notes, key=lambda n: n["start"])
    last_tick = 0

    for n in notes_sorted:
        start_sec = float(n["start"])
        end_sec = float(n["end"])
        dur_sec = max(0.05, end_sec - start_sec)

        start_tick = int(round(start_sec * ticks_per_second))
        end_tick = int(round(end_sec * ticks_per_second))
        dur_ticks = max(1, end_tick - start_tick)

        delta = max(0, start_tick - last_tick)
        track.append(mido.Message("note_on", note=int(n["midi"]), velocity=90, time=delta))
        track.append(mido.Message("note_off", note=int(n["midi"]), velocity=0, time=dur_ticks))

        last_tick = start_tick + dur_ticks

    mid.save(out_path)


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def generate_adsr_envelope(
    length: int, sr: int, attack: float, decay: float, sustain: float, release: float
) -> np.ndarray:
    """
    Generate an ADSR (Attack, Decay, Sustain, Release) envelope.

    Args:
        length: Total length in samples
        sr: Sample rate
        attack: Attack time in seconds
        decay: Decay time in seconds
        sustain: Sustain level (0-1)
        release: Release time in seconds
    """
    envelope = np.ones(length, dtype=np.float32)

    attack_samples = int(attack * sr)
    decay_samples = int(decay * sr)
    release_samples = int(release * sr)

    # Attack phase
    if attack_samples > 0 and attack_samples < length:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)

    # Decay phase
    if decay_samples > 0 and (attack_samples + decay_samples) < length:
        decay_start = attack_samples
        decay_end = attack_samples + decay_samples
        envelope[decay_start:decay_end] = np.linspace(1.0, sustain, decay_samples)

    # Sustain phase (already set to 1.0 by default, we scale later)
    sustain_start = attack_samples + decay_samples
    sustain_end = max(sustain_start, length - release_samples)
    if sustain_start < sustain_end:
        envelope[sustain_start:sustain_end] = sustain

    # Release phase
    if release_samples > 0 and release_samples < length:
        envelope[-release_samples:] = np.linspace(sustain, 0.0, release_samples)

    return envelope


def generate_instrument_tone(
    freq: float, duration: float, sr: int, instrument: str = "piano"
) -> np.ndarray:
    """
    Generate an instrument tone using additive synthesis.

    Args:
        freq: Fundamental frequency in Hz
        duration: Duration in seconds
        sr: Sample rate
        instrument: Instrument name (piano, guitar, strings, bells, synth, pads)
    """
    if instrument not in INSTRUMENTS:
        instrument = "piano"

    instrument_config = INSTRUMENTS[instrument]
    n_samples = int(duration * sr)
    t = np.linspace(0, duration, n_samples, False)

    # Generate tone using additive synthesis (sum of harmonics)
    tone = np.zeros(n_samples, dtype=np.float32)

    for harmonic_mult, amplitude in instrument_config["harmonics"]:
        harmonic_freq = freq * harmonic_mult
        # Add slight detuning for warmth
        detune = np.random.uniform(-0.5, 0.5)
        tone += amplitude * np.sin(2 * np.pi * (harmonic_freq + detune) * t)

    # Normalize the harmonics
    tone = tone / len(instrument_config["harmonics"])

    # Apply ADSR envelope
    envelope = generate_adsr_envelope(
        n_samples,
        sr,
        instrument_config["attack"],
        instrument_config["decay"],
        instrument_config["sustain"],
        instrument_config["release"],
    )

    tone = tone * envelope

    # Apply brightness (simple low-pass filter simulation)
    brightness = instrument_config["brightness"]
    if brightness < 1.0:
        # Soften high frequencies
        tone = tone * (1.0 - (1.0 - brightness) * 0.3)

    return tone


def notes_to_wav(
    notes: List[Dict], out_path: Path, sr: int = 44100, instrument: str = "piano"
) -> None:
    """
    Render notes to a WAV file using the specified instrument.

    Args:
        notes: List of note dictionaries with 'midi', 'start', and 'end' keys
        out_path: Output file path
        sr: Sample rate (default: 44100)
        instrument: Instrument type (piano, guitar, strings, bells, synth, pads)
    """
    if not notes:
        raise ValueError("No notes to render")

    max_time = max(n["end"] for n in notes)
    total_samples = int(sr * (max_time + 0.5))
    audio = np.zeros(total_samples, dtype=np.float32)

    for n in notes:
        start_sample = int(sr * n["start"])
        end_sample = int(sr * n["end"])
        end_sample = max(end_sample, start_sample + 1)

        duration = (end_sample - start_sample) / sr
        freq = midi_to_freq(int(n["midi"]))

        # Generate instrument tone
        tone = generate_instrument_tone(freq, duration, sr, instrument)

        # Ensure tone length matches exactly
        tone = tone[:end_sample - start_sample]

        # Mix into audio buffer
        audio[start_sample:start_sample + len(tone)] += tone * 0.5

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.85  # Leave some headroom

    audio_int16 = (audio * 32767).astype(np.int16)

    # Write WAV
    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
