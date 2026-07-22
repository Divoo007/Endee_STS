# I / ME — v1 snapshot (2026-07-21)

Working version of the I/ME sign, before a small tuning pass (slightly less wrist
bend + finger angled slightly downward). Kept so that tuning can be reverted.

v1 characteristics:
- Arm: `RightUpperArm` [RIGHT -12, UP 66], `RightLowerArm` [RIGHT -58, UP 44] --
  hand held ~12cm in front of the chest, index pointing back to touch it.
- Wrist (`_ME_WRIST`): a full-orientation delta, axis (0.4608, 0.8836, 0.0832),
  angle 115.55 deg -- pins the index aim (unchanged since the very first working
  pass) AND pins the palm normal to world -X, the character's own right side
  (this took two corrections to land: world-DOWN was rejected as an unnatural
  bend, world+X was rejected as the wrong "right" -- screen-right instead of the
  character's own right).
- Index lightly extended (POINT handshape, curl 0.0), tip touching the chest
  ~2cm short of a perfectly firm contact (a small floating gap, noted but not
  yet chased further since curling/re-folding both made it worse, not better).
- Tap: a small upper-arm-only up-bob (RIGHT -12 -> -18) that lifts the fingertip
  ~3.5cm without moving the elbow (reads as a fingertip tap, not an arm pump).

To revert the sign only: restore `_ME_WRIST` / `_ME_TOUCH` / `_ME_LIFT` / `ME_SIGN`
from this copy of sign_words.py, then re-run `export_word_signs.py` and re-export
the Web build.
