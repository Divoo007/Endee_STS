"""
Fixed-sentence sign-language prototype: given only an emotion (the
sentence is hardcoded to sign_words.SENTENCE, for testing one sentence at a
time before this expands to arbitrary sentences), render a video of the
avatar performing that sentence's placeholder hand signs word by word,
holding the chosen emotion's facial expression constant for the whole clip
-- same structure as the old isl_avatar prototype, on the new Godot/VRM
pipeline.

Usage:
    python3 render_signs.py --emotion happy
    python3 render_signs.py --emotion angry
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from sign_words import SENTENCE, WORD_SIGNS

EMOTIONS = ["happy", "sad", "angry", "surprised", "relaxed"]
FPS = 60
SECONDS_PER_WORD = 1.6
QUIT_AFTER_BUFFER_SECONDS = 1.5

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GODOT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "godot")


def tokenize(sentence):
    return re.findall(r"[a-z]+", sentence.lower())


def render_video(emotion, output_path, seconds_per_word=SECONDS_PER_WORD):
    if emotion not in EMOTIONS:
        raise ValueError(f"Unknown emotion '{emotion}'. Supported: {EMOTIONS}")
    if shutil.which("godot") is None:
        raise RuntimeError("godot not found on PATH (brew install --cask godot)")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH")

    words = tokenize(SENTENCE)
    unknown = [w for w in words if w not in WORD_SIGNS]
    if unknown:
        raise ValueError(
            f"No sign data for: {unknown}. Supported words: {sorted(WORD_SIGNS)}"
        )

    config = {
        "sentence": SENTENCE,
        "emotion": emotion,
        "words": words,
        "keyframes": {w: WORD_SIGNS[w] for w in set(words)},
        "seconds_per_word": seconds_per_word,
    }
    total_seconds = len(words) * seconds_per_word + QUIT_AFTER_BUFFER_SECONDS
    quit_after_frames = int(total_seconds * FPS)

    tmp_dir = tempfile.mkdtemp(prefix="sentence_avatar_signs_")
    try:
        config_path = os.path.join(tmp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        avi_path = os.path.join(tmp_dir, "render.avi")
        cmd = [
            "godot", "--path", GODOT_PROJECT_DIR,
            "res://scenes/SignMain.tscn",
            "--write-movie", avi_path,
            "--quit-after", str(quit_after_frames),
            "--", "--config", config_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not os.path.exists(avi_path):
            raise RuntimeError(
                f"Godot render failed (exit {result.returncode}):\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", avi_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description=f"Sign-language prototype for the fixed sentence {SENTENCE!r}"
    )
    parser.add_argument(
        "--emotion", required=True, choices=EMOTIONS,
        help="Facial expression held constant for the whole clip.",
    )
    parser.add_argument(
        "--seconds-per-word", type=float, default=SECONDS_PER_WORD,
        help=f"Duration of each word's sign (default {SECONDS_PER_WORD}).",
    )
    parser.add_argument(
        "--output", default=os.path.join(PROJECT_ROOT, "output_signs.mp4"),
        help="Output mp4 path (default sentence_avatar/output_signs.mp4).",
    )
    args = parser.parse_args()

    render_video(args.emotion, args.output, args.seconds_per_word)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    sys.exit(main())
