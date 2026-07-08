# sentence_avatar

Given 1-2 fixed sentences and 2-3 emotions, renders a video of a 3D VRM
avatar performing each sentence under each emotion — real facial
expressions (joy/angry/sorrow), articulated fingers, and a body-language
pose, all with continuous small motion so nothing sits frozen — held for a
few seconds per segment, with the sentence and emotion shown as an
on-screen caption. No speech synthesis or lip-sync; the sentence is shown
as text, not spoken.

This is a separate system from `../isl_avatar/` (the 2D sign-language
prototype) — different goal (general emotional performance, not formal
sign language) and different tech (a real 3D VRM humanoid in Godot instead
of a hand-drawn 2D rig).

## Usage

```bash
python3 render.py --sentence "I am having tea." --emotions happy angry surprised
python3 render.py --sentence "I'm so glad you came." --sentence "Get out of my house." \
    --emotions surprised angry relaxed
```

- 1 or 2 `--sentence` flags.
- 2 or 3 `--emotions`, from: `happy sad angry surprised relaxed`.
- Segments play back to back into one `output.mp4`: `emotions[i]` performs
  `sentences[i % len(sentences)]` (round-robin), so with 2 sentences and 3
  emotions the first sentence gets acted twice, under the 1st and 3rd
  emotions.

Requires [Godot 4](https://godotengine.org/) (`brew install --cask godot`)
and `ffmpeg` on `PATH`.

## How it works

- `godot/` is a Godot 4 project. `assets/avatars/vipe_hero.vrm` is imported
  via the vendored `godot-vrm` addon into a humanoid `Skeleton3D` + mesh
  with viseme/blink/mood blend shapes and per-finger bones.
- `scripts/Director.gd` reads a JSON config (sentences, emotions, segment
  duration) passed as a Godot CLI user arg, and for each segment:
  - sets the mesh's blend shape weights for that emotion's facial preset
    (`FACE_PRESETS`),
  - eases the skeleton's arm/spine/head bones into that emotion's held
    body pose (`BODY_PRESETS`),
  - curls the fingers into that emotion's held hand shape
    (`FINGER_CURL_PRESETS`), computed relative to the hand's *actual*
    current orientation (see below) so the curl looks right regardless of
    how the arm is posed,
  - layers a continuous small wrist-wiggle + finger-fidget oscillation on
    top of the held pose every frame, so the hands are always visibly
    moving rather than frozen,
  - updates the caption `Label`s.
- `render.py` writes that config to a temp file, shells out to
  `godot --write-movie ... -- --config ...` to render frames deterministically,
  then re-encodes the resulting `.avi` to `output.mp4` with `ffmpeg`.

### Shared rigging: `scripts/{arm_rig,hand_rig,face_expressions}.gd`

Both `Director.gd` (emotion demo) and `SignDirector.gd` (sign-language demo)
pose the skeleton through the same three small utility scripts rather than
each rolling its own bone math:

- **`arm_rig.gd`** -- spine/shoulder/arm/head. Each bone's target is a
  rotation in GLOBAL/world space (`Vector3.FORWARD`/`RIGHT`/`UP`), applied
  on top of where that bone's rest orientation *actually* ends up given its
  parent's current pose -- not the bone's own independent bind-pose rest.
- **`hand_rig.gd`** -- fingers and wrist wiggle. Each bone's target is a
  rotation LOCAL to its own rest frame, composed against its parent's
  actual current orientation. Fingers use a local axis (not global) because
  every finger bone shares a consistent rest convention, so "curl toward
  the palm" means the same local axis regardless of which way the hand is
  currently rotated.
- **`face_expressions.gd`** -- blend-shape mapping, no bones involved.

The distinction between the first two mattered more than it looks: an
earlier version composed *arm* deltas the same local-frame way `hand_rig.gd`
correctly uses for fingers. That fixed the immediate symptom it was chasing
(fingers curling the wrong way once the wrist had rotated) but, when
applied to the arm chain, silently changed what the axis constants meant --
a local axis is whatever direction that specific bone's own idiosyncratic
rest orientation happens to point, not world space. Fingers get away with a
fixed local axis because every finger bone shares a consistent rest
convention; shoulder/upper-arm/lower-arm don't, so the same `FORWARD` that
reliably raised an arm in isolation would swing a different bone sideways
once actually chained with its (also posed) parent. Symptom at the time:
poses that only posed one arm joint looked fine; poses raising the whole
arm read as one rigid stick with no visible elbow, or swung the hand behind
the body instead of down at the side. Fixed by keeping the delta in GLOBAL
space (matching what was actually verified per-bone by checking hand
position after rotating each candidate axis) while still composing against
the *actual* parent for correct chaining -- see the comment at the top of
`arm_rig.gd`.

Net effect of getting this right: raising the shoulder now visibly carries
the whole arm, and the elbow's own bend applies on top of wherever the
upper arm actually ended up, instead of each joint computing an independent
rotation from its own rest as if the other joints hadn't moved.

### Why not `--headless`?

Godot's `--headless` flag uses a dummy, GPU-less renderer that cannot
actually draw anything (confirmed by testing: it crashes on any real draw
call). Producing real video frames requires Godot's actual renderer
(Metal/Vulkan/GL), so `render.py` runs Godot normally — this briefly opens
a real (though tiny, off-focus) window during each render. That means this
only works on a machine with an active local display/GUI session, not on a
true remote/CI headless box without a virtual display.

## Sign-language prototype (one fixed sentence, for testing)

```bash
python3 render_signs.py --emotion happy
```

Separate from the emotion demo above. Takes only `--emotion` — the
sentence is hardcoded to `sign_words.SENTENCE`
(`"Are you going to drink tea tomorrow?"`) while this is still a one-
sentence proof of concept; it'll take arbitrary sentences once the
per-word sign data covers more than one sentence's vocabulary. The chosen
emotion's facial expression is held constant for the whole clip (same
`FaceExpressions` mapping as the emotion demo) while the avatar signs each
word of the sentence in turn, one hand-authored keyframed gesture per word,
captioned with the current word.

