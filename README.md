# YapLab

YapLab is an emotional text-to-speech studio with a React + Tailwind frontend and a FastAPI backend. The root `app.py` builds the frontend when needed, starts the API, and serves everything together at `http://127.0.0.1:8000`.

## Quick start

The downloadable archive includes the built frontend, so the normal run only needs Python 3.10+. Node 22+ and pnpm/npm are needed when you edit or rebuild the React source.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`.

The four studio personas are Zubeda and Khalda (women), plus Samundar Khan and Jameed (men). The accent control selects a matching neural speaker for each persona.

For frontend development:

```bash
cd frontend
pnpm install
pnpm dev
```

If the built frontend is missing or older than the source, `python app.py` rebuilds it automatically after Node dependencies are installed.

YapLab uses lightweight online neural speech for more natural output and downloadable MP3 audio. It needs an internet connection while generating, but no GPU or API key. If neural speech is unavailable, the backend tries the optional local YapNet checkpoint and then the computer's installed speech voices. On Linux, install `espeak-ng` for that final offline fallback.

## Project structure

```text
YapLab/
├── app.py                         # one command launcher
├── backend/
│   ├── main.py                    # FastAPI application factory
│   ├── api/
│   │   ├── routes.py              # health, voices and TTS endpoints
│   │   └── schemas.py             # request validation
│   ├── core/settings.py           # shared paths and settings
│   ├── services/tts_engine.py     # neural + checkpoint + system inference
│   └── ml/
│       ├── tokenizer.py           # text normalization
│       └── yapnet.py              # compact experimental TTS model
├── frontend/
│   ├── app/                       # page shell, metadata and global theme
│   ├── components/
│   │   ├── yaplab/                # header, hero, studio and page sections
│   │   └── ui/                    # accessible Select, Slider and RadioGroup
│   ├── data/studio.ts             # voices, accents, tones and examples
│   └── public/favicon.svg
├── training/                      # optional from-scratch experiment
├── models/                        # optional local checkpoint
├── docs/datasets.md               # lightweight dataset plan
├── requirements.txt               # app-only Python packages
└── requirements-training.txt      # optional ML packages
```

## API

- `GET /api/health` — engine status
- `GET /api/voices` — voices, emotions and accents
- `POST /api/tts` — returns downloadable MP3 or WAV audio

Example request:

```json
{
  "text": "Plot twist: the weird idea was the good idea.",
  "voice": "zubeda",
  "emotion": "happy",
  "accent": "british",
  "speed": 1.0,
  "pitch": 0
}
```

## About training

Training a natural multi-voice, multi-emotion, multi-accent TTS model from scratch on a CPU is not realistic for an everyday laptop. The included YapNet code is a compact learning experiment, not a promise of production-quality speech.

For the lightest local experiment, use LJSpeech plus the RAVDESS speech-only archive. Add VCTK later only if you want learned accents. See [docs/datasets.md](docs/datasets.md).

Install the training stack separately:

```bash
pip install -r requirements-training.txt
python -m training.prepare_datasets \
  --ljspeech data/raw/ljspeech \
  --ravdess data/raw/ravdess
python -m training.train --config training/config.json
```

The training script writes `models/yaplab_emotion_tts.pt`. Until that real checkpoint exists, YapLab stays usable through system and browser voices; the project never labels random weights as a trained model.
