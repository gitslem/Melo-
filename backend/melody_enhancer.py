"""
Melody enhancement and transformation utilities.
"""
from typing import List, Dict
import numpy as np
from music_theory import quantize_to_scale, SCALES


def enhance_melody(
    notes: List[Dict],
    mode: str = "smooth",
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Transform a melody using various enhancement modes.

    Args:
        notes: List of note dictionaries
        mode: Enhancement mode - "smooth", "bounce", "trap_run", "afro_vibe", "choir"
        intensity: How much to apply the effect (0.0 - 1.0)
        root: Root note for scale-based transformations
        scale: Scale name for quantization

    Returns:
        Enhanced melody notes
    """
    if not notes:
        return []

    enhancers = {
        "smooth": smooth_melody,
        "bounce": bounce_melody,
        "trap_run": trap_run_melody,
        "afro_vibe": afro_vibe_melody,
        "choir": choir_harmony,
    }

    enhancer = enhancers.get(mode, smooth_melody)
    return enhancer(notes, intensity, root, scale)


def smooth_melody(
    notes: List[Dict],
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Smooth out large melodic jumps, create more stepwise motion.

    Args:
        notes: Original notes
        intensity: How much to smooth (0.0 = original, 1.0 = very smooth)
        root: Root note
        scale: Scale name

    Returns:
        Smoothed melody
    """
    if len(notes) < 2:
        return notes

    smoothed = [notes[0].copy()]

    for i in range(1, len(notes)):
        prev_midi = smoothed[-1]["midi"]
        curr_midi = notes[i]["midi"]
        interval = curr_midi - prev_midi

        # If jump is too large, reduce it
        if abs(interval) > 5:  # More than a fourth
            # Blend between original and smoothed
            target_midi = prev_midi + np.sign(interval) * min(abs(interval), 3)
            new_midi = int(curr_midi * (1 - intensity) + target_midi * intensity)
            new_midi = quantize_to_scale(new_midi, root, scale)
        else:
            new_midi = curr_midi

        smoothed.append({
            "midi": new_midi,
            "start": notes[i]["start"],
            "end": notes[i]["end"],
        })

    return smoothed


def bounce_melody(
    notes: List[Dict],
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Create a bouncy, staccato feel with shorter notes.

    Args:
        notes: Original notes
        intensity: How bouncy (0.0 = original, 1.0 = very short)
        root: Root note
        scale: Scale name

    Returns:
        Bouncy melody
    """
    bouncy = []

    for note in notes:
        duration = note["end"] - note["start"]

        # Shorten notes based on intensity
        staccato_duration = duration * (1.0 - intensity * 0.7)
        staccato_duration = max(0.05, staccato_duration)

        bouncy.append({
            "midi": note["midi"],
            "start": note["start"],
            "end": note["start"] + staccato_duration,
        })

    return bouncy


def trap_run_melody(
    notes: List[Dict],
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Add melodic runs, slides, and triplets for trap style.

    Args:
        notes: Original notes
        intensity: How much to add runs
        root: Root note
        scale: Scale name (typically harmonic minor or trap scale)

    Returns:
        Trap-style melody with runs
    """
    if len(notes) < 2:
        return notes

    trap_notes = []

    for i in range(len(notes) - 1):
        curr_note = notes[i]
        next_note = notes[i + 1]

        trap_notes.append(curr_note.copy())

        # Check if there's a large interval
        interval = abs(next_note["midi"] - curr_note["midi"])

        # Add slide/run notes for large intervals
        if interval > 3 and np.random.random() < intensity:
            gap_time = next_note["start"] - curr_note["end"]

            # Only add runs if there's enough time
            if gap_time > 0.15:
                num_fill_notes = min(3, interval // 2)
                fill_duration = gap_time / (num_fill_notes + 1)

                # Create ascending or descending run
                direction = 1 if next_note["midi"] > curr_note["midi"] else -1
                step_size = interval // (num_fill_notes + 1)

                for j in range(num_fill_notes):
                    fill_midi = curr_note["midi"] + direction * step_size * (j + 1)
                    fill_midi = quantize_to_scale(fill_midi, root, scale)

                    fill_start = curr_note["end"] + fill_duration * j
                    fill_end = fill_start + fill_duration * 0.7  # Short notes

                    trap_notes.append({
                        "midi": fill_midi,
                        "start": fill_start,
                        "end": fill_end,
                    })

    # Add the last note
    trap_notes.append(notes[-1].copy())

    return trap_notes


def afro_vibe_melody(
    notes: List[Dict],
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Add Afrobeat syncopation and rhythmic stagger.

    Args:
        notes: Original notes
        intensity: How much syncopation to add
        root: Root note
        scale: Scale name (typically afrobeat scale)

    Returns:
        Afrobeat-style melody
    """
    afro_notes = []

    for i, note in enumerate(notes):
        new_note = note.copy()

        # Add syncopation - shift some notes slightly off-beat
        if i % 2 == 1 and intensity > 0.3:  # Odd-numbered notes
            # Detect beat (assume 120 BPM default)
            beat_duration = 0.5  # seconds
            grid_size = beat_duration / 4  # 16th notes

            # Shift forward slightly
            offset = grid_size * 0.3 * intensity
            new_note["start"] += offset
            new_note["end"] += offset

        # Occasionally add repetition/stutter
        if intensity > 0.6 and i < len(notes) - 1:
            gap = notes[i + 1]["start"] - note["end"]
            if gap > 0.2 and np.random.random() < 0.3:
                # Add a repeated note
                repeat_duration = min(0.1, gap * 0.4)
                repeat_note = {
                    "midi": note["midi"],
                    "start": note["end"] + gap * 0.3,
                    "end": note["end"] + gap * 0.3 + repeat_duration,
                }
                afro_notes.append(new_note)
                afro_notes.append(repeat_note)
                continue

        afro_notes.append(new_note)

    # Sort by start time
    afro_notes.sort(key=lambda n: n["start"])

    return afro_notes


def choir_harmony(
    notes: List[Dict],
    intensity: float = 0.7,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Add harmonies to create a choir effect (still monophonic, but with chord tones).

    Args:
        notes: Original notes (melody line)
        intensity: How dense the harmony (affects note selection)
        root: Root note
        scale: Scale name

    Returns:
        Notes with harmony tones added in sequence
    """
    harmony_notes = []

    for note in notes:
        # Keep original melody note
        harmony_notes.append(note.copy())

        # Add harmony notes based on intensity
        if intensity > 0.3:
            # Add third above
            third_up = note["midi"] + 3  # Minor third
            if scale in ["major", "major_pentatonic", "lydian", "mixolydian"]:
                third_up = note["midi"] + 4  # Major third

            third_up = quantize_to_scale(third_up, root, scale)

            # Create harmony note (slightly offset in time for texture)
            harmony_duration = (note["end"] - note["start"]) * 0.8
            harmony_notes.append({
                "midi": third_up,
                "start": note["start"] + 0.02,  # Slight delay
                "end": note["start"] + harmony_duration,
            })

        if intensity > 0.6:
            # Add fifth above
            fifth_up = note["midi"] + 7
            fifth_up = quantize_to_scale(fifth_up, root, scale)

            harmony_duration = (note["end"] - note["start"]) * 0.7
            harmony_notes.append({
                "midi": fifth_up,
                "start": note["start"] + 0.04,
                "end": note["start"] + harmony_duration,
            })

        if intensity > 0.8:
            # Add octave
            octave_up = note["midi"] + 12
            octave_up = min(127, octave_up)  # Stay within MIDI range

            harmony_duration = (note["end"] - note["start"]) * 0.9
            harmony_notes.append({
                "midi": octave_up,
                "start": note["start"] + 0.01,
                "end": note["start"] + harmony_duration,
            })

    # Sort by start time
    harmony_notes.sort(key=lambda n: n["start"])

    return harmony_notes


def add_ornamentation(
    notes: List[Dict],
    style: str = "trill",
    density: float = 0.5,
    root: str = "C",
    scale: str = "minor"
) -> List[Dict]:
    """
    Add ornamental notes (trills, grace notes, etc.).

    Args:
        notes: Original notes
        style: "trill", "grace", "mordent"
        density: How many notes to ornament (0.0 - 1.0)
        root: Root note
        scale: Scale name

    Returns:
        Ornamented melody
    """
    if style == "grace":
        return add_grace_notes(notes, density, root, scale)
    elif style == "trill":
        return add_trills(notes, density, root, scale)
    else:
        return notes


def add_grace_notes(
    notes: List[Dict],
    density: float,
    root: str,
    scale: str
) -> List[Dict]:
    """Add quick grace notes before main notes."""
    ornamented = []

    for note in notes:
        # Randomly add grace note based on density
        if np.random.random() < density:
            grace_duration = 0.05
            grace_midi = note["midi"] + 1  # Upper neighbor
            grace_midi = quantize_to_scale(grace_midi, root, scale)

            ornamented.append({
                "midi": grace_midi,
                "start": max(0, note["start"] - grace_duration),
                "end": note["start"],
            })

        ornamented.append(note.copy())

    return ornamented


def add_trills(
    notes: List[Dict],
    density: float,
    root: str,
    scale: str
) -> List[Dict]:
    """Add trills to longer notes."""
    ornamented = []

    for note in notes:
        duration = note["end"] - note["start"]

        # Only trill on longer notes
        if duration > 0.3 and np.random.random() < density:
            trill_duration = 0.06
            num_trills = int(duration / trill_duration)

            # Alternate between main note and upper neighbor
            upper_neighbor = quantize_to_scale(note["midi"] + 1, root, scale)

            for i in range(num_trills):
                trill_midi = note["midi"] if i % 2 == 0 else upper_neighbor
                trill_start = note["start"] + i * trill_duration
                trill_end = min(note["end"], trill_start + trill_duration)

                ornamented.append({
                    "midi": trill_midi,
                    "start": trill_start,
                    "end": trill_end,
                })
        else:
            ornamented.append(note.copy())

    return ornamented


def extend_melody_duration(
    notes: List[Dict],
    min_duration: float = 15.0
) -> List[Dict]:
    """
    Extend melody to minimum duration by repeating and varying the pattern.

    Args:
        notes: Original notes
        min_duration: Minimum duration in seconds (default: 15.0)

    Returns:
        Extended melody notes
    """
    if not notes:
        return []

    # Calculate current duration
    current_duration = max(n["end"] for n in notes)

    # If already long enough, return as-is
    if current_duration >= min_duration:
        return notes

    extended = notes.copy()
    offset = current_duration

    # Repeat the melody until we reach minimum duration
    while offset < min_duration:
        # Create a variation of the original melody
        for note in notes:
            new_note = note.copy()
            new_note["start"] = note["start"] + offset
            new_note["end"] = note["end"] + offset

            # Add slight variation to avoid monotony
            # Occasionally transpose by octave or fifth
            if np.random.random() < 0.2:
                variation = np.random.choice([12, -12, 7, -7, 0])
                new_note["midi"] = max(36, min(96, note["midi"] + variation))

            extended.append(new_note)

        offset += current_duration

    # Trim notes that extend beyond min_duration
    extended = [n for n in extended if n["start"] < min_duration]

    # Sort by start time
    extended.sort(key=lambda n: n["start"])

    return extended
