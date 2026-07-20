"""
LLM glossing: English transcript (+ optional prosody) -> ISL gloss + emotion.

One OpenAI chat call turns a sentence into an ISL-ordered gloss constrained to
the project's fixed vocabulary, tagging each word with a per-word emotion and
intensity plus an overall emotion/intensity. The reply is requested as
structured JSON (json_schema when the model supports it, json_object
otherwise) and then re-validated against the live vocabulary -- we never trust
the model to only emit known words unchecked.

Public surface:
    * :func:`run_gloss`  - the orchestrator used by the API endpoints.
    * :func:`validate_gloss` - filter/repair a gloss list against the contract.
    * :class:`LLMNotConfigured` - raised when no OPENAI_API_KEY is available.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from config import ALLOWED_EMOTIONS, SETTINGS, load_vocab

logger = logging.getLogger("backend.gloss")


class LLMNotConfigured(RuntimeError):
    """Raised when the OpenAI API key needed for glossing is not set."""


# ---------------------------------------------------------------------------
# Prompt
#
# Kept as an easily-editable module constant. {vocab} and {emotions} are filled
# in live from the current vocabulary / emotion enum so the prompt never drifts
# out of sync with sign_words.py.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """\
You are an expert Indian Sign Language (ISL) gloss generator for an avatar.

Your job: convert an English sentence into an ISL GLOSS -- an ordered list of
sign words the avatar performs -- and tag ONE emotion for the whole delivery.

HARD CONSTRAINTS (obey exactly):
1. Use ONLY words from this fixed vocabulary (exact spelling, incl. underscores):
   {vocab}
   Never invent a word or translate to one outside this list. If a concept has no
   matching vocabulary word, omit it.
2. Emit gloss words ONLY for concepts ACTUALLY PRESENT in the sentence. Never pad
   the gloss with words the speaker did not say (e.g. do NOT add "none"/"nothing"
   unless the sentence actually expresses absence).
3. Output ISL word ORDER, not English order. ISL is topic-comment and DROPS
   function words -- articles (a/an/the), every form of "to be" (is/am/are/was/
   were/be), auxiliaries (do/does/did/will/can), and prepositions (to/of/for/at).
   DROP those words entirely; never gloss them. Examples:
     "are you a good teacher"  -> YOU TEACHER GOOD   (drop "are", "a")
     "you are drinking"        -> YOU DRINK          (drop "are", "-ing")
4. Choose EXACTLY ONE emotion for the whole utterance from this set: {emotions}.
   Put it in "overall_emotion" with an "overall_intensity" (0.0-1.0 = how strongly
   it is felt), and tag EVERY gloss word with that SAME emotion and intensity.

ONE EMOTION PER SENTENCE (the most important rule):
In sign language a single facial expression is HELD across the whole clause -- the
raised "question" brow stays up for the entire question; an angry face stays angry
throughout. So this pipeline uses ONE emotion for the ENTIRE utterance. Decide the
sentence's single dominant emotion FIRST, then give EVERY gloss word that identical
emotion and intensity. NEVER give one word a different emotion from the rest just
because that word (e.g. "good" or "bad") has a feeling of its own. The meaning of
the whole sentence decides the emotion -- never a single word in isolation.

HOW TO PICK THE ONE EMOTION:
Step 1 -- Is it a QUESTION? If the sentence ASKS something -- interrogative form
  (are/do/does/is/can/what/why/how/who ...) or a question mark -- the emotion is
  "question", FULL STOP, whatever words it contains. "are you a bad teacher?" is a
  QUESTION, not anger; "is this good?" is a QUESTION, not happiness. The
  interrogative ALWAYS wins over the feeling of any word inside it.
Step 2 -- Otherwise judge the STATEMENT's overall tone:
  - Praise / approval / good news             -> "happy"    ("you are a good teacher.")
  - Criticism / insult / bad news (statement) -> "angry"    ("you are a bad teacher.")
  - Loss / disappointment / apology           -> "sad"
  - Shock / amazement                         -> "surprised"
  - Not-knowing / "there is nothing" / a shrug-> "doubtful"
  - A request or appeal, or bare "please"     -> "pleading"  (soft ask -> low
    intensity, begging -> high). Overridden only by clear context, e.g.
    "yes, please" is glad acceptance -> "happy".
  - Positive words said flat / drawn-out / sing-song (needs prosody) -> "sarcasm".
  - Genuinely flat, affectless content        -> "neutral"  (last resort; prefer a
    real emotion at intensity 0.5-0.9 whenever the sentence supports one).

PROSODY (when provided): high pitch + loud + fast + wide range -> raise the
intensity (anger/excitement/surprise); low + quiet + slow + flat -> calmer/sadder,
lower intensity; upbeat words with flat or exaggerated delivery -> lean "sarcasm".
Prosody adjusts the INTENSITY and can tip a borderline choice, but it never breaks
the one-emotion-per-sentence rule.

