import os
from uuid import uuid4
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from audio_processing import extract_melody_notes, analyze_melody
from melody_generator import notes_to_midi, notes_to_wav
from rhythm_processor import quantize_rhythm, detect_tempo
from melody_enhancer import enhance_melody, extend_melody_duration
from music_theory import get_available_scales, get_scales_by_category
from supabase_storage import supabase_storage


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
HUMS_DIR = STORAGE_DIR / "hums"
MELODIES_DIR = STORAGE_DIR / "melodies"
AUDIO_DIR = STORAGE_DIR / "audio"

for d in [HUMS_DIR, MELODIES_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Hum2Melody AI - Enhanced")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/scales")
async def get_scales():
    """Get available scales organized by category."""
    return JSONResponse({
        "scales": get_available_scales(),
        "categories": get_scales_by_category(),
    })


@app.post("/api/hum-to-melody")
async def hum_to_melody(
    file: UploadFile = File(...),
    instrument: str = Form("piano"),
    scale: Optional[str] = Form(None),
    root: Optional[str] = Form(None),
    auto_detect_key: bool = Form(True),
    quantize_grid: Optional[str] = Form(None),
    groove_template: str = Form("straight"),
    humanize: float = Form(0.0),
    enhancement_mode: Optional[str] = Form(None),
    enhancement_intensity: float = Form(0.7),
):
    """
    Convert hummed audio to MIDI and synthesized melody.

    Args:
        file: Audio file (WAV, MP3, etc.)
        instrument: Instrument for synthesis (piano, guitar, strings, bells, synth, pads)
        scale: Scale name (e.g., "minor", "major", "afrobeat"). Auto-detected if not provided.
        root: Root note (e.g., "C", "D#"). Auto-detected if not provided.
        auto_detect_key: Whether to auto-detect the key
        quantize_grid: Rhythmic grid for quantization ("1/4", "1/8", "1/16", or None)
        groove_template: Groove pattern (straight, swing, afrobeat, trap)
        humanize: Humanization amount (0.0 - 1.0)
        enhancement_mode: Melody enhancement (smooth, bounce, trap_run, afro_vibe, choir, or None)
        enhancement_intensity: Enhancement intensity (0.0 - 1.0)

    Returns:
        JSON with file URLs and melody information
    """
    # Basic validation
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio type")

    file_ext = ".wav"  # we'll convert anything to wav internally
    hum_id = str(uuid4())
    raw_path = HUMS_DIR / f"{hum_id}{file_ext}"

    # Save uploaded file
    content = await file.read()
    raw_path.write_bytes(content)

    # Process to extract melody notes
    try:
        notes, detected_root, detected_scale = extract_melody_notes(
            raw_path,
            scale=scale,
            root=root,
            auto_detect_key=auto_detect_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting melody: {e}")

    if not notes:
        raise HTTPException(status_code=422, detail="Could not detect a clear melody. Try humming closer to the mic.")

    # Store original note count for comparison
    original_note_count = len(notes)

    # Apply rhythm quantization if requested
    if quantize_grid:
        detected_bpm = detect_tempo(notes)
        notes = quantize_rhythm(
            notes,
            grid=quantize_grid,
            bpm=detected_bpm,
            humanize=humanize,
            groove_template=groove_template
        )

    # Apply melody enhancement if requested (default to smooth if none specified)
    if enhancement_mode:
        notes = enhance_melody(
            notes,
            mode=enhancement_mode,
            intensity=enhancement_intensity,
            root=detected_root,
            scale=detected_scale
        )
    else:
        # Apply smooth enhancement by default for better-sounding melodies
        notes = enhance_melody(
            notes,
            mode="smooth",
            intensity=0.5,
            root=detected_root,
            scale=detected_scale
        )

    # Extend melody to minimum 15 seconds for richer compositions
    notes = extend_melody_duration(notes, min_duration=15.0)

    # Analyze melody
    analysis = analyze_melody(notes)

    # Generate MIDI
    midi_path = MELODIES_DIR / f"{hum_id}.mid"
    notes_to_midi(notes, midi_path)

    # Generate audio preview with selected instrument
    audio_path = AUDIO_DIR / f"{hum_id}.wav"
    notes_to_wav(notes, audio_path, instrument=instrument)

    # Try to upload to Supabase if configured, otherwise use local files
    if supabase_storage.enabled:
        try:
            # Upload files to Supabase Storage
            hum_url = supabase_storage.upload_file(
                "hums",
                raw_path,
                f"{hum_id}.wav",
                "audio/wav"
            )
            midi_url = supabase_storage.upload_file(
                "melodies",
                midi_path,
                f"{hum_id}.mid",
                "audio/midi"
            )
            audio_url = supabase_storage.upload_file(
                "audio",
                audio_path,
                f"{hum_id}.wav",
                "audio/wav"
            )

            # Save metadata to database
            metadata = {
                "hum_url": hum_url,
                "midi_url": midi_url,
                "audio_url": audio_url,
                "detected_root": detected_root,
                "detected_scale": detected_scale,
                "note_count": len(notes),
                "instrument": instrument,
                "quantize_grid": quantize_grid,
                "groove_template": groove_template,
                "enhancement_mode": enhancement_mode,
                "duration": analysis.get("duration"),
                "pitch_range": analysis.get("pitch_range"),
                "avg_interval": analysis.get("avg_interval"),
            }
            supabase_storage.save_melody_metadata(hum_id, metadata)

        except Exception as e:
            print(f"Supabase upload failed, falling back to local: {e}")
            # Fall back to local URLs
            midi_url = f"/files/midi/{midi_path.name}"
            audio_url = f"/files/audio/{audio_path.name}"
    else:
        # Use local file URLs
        midi_url = f"/files/midi/{midi_path.name}"
        audio_url = f"/files/audio/{audio_path.name}"

    # Convert all numpy types to native Python types for JSON serialization
    response_data = {
        "id": hum_id,
        "midi_url": midi_url,
        "audio_url": audio_url,
        "note_count": len(notes),
        "original_note_count": original_note_count,
        "detected_key": {
            "root": detected_root,
            "scale": detected_scale,
        },
        "analysis": convert_numpy_types(analysis),
        "notes": convert_numpy_types(notes),  # Include notes for frontend visualization
        "settings": {
            "instrument": instrument,
            "scale": detected_scale,
            "root": detected_root,
            "quantize_grid": quantize_grid,
            "groove_template": groove_template,
            "enhancement_mode": enhancement_mode,
        }
    }

    return JSONResponse(response_data)


@app.get("/files/midi/{filename}")
async def get_midi(filename: str):
    path = MELODIES_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="audio/midi", filename=filename)


@app.get("/files/audio/{filename}")
async def get_audio(filename: str):
    path = AUDIO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="audio/wav", filename=filename)
