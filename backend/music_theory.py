"""
Music theory utilities for key detection and scale quantization.
"""
from typing import List, Dict, Tuple
import numpy as np
from collections import Counter


# Define all scales as semitone intervals from the root note
SCALES = {
    # Western scales
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],  # Natural minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],

    # Pentatonic scales
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],

    # Blues scales
    "blues": [0, 3, 5, 6, 7, 10],
    "major_blues": [0, 2, 3, 4, 7, 9],

    # Afrobeat / World scales
    "afrobeat": [0, 2, 3, 5, 7, 9, 10],  # Minor with major 6th
    "afro_pentatonic": [0, 2, 5, 7, 10],

    # Trap / Hip-hop scales
    "trap": [0, 2, 3, 5, 7, 8, 11],  # Harmonic minor variant
    "trap_pentatonic": [0, 3, 5, 7, 10],

    # Exotic scales
    "arabic": [0, 1, 4, 5, 7, 8, 11],
    "japanese": [0, 1, 5, 7, 8],
    "hungarian_minor": [0, 2, 3, 6, 7, 8, 11],
    "spanish": [0, 1, 4, 5, 7, 8, 10],  # Phrygian dominant
}


# Note names for display
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_key(notes: List[Dict]) -> Tuple[str, str]:
    """
    Detect the most likely key and scale from a list of notes.

    Args:
        notes: List of note dictionaries with 'midi' key

    Returns:
        Tuple of (root_note, scale_name) e.g., ("C", "major")
    """
    if not notes:
        return ("C", "minor")

    # Count note frequencies (weighted by duration)
    pitch_class_weights = Counter()

    for note in notes:
        duration = note["end"] - note["start"]
        pitch_class = note["midi"] % 12
        pitch_class_weights[pitch_class] += duration

    # Try all 12 keys with common scales
    best_score = -1
    best_key = ("C", "minor")

    scales_to_try = ["major", "minor", "harmonic_minor", "minor_pentatonic",
                     "major_pentatonic", "dorian", "phrygian"]

    for root in range(12):
        for scale_name in scales_to_try:
            scale = SCALES[scale_name]

            # Calculate how well the notes fit this scale
            score = 0
            total_weight = sum(pitch_class_weights.values())

            for pitch_class, weight in pitch_class_weights.items():
                # Check if this pitch class is in the scale
                relative_pitch = (pitch_class - root) % 12
                if relative_pitch in scale:
                    score += weight
                else:
                    # Penalize notes outside the scale
                    score -= weight * 0.5

            # Normalize score
            if total_weight > 0:
                score = score / total_weight

            if score > best_score:
                best_score = score
                best_key = (NOTE_NAMES[root], scale_name)

    return best_key


def quantize_to_scale(midi_note: int, root: str = "C", scale: str = "minor") -> int:
    """
    Snap a MIDI note to the nearest note in the specified scale.

    Args:
        midi_note: MIDI note number (0-127)
        root: Root note name (e.g., "C", "D#", "F")
        scale: Scale name (e.g., "major", "minor", "afrobeat")

    Returns:
        Quantized MIDI note number
    """
    # Get root note number (0-11)
    if root not in NOTE_NAMES:
        root = "C"
    root_num = NOTE_NAMES.index(root)

    # Get scale intervals
    if scale not in SCALES:
        scale = "minor"
    scale_intervals = SCALES[scale]

    # Calculate octave and pitch class
    octave = midi_note // 12
    pitch_class = midi_note % 12

    # Find relative pitch from root
    relative_pitch = (pitch_class - root_num) % 12

    # Find nearest scale degree
    closest = min(scale_intervals, key=lambda d: abs(d - relative_pitch))

    # Reconstruct MIDI note
    quantized_pitch = (root_num + closest) % 12
    return octave * 12 + quantized_pitch


def transpose_notes(notes: List[Dict], semitones: int) -> List[Dict]:
    """
    Transpose all notes by a specified number of semitones.

    Args:
        notes: List of note dictionaries
        semitones: Number of semitones to transpose (positive or negative)

    Returns:
        New list of transposed notes
    """
    transposed = []
    for note in notes:
        new_note = note.copy()
        new_note["midi"] = max(0, min(127, note["midi"] + semitones))
        transposed.append(new_note)
    return transposed


def get_scale_info(scale_name: str) -> Dict:
    """
    Get information about a scale.

    Args:
        scale_name: Name of the scale

    Returns:
        Dictionary with scale information
    """
    if scale_name not in SCALES:
        scale_name = "minor"

    intervals = SCALES[scale_name]

    # Categorize the scale
    category = "other"
    if "minor" in scale_name or scale_name in ["dorian", "phrygian", "locrian"]:
        category = "minor"
    elif "major" in scale_name or scale_name in ["lydian", "mixolydian"]:
        category = "major"
    elif "pentatonic" in scale_name:
        category = "pentatonic"
    elif "afro" in scale_name:
        category = "afrobeat"
    elif "trap" in scale_name or "blues" in scale_name:
        category = "urban"

    return {
        "name": scale_name,
        "intervals": intervals,
        "num_notes": len(intervals),
        "category": category,
    }


def get_available_scales() -> List[str]:
    """
    Get list of all available scale names.

    Returns:
        List of scale names
    """
    return list(SCALES.keys())


def get_scales_by_category() -> Dict[str, List[str]]:
    """
    Get scales organized by category.

    Returns:
        Dictionary mapping categories to scale lists
    """
    categories = {
        "Western": ["major", "minor", "harmonic_minor", "melodic_minor"],
        "Modes": ["dorian", "phrygian", "lydian", "mixolydian", "locrian"],
        "Pentatonic": ["major_pentatonic", "minor_pentatonic"],
        "Blues": ["blues", "major_blues"],
        "Afrobeat": ["afrobeat", "afro_pentatonic"],
        "Trap/Hip-hop": ["trap", "trap_pentatonic"],
        "World": ["arabic", "japanese", "hungarian_minor", "spanish"],
    }
    return categories
