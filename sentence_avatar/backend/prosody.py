"""
Prosody extraction and summarization.

Uses the ``opensmile`` package with the eGeMAPSv02 *Functionals* feature set to
compute paralinguistic features from a recording, then boils the ~88 raw
features down to a SMALL dict of labeled, human-readable statistics.

Why summarize? An LLM has no grounded sense of what a raw feature vector like
"F0semitoneFrom27.5Hz_sma3nz_amean = 34.2" means, but it can reason well over a
short list of derived, labeled stats ("pitch_mean_hz: 182, speaking_rate_wpm:
145, notes: high pitch, wide range -> excited/agitated"). So we hand the LLM the
summary only, never the raw vectors.

Everything here degrades gracefully: any failure returns ``None`` (the endpoint
still succeeds with ``prosody: null``) rather than raising.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("backend.prosody")

# eGeMAPSv02 encodes F0 as semitones above 27.5 Hz. Convert back to Hz with:
#   hz = 27.5 * 2 ** (semitones / 12)
_F0_BASE_HZ = 27.5


def audio_duration_seconds(audio_path: str) -> Optional[float]:
    """Best-effort audio duration in seconds.

    Tries soundfile first (fast, no decode of the whole file). Returns ``None``
    if the format is not readable without extra system codecs.
    """
    try:
        import soundfile as sf

        info = sf.info(audio_path)
        if info.samplerate:
            return float(info.frames) / float(info.samplerate)
    except Exception as exc:  # noqa: BLE001 - duration is optional
        logger.debug("soundfile could not read duration for %s: %s", audio_path, exc)
    return None


def _semitones_to_hz(semitones: float) -> float:
    return _F0_BASE_HZ * (2.0 ** (semitones / 12.0))


def _get(row: Dict[str, Any], key: str) -> Optional[float]:
    """Fetch a feature by column name, returning None if absent/NaN."""
    value = row.get(key)
    if value is None:
        return None
    try:
        fvalue = float(value)
    except (TypeError, ValueError):
        return None
    # openSMILE emits NaN for undefined features (e.g. F0 on unvoiced audio).
    if fvalue != fvalue:  # NaN check
        return None
    return fvalue


def _heuristic_notes(
    pitch_mean_hz: Optional[float],
    pitch_range_hz: Optional[float],
    loudness: Optional[float],
    speaking_rate_wpm: Optional[float],
) -> str:
    """Compose a short human-readable interpretation from the summary stats.

    These are deliberately coarse, labeled cues for the LLM -- NOT a clinical
    judgement. Thresholds are rough and easy to tune.
    """
    cues = []
    if pitch_mean_hz is not None:
        if pitch_mean_hz >= 200:
            cues.append("high pitch")
        elif pitch_mean_hz <= 120:
            cues.append("low pitch")
        else:
            cues.append("mid pitch")
    if pitch_range_hz is not None:
        if pitch_range_hz >= 80:
            cues.append("wide range")
        elif pitch_range_hz <= 25:
            cues.append("flat/narrow range")
    if loudness is not None:
        if loudness >= 0.8:
            cues.append("loud")
        elif loudness <= 0.25:
            cues.append("quiet")
    if speaking_rate_wpm is not None:
        if speaking_rate_wpm >= 170:
            cues.append("fast rate")
        elif speaking_rate_wpm <= 90:
            cues.append("slow rate")

    if not cues:
        return "no strong prosodic cues"

    # A light, transparent mapping from cue combinations to an affect guess.
    joined = ", ".join(cues)
    excited = any(c in cues for c in ("high pitch", "wide range", "loud", "fast rate"))
    subdued = any(c in cues for c in ("low pitch", "flat/narrow range", "quiet", "slow rate"))
    if excited and not subdued:
        return f"{joined} -> excited/agitated"
    if subdued and not excited:
        return f"{joined} -> calm/subdued"
    return joined


def extract_prosody(
    audio_path: str,
    transcript: str = "",
    duration_seconds: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Extract and summarize prosody for one recording.

    Args:
        audio_path: Path to the (already saved) audio file.
        transcript: Transcript text, used only to estimate speaking rate.
        duration_seconds: Known audio duration; if omitted we probe the file.

    Returns:
        A small dict of labeled stats, or ``None`` if extraction failed for any
        reason (missing package, unreadable audio, silent clip, ...).
    """
    try:
        import opensmile

        smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
        # Functionals level yields a single-row DataFrame per file.
        frame = smile.process_file(audio_path)
        row: Dict[str, Any] = frame.iloc[0].to_dict()
    except Exception as exc:  # noqa: BLE001 - prosody must never crash a request
        logger.warning("Prosody extraction failed for %s: %s", audio_path, exc)
        return None

    try:
        # --- Pitch (F0) ---------------------------------------------------
        f0_mean_st = _get(row, "F0semitoneFrom27.5Hz_sma3nz_amean")
        f0_p20_st = _get(row, "F0semitoneFrom27.5Hz_sma3nz_percentile20.0")
        f0_p80_st = _get(row, "F0semitoneFrom27.5Hz_sma3nz_percentile80.0")

        pitch_mean_hz = round(_semitones_to_hz(f0_mean_st), 1) if f0_mean_st is not None else None
        pitch_range_hz = None
        if f0_p20_st is not None and f0_p80_st is not None:
            pitch_range_hz = round(_semitones_to_hz(f0_p80_st) - _semitones_to_hz(f0_p20_st), 1)

        # --- Loudness / energy -------------------------------------------
        loudness = _get(row, "loudness_sma3_amount") or _get(row, "loudness_sma3_amean")
        if loudness is not None:
            loudness = round(loudness, 3)

        # --- Voice quality (easy extras) ---------------------------------
        jitter = _get(row, "jitterLocal_sma3nz_amean")
        shimmer = _get(row, "shimmerLocaldB_sma3nz_amean")
        hnr = _get(row, "HNRdBACF_sma3nz_amean")

        # --- Voiced / pause structure ------------------------------------
        voiced_per_sec = _get(row, "VoicedSegmentsPerSec")
        mean_voiced_len = _get(row, "MeanVoicedSegmentLengthSec")
        # eGeMAPS labels the unvoiced-run stat (a proxy for pause length) as
        # MeanUnvoicedSegmentLength. Treat it as an approximate pause measure.
        mean_pause_len = _get(row, "MeanUnvoicedSegmentLength")

        # --- Speaking rate (derived, not from openSMILE) -----------------
        dur = duration_seconds if duration_seconds is not None else audio_duration_seconds(audio_path)
        word_count = len([w for w in transcript.split() if w.strip()])
        speaking_rate_wpm: Optional[float] = None
        if dur and dur > 0 and word_count > 0:
            speaking_rate_wpm = round(word_count / (dur / 60.0), 0)

        summary: Dict[str, Any] = {
            "pitch_mean_hz": pitch_mean_hz,
            "pitch_range_hz": pitch_range_hz,
            "loudness": loudness,
            "speaking_rate_wpm": speaking_rate_wpm,
            "voiced_segments_per_sec": round(voiced_per_sec, 2) if voiced_per_sec is not None else None,
            "mean_voiced_segment_sec": round(mean_voiced_len, 3) if mean_voiced_len is not None else None,
            "mean_pause_sec": round(mean_pause_len, 3) if mean_pause_len is not None else None,
            "jitter": round(jitter, 4) if jitter is not None else None,
            "shimmer_db": round(shimmer, 3) if shimmer is not None else None,
            "hnr_db": round(hnr, 2) if hnr is not None else None,
            "duration_sec": round(dur, 2) if dur else None,
            "word_count": word_count,
        }
        summary["notes"] = _heuristic_notes(
            pitch_mean_hz, pitch_range_hz, loudness, speaking_rate_wpm
        )
        return summary
    except Exception as exc:  # noqa: BLE001 - summarization must not crash a request
        logger.warning("Prosody summarization failed for %s: %s", audio_path, exc)
        return None
