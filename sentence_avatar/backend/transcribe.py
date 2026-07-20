"""
Speech-to-text abstraction for the ISL avatar backend.

A tiny pluggable :class:`Transcriber` interface with two implementations:

* :class:`FasterWhisperTranscriber` - local, offline, the default. Runs
  faster-whisper on this machine. Decodes any ffmpeg-readable container
  (.wav/.webm/.mp3/...) internally.
* :class:`OpenAIWhisperTranscriber` - OpenAI's hosted audio transcription API,
  using the same OPENAI_API_KEY. Selected with ``TRANSCRIBER=openai``.

Both are biased toward the closed vocabulary via an ``initial_prompt`` so that
common domain words transcribe more reliably.

Models are loaded lazily on first use so importing this module is cheap and the
FastAPI app starts fast even when transcription is never exercised.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from config import SETTINGS

logger = logging.getLogger("backend.transcribe")


@dataclass
class TranscriptionResult:
    """Result of a transcription.

    Attributes:
        text: The recognized transcript (whitespace-trimmed).
        duration: Audio duration in seconds, when the backend can supply it.
            Used downstream to estimate speaking rate (words per minute).
            ``None`` when unknown.
    """

    text: str
    duration: Optional[float] = None


class Transcriber(ABC):
    """Abstract speech-to-text backend."""

    #: Short label reported by /api/health (e.g. "faster-whisper:base").
    label: str = "abstract"

    @abstractmethod
    def transcribe(self, audio_path: str, initial_prompt: Optional[str] = None) -> TranscriptionResult:
        """Transcribe the audio file at ``audio_path``.

        Args:
            audio_path: Path to a decodable audio file on disk.
            initial_prompt: Optional text that biases decoding toward the
                expected vocabulary.

        Returns:
            A :class:`TranscriptionResult`.
        """
        raise NotImplementedError


class FasterWhisperTranscriber(Transcriber):
    """Local transcription with faster-whisper (CTranslate2 Whisper)."""

    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        language: Optional[str] = None,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language  # None => auto-detect
        self.label = f"faster-whisper:{model_size}"
        self._model = None  # lazily constructed WhisperModel

    def _get_model(self):
        """Load the Whisper model on first use (can take a few seconds)."""
        if self._model is None:
            # Imported lazily so the dependency is only required when actually
            # transcribing locally.
            from faster_whisper import WhisperModel

            logger.info(
                "Loading faster-whisper model '%s' (device=%s, compute=%s)...",
                self.model_size,
                self.device,
                self.compute_type,
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str, initial_prompt: Optional[str] = None) -> TranscriptionResult:
        model = self._get_model()
        # `segments` is a generator; iterate to materialize the transcript.
        segments, info = model.transcribe(
            audio_path,
            initial_prompt=initial_prompt,
            language=self.language,  # None => auto-detect; pinned to "en" by default
            beam_size=5,
            vad_filter=True,  # drop non-speech, helps on short recordings
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        duration = getattr(info, "duration", None)
        logger.info("Transcribed %.2fs of audio: %r", duration or -1.0, text)
        return TranscriptionResult(text=text, duration=duration)


class OpenAIWhisperTranscriber(Transcriber):
    """Transcription via OpenAI's hosted audio transcription API."""

    def __init__(self, api_key: Optional[str], model: str, language: Optional[str] = None) -> None:
        if not api_key:
            # Surface the misconfiguration eagerly and clearly.
            raise RuntimeError(
                "TRANSCRIBER=openai requires OPENAI_API_KEY to be set."
            )
        self.api_key = api_key
        self.model = model
        self.language = language  # None => auto-detect
        self.label = f"openai:{model}"
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def transcribe(self, audio_path: str, initial_prompt: Optional[str] = None) -> TranscriptionResult:
        client = self._get_client()
        kwargs: dict = {}
        if self.language:
            kwargs["language"] = self.language
        with open(audio_path, "rb") as fh:
            response = client.audio.transcriptions.create(
                model=self.model,
                file=fh,
                prompt=initial_prompt or "",
                response_format="text",
                **kwargs,
            )
        # With response_format="text" the SDK returns a plain string.
        text = (response if isinstance(response, str) else getattr(response, "text", "")).strip()
        # The transcription API does not return duration; leave it to the caller
        # to probe the file (see prosody.audio_duration_seconds).
        logger.info("OpenAI transcription: %r", text)
        return TranscriptionResult(text=text, duration=None)


def build_transcriber() -> Transcriber:
    """Construct the transcriber selected by configuration.

    Falls back to local faster-whisper for any unrecognized TRANSCRIBER value.
    """
    if SETTINGS.transcriber == "openai":
        return OpenAIWhisperTranscriber(
            api_key=SETTINGS.openai_api_key,
            model=SETTINGS.openai_whisper_model,
            language=SETTINGS.whisper_language,
        )
    if SETTINGS.transcriber != "local":
        logger.warning(
            "Unknown TRANSCRIBER=%r; falling back to local faster-whisper.",
            SETTINGS.transcriber,
        )
    return FasterWhisperTranscriber(
        model_size=SETTINGS.whisper_model,
        device=SETTINGS.whisper_device,
        compute_type=SETTINGS.whisper_compute_type,
        language=SETTINGS.whisper_language,
    )
