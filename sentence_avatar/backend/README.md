# ISL Avatar Speech Backend

FastAPI middle layer for the `sentence_avatar` project. It turns a spoken or
typed sentence (drawn from a **fixed, small vocabulary**) into a structured
**performance request** that the Godot ISL avatar consumes.

```
audio ──▶ Whisper (transcribe) ──▶ openSMILE (prosody) ──▶ summarize ──┐
                                                                       ├─▶ OpenAI LLM
text  ─────────────────────────────────────────────────────────────────┘   (gloss + emotion)
                                                                             │
                                                                             ▼
                                                     validate against vocab ──▶ contract JSON
```

The vocabulary is read **live** from `../sign_words.py` (`WORD_SIGNS` keys), so
the backend stays in sync as signs are added — nothing is hardcoded.

---

## Setup

Requires **Python 3.10+** and (for audio decoding of `.webm`/`.mp3`) the
**`ffmpeg`** binary on your `PATH`.

```bash
cd sentence_avatar/backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt        # large: pulls CTranslate2, PyAV, etc.

cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```

Install `ffmpeg` if you don't have it:

```bash
# macOS
brew install ffmpeg
# Debian/Ubuntu
sudo apt-get install -y ffmpeg
```

## Run

```bash
uvicorn app:app --reload --port 8000
```

- API is under `http://localhost:8000/api/...`
- The built Godot web app (if present at `../web_build/`) is served at
  `http://localhost:8000/` so the whole demo runs from one server. If the
  build dir is missing, the API still runs and `/` returns a small JSON notice.

> The first `/api/gloss-audio` call downloads/loads the Whisper model, which
> can take several seconds. Text-only glossing never loads Whisper.

---

## Configuration

All settings are environment variables (see `.env.example` for the annotated
list). Highlights:

| Variable | Default | Meaning |
| --- | --- | --- |
| `OPENAI_API_KEY` | *(unset)* | Required; gloss endpoints 503 without it. |
| `OPENAI_MODEL` | `gpt-4o` | Chat model for glossing. |
| `TRANSCRIBER` | `local` | `local` (faster-whisper) or `openai` (hosted API). |
| `WHISPER_MODEL` | `base` | Local model size (`tiny`…`large-v3`). |
| `WHISPER_DEVICE` | `auto` | `auto` \| `cpu` \| `cuda`. |
| `WHISPER_COMPUTE_TYPE` | `int8` | Precision (`int8` fast on CPU, `float16` on GPU). |
| `SENTENCE_AVATAR_DIR` | `../` | Where `sign_words.py` lives. |
| `WEB_BUILD_DIR` | `../web_build` | Static site served at `/`. |

---

## API

### `GET /api/health`
```json
{ "ok": true, "whisper": "faster-whisper:base", "llm_configured": false }
```

### `GET /api/vocab`
```json
{ "words": ["are", "bad", "drink", "empty", "going", "good", "hello", "no", "none", "nothing", "please", "tea", "teacher", "thank_you", "to", "tomorrow", "yes", "you"] }
```

### `POST /api/gloss-text`
Body:
```json
{ "text": "you are drinking tea tomorrow" }
```

### `POST /api/gloss-audio`
Multipart file upload (`.wav` / `.webm` / `.mp3`) under field name `file`.

### Output contract (both gloss endpoints)

```json
{
  "caption": "you are drinking tea tomorrow",
  "gloss": [
    {"word": "tomorrow", "emotion": "happy",   "intensity": 0.7},
    {"word": "tea",      "emotion": "happy",   "intensity": 0.7},
    {"word": "you",      "emotion": "neutral", "intensity": 0.3},
    {"word": "drink",    "emotion": "happy",   "intensity": 0.9}
  ],
  "overall_emotion": "happy",
  "overall_intensity": 0.7,
  "transcript": "you are drinking tea tomorrow",
  "prosody": null
}
```

Guarantees:

- `emotion` is one of `["neutral","happy","angry","sad","question","surprised"]`.
- `intensity` and `overall_intensity` are floats in `0.0`–`1.0`.
- **Every `word` in `gloss` is a key present in the vocabulary.** Unknown words
  from the LLM trigger one corrective retry, then are dropped (and logged);
  they are never returned.
- `gloss` is in ISL order (the LLM reorders English → ISL, dropping function
  words), constrained to the vocabulary.
- `transcript` is present on both endpoints (echoes input text for
  `gloss-text`). `prosody` is `null` for `gloss-text` and for any audio request
  where prosody extraction fails; otherwise it is a labeled summary dict, e.g.:

```json
{
  "pitch_mean_hz": 182, "pitch_range_hz": 90, "loudness": 0.42,
  "speaking_rate_wpm": 145, "voiced_segments_per_sec": 2.1,
  "mean_pause_sec": 0.18, "jitter": 0.012, "shimmer_db": 1.1, "hnr_db": 14.3,
  "duration_sec": 2.4, "word_count": 5,
  "notes": "high pitch, wide range, fast rate -> excited/agitated"
}
```

---

## Example requests

```bash
# Health
curl -s http://localhost:8000/api/health | jq

# Vocabulary
curl -s http://localhost:8000/api/vocab | jq

# Text glossing
curl -s http://localhost:8000/api/gloss-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "you are drinking tea tomorrow"}' | jq

# Audio glossing (record a wav/webm/mp3 first)
curl -s http://localhost:8000/api/gloss-audio \
  -F 'file=@recording.wav' | jq
```

---

## How the pieces fit

| File | Responsibility |
| --- | --- |
| `app.py` | FastAPI app: endpoints, CORS, static mount. |
| `transcribe.py` | `Transcriber` abstraction + faster-whisper / OpenAI impls. |
| `prosody.py` | openSMILE eGeMAPSv02 extraction → labeled summary. |
| `gloss.py` | OpenAI client, prompt, structured call, `validate_gloss`. |
| `config.py` | Env-driven settings + live vocabulary loader. |

### Downstream

The contract JSON maps directly onto the Godot avatar's direct-gloss entry
point (`SignDirector.gd` accepts a config with an explicit `gloss` array plus
`emotion` and `caption`). Feeding `{gloss, emotion, caption}` performs exactly
those signs in ISL order — no more re-deriving gloss from an English sentence
inside the avatar.

## Notes / caveats

- **`ffmpeg` is a system dependency** for decoding `.webm`/`.mp3` (both
  faster-whisper's PyAV and openSMILE's audio reader rely on it). `.wav` works
  without it.
- Prosody is best-effort: silent or very short clips can yield `NaN` features,
  in which case the affected stats are `null` (or the whole `prosody` object is
  `null`). This never fails the request.
- eGeMAPS reports F0 in semitones above 27.5 Hz; `prosody.py` converts to Hz.
- The vocabulary grows over time; restart is **not** required — `sign_words.py`
  is reloaded on each vocab read.
