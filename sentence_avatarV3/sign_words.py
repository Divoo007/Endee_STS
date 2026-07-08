"""
Per-word hand-sign keyframe data for one fixed test sentence.

*** PLACEHOLDER SIGNS - NOT VERIFIED SIGN LANGUAGE ***
Same caveat as the old isl_avatar/signs.py: these were NOT derived from a
real sign-language reference (no way to watch/verify ASL/ISL/BSL videos
here). They're plausible-looking, distinct arm/hand motions per word, meant
to prove out the per-word keyframe pipeline end to end -- not to teach
anyone a real sign. Before using this for anything real, replace the
keyframes below with ones checked against an actual sign-language reference
for each word; the data format is a plain list of keyframes so that's a
data edit, not a rewrite.

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

*** This is the ONLY thing finger/handshape data affects: elbow, wrist and
every other arm/torso/head bone are driven purely by the axis/angle fields
above and are untouched by curl_left/curl_right. ***

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

WORD_SIGNS = {
    # Placeholder: both hands lift from the sides to about waist height and
    # back, open palms, a generic "questioning" gesture for the auxiliary
    # verb.
    "are": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 15},
            "LeftUpperArm": {"axis": "FORWARD", "angle": -15},
            "RightLowerArm": {"axis": "FORWARD", "angle": 40},
            "LeftLowerArm": {"axis": "FORWARD", "angle": -40},
            "curl_left": {"Thumb": 0.1, "Index": 0.1, "Middle": 0.1, "Ring": 0.1, "Little": 0.1},
            "curl_right": {"Thumb": 0.1, "Index": 0.1, "Middle": 0.1, "Ring": 0.1, "Little": 0.1}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: right arm extends up and out with a true pointing
    # handshape -- index finger straight, other fingers and thumb curled
    # into the palm -- a "pointing at you" gesture.
    "you": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.55, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 30},
            "RightLowerArm": {"axis": "FORWARD", "angle": -10},
            "curl_right": {"Thumb": 0.75, "Index": 0.0, "Middle": 0.85, "Ring": 0.85, "Little": 0.85}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: right hand sweeps from near the body outward, fingers
    # held flat and together (an open "presenting a direction" hand).
    "going": [
        {"t": 0.0, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 12},
            "RightLowerArm": {"axis": "FORWARD", "angle": 45},
            "curl_right": {"Thumb": 0.2, "Index": 0.05, "Middle": 0.05, "Ring": 0.05, "Little": 0.05}},
        {"t": 0.6, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 35},
            "RightLowerArm": {"axis": "FORWARD", "angle": 5},
            "curl_right": {"Thumb": 0.15, "Index": 0.0, "Middle": 0.0, "Ring": 0.0, "Little": 0.0}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: brief, low-amplitude two-hand lift -- a short
    # transitional gesture for the function word.
    "to": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 10},
            "LeftUpperArm": {"axis": "FORWARD", "angle": -10},
            "RightLowerArm": {"axis": "FORWARD", "angle": 30},
            "LeftLowerArm": {"axis": "FORWARD", "angle": -30}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: right hand shaped as if gripping a cup -- thumb held
    # apart like a handle, the other four fingers wrapped around the
    # cup -- and rises toward the mouth, then returns.
    "drink": [
        {"t": 0.0, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 15},
            "RightLowerArm": {"axis": "FORWARD", "angle": 40},
            "curl_right": {"Thumb": 0.3, "Index": 0.65, "Middle": 0.65, "Ring": 0.65, "Little": 0.65}},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 20},
            "RightLowerArm": {"axis": "FORWARD", "angle": 70},
            "curl_right": {"Thumb": 0.35, "Index": 0.7, "Middle": 0.7, "Ring": 0.7, "Little": 0.7},
            "Head": {"axis": "RIGHT", "angle": -6}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: right hand at chest height with a small back-and-forth
    # wiggle (echoing the old isl_avatar prototype's "tea" stirring sign),
    # thumb and index pinched together as if holding a tea bag, other
    # fingers tucked out of the way.
    "tea": [
        {"t": 0.0, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 12},
            "RightLowerArm": {"axis": "FORWARD", "angle": 35},
            "curl_right": {"Thumb": 0.55, "Index": 0.55, "Middle": 0.8, "Ring": 0.8, "Little": 0.8}},
        {"t": 0.33, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 16},
            "RightLowerArm": {"axis": "FORWARD", "angle": 42},
            "curl_right": {"Thumb": 0.55, "Index": 0.55, "Middle": 0.8, "Ring": 0.8, "Little": 0.8}},
        {"t": 0.66, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 10},
            "RightLowerArm": {"axis": "FORWARD", "angle": 30},
            "curl_right": {"Thumb": 0.55, "Index": 0.55, "Middle": 0.8, "Ring": 0.8, "Little": 0.8}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Placeholder: right forearm arcs up from near the body in a
    # thumbs-up-shaped fist (thumb extended, other fingers curled),
    # loosely echoing ASL's real "tomorrow" (a forward arc from the cheek).
    "tomorrow": [
        {"t": 0.0, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 20},
            "RightLowerArm": {"axis": "FORWARD", "angle": 55},
            "curl_right": {"Thumb": 0.0, "Index": 0.95, "Middle": 0.95, "Ring": 0.95, "Little": 0.95},
            "Head": {"axis": "RIGHT", "angle": -4}},
        {"t": 0.6, **NEUTRAL_POSE,
            "RightUpperArm": {"axis": "FORWARD", "angle": 30},
            "RightLowerArm": {"axis": "FORWARD", "angle": 20},
            "curl_right": {"Thumb": 0.0, "Index": 0.9, "Middle": 0.9, "Ring": 0.9, "Little": 0.9}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
}
