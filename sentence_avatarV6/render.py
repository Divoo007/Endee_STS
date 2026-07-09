"""
Given 1-2 fixed sentences and 2-3 emotions, render a video of a VRM avatar
(loaded in Godot) performing each sentence under each emotion: facial
expression (viseme/blink blend shapes) + a hand-authored body-language pose,
held for a fixed duration per segment, with the sentence + emotion shown as
an on-screen caption. Segments are paired round-robin: emotions[i] performs
sentences[i % len(sentences)], played back to back into one output video.

Usage:
    python3 render.py --sentence "The tea is ready." --emotions happy sad angry
    python3 render.py --sentence "I'm so glad you came." --sentence "Get out." \\
        --emotions surprised angry relaxed

Requires Godot on PATH (`brew install --cask godot`) and ffmpeg. Rendering
uses Godot's real renderer (not --headless, which has no GPU backend and
cannot produce frames) via `--write-movie`, so a Godot window briefly opens
during render -- this only works on a machine with an active display
session, not a true remote/CI headless box.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

EMOTIONS = ["happy", "sad", "angry", "surprised", "relaxed"]
FPS = 60
SECONDS_PER_SEGMENT = 3.5
QUIT_AFTER_BUFFER_SECONDS = 1.5  # safety margin on top of Director.gd's own quit()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GODOT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "godot")


def render_video(sentences, emotions, output_path, seconds_per_segment=SECONDS_PER_SEGMENT):
    if not (1 <= len(sentences) <= 2):
        raise ValueError(f"Expected 1-2 sentences, got {len(sentences)}: {sentences}")
    if not (2 <= len(emotions) <= 3):
        raise ValueError(f"Expected 2-3 emotions, got {len(emotions)}: {emotions}")
    unknown = [e for e in emotions if e not in EMOTIONS]
    if unknown:
        raise ValueError(f"Unknown emotion(s) {unknown}. Supported: {EMOTIONS}")
    if shutil.which("godot") is None:
        raise RuntimeError("godot not found on PATH (brew install --cask godot)")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH")

    config = {
        "sentences": sentences,
        "emotions": emotions,
        "seconds_per_segment": seconds_per_segment,
    }
    total_seconds = len(emotions) * seconds_per_segment + QUIT_AFTER_BUFFER_SECONDS
    quit_after_frames = int(total_seconds * FPS)

    tmp_dir = tempfile.mkdtemp(prefix="sentence_avatar_")
    try:
        config_path = os.path.join(tmp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)

        avi_path = os.path.join(tmp_dir, "render.avi")
        cmd = [
            "godot", "--path", GODOT_PROJECT_DIR,
            "res://scenes/Main.tscn",  # explicit: project's default scene is the sign-language web app
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
        description="Sentence + emotion -> VRM avatar video (Godot)"
    )
    parser.add_argument(
        "--sentence", action="append", dest="sentences", required=True,
        help="Sentence to perform. Pass 1 or 2 times.",
    )
    parser.add_argument(
        "--emotions", nargs="+", required=True, choices=EMOTIONS,
        help="2 or 3 emotions, in playback order.",
    )
    parser.add_argument(
        "--seconds-per-segment", type=float, default=SECONDS_PER_SEGMENT,
        help=f"Duration of each emotion segment (default {SECONDS_PER_SEGMENT}).",
    )
    parser.add_argument(
        "--output", default=os.path.join(PROJECT_ROOT, "output.mp4"),
        help="Output mp4 path (default sentence_avatar/output.mp4).",
    )
    args = parser.parse_args()

    render_video(args.sentences, args.emotions, args.output, args.seconds_per_segment)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    sys.exit(main())
