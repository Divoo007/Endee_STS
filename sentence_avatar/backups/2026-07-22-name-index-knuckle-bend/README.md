# NAME sign — index bent from the KNUCKLE (MCP / base), 2026-07-22

Snapshot of the working NAME sign BEFORE switching the index bend from the base
knuckle (MCP, `_base_bend`) to the PIP joint.

This version's NAME_HAND (see sign_words.py):
  NAME_HAND = {"Thumb": 0.5, "Index": 0.8, "Middle": 1.0, "Ring": 1.0, "Little": 1.0,
               "_base_bend": ["Index"], "_thumb_axis": [0.61, -0.42, 0.14]}
- Palm-forward hand, index base-bent ~76deg at the MCP (points forward at viewer),
  thumb a natural distributed curl pointing forward, three fisted, dragged L->R.

To revert: restore this sign_words.py (or just the NAME_HAND + NAME_SIGN blocks),
re-run export_word_signs.py, and re-export the Web build. The rig still supports
`_base_bend`, so no .gd revert is needed.