- `sign_words.py` is where the sign data actually lives — `SENTENCE`, and
  `WORD_SIGNS`, a dict of word -> list of keyframes (`{"t": 0-1, <bone
  name>: {"axis", "angle"}, "curl_left"/"curl_right": <handshape>}`), in the
  same spirit (and with the same "placeholder, not verified" caveat) as the
  old `isl_avatar/signs.py`. Unknown words raise an error before anything
  renders. To add a new sentence: add its words' keyframes to `WORD_SIGNS`
  and point `SENTENCE` at it (or, once this expands past one sentence,
  pass sentences in directly).
- `<handshape>` is either a single 0.0-1.0 number (every finger curls the
  same amount) or a per-finger dict `{"Thumb": 0-1, "Index": 0-1, "Middle":
  0-1, "Ring": 0-1, "Little": 0-1}` so a word's handshape can actually look
  like the thing it's signing instead of just a generic open-hand-to-fist
  slider -- e.g. "you" points (`"Index": 0.0` straight, everything else
  curled), "drink" grips a cup (thumb held apart from four curled fingers),
  "tea" pinches (thumb + index together, the rest tucked away), "tomorrow"
  is a thumbs-up-shaped fist (`"Thumb": 0.0`, everything else curled). Arm
  position (which bone rotates how far) and handshape (which fingers curl
  how far) are independent knobs — editing one never touches the other.
- `scripts/hand_rig.gd`'s `apply_fingers()` is what makes per-finger
  handshapes possible: `apply()` (what the emotion demo uses, unchanged)
  is now a thin wrapper that just builds a uniform-curl dict and calls
  `apply_fingers()`.
- `scripts/SignDirector.gd` reads the resolved per-word keyframes from the
  config, samples each word's keyframe list every frame (linear walk +
  slerp between the two surrounding keyframes, same interpolation shape as
  `isl_avatar/main.py`'s old `interpolate()`), and applies the result via
  the same bone/finger posing machinery as `Director.gd`.
