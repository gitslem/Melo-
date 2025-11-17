from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import librosa
from music_theory import quantize_to_scale, detect_key


def extract_melody_notes(
    path: Path,
    scale: Optional[str] = None,
    root: Optional[str] = None,
    auto_detect_key: bool = True
) -> Tuple[List[Dict], str, str]:
    """
    Load audio and extract a monophonic melody as a list of note dicts.

    Args:
        path: Path to audio file
        scale: Scale name (e.g., "minor", "major", "afrobeat"). If None, uses detected scale.
        root: Root note (e.g., "C", "D#"). If None, uses detected root.
        auto_detect_key: Whether to auto-detect the key

    Returns:
        Tuple of (notes, detected_root, detected_scale)
        notes: List of {"midi": int, "start": float_sec, "end": float_sec}
        detected_root: Detected or provided root note
        detected_scale: Detected or provided scale name
    """
    y, sr = librosa.load(path, sr=22050, mono=True)
    y = librosa.util.normalize(y)

    # Use librosa.yin for fundamental frequency estimation
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
        frame_length=2048,
        hop_length=512,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=512)

    # First pass: extract raw notes without quantization
    raw_notes: List[Dict] = []
    current_note = None

    for t, freq in zip(times, f0):
        if np.isnan(freq) or freq <= 0:
            midi = None
        else:
            midi = int(round(librosa.hz_to_midi(float(freq))))

        if midi is None:
            # end current note if any
            if current_note is not None:
                current_note["end"] = float(t)
                raw_notes.append(current_note)
                current_note = None
            continue

        if current_note is None:
            # start new note
            current_note = {"midi": int(midi), "start": float(t), "end": float(t)}
        else:
            # continue same note or start new one if pitch changed
            if midi == current_note["midi"]:
                current_note["end"] = float(t)
            else:
                # close previous
                current_note["end"] = float(t)
                raw_notes.append(current_note)
                # start new
                current_note = {"midi": int(midi), "start": float(t), "end": float(t)}

    # close last note
    if current_note is not None:
        current_note["end"] = float(times[-1])
        raw_notes.append(current_note)

    # filter very short notes
    min_duration = 0.08  # 80 ms
    raw_notes = [n for n in raw_notes if (n["end"] - n["start"]) >= min_duration]

    if not raw_notes:
        return [], "C", "minor"

    # Detect key if requested and not provided
    if auto_detect_key and (root is None or scale is None):
        detected_root, detected_scale = detect_key(raw_notes)
        if root is None:
            root = detected_root
        if scale is None:
            scale = detected_scale
    else:
        # Use defaults if not provided
        if root is None:
            root = "C"
        if scale is None:
            scale = "minor"

    # Second pass: quantize to detected/specified scale
    notes = []
    for note in raw_notes:
        quantized_midi = quantize_to_scale(note["midi"], root, scale)
        notes.append({
            "midi": quantized_midi,
            "start": note["start"],
            "end": note["end"],
        })

    # shift notes to start at 0
    if notes:
        first_start = notes[0]["start"]
        for n in notes:
            n["start"] -= first_start
            n["end"] -= first_start

    return notes, root, scale


def analyze_melody(notes: List[Dict]) -> Dict:
    """
    Analyze melody characteristics.

    Args:
        notes: List of note dictionaries

    Returns:
        Dictionary with analysis results
    """
    if not notes:
        return {
            "num_notes": 0,
            "duration": 0.0,
            "pitch_range": 0,
            "avg_interval": 0.0,
        }

    midis = [n["midi"] for n in notes]
    duration = max(n["end"] for n in notes)

    # Calculate intervals
    intervals = [abs(midis[i+1] - midis[i]) for i in range(len(midis) - 1)]
    avg_interval = np.mean(intervals) if intervals else 0

    return {
        "num_notes": len(notes),
        "duration": duration,
        "pitch_range": max(midis) - min(midis),
        "avg_interval": avg_interval,
        "lowest_note": min(midis),
        "highest_note": max(midis),
    }
