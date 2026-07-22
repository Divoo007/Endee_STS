# TODAY sign — v1 snapshot (2026-07-21)

Snapshot of the TODAY sign BEFORE the "wrist twist + arm extended diagonally"
experiment, saved so we can revert if that direction doesn't work out.

This v1 is the version the user approved for HEIGHT/position and wrist look:

- Handshape: ONE (index extended, thumb closed about BACK).
- Wrist: a single world `FORWARD 90` roll that turns the index to point straight
  DOWN (an earlier "solved palmar-flexion" wrist read worse and was reverted; this
  FORWARD-90 version is the kept one).
- Arm: forearm ~horizontal across the chest, hand centred + forward. Bob driven by
  the upper-arm RIGHT angle (more negative = higher): high -30 (hand y~1.38) <->
  low -13 (hand y~1.28), ~10 cm, RAISED into the mid/upper-chest region.
- Motion: rise -> tap DOWN -> up -> tap DOWN -> settle. Index points straight down
  through the whole bob.

To restore: copy this `sign_words.py`'s TODAY block back (the `_TODAY_WRIST`,
`_today_key`, `TODAY_SIGN` definitions), re-run `export_word_signs.py`, and re-export
the Web build.
