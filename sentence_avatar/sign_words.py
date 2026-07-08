"""
Per-word hand-sign keyframe data for one fixed test sentence.

*** ISL-INSPIRED SIGNS - APPROXIMATE, NOT VIDEO-VERIFIED ***
The content-word signs below (you/going/drink/tea/tomorrow) are modelled on
documented Indian Sign Language (ISL) descriptions -- the iconic form of
each sign (where the hand goes, its shape, and how it moves), not a
generic open-to-fist wiggle:
  - you      : index finger points at the addressee, arm extended forward.
  - drink    : cupped "C" hand (as if holding a glass) raised to the mouth
               and tilted, head tips back slightly.
  - tea      : two hands -- the non-dominant hand cups an imaginary glass/
               cup at chest height while the dominant index finger stirs
               above it in small circles.
  - tomorrow : index finger extended, the forearm/wrist rolls forward in an
               arc (the "moving forward in time" future gesture).
  - going    : flat hand pushes forward/away from the body.
These were reconstructed from *textual* ISL references and cross-checked
against the requester's own description; they were NOT verified frame-by-
frame against ISL video (the authoritative portal indiansignlanguage.org
is behind a bot wall here, and video can't be watched in this environment),
so treat them as a faithful-as-possible approximation, not a teaching-grade
reference. The function words "are"/"to" are kept as light, non-committal
lifts -- ISL grammar generally drops the copula and infinitive marker
rather than signing them. Refining any sign is a data edit to the keyframes
below, not a code change.

Keyframe format: each word maps to a list of keyframes, each a dict with
"t" (0.0-1.0, fraction of that word's on-screen duration) plus any of the
POSE_BONES (below) mapped to {"axis": "RIGHT"|"UP"|"FORWARD", "angle": deg}
-- a GLOBAL-space rotation applied on top of that bone's actual (parent-
relative) rest orientation, same convention as sentence_avatar's emotion
BODY_PRESETS/ArmRig -- and/or "curl_left"/"curl_right" giving that hand's
shape: either a single 0.0-1.0 number (every finger curls the same amount,
0.0 open hand - 1.0 full fist) or a per-finger dict
{"Thumb": 0-1, "Index": 0-1, "Middle": 0-1, "Ring": 0-1, "Little": 0-1} so a
handshape can differ per finger -- e.g. "Index": 0.0 with the rest near 1.0
for a pointing hand, or "Thumb": 0.0 with the rest near 1.0 for a
thumbs-up-shaped fist. A finger missing from a per-finger dict defaults to
0.0 (open). Bones/curls not mentioned in a keyframe default to
NEUTRAL_POSE's value. Keyframes must be sorted by "t" and should start and
end at NEUTRAL_POSE so words blend cleanly into each other.

*** curl_left/curl_right affect ONLY finger curl: elbow, wrist and every
other arm/torso/head bone are driven purely by the axis/angle fields above
and are untouched by curl_left/curl_right. ***

A keyframe may also set "RightWrist"/"LeftWrist" -- {"axis": ..., "angle":
deg} in the same GLOBAL-space convention as the POSE_BONES above -- to
rotate just the wrist, independent of the elbow/shoulder angles that
position the hand. This is a separate, opt-in knob (most words never set
it and get no wrist rotation at all, exactly as before it existed): curling
fingers can only close them toward the palm, it can never change which way
the palm/fingers are actually AIMED, so re-aiming a handshape (e.g. so
"you"'s pointing finger reaches toward the camera instead of wherever the
raised forearm happens to leave it) needs this instead of a curl tweak.

UpperArm/LowerArm angle guide (right arm; mirror the sign for left):
NEUTRAL is arms hanging at the sides. A positive UpperArm angle raises the
arm; LowerArm's angle is *additional* rotation on top of wherever UpperArm
actually ended up (see ArmRig), continuing the same rotational sense, so a
small UpperArm (~10-30) plus a larger LowerArm (~30-70) bends the elbow to
bring the hand up to chest/face height while keeping the upper arm mostly
at the side -- overshooting either number is what previously put hands
implausibly high (near/above the head) or hid them behind the body.
"""

