# Avatar provenance — realistic signer

- **Name**: Male_Adult_04 (a `_facial` variant, with ARKit/FACS facial blendshapes)
- **Collection**: Microsoft Rocketbox (115 rigged realistic human avatars)
- **Source**: https://github.com/microsoft/Microsoft-Rocketbox  (Assets/Avatars/Adults/Male_Adult_04)
- **License**: **MIT** — free for any use, incl. commercial, no attribution required.
- **Format**: FBX (3ds-Max Biped skeleton "Bip01 ...") + .tga PBR textures, imported
  natively by Godot (ufbx). NOT a VRM.

## How it's driven (see scripts/SignDirector.gd `_adapt_skeleton`)

The mesh skin binds to bones BY NAME, so we do NOT rename the Biped bones.
Instead the rigs (arm_rig/hand_rig) take a VRM->Biped **name map** and translate
at lookup, so all the sign logic runs unchanged. The Biped orients bones
differently from the old VRM, so every sign pose was re-derived on this rig
(sign_words.py); the previous stylized-avatar values are kept in
sign_words_vrm_backup.py. Finger curl uses the BACK local axis here (fingers
curl toward the palm about BACK, the thumb tucks across the palm about UP —
found by rendering all 6 candidate axes side by side; FORWARD only splays
the fingers straight, it does not close them).
Emotions use the avatar's ARKit + FACS blendshapes (face_expressions.gd),
which finally make a faithful single raised eyebrow (Question) possible.