EXAMPLES (every word shares the one emotion):
  "are you a bad teacher?"  -> gloss: YOU TEACHER BAD   | all "question"
  "you are a bad teacher."  -> gloss: YOU TEACHER BAD   | all "angry"
  "you are a good teacher!" -> gloss: YOU TEACHER GOOD  | all "happy"
  "hello teacher"           -> gloss: HELLO TEACHER     | all "happy"
  "please"                  -> gloss: PLEASE            | "pleading"

Return ONLY the structured JSON object requested. No prose, no markdown.
"""


def build_system_prompt(vocab: List[str]) -> str:
    """Render the system prompt with the live vocabulary and emotion enum."""
    return SYSTEM_PROMPT_TEMPLATE.format(
        vocab=", ".join(vocab),
        emotions=ALLOWED_EMOTIONS,
    )


def _build_user_message(text: str, prosody: Optional[Dict[str, Any]]) -> str:
    """Assemble the user turn: the transcript plus optional prosody summary."""
    parts = [f"Sentence to gloss: {text!r}"]
    if prosody:
        parts.append(
            "Prosody summary (derived acoustic stats; reason over these):\n"
            + json.dumps(prosody, indent=2)
        )
    else:
        parts.append("No prosody available (text-only input).")
    parts.append("Produce the ISL gloss JSON now.")
    return "\n\n".join(parts)


def _json_schema(vocab: List[str]) -> Dict[str, Any]:
    """Structured-output schema. Constrains `word` to the vocab at decode time.

    Note: OpenAI strict json_schema does not support numeric min/max, so
    intensity bounds are enforced by :func:`validate_gloss`, not the schema.
    """
    return {
        "name": "isl_gloss",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "gloss": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "word": {"type": "string", "enum": vocab},
                            "emotion": {"type": "string", "enum": ALLOWED_EMOTIONS},
                            "intensity": {"type": "number"},
                        },
                        "required": ["word", "emotion", "intensity"],
                    },
                },
                "overall_emotion": {"type": "string", "enum": ALLOWED_EMOTIONS},
                "overall_intensity": {"type": "number"},
            },
            "required": ["gloss", "overall_emotion", "overall_intensity"],
        },
    }


# ---------------------------------------------------------------------------
# OpenAI client (lazy singleton)
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    """Return a cached OpenAI client, or raise a clear error if unconfigured."""
    global _client
    if not SETTINGS.llm_configured:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Export it (or put it in .env) before "
            "calling the gloss endpoints."
        )
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(api_key=SETTINGS.openai_api_key)
    return _client


def _chat(messages: List[Dict[str, str]], vocab: List[str]) -> str:
    """Call the chat model, preferring strict json_schema, then json_object.

    Returns the raw JSON string content. Raises on transport/API errors.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=SETTINGS.openai_model,
            temperature=SETTINGS.openai_temperature,
            messages=messages,
            response_format={"type": "json_schema", "json_schema": _json_schema(vocab)},
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # noqa: BLE001 - model may not support json_schema
        logger.info("json_schema response_format unavailable (%s); using json_object.", exc)
        response = client.chat.completions.create(
            model=SETTINGS.openai_model,
            temperature=SETTINGS.openai_temperature,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _clamp01(value: Any, default: float = 0.5) -> float:
    """Coerce to a float in [0.0, 1.0], falling back to ``default``."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return max(0.0, min(1.0, f))


def _normalize_word(word: Any) -> str:
    """Normalize a candidate gloss word toward a vocabulary key.

    Lowercases and turns spaces/hyphens into underscores so "Thank You" and
    "thank-you" both map to the key "thank_you".
    """
    if not isinstance(word, str):
        return ""
    return word.strip().lower().replace("-", "_").replace(" ", "_")


def validate_gloss(
    gloss: Any,
    vocab: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Filter/repair a gloss list against the output contract.

    Guarantees every returned item has a `word` present in ``vocab``, an
    `emotion` from the allowed set (coerced to "neutral" otherwise), and an
    `intensity` clamped to [0.0, 1.0].

    Returns:
        ``(validated_gloss, dropped_words)`` where ``dropped_words`` lists the
        raw words that were not in the vocabulary (for logging / retry).
    """
    if vocab is None:
        vocab = load_vocab()
    vocab_set = set(vocab)

    validated: List[Dict[str, Any]] = []
    dropped: List[str] = []

    if not isinstance(gloss, list):
        return validated, dropped

    for item in gloss:
        if not isinstance(item, dict):
            continue
        raw_word = item.get("word", "")
        word = _normalize_word(raw_word)
        if word not in vocab_set:
            dropped.append(str(raw_word))
            continue
        emotion = item.get("emotion")
        if emotion not in ALLOWED_EMOTIONS:
            emotion = "neutral"
        validated.append(
            {
                "word": word,
                "emotion": emotion,
                "intensity": _clamp01(item.get("intensity"), default=0.5),
            }
        )
    return validated, dropped


def _literal_gloss(
    text: str,
    vocab: List[str],
    emotion: str = "neutral",
    intensity: float = 0.6,
) -> List[Dict[str, Any]]:
    """Literal word-for-word gloss, used when NO LLM is available.

    Each input word that EXACTLY matches a vocabulary sign is emitted in the
    order it was spoken -- no reordering, no stemming, no dropping, and no
    emotion guessing. The caller supplies the emotion (from the web app's
    expression dropdown) and it is applied uniformly to every word; words with
    no matching sign are simply not performed.

    NOTE: the non-lexical signs (are/to/going) are neutral "hold" animations, so
    including them just makes the avatar stay still for those words, as intended.
    """
    vocab_set = set(vocab)
    emotion = emotion if emotion in ALLOWED_EMOTIONS else "neutral"
    intensity = _clamp01(intensity, 0.6)
    result: List[Dict[str, Any]] = []
    for token in (text or "").lower().split():
        word = token.strip(".,!?;:\"'()[]-")
        if word in vocab_set:
            result.append({"word": word, "emotion": emotion, "intensity": intensity})
    return result


def _summarize_overall(
    gloss: List[Dict[str, Any]],
    model_emotion: Any,
    model_intensity: Any,
) -> Tuple[str, float]:
    """Pick the ONE overall emotion/intensity for the whole utterance.

    Trust the model's own overall_emotion when it named a real (non-neutral) one.
    Otherwise (the model said neutral, or gave nothing) fall back to the strongest
    non-neutral per-word emotion, so a lone emotive word (e.g. "bad" -> angry in
    the rule path) still colours the whole sentence instead of defaulting to a
    blank neutral face.
    """
    if model_emotion in ALLOWED_EMOTIONS and model_emotion != "neutral":
        return model_emotion, _clamp01(model_intensity, default=0.3)
    non_neutral = [g for g in gloss if g.get("emotion", "neutral") != "neutral"]
    if non_neutral:
        top = max(non_neutral, key=lambda g: g["intensity"])
        return top["emotion"], _clamp01(top["intensity"], default=0.3)
    if model_emotion in ALLOWED_EMOTIONS:
        return model_emotion, _clamp01(model_intensity, default=0.3)
    if gloss:
        top = max(gloss, key=lambda g: g["intensity"])
        return top["emotion"], _clamp01(top["intensity"], default=0.3)
    return "neutral", 0.3


def _enforce_uniform_emotion(
    gloss: List[Dict[str, Any]], emotion: str, intensity: float
) -> List[Dict[str, Any]]:
    """Force ONE emotion across the whole utterance.

    A signer holds a single facial expression through a clause, so every gloss
    word carries the same emotion + intensity. This is the hard guarantee behind
    the prompt's one-emotion rule: even if the model (or the rule fallback) tags
    an emotive word like "good"/"bad" differently from the rest, the avatar's face
    can never flip mid-sentence (the "question on one word, angry on the next" bug).
    """
    for item in gloss:
        item["emotion"] = emotion
        item["intensity"] = intensity
    return gloss


# Each word's DEFAULT facial expression, applied ONLY when that word was left
# "neutral" -- so the LLM can always override it per word. This is the safety net
# behind the prompt: NONE/NOTHING/EMPTY -> "doubtful" ("I don't know"), BAD ->
# "angry" (displeasure), GOOD -> "happy" (approval), PLEASE -> "pleading" (an
# appeal). "please" is context-dependent, so the prompt is told to override this
# in clear cases (e.g. "yes, please" -> happy) by emitting that emotion explicitly;
# the default here only catches the standalone/ambiguous "please" the LLM leaves
# neutral, giving it the pleading face. Keeps word<->expression in the gloss layer.
_WORD_DEFAULT_EMOTION: Dict[str, Tuple[str, float]] = {
    "none": ("doubtful", 0.75),
    "nothing": ("doubtful", 0.75),
    "empty": ("doubtful", 0.75),
    "bad": ("angry", 0.7),
    "good": ("happy", 0.7),
    "please": ("pleading", 0.7),
}


def _apply_word_emotion_defaults(gloss: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fill in each word's default emotion where none was assigned (== neutral)."""
    for item in gloss:
        default = _WORD_DEFAULT_EMOTION.get(item.get("word"))
        if default and item.get("emotion", "neutral") == "neutral":
            item["emotion"], item["intensity"] = default[0], default[1]
    return gloss


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_gloss(
    text: str,
    prosody: Optional[Dict[str, Any]] = None,
    vocab: Optional[List[str]] = None,
    emotion: str = "neutral",
    intensity: float = 0.6,
) -> Dict[str, Any]:
    """Gloss ``text`` into the output contract (without transcript/prosody keys).

    Performs one corrective retry if the model emits words outside the
    vocabulary, drops any remaining unknowns, and falls back to a naive
    in-order gloss if the model output is unparseable twice.

    Args:
        text: The sentence to gloss (transcript or typed text).
        prosody: Optional prosody summary dict to inform emotion/intensity.
        vocab: Optional explicit vocabulary; defaults to the live vocab.

    Returns:
        ``{"caption", "gloss", "overall_emotion", "overall_intensity",
        "glossed_by"}`` where ``glossed_by`` is "llm" or "rules".

    Never raises for a missing key: without an OPENAI_API_KEY it falls back to a
    LITERAL word-for-word gloss (known words in spoken order) with the caller's
    chosen ``emotion`` applied uniformly, so speech/text still drive the avatar.
    """
    if vocab is None:
        vocab = load_vocab()

    # No LLM -> LITERAL word-for-word gloss. No rules, no reordering, no emotion
    # inference: the caller (the web app's expression dropdown) supplies the one
    # emotion, applied uniformly. This is the whole no-key path now.
    if not SETTINGS.llm_configured:
        logger.info("No OPENAI_API_KEY; literal word-for-word gloss (emotion from caller).")
        emo = emotion if emotion in ALLOWED_EMOTIONS else "neutral"
        inten = _clamp01(intensity, 0.6)
        return {
            "caption": text,
            "gloss": _literal_gloss(text, vocab, emo, inten),
            "overall_emotion": emo,
            "overall_intensity": inten,
            "glossed_by": "literal",
        }

    system = build_system_prompt(vocab)
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": _build_user_message(text, prosody)},
    ]

    parsed: Optional[Dict[str, Any]] = None
    validated: List[Dict[str, Any]] = []
    dropped: List[str] = []

    # --- Attempt 1 --------------------------------------------------------
    try:
        raw = _chat(messages, vocab)
        parsed = json.loads(raw)
        validated, dropped = validate_gloss(parsed.get("gloss"), vocab)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("LLM returned unparseable JSON on attempt 1: %s", exc)
    except Exception as exc:  # noqa: BLE001 - API/transport errors
        logger.error("LLM call failed on attempt 1: %s", exc)

    # --- Attempt 2 (corrective retry) ------------------------------------
    # Retry once if the model emitted unknown words, or produced nothing usable.
    if dropped or not validated:
        if dropped:
            logger.info("Dropping out-of-vocabulary words, retrying: %s", dropped)
        # Feed the model back its own (bad) reply and an explicit correction.
        if parsed is not None:
            messages.append({"role": "assistant", "content": json.dumps(parsed)})
        correction = (
            "That response was not acceptable. Use ONLY these exact words in "
            f"the gloss: {', '.join(vocab)}. "
        )
        if dropped:
            correction += f"These words are NOT allowed and must be removed: {dropped}. "
        correction += "Return the corrected structured JSON only."
        messages.append({"role": "user", "content": correction})

        try:
            raw = _chat(messages, vocab)
            parsed2 = json.loads(raw)
            validated2, dropped2 = validate_gloss(parsed2.get("gloss"), vocab)
            if dropped2:
                logger.info("Still dropping after retry (final): %s", dropped2)
            # Keep the retry result if it produced anything usable.
            if validated2:
                validated = validated2
                parsed = parsed2
        except Exception as exc:  # noqa: BLE001
            logger.warning("Corrective retry failed: %s", exc)

    # --- Fallback (LLM produced nothing usable) --------------------------
    # Degrade to a literal, neutral gloss so the avatar still performs the known
    # words. (The expression dropdown feeds the no-LLM path, not this one.)
    if not validated:
        logger.warning("LLM gave no usable gloss; literal neutral fallback for: %r", text)
        return {
            "caption": text,
            "gloss": _literal_gloss(text, vocab, "neutral", 0.4),
            "overall_emotion": "neutral",
            "overall_intensity": 0.4,
            "glossed_by": "literal",
        }

    validated = _apply_word_emotion_defaults(validated)
    overall_emotion, overall_intensity = _summarize_overall(
        validated,
        (parsed or {}).get("overall_emotion"),
        (parsed or {}).get("overall_intensity"),
    )
    validated = _enforce_uniform_emotion(validated, overall_emotion, overall_intensity)

    return {
        "caption": text,
        "gloss": validated,
        "overall_emotion": overall_emotion,
        "overall_intensity": overall_intensity,
        "glossed_by": "llm",
    }