- Runs in the same Godot project. `SignMain.tscn` is the project's default
  scene (see the web app below); `render.py` (the emotion demo) explicitly
  passes `res://scenes/Main.tscn` on the `godot` CLI invocation so it isn't
  affected by that default. Writes to `output_signs.mp4` by default
  (separate from the emotion demo's `output.mp4`).

## Web app (live, in the browser)

```bash
./serve_web.sh          # exports the Web build, serves it at :8765
open http://localhost:8765/index.html
```

The same sign-language flow as `render_signs.py` above, but interactive
and running live in the browser via Godot's Web (WebAssembly) export
instead of rendering a video: type any sentence, pick an emotion, hit
**Perform**, and the avatar signs it in real time. Submitting again while
one is still playing cancels it and starts the new one. Unsupported words
(anything outside `sign_words.WORD_SIGNS`) show an error under the form
instead of crashing.

Requires the Godot Web export templates
(`brew install --cask godot` doesn't include these — see
[Export templates](#export-templates-one-time-setup) below).

### How the web app differs from the CLI path

`scripts/SignDirector.gd` has two entry points into the *same* `_perform()`
animation code (see the file's top comment):

- **CLI/video** (`render_signs.py`): reads `--config <path>` (a JSON file
  with words + resolved keyframes), plays once, quits — used for
  `--write-movie` rendering.
- **Web**: a page can't pass CLI args, so instead `_ready()` detects
  `OS.has_feature("web")` and calls `_setup_web_bridge()`, which registers
  a JS-callable `window.godotPerform(sentence, emotion)` via
  `JavaScriptBridge.create_callback`. The browser calls that on every
  "Perform" click with live, user-typed text; `perform_web()` tokenizes it
  in GDScript and looks words up in `res://data/word_signs.json` — a
  static snapshot of `sign_words.WORD_SIGNS` (see `export_word_signs.py`;
  `serve_web.sh` regenerates it before every export) bundled into the
  build, since there's no `--config` file to read in a browser. It doesn't
  quit when done, so the page stays alive for the next submission.

None of the animation/posing/expression code differs between the two paths
— only how (sentence, emotion, words, keyframes) arrive.

**A sharp edge that cost real debugging time**: `JavaScriptBridge.create_callback()`'s
return value is refcounted. Storing it in a local variable inside the
setup function let it get garbage-collected the moment that function
returned — `window.godotPerform` was still a function (assignment
"worked"), but calling it from JS silently did nothing, no error either
side. Fixed by keeping the callback alive in an instance variable
(`_js_perform_callback`) for the life of the scene.

**Another one**: Godot's Web loader sets the canvas to `position: absolute;
top: 0` at runtime (not visible in the static HTML/CSS), so it renders
*underneath* whatever's injected via `head_include`, regardless of DOM
order. The sentence/emotion captions (bottom of frame) were unaffected,
but the word caption (anchored near the top of the 3D scene) was rendering
directly behind the form — present, just invisible. Fixed with a small
script in `head_include` that measures the form's actual rendered height
and repositions the canvas below it (`html/head_include` in
`export_presets.cfg`).

### Export templates (one-time setup)

The Web export needs platform export templates matching the installed
Godot version, which `brew install --cask godot` does not include:

```bash
# Download the .tpz matching your Godot version from
# https://github.com/godotengine/godot/releases (~1.3GB, all platforms bundled),
# then extract just the web_*.zip files + version.txt into:
#   ~/Library/Application Support/Godot/export_templates/<version>/
```

`export_presets.cfg` (checked in) configures the "Web" preset:
`variant/thread_support=false` so it runs behind a plain static file
server (no COOP/COEP headers needed for `SharedArrayBuffer`), and
`html/head_include` carries the injected sentence/emotion form + the
canvas-layout fix above.

## Avatar: VIPE Hero (CC-BY, attribution required)

The default avatar ships real VRM "mood" blend shapes (`joy`/`angry`/
`sorrow`/`fun`, used directly for `happy`/`angry`/`sad`) and a proper
VRoid-style hand mesh with separated finger geometry — both required for
the expression and finger articulation above to actually be visible.

An earlier default (the CC0 `100Avatars` series) turned out to have no
mood blend shapes at all (checked across the whole series, not just one
avatar) and a low-poly "mitten" hand mesh with no separate fingers — no
amount of bone animation could make individual fingers show up on that
mesh. See `assets/avatars/SOURCE.md` for the full writeup and swap
instructions, and for this avatar's required attribution text.

## Known limitations

- No lip-sync or speech audio; the sentence is a caption only.
- "surprised" has no dedicated mood blend shape on this avatar, so it's
  approximated with a wide-open mouth shape + open eyes instead of a real
  expression preset.
- Poses are a fixed held stance per segment (arms/torso/head), with a
  continuous idle wiggle layered on the hands/fingers — not a full
  hand-authored animation curve for the whole body.
- The sign-language prototype's gestures are placeholders, not verified
  against any real sign language (same caveat the old `isl_avatar`
  prototype carried) — they exist to prove out the per-word keyframe
  pipeline, not to teach anyone an actual sign.
