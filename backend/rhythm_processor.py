"""
Rhythm processing and quantization utilities.
"""
from typing import List, Dict
import numpy as np


def quantize_rhythm(
    notes: List[Dict],
    grid: str = "1/8",
    bpm: float = 120,
    humanize: float = 0.0,
    groove_template: str = "straight"
) -> List[Dict]:
    """
    Quantize note timings to a rhythmic grid.

    Args:
        notes: List of note dictionaries with 'start', 'end', 'midi' keys
        grid: Quantization grid - "1/4", "1/8", "1/16", "1/32"
        bpm: Tempo in beats per minute
        humanize: Amount of humanization (0.0 = strict, 1.0 = loose)
        groove_template: Groove pattern - "straight", "swing", "afrobeat", "trap"

    Returns:
        New list of quantized notes
    """
    if not notes:
        return []

    # Calculate grid size in seconds
    beat_duration = 60.0 / bpm
    grid_divisions = {
        "1/4": 1.0,
        "1/8": 0.5,
        "1/16": 0.25,
        "1/32": 0.125,
    }
    grid_size = beat_duration * grid_divisions.get(grid, 0.5)

    # Get groove pattern
    groove = get_groove_pattern(groove_template, grid)

    quantized_notes = []

    for i, note in enumerate(notes):
        start = note["start"]
        end = note["end"]
        duration = end - start

        # Find nearest grid position
        grid_position = round(start / grid_size)
        quantized_start = grid_position * grid_size

        # Apply groove swing
        groove_index = grid_position % len(groove)
        swing_offset = groove[groove_index] * grid_size
        quantized_start += swing_offset

        # Apply humanization (random variation)
        if humanize > 0:
            max_deviation = grid_size * 0.3 * humanize
            random_offset = np.random.uniform(-max_deviation, max_deviation)
            quantized_start += random_offset

        # Quantize duration to grid
        duration_grids = max(1, round(duration / grid_size))
        quantized_end = quantized_start + (duration_grids * grid_size)

        # Ensure non-negative start time
        quantized_start = max(0.0, quantized_start)
        quantized_end = max(quantized_start + 0.05, quantized_end)

        quantized_notes.append({
            "midi": note["midi"],
            "start": quantized_start,
            "end": quantized_end,
        })

    # Sort by start time
    quantized_notes.sort(key=lambda n: n["start"])

    # Normalize to start at 0
    if quantized_notes:
        first_start = quantized_notes[0]["start"]
        for note in quantized_notes:
            note["start"] -= first_start
            note["end"] -= first_start

    return quantized_notes


def get_groove_pattern(template: str, grid: str) -> List[float]:
    """
    Get groove swing pattern for different styles.

    Args:
        template: Groove template name
        grid: Grid size for context

    Returns:
        List of swing offsets (as fractions, 0.0 = no swing)
    """
    patterns = {
        "straight": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

        # Classic swing - every other note is delayed
        "swing": [0.0, 0.15, 0.0, 0.15, 0.0, 0.15, 0.0, 0.15],

        # Afrobeat - syncopated, emphasis on off-beats
        "afrobeat": [0.0, 0.05, 0.1, 0.0, 0.08, 0.0, 0.12, 0.05],

        # Trap - triplet feel with delayed hi-hats
        "trap": [0.0, 0.0, 0.2, 0.0, 0.1, 0.0, 0.15, 0.0],

        # Shuffle - strong triplet swing
        "shuffle": [0.0, 0.25, 0.0, 0.25, 0.0, 0.25, 0.0, 0.25],

        # Drunk/humanized - slightly random
        "drunk": [0.02, -0.03, 0.04, -0.02, 0.03, -0.04, 0.01, -0.01],
    }

    return patterns.get(template, patterns["straight"])