POSE_BONES = [
    "Spine", "Chest", "LeftShoulder", "RightShoulder",
    "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "Head",
]

# Comfortable standing pose (arms hanging naturally at the sides) that
# every word's keyframes are expressed relative to, and that the avatar
# returns to between words. Same numbers as sentence_avatar's "relaxed"
# emotion (Director.gd BODY_PRESETS).
NEUTRAL_POSE = {
    "RightUpperArm": {"axis": "FORWARD", "angle": -70},
    "LeftUpperArm": {"axis": "FORWARD", "angle": 70},
    "RightLowerArm": {"axis": "FORWARD", "angle": -15},
    "LeftLowerArm": {"axis": "FORWARD", "angle": 15},
    "Head": {"axis": "RIGHT", "angle": 3},
    "curl_left": 0.2,
    "curl_right": 0.2,
}

SENTENCE = "Are you going to drink tea tomorrow?"

# Reusable handshapes (per-finger curl dicts, 0=straight .. 1=fully curled).
POINT = {"Thumb": 0.75, "Index": 0.0, "Middle": 0.9, "Ring": 0.9, "Little": 0.9}   # index out, rest fisted
FLAT = {"Thumb": 0.1, "Index": 0.05, "Middle": 0.05, "Ring": 0.05, "Little": 0.05}  # open flat hand
CUP_C = {"Thumb": 0.35, "Index": 0.5, "Middle": 0.5, "Ring": 0.5, "Little": 0.5}    # curved "C", holding a glass
OPEN = {"Thumb": 0.1, "Index": 0.1, "Middle": 0.1, "Ring": 0.1, "Little": 0.1}      # relaxed open hand

