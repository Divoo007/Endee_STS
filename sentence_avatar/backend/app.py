"""
FastAPI app for the speech -> Indian Sign Language avatar pipeline.

Pipeline (audio path):
    audio upload -> Whisper transcribe -> openSMILE prosody -> summarize
                 -> OpenAI LLM gloss -> validate against vocab -> contract JSON

The text path skips transcription and prosody. Both paths return the exact
output contract documented in README.md.

Run:
    uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import SETTINGS, load_vocab, whisper_initial_prompt
from gloss import LLMNotConfigured, run_gloss
from prosody import extract_prosody
from transcribe import Transcriber, build_transcriber


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles that makes the browser REVALIDATE every file before reusing it.

    The Godot web export ships a large, always-same-named ``index.pck``. Without
    an explicit Cache-Control the browser caches it heuristically and keeps
    serving a STALE build after a re-export ("I don't see any change"). Sending
    ``no-cache`` still allows fast 304s -- it only forbids reusing the cached copy
    without first checking ETag/Last-Modified -- so a fresh export is always
    picked up on the next reload.
    """

    async def get_response(self, path: str, scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response

logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("backend.app")

app = FastAPI(
    title="ISL Avatar Speech Backend",
    description="Speech/text -> Indian Sign Language gloss + emotion for the Godot avatar.",
    version="1.0.0",
)

# Wide-open CORS: this is a single-host demo; the frontend is served from the
# same origin, but we allow all origins so the API is also usable standalone.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Lazily-built transcriber ------------------------------------------------
# Whisper models are heavy to load; only build the transcriber when the audio
# endpoint is first exercised (never for text-only use).
_transcriber: Optional[Transcriber] = None


def get_transcriber() -> Transcriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = build_transcriber()
    return _transcriber


# --- Request/response models -------------------------------------------------
class TextRequest(BaseModel):
    """Body for POST /api/gloss-text."""

    text: str = Field(..., description="Sentence to gloss, from the fixed vocabulary.")
    emotion: Optional[str] = Field(
        None,
        description=(
            "Expression to apply in the LITERAL (no-LLM) path -- from the web app's "
            "expression dropdown. IGNORED when the LLM is enabled (the LLM decides "
            "emotion). Defaults to 'neutral'."
        ),
    )


# --- Endpoints ---------------------------------------------------------------
@app.get("/api/health")
def health() -> Dict[str, Any]:
    """Liveness + configuration probe."""
    return {
        "ok": True,
        "whisper": SETTINGS.transcriber_label,
        "llm_configured": SETTINGS.llm_configured,
    }


@app.get("/api/vocab")
def vocab() -> Dict[str, Any]:
    """Return the live vocabulary so the frontend can show what's supported."""
    return {"words": load_vocab()}


@app.post("/api/gloss-text")
def gloss_text(req: TextRequest) -> Dict[str, Any]:
    """Gloss a typed sentence (no transcription, no prosody)."""
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="`text` must be a non-empty string.")

    # run_gloss never raises: with the LLM it reorders + auto-detects emotion
    # (and IGNORES req.emotion); without it, a literal word-for-word gloss uses
    # req.emotion (the web app's expression dropdown) uniformly.
    result = run_gloss(text, prosody=None, emotion=(req.emotion or "neutral"))

    # Contract: transcript echoes the input text; prosody is null for text input.
    result["transcript"] = text
    result["prosody"] = None
    return result


@app.post("/api/gloss-audio")
async def gloss_audio(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Transcribe a recording, extract prosody, and gloss it.

    Works with no OPENAI_API_KEY: Whisper + openSMILE still run, and glossing
    falls back to rules (see run_gloss) so the avatar performs for testing.
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    tmp_path: Optional[str] = None
    try:
        # Persist the upload to a temp file so both Whisper and openSMILE can
        # read it by path.
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 1) Transcribe (biased toward the closed vocabulary).
        vocab_words = load_vocab()
        transcriber = get_transcriber()
        transcription = transcriber.transcribe(
            tmp_path,
            initial_prompt=whisper_initial_prompt(vocab_words),
        )
        transcript = transcription.text

        # 2) Prosody (degrades to None on any failure).
        prosody = extract_prosody(
            tmp_path,
            transcript=transcript,
            duration_seconds=transcription.duration,
        )

        # 3) Gloss with transcript + prosody as context.
        result = run_gloss(transcript, prosody=prosody, vocab=vocab_words)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - surface a clean 500 with context
        logger.exception("gloss-audio failed")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    result["transcript"] = transcript
    result["prosody"] = prosody
    return result


# --- Static frontend ---------------------------------------------------------
# Serve the built Godot web app at "/" so the whole demo runs from one server.
# Mounted LAST so the /api/* routes take precedence over the catch-all mount.
if SETTINGS.web_build_dir.is_dir():
    app.mount("/", NoCacheStaticFiles(directory=str(SETTINGS.web_build_dir), html=True), name="web")
    logger.info("Serving web build from %s", SETTINGS.web_build_dir)
else:
    logger.warning(
        "Web build dir not found (%s); serving API only. "
        "Build/export the Godot web app or set WEB_BUILD_DIR.",
        SETTINGS.web_build_dir,
    )

    @app.get("/")
    def root() -> Dict[str, Any]:
        """Fallback root when no web build is present."""
        return {
            "service": "ISL Avatar Speech Backend",
            "web_build": "not found",
            "endpoints": ["/api/health", "/api/vocab", "/api/gloss-text", "/api/gloss-audio"],
        }
