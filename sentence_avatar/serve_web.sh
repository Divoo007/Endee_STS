#!/bin/bash
# Builds the sign-language web app and serves it locally.
#
# Usage: ./serve_web.sh [port]
#
# Re-run export_word_signs.py first if you've edited sign_words.py -- the
# web build reads a bundled JSON snapshot, not sign_words.py directly.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8765}"

python3 export_word_signs.py

echo "Exporting Godot Web build..."
godot --headless --path godot --export-release "Web" ../web_build/index.html

echo "Serving web_build/ at http://localhost:${PORT}/index.html"
cd web_build
python3 -m http.server "$PORT"
