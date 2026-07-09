"""
Hard-coded 3-sentence ISL demo renderer.

Give it one of the demo sentences with a trailing (Emotion); it renders the
avatar signing the ISL gloss (TOMORROW TEA YOU DRINK) with that emotion held
on the face/head.

Usage:
    python3 render_signs.py --sentence "You are drinking tea tomorrow. (Happy)"
    python3 render_signs.py --sentence "You are drinking tea tomorrow. (Angry)"
    python3 render_signs.py --sentence "Why are you drinking tea tomorrow? (Question)"

The sentence->gloss + emotion parsing lives in SignDirector.gd so the web app
and this CLI share one implementation; here we just pass the raw sentence and
the full per-word keyframe table (WORD_SIGNS) through the config.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

from sign_words import WORD_SIGNS

FPS = 60
SECONDS_PER_WORD = 1.8
GLOSS_LEN = 4  # TOMORROW TEA YOU DRINK
QUIT_AFTER_BUFFER_SECONDS = 1.5

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GODOT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "godot")


def render_video(sentence, output_path, seconds_per_word=SECONDS_PER_WORD):
    if shutil.which("godot") is None:
        raise RuntimeError("godot not found on PATH (brew install --cask godot)")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH")

    config = {
        "sentence": sentence,
        "keyframes": WORD_SIGNS,
        "seconds_per_word": seconds_per_word,
    }
    total_seconds = GLOSS_LEN * seconds_per_word + QUIT_AFTER_BUFFER_SECONDS
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
        description="Hard-coded 3-sentence ISL demo renderer (sentence -> ISL gloss + bracketed emotion)."
    )
    parser.add_argument(
        "--sentence", required=True,
        help='Demo sentence ending in an emotion, e.g. "You are drinking tea tomorrow. (Happy)".',
    )
    parser.add_argument(
        "--seconds-per-word", type=float, default=SECONDS_PER_WORD,
        help=f"Duration of each sign (default {SECONDS_PER_WORD}).",
    )
    parser.add_argument(
        "--output", default=os.path.join(PROJECT_ROOT, "output_signs.mp4"),
        help="Output mp4 path (default sentence_avatar/output_signs.mp4).",
    )
    args = parser.parse_args()

    render_video(args.sentence, args.output, args.seconds_per_word)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    sys.exit(main())