WORD_SIGNS = {
    # Auxiliary verb -- ISL generally drops the copula, so this is kept as a
    # light, non-committal two-hand "question" lift (open palms rise a
    # little and settle) rather than a specific lexical sign.
    "are": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 15},
            "LeftUpperArm": {"axis": "FORWARD", "angle": -15},
            "RightLowerArm": {"axis": "FORWARD", "angle": 40},
            "LeftLowerArm": {"axis": "FORWARD", "angle": -40},
            "curl_left": OPEN, "curl_right": OPEN},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # ISL "you": index finger points at the addressee with the arm carried
    # OUT IN FRONT of the body toward them (here, toward the camera/viewer),
    # not raised out to the side. The upper arm rotates about the vertical
    # (UP) axis to swing the whole arm forward into the space between signer
    # and viewer (reach ~+0.29 in Z, chest height); a small wrist turn aims
    # the extended index at the lens. Bringing the arm genuinely forward
    # (rather than the earlier side-raise + wrist-only turn) is the "arm out
    # front" the requester asked for.
    "you": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "UP", "angle": 52},
            "RightLowerArm": {"axis": "FORWARD", "angle": 32},
            "RightWrist": {"axis": "UP", "angle": 20},
            "curl_right": POINT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # ISL "going": flat hand pushes forward and away from the body in the
    # direction of travel -- starts up near the chest, then extends out into
    # the forward space, fingers held flat and together the whole time.
    "going": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.35, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 15},
            "RightLowerArm": {"axis": "FORWARD", "angle": 55},
            "curl_right": FLAT},
        {"t": 0.7, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "UP", "angle": 45},
            "RightLowerArm": {"axis": "FORWARD", "angle": 40},
            "curl_right": FLAT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Infinitive marker -- like "are", ISL doesn't lexicalise "to"; kept as a
    # brief, low-amplitude single-hand lift so the word still gets a beat.
    "to": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 12},
            "RightLowerArm": {"axis": "FORWARD", "angle": 32},
            "curl_right": OPEN},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # ISL "drink": a cupped "C" hand (as if holding a glass) is raised to the
    # mouth and tilted up while the head tips slightly back -- miming taking
    # a drink. The forearm swings up-and-across (LowerArm about the vertical
    # axis) to bring the hand to mouth height (~1.34) near centre-front; the
    # wrist tilts the "glass" toward the lips at the peak.
    "drink": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.3, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 18},
            "RightLowerArm": {"axis": "UP", "angle": 105},
            "curl_right": CUP_C},
        {"t": 0.6, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 22},
            "RightLowerArm": {"axis": "UP", "angle": 122},
            "RightWrist": {"axis": "RIGHT", "angle": -45},
            "Head": {"axis": "RIGHT", "angle": -18},
            "curl_right": CUP_C},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # ISL "tea": two-handed -- the non-dominant (left) hand cups an imaginary
    # glass at upper-chest height while the dominant (right) index finger
    # stirs above it in small circles. The stir is animated by rocking the
    # right forearm (LowerArm about the vertical axis) and turning the wrist
    # between keyframes; the left cup is held in place across the sign. Both
    # hands sit low at chest level (not up at the face) so it reads as
    # "stirring a cup", deliberately distinct from "drink" (one hand, to the
    # mouth). Placements come from the reach probe (left ~chest-centre-front,
    # right just beside/above it).
    "tea": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.2, **NEUTRAL_POSE,
            "LeftUpperArm": {"axis": "FORWARD", "angle": -12},
            "LeftLowerArm": {"axis": "UP", "angle": -135},
            "curl_left": CUP_C,
            "RightUpperArm": {"axis": "FORWARD", "angle": 10},
            "RightLowerArm": {"axis": "UP", "angle": 140},
            "RightWrist": {"axis": "RIGHT", "angle": -20},
            "curl_right": POINT},
        {"t": 0.45, **NEUTRAL_POSE,
            "LeftUpperArm": {"axis": "FORWARD", "angle": -12},
            "LeftLowerArm": {"axis": "UP", "angle": -135},
            "curl_left": CUP_C,
            "RightUpperArm": {"axis": "FORWARD", "angle": 12},
            "RightLowerArm": {"axis": "UP", "angle": 155},
            "RightWrist": {"axis": "RIGHT", "angle": 12},
            "curl_right": POINT},
        {"t": 0.7, **NEUTRAL_POSE,
            "LeftUpperArm": {"axis": "FORWARD", "angle": -12},
            "LeftLowerArm": {"axis": "UP", "angle": -135},
            "curl_left": CUP_C,
            "RightUpperArm": {"axis": "FORWARD", "angle": 10},
            "RightLowerArm": {"axis": "UP", "angle": 138},
            "RightWrist": {"axis": "RIGHT", "angle": -20},
            "curl_right": POINT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # ISL "tomorrow": index finger extended, the forearm/wrist rolls FORWARD
    # in an arc -- the "moving ahead in time / the day to come" future
    # gesture. The hand is held up near shoulder/head height and the wrist
    # pitches forward (about the sideways RIGHT axis) from tipped-back
    # through to tipped-forward across the sign, so the extended index
    # visibly rolls over rather than sitting still.
    "tomorrow": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.3, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 35},
            "RightLowerArm": {"axis": "UP", "angle": 100},
            "RightWrist": {"axis": "RIGHT", "angle": -45},
            "Head": {"axis": "RIGHT", "angle": -4},
            "curl_right": POINT},
        {"t": 0.6, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 36},
            "RightLowerArm": {"axis": "UP", "angle": 100},
            "RightWrist": {"axis": "RIGHT", "angle": 0},
            "curl_right": POINT},
        {"t": 0.85, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 38},
            "RightLowerArm": {"axis": "UP", "angle": 98},
            "RightWrist": {"axis": "RIGHT", "angle": 50},
            "curl_right": POINT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
}
