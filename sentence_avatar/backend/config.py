"""
Environment-driven configuration for the speech -> ISL avatar backend.

Every tunable is read from the process environment (optionally seeded from a
``.env`` file via python-dotenv) with a sensible default, so the service runs
out of the box for a demo and can be reconfigured for production without code
changes. See ``.env.example`` for the full, documented list.

Nothing here performs network or GPU work at import time -- it only reads
strings and computes paths. Heavy objects (Whisper models, the OpenAI client)
are constructed lazily by the modules that own them.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

try:
    # Optional: load a local .env into os.environ if present. Never fatal --
    # in production the environment is usually injected by the platform.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience, not a requirement
    pass


# The allowed emotion labels. This is the single source of truth for the enum
# referenced by the output contract, the LLM prompt, and validation.
ALLOWED_EMOTIONS: List[str] = [
    "neutral",
    "happy",
    "angry",
    "sad",
    "question",
    "surprised",
    "pleading",
]


def _env(name: str, default: str) -> str:
    """Read a string env var, treating an empty string as "unset"."""
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_optional(name: str) -> Optional[str]:
    """Read an env var that may legitimately be absent (e.g. the API key)."""
    value = os.environ.get(name)
    return value if value not in (None, "") else None


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the backend configuration.

    Built once from the environment at import time (see :data:`SETTINGS`).
    """

    # --- OpenAI (LLM glossing + optional OpenAI Whisper) ---------------------
    openai_api_key: Optional[str] = field(default_factory=lambda: _env_optional("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4o"))
    # Sampling temperature for the gloss call. Low by default for determinism.
    openai_temperature: float = field(
        default_factory=lambda: float(_env("OPENAI_TEMPERATURE", "0.2"))
    )

    # --- Transcription -------------------------------------------------------
    # "local"  -> faster-whisper running on this machine (default).
    # "openai" -> OpenAI's hosted audio transcription API (uses the same key).
    transcriber: str = field(default_factory=lambda: _env("TRANSCRIBER", "local").lower())
    # Local faster-whisper model size: tiny | base | small | medium | large-v3 ...
    # Default "medium": far more accurate than base on short, domain-specific
    # clips (base frequently mis-hears the small vocabulary). ~1.5 GB, downloaded
    # once on first audio request; slower on CPU but acceptable for short utterances.
    whisper_model: str = field(default_factory=lambda: _env("WHISPER_MODEL", "medium"))
    # Force the decoding language (ISO-639-1). We only expect English here, so
    # pinning it stops Whisper from mis-detecting a short clip as another language
    # (a common cause of garbled transcripts). Set WHISPER_LANGUAGE="" to auto-detect.
    whisper_language: Optional[str] = field(default_factory=lambda: _env_optional("WHISPER_LANGUAGE") or "en")
    # faster-whisper device: "cpu" | "cuda" | "auto".
    whisper_device: str = field(default_factory=lambda: _env("WHISPER_DEVICE", "auto"))
    # faster-whisper compute type: "int8" (fast CPU default) | "int8_float16" |
    # "float16" (GPU) | "float32" | "default".
    whisper_compute_type: str = field(
        default_factory=lambda: _env("WHISPER_COMPUTE_TYPE", "int8")
    )
    # Model name for the OpenAI hosted transcription API (when TRANSCRIBER=openai).
    openai_whisper_model: str = field(
        default_factory=lambda: _env("OPENAI_WHISPER_MODEL", "whisper-1")
    )

    # --- Paths ---------------------------------------------------------------
    # Directory that contains sign_words.py (the vocabulary source of truth).
    # Defaults to the parent of this backend/ directory, i.e. sentence_avatar/.
    sentence_avatar_dir: Path = field(
        default_factory=lambda: Path(
            _env(
                "SENTENCE_AVATAR_DIR",
                str(Path(__file__).resolve().parent.parent),
            )
        ).resolve()
    )

    # Built Godot web app to serve at "/". Defaults to sentence_avatar/web_build.
    web_build_dir: Path = field(
        default_factory=lambda: Path(
            _env(
                "WEB_BUILD_DIR",
                str(Path(__file__).resolve().parent.parent / "web_build"),
            )
        ).resolve()
    )

    # --- Misc ---------------------------------------------------------------
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO").upper())

    @property
    def llm_configured(self) -> bool:
        """True when an OpenAI API key is available for the gloss call."""
        return bool(self.openai_api_key)

    @property
    def transcriber_label(self) -> str:
        """Human-readable description of the active transcription backend."""
        if self.transcriber == "openai":
            return f"openai:{self.openai_whisper_model}"
        return f"faster-whisper:{self.whisper_model}"


# Single shared settings instance for the whole process.
SETTINGS = Settings()


# ---------------------------------------------------------------------------
# Vocabulary loading
#
# The vocabulary is the set of keys in sign_words.py's WORD_SIGNS dict. We read
# it LIVE from that module (never hardcode it) so the backend stays in sync as
# signs are added. sign_words.py is pure Python data, so reloading it is cheap
# and lets /api/vocab reflect edits without a server restart.
# ---------------------------------------------------------------------------


def _import_sign_words():
    """Import (and reload) the project's sign_words module.

    Raises a clear RuntimeError if it cannot be located, so a misconfigured
    SENTENCE_AVATAR_DIR fails loudly instead of silently returning an empty
    vocabulary.
    """
    parent = str(SETTINGS.sentence_avatar_dir)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    try:
        module = importlib.import_module("sign_words")
        # Reload so a running server picks up edits to sign_words.py live.
        module = importlib.reload(module)
        return module
    except Exception as exc:  # pragma: no cover - depends on deployment layout
        raise RuntimeError(
            f"Could not import sign_words.py from '{parent}'. "
            "Set SENTENCE_AVATAR_DIR to the directory that contains it."
        ) from exc


def load_vocab() -> List[str]:
    """Return the sorted list of known ISL gloss words (WORD_SIGNS keys)."""
    module = _import_sign_words()
    word_signs = getattr(module, "WORD_SIGNS", None)
    if not isinstance(word_signs, dict) or not word_signs:
        raise RuntimeError("sign_words.WORD_SIGNS is missing or not a non-empty dict.")
    return sorted(word_signs.keys())


@lru_cache(maxsize=1)
def _initial_prompt_cache_key(vocab_tuple: tuple) -> str:
    """Internal memoization key helper (see :func:`whisper_initial_prompt`)."""
    return ", ".join(w.replace("_", " ") for w in vocab_tuple)


def whisper_initial_prompt(vocab: Optional[List[str]] = None) -> str:
    """Build a Whisper ``initial_prompt`` that biases decoding toward the vocab.

    With a bounded, closed vocabulary we can prime Whisper with the expected
    words to push transcription accuracy. Underscores in gloss keys (e.g.
    ``thank_you``) are rendered as spaces so the prompt reads naturally.
    """
    words = vocab if vocab is not None else load_vocab()
    natural = _initial_prompt_cache_key(tuple(words))
    return (
        "This is a short sentence spoken in simple English using a small, fixed "
        f"vocabulary. Expected words include: {natural}."
    )
