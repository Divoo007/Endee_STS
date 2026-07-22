# sorry — v1 snapshot (2026-07-20)

First working version of the SORRY sign, before the "bigger + smoother circle,
proper visible-thumb fist" rework. Kept so that rework can be reverted.

v1 characteristics:
- FIST_TIGHT handshape (thumb fully tucked at 1.1/BACK — the thumb "disappears").
- 4-keyframe-per-loop rub circle (linear interpolation => the path is a square,
  so the motion visibly "breaks" at each corner).
- radius ~3 cm.

To revert the sign only: restore `SORRY_SIGN` / `_sorry_key` / `_SORRY_*` from this
copy of sign_words.py, then re-run `export_word_signs.py` and re-export the Web build.