def adjust_note_lengths(
    notes: List[Dict],
    style: str = "normal",
    legato: float = 0.95
) -> List[Dict]:
    """
    Adjust note lengths based on articulation style.

    Args:
        notes: List of note dictionaries
        style: "staccato", "normal", "legato"
        legato: Legato amount (0.0 = very short, 1.0 = full length)

    Returns:
        Notes with adjusted durations
    """
    if not notes:
        return []

    adjusted = []

    length_multipliers = {
        "staccato": 0.3,
        "normal": 0.8,
        "legato": 0.95,
    }

    multiplier = length_multipliers.get(style, 0.8)

    for i, note in enumerate(notes):
        new_note = note.copy()
        duration = note["end"] - note["start"]

        # Calculate new duration
        new_duration = duration * multiplier

        # For legato, notes can connect to next note
        if style == "legato" and i < len(notes) - 1:
            next_start = notes[i + 1]["start"]
            max_duration = next_start - note["start"]
            new_duration = min(new_duration, max_duration * legato)

        # Ensure minimum duration
        new_duration = max(0.05, new_duration)

        new_note["end"] = note["start"] + new_duration
        adjusted.append(new_note)

    return adjusted


def detect_tempo(notes: List[Dict]) -> float:
    """
    Estimate the tempo (BPM) from note timings.

    Args:
        notes: List of note dictionaries

    Returns:
        Estimated BPM (defaults to 120 if cannot detect)
    """
    if len(notes) < 4:
        return 120.0

    # Calculate inter-onset intervals (time between note starts)
    onsets = [n["start"] for n in notes]
    intervals = np.diff(onsets)

    # Filter out very short or very long intervals
    intervals = intervals[(intervals > 0.1) & (intervals < 2.0)]

    if len(intervals) == 0:
        return 120.0

    # Find the most common interval (mode)
    # This is likely the basic beat unit
    hist, bins = np.histogram(intervals, bins=20)
    most_common_interval = bins[np.argmax(hist)]

    # Assume this interval represents a quarter note or eighth note
    # Try both and pick the one that gives a reasonable BPM
    bpm_quarter = 60.0 / most_common_interval
    bpm_eighth = 60.0 / (most_common_interval * 2)

    # Prefer BPM in typical range (60-180)
    if 60 <= bpm_quarter <= 180:
        return round(bpm_quarter)
    elif 60 <= bpm_eighth <= 180:
        return round(bpm_eighth)
    else:
        # Normalize to typical range
        if bpm_quarter < 60:
            return round(bpm_quarter * 2)
        elif bpm_quarter > 180:
            return round(bpm_quarter / 2)

    return 120.0


def apply_groove_template(
    notes: List[Dict],
    template: str = "afrobeat",
    intensity: float = 0.5
) -> List[Dict]:
    """
    Apply a pre-defined groove template to notes.

    Args:
        notes: List of note dictionaries
        template: Template name ("afrobeat", "trap", "swing", etc.)
        intensity: How much to apply the groove (0.0 - 1.0)

    Returns:
        Notes with groove applied
    """
    if not notes or intensity == 0:
        return notes

    # Detect tempo first
    bpm = detect_tempo(notes)

    # Apply rhythm quantization with groove
    grooved = quantize_rhythm(
        notes,
        grid="1/16",
        bpm=bpm,
        humanize=intensity * 0.3,
        groove_template=template
    )

    return grooved


def add_triplet_feel(notes: List[Dict], strength: float = 0.5) -> List[Dict]:
    """
    Convert notes to have a triplet feel (for trap/hip-hop styles).

    Args:
        notes: List of note dictionaries
        strength: How much triplet feel to apply (0.0 - 1.0)

    Returns:
        Notes with triplet timing
    """
    if not notes or strength == 0:
        return notes

    bpm = detect_tempo(notes)
    triplet_notes = []

    for note in notes:
        # Convert timing to triplet grid
        beat_duration = 60.0 / bpm
        triplet_duration = beat_duration / 3

        # Snap to triplet grid
        triplet_pos = round(note["start"] / triplet_duration)
        new_start = triplet_pos * triplet_duration

        # Blend between original and triplet timing
        blended_start = note["start"] * (1 - strength) + new_start * strength

        duration = note["end"] - note["start"]

        triplet_notes.append({
            "midi": note["midi"],
            "start": blended_start,
            "end": blended_start + duration,
        })

    return triplet_notes
