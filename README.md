# Melo - Enhanced AI Melody Generator

Transform your hummed melodies into professional-quality musical arrangements with AI-powered music generation. Melo takes your vocal ideas and converts them into polished MIDI files and synthesized audio with multiple instruments, scales, and enhancement modes.
<img width="1512" height="982" alt="Screenshot 2025-11-16 at 15 40 09" src="https://github.com/user-attachments/assets/32848af5-3260-4b2d-8867-66141d7faf53" />
<img width="1512" height="982" alt="Screenshot 2025-11-16 at 15 39 51" src="https://github.com/user-attachments/assets/65249ccc-8786-4689-9333-3fb107dddaa7" />
<img width="1512" height="982" alt="Screenshot 2025-11-16 at 16 53 40" src="https://github.com/user-attachments/assets/edf2d489-c514-4403-a12e-402c452d96ea" />
<img width="1512" height="982" alt="Screenshot 2025-11-16 at 16 53 10" src="https://github.com/user-attachments/assets/1d279f36-08ed-4a2f-8ad4-2f6091f43ad2" />



## Features

### Core Capabilities

- **Multi-Instrument Rendering**: Choose from 6 professionally-tuned instruments:
  - Piano - Classic acoustic piano sound
  - Guitar - Rich harmonic guitar tones
  - Strings - Smooth orchestral strings
  - Bells - Bright, crystalline bell tones
  - Synth Lead - Modern synthesizer sounds
  - Pads - Lush, atmospheric pad sounds

- **Advanced Scale Detection & Switching**:
  - Auto-detect your melody's key and scale
  - 20+ scales including Major, Minor, Afrobeat, Trap, Phrygian, Arabic, Japanese, and more
  - Organized by category: Western, Modes, Pentatonic, Blues, Afrobeat, Trap/Hip-hop, World

- **Rhythm Quantization**:
  - Snap notes to musical grids (1/4, 1/8, 1/16 notes)
  - Multiple groove templates: Straight, Swing, Afrobeat, Trap, Shuffle
  - Humanize mode for natural feel (0-100% adjustable)

- **Melody Enhancement Modes**:
  - **Smooth**: Create legato, flowing melodies with reduced jumps
  - **Bounce**: Add staccato, energetic feel
  - **Trap Run**: Add melodic slides and triplets for trap/hip-hop
  - **Afro Vibe**: Syncopated rhythms with Afrobeat character
  - **Choir Harmony**: Automatic harmony generation with thirds and fifths

## Tech Stack


- **Backend**: Python, FastAPI, Uvicorn
- **Audio Processing**: Librosa (YIN pitch detection), NumPy, SciPy
- **Music Generation**: Mido (MIDI), Custom additive synthesis engine
- **Storage**: Local filesystem + optional Supabase integration
- **Frontend**: Vanilla JavaScript, HTML5, CSS3

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Backend runs at: http://127.0.0.1:8000

### 2. Frontend

**Option A: Direct file access**
- Open `frontend/index.html` directly in your browser

**Option B: Local server (recommended)**
```bash
python -m http.server 5500
```
Then open: http://127.0.0.1:5500/frontend/index.html

### 3. Usage

1. **Select your settings**:
   - Choose an instrument (Piano, Guitar, Strings, etc.)
   - Pick a scale or use auto-detection
   - Configure rhythm quantization (optional)
   - Select a melody enhancement mode (optional)

2. **Record your melody**:
   - Click "Start Recording"
   - Hum, whistle, or sing your melody
   - Click "Stop & Generate"

3. **Get your results**:
   - Audio preview with your selected instrument
   - MIDI file ready for your DAW
   - Detailed analysis: note count, duration, pitch range, detected key

## Project Structure

```
Melo/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── audio_processing.py       # Pitch detection and note extraction
│   ├── melody_generator.py       # MIDI and audio synthesis
│   ├── music_theory.py           # Scale definitions and key detection
│   ├── rhythm_processor.py       # Quantization and groove templates
│   ├── melody_enhancer.py        # Enhancement modes and transformations
│   ├── supabase_storage.py       # Optional cloud storage
│   ├── requirements.txt          # Python dependencies
│   └── storage/                  # Generated files
│       ├── hums/                 # Recorded audio
│       ├── melodies/             # MIDI files
│       └── audio/                # Synthesized audio
├── frontend/
│   └── index.html                # Single-page web application
├── render.yaml                   # Render.com deployment config
├── supabase_schema.sql           # Supabase database schema
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Deployment

### Deploy to Render

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com):
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Set environment variables (see below)
   - Deploy!

3. **Environment Variables** (optional):
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   ```

### Supabase Integration (Optional)

Melo works perfectly with local file storage, but you can optionally use Supabase for cloud storage and metadata tracking.

1. **Create a Supabase project** at [supabase.com](https://supabase.com)

2. **Create storage buckets**:
   - `hums` - for recorded audio
   - `melodies` - for MIDI files
   - `audio` - for synthesized audio

3. **Run the SQL schema**:
   - Go to SQL Editor in Supabase dashboard
   - Copy and run `supabase_schema.sql`

4. **Set environment variables**:
   - Copy `.env.example` to `.env`
   - Add your Supabase URL and anon key

5. **Deploy** - Melo will automatically use Supabase if configured!

## API Documentation

### Endpoints

**POST /api/hum-to-melody**
- Upload audio and generate melody
- Parameters:
  - `file`: Audio file (required)
  - `instrument`: Instrument choice (default: "piano")
  - `scale`: Scale name or "auto" (default: auto-detect)
  - `root`: Root note (default: auto-detect)
  - `quantize_grid`: "1/4", "1/8", "1/16", or null
  - `groove_template`: "straight", "swing", "afrobeat", "trap", "shuffle"
  - `humanize`: 0.0 - 1.0 (default: 0)
  - `enhancement_mode`: "smooth", "bounce", "trap_run", "afro_vibe", "choir", or null
  - `enhancement_intensity`: 0.0 - 1.0 (default: 0.7)

**GET /api/scales**
- Get available scales organized by category

**GET /health**
- Health check endpoint

### Response Format

```json
{
  "id": "uuid",
  "midi_url": "/files/midi/uuid.mid",
  "audio_url": "/files/audio/uuid.wav",
  "note_count": 24,
  "original_note_count": 28,
  "detected_key": {
    "root": "C",
    "scale": "minor"
  },
  "analysis": {
    "num_notes": 24,
    "duration": 4.5,
    "pitch_range": 12,
    "avg_interval": 2.3
  },
  "settings": {
    "instrument": "piano",
    "scale": "minor",
    "root": "C",
    "quantize_grid": "1/8",
    "groove_template": "straight",
    "enhancement_mode": "smooth"
  }
}
```

## Development

### Running Tests

```bash
cd backend
pytest
```

### Adding New Instruments

Edit `backend/melody_generator.py` and add to the `INSTRUMENTS` dictionary:

```python
"your_instrument": {
    "harmonics": [(1.0, 1.0), (2.0, 0.5), ...],
    "attack": 0.01,
    "decay": 0.05,
    "sustain": 0.7,
    "release": 0.15,
    "brightness": 1.2,
}
```

### Adding New Scales

Edit `backend/music_theory.py` and add to the `SCALES` dictionary:

```python
"your_scale": [0, 2, 4, 5, 7, 9, 11],  # Semitone intervals
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Audio processing powered by [Librosa](https://librosa.org/)
- MIDI generation with [Mido](https://mido.readthedocs.io/)
- Optional storage with [Supabase](https://supabase.com/)

## Support

For issues, questions, or feature requests, contact SLEM.
