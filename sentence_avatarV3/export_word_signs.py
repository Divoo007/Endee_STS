"""
Regenerates godot/data/word_signs.json from sign_words.py's WORD_SIGNS.

sign_words.py stays the single source of truth for sign data (edited in
Python, same as the old isl_avatar/signs.py); this bundles it into a static
resource the Godot Web export can load at runtime, since a browser build
has no --config CLI arg to pass resolved keyframe data through. Run this
whenever WORD_SIGNS changes, before (re-)exporting the web build.

Usage:
    python3 export_word_signs.py
"""

import json
import os

from sign_words import WORD_SIGNS

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "godot", "data", "word_signs.json")


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(WORD_SIGNS, f)
    print(f"Wrote {OUTPUT_PATH} ({len(WORD_SIGNS)} words)")


if __name__ == "__main__":
    main()
