# Avatar provenance

- **Name**: VIPE Hero #1
- **Collection**: `vipe-heroes-genesis` ("VIPE Heroes Genesis" — Genesis PFP
  collection of the VIPE NFT Avatar Marketplace)
- **Source registry**: [opensourceavatars.com](https://opensourceavatars.com)
  (backed by [ToxSam/open-source-avatars](https://github.com/ToxSam/open-source-avatars))
- **Data record**: `https://raw.githubusercontent.com/ToxSam/open-source-avatars/main/data/avatars/vipe-heroes-genesis.json`
- **Direct download URL**: `https://dweb.link/ipfs/Qma1z2WUWv33JHb4gJTKChUWs3z9M2dnpiPWAHidmruu4z/default_1.vrm`
  (IPFS; `dweb.link` sometimes 404s transiently — `ipfs.io`, `cloudflare-ipfs.com`,
  or `gateway.pinata.cloud` serving the same `/ipfs/<hash>` path all work)
- **License**: CC-BY — **attribution required**. Credit "VIPE Heroes Genesis
  by VIPE NFT Avatar Marketplace" when this avatar (or renders made with it)
  is shared publicly.
- **Format**: VRM spec 0.0 (glTF-binary), imported into Godot via the
  `godot-vrm` addon.

## Why this avatar over the previous default ("Robert", 100Avatars series)

The first avatar tried (`100avatars-r1` collection, CC0) turned out to have:
- no VRM "mood" blend shapes (only visemes + blink) -- checked, and confirmed
  true across the whole `100Avatars` series, not just that one avatar.
- a low-poly "mitten" hand mesh with no separated finger geometry, so no
  amount of finger-bone animation could make individual fingers visible.

This avatar ships real `joy`/`angry`/`sorrow`/`fun` blend shapes (used
directly for facial expression -- see `FACE_PRESETS` in `Director.gd`) and
a proper VRoid-style hand mesh with visibly distinct fingers, so both
expression and finger articulation actually read on screen.

To swap in a different avatar: pick any `model_file_url` from that JSON (or
another collection listed in
`https://raw.githubusercontent.com/ToxSam/open-source-avatars/main/data/projects.json`),
download it, drop it in this folder, update the reference in
`scenes/Main.tscn`, and check its license/attribution requirements in
`projects.json` before using it publicly.
