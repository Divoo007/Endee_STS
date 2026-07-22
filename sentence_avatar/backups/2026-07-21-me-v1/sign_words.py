"""
Per-word ISL-gloss hand-sign keyframes, re-derived for the REALISTIC avatar
(Microsoft Rocketbox Male_Adult_04, a 3ds-Max Biped rig).

These were re-fitted from scratch on the Biped skeleton so the gestures LOOK
the same as the perfected stylized-avatar signs, even though the underlying
numbers differ (the Biped orients its bones differently, so the old angles do
not transfer -- see sign_words_vrm_backup.py for the original VRM values).

Format (same as before, plus one addition): each word -> list of keyframes,
each a dict with "t" (0-1 fraction of the word's duration) plus any of the
POSE_BONES mapped to a rotation, and/or "curl_left"/"curl_right" handshapes and
"RightWrist"/"LeftWrist" aims.

A bone's rotation is EITHER a single {"axis","angle"} (global-space, same
convention as ArmRig) OR a LIST of them composed in order -- the list form is
new, and is what lets a single bone both raise and swing inward (e.g. bringing
the hand to the mouth for "drink"). Bones/curls not named in a keyframe fall
back to NEUTRAL_POSE. Keyframes start and end at NEUTRAL_POSE so words blend.

Signs are selected/reordered per utterance by the speech/text -> LLM gloss
pipeline (see backend/); this module is just the per-word keyframe data (the
single source of truth), bundled to godot/data/word_signs.json by
export_word_signs.py for the web build. (are/going/to are non-lexical.)
"""

POSE_BONES = [
    "Spine", "Chest", "LeftShoulder", "RightShoulder",
    "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "Head",
]

# Relaxed standing pose (arms hanging at the sides), on the Biped rig. The arms
# rest at ~44 deg with STRAIGHT forearms so the hands settle at the outer thighs
# -- an earlier -50/-8 (arms lower + forearms angled in/forward) drew the hands
# together in front of the pelvis ("fig-leaf"). Keep the hands out at the sides.
# NOTE: SignDirector.BIPED_ARM_NEUTRAL must mirror these arm values -- it detects
# "this bone is at rest" by matching them (to swap in the VRM's deeper neutral).
NEUTRAL_POSE = {
    "RightUpperArm": {"axis": "FORWARD", "angle": -44},
    "LeftUpperArm": {"axis": "FORWARD", "angle": 44},
    "RightLowerArm": {"axis": "FORWARD", "angle": 0},
    "LeftLowerArm": {"axis": "FORWARD", "angle": 0},
    "Head": {"axis": "RIGHT", "angle": 0},
    "curl_left": 0.15,
    "curl_right": 0.15,
}

# Reusable handshapes (per-finger curl, 0=straight .. 1=fully curled).
POINT = {"Thumb": 0.6, "Index": 0.0, "Middle": 0.95, "Ring": 0.95, "Little": 0.95}
CUP = {"Thumb": 0.3, "Index": 0.5, "Middle": 0.5, "Ring": 0.5, "Little": 0.5}
STIR = {"Thumb": 0.6, "Index": 0.0, "Middle": 0.85, "Ring": 0.85, "Little": 0.85}
# Fist with the thumb EXTENDED (thumb curl 0 = straight); the four fingers close
# fully. Orientation of the thumb (up for GOOD, down for BAD) is set by the arm
# pose, not the curl. FLAT = open hand, fingers together (B-hand). FIST = closed.
THUMB_OUT = {"Thumb": 0.0, "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}
FIST = {"Thumb": 1.1, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}
FLAT = {"Thumb": 0.15, "Index": 0.0, "Middle": 0.0, "Ring": 0.0, "Little": 0.0}
# Grip a glass/bottle (DRINK): fingers wrap a cylinder, thumb closes over.
GRIP = {"Thumb": 0.55, "Index": 0.75, "Middle": 0.75, "Ring": 0.75, "Little": 0.75}
# Delicate pinch of thumb+index (TEA, holding a tiny cup); other fingers curled.
PINCH = {"Thumb": 0.55, "Index": 0.7, "Middle": 0.85, "Ring": 0.9, "Little": 0.9}
# Two fingers (index+middle) extended, spread; ring/little closed (NO "V").
TWO_OPEN = {"Thumb": 0.5, "Index": 0.0, "Middle": 0.0, "Ring": 1.0, "Little": 1.0}
TWO_SHUT = {"Thumb": 0.4, "Index": 0.75, "Middle": 0.75, "Ring": 1.0, "Little": 1.0}
# Fully closed fist, thumb folded across the PALM (YES). The thumb curls about a
# per-handshape axis of BACK, NOT the rig's global UP: about UP the thumb only ever
# sweeps around the DORSUM / radial side of the hand -- at NO value does it reach
# the palm, so it lies across the BACK of the hand and looks broken. BACK folds it
# the correct way, across the front of the curled fingers, into a real fist.
# "_thumb_axis" is read per handshape by SignDirector (the global UP still suits the
# pinch shapes -- tea's OK, please's PURSE -- which pull the thumb toward the index).
# ~1.1 lands the thumb across the palm; same treatment on every fist shape.
FIST_TIGHT = {"Thumb": 1.1, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}
# Little finger extended, everything else closed incl. thumb ("I"/pinky-out, BAD).
# Thumb folds across the palm about BACK, like FIST_TIGHT.
PINKY = {"Thumb": 1.1, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 0.0}
# "OK" ring: thumb + index curl to touch in a circle, the other three extended
# straight (TEA, held near the mouth).
OK = {"Thumb": 0.5, "Index": 0.6, "Middle": 0.0, "Ring": 0.0, "Little": 0.0}
# Purse / flower-bud: all five fingertips drawn together to a point (PLEASE).
PURSE = {"Thumb": 0.55, "Index": 0.62, "Middle": 0.62, "Ring": 0.62, "Little": 0.62}
# CONE / true flower-bud (PLEASE): the five fingers curve to a shared point but stay
# DISTINCT so it reads as a bunched pinch, not one raised finger. The balance that
# matters: (1) "_converge" is MODERATE (0.5) -- it fans the tips toward a point + opposes
# the thumb (a hand-rig capability plain curl lacks; see hand_rig.gd), but pushed hard
# (1.5) it over-adducts the ring+little BEHIND the middle so the hand collapses into a
# single column that looks like the middle finger. At 0.5 the fingers keep visible gaps.
# (2) LIGHT, GRADUATED curl -- fingers stay fairly extended (distinct digits, not a
# fist) with the longer ones curling a bit more (middle most ... little least) so the
# tips land level instead of the long middle towering. (3) the thumb curls about BACK
# to join from the front. Absent (off) on every other handshape, so nothing else
# changes. NOTE: the pinch only READS once the wrist also turns the open fan toward the
# camera (the UP -50 in please's RightWrist) -- shape and camera-facing go together.
CONE = {"Thumb": 0.4, "Index": 0.42, "Middle": 0.55, "Ring": 0.47, "Little": 0.35,
        "_thumb_axis": "BACK", "_converge": 0.5}
# Index only extended, others closed -- a clean pointing "1" (TEACHER's two crossed
# pointers), thumb CLOSED. The thumb folds across the palm (curl ~1.1 about BACK, the
# same axis the fists use) so it tucks out of the way; about the rig-default UP it juts
# out to the radial side like a stray extra digit (the "thumb about UP never tucks"
# trap -- see the curl-axis note in CLAUDE.md). (An earlier FORWARD tuck looked closed
# head-on but jutted from the shipped ~19deg-off camera; BACK is closed from every angle.)
ONE = {"Thumb": 1.1, "_thumb_axis": "BACK", "Index": 0.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}
# Natural closed fist (SORRY): four fingers fully closed, thumb TUCKED INTO the palm
# the way a real relaxed fist tucks it -- folded down/across the front of the fingers,
# with a portion of the thumb still visible on the radial side (not jammed fully out of
# sight). The thumb MUST curl about BACK, like the other fists: that is the anatomically
# correct fold direction (down toward the palm). About the rig-default UP the thumb
# instead sweeps up and HYPEREXTENDS its tip BACKWARD off the dorsum -- the "thumb bent
# the wrong way" bug (an earlier ~0.9-about-UP version did exactly that; don't revert).
# The curl amount is MODERATE (~0.7), NOT the full 1.1 that FIST_TIGHT uses: at 1.1 the
# thumb folds flat across the palm and, from the shipped ~19deg-off camera (which views
# the radial/thumb side), it tucks fully out of sight; at ~0.7 it stays tucked-but-
# -visible -- a sliver of thumb reads on the side exactly like a real fist. Verified
# ship + front in PoseLab.
FIST_A = {"Thumb": 0.7, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}

SENTENCE = "Hello teacher, you drink."

# NONE / NOTHING / EMPTY: two-handed CIRCULAR RUB ("wiping the hands clean ->
# nothing"), matching the ISLRTC reference (ISL_dictionary/None_Nothing_Empty.mp4).
# Both hands are COMPLETELY FLAT, LEVEL palms: the LEFT is held still, palm up, at
# centre chest as the base; the RIGHT flat palm (palm DOWN, back to the camera) RUBS a
# small CIRCLE just over it, the two palms kept a SLIGHT GAP apart so they read as
# rubbing but the fingers never touch. The trick is that BOTH hands are level/parallel
# (see the wrist pitches in _NONE_LEFT and _none_right) -- parallel flat plates keep a
# constant gap even held close, so no interpenetration anywhere in the circle.
# FOUR earlier tries were WRONG, don't revert: (a) right cupping down into the left so
# fingertips clipped; (b) an up/down linear wipe -- flat but KILLED the rotation; (c)
# hands held apart doing a stir beside the left (read as a shrug); (d) right plate
# raised high with its fingers still DROOPING down -- the drooped fingers stabbed the
# left even from a height. Fix = level the right hand fully, then close a slight gap.
_NONE_LEFT = {
    "LeftUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": -70}],
    "LeftLowerArm": [{"axis": "RIGHT", "angle": -45}],
    # [FORWARD 90, RIGHT 30]: FORWARD 90 rolls the palm UP, RIGHT 30 pitches the hand
    # flat/HORIZONTAL so it's a level palm-up plate. This is key to not-intersecting:
    # a plain FORWARD 90 left the fingers pointing UP (~y1.40) straight into the right
    # hand's circling path (they clipped); pitched flat, the left fingers point FORWARD
    # and level (~y1.27) so the right plate clears them.
    "LeftWrist": [{"axis": "FORWARD", "angle": 90}, {"axis": "RIGHT", "angle": 30}],
    # FLAT's default thumb (curl 0.15, default UP-axis fold) still stands proud out of
    # the palm plane in THIS wrist orientation -- straight up into the right hand's
    # circling path. A large NEGATIVE curl about the same UP axis (rather than a
    # different axis -- BACK/RIGHT/FORWARD all left it untouched, since the rest pose's
    # thumb-pointing direction is itself close to UP here) swings it back down flush
    # alongside the palm/fingers. Own dict, not a FLAT edit -- FLAT is shared by other
    # signs whose thumb orientation is fine as-is.
    "curl_left": {"Thumb": -1.6, "Index": 0.0, "Middle": 0.0, "Ring": 0.0, "Little": 0.0},
}
def _none_right(up, bend):
    # Right COMPLETELY-FLAT LEVEL plate held just over the left palm, tracing a small
    # circle -- the two flat palms RUB with only a slight gap. Two things make this read
    # right, both hard-won:
    #  * LEVEL FINGERS (no droop). The wrist pitch is RIGHT -58 (was -30). At -30 the
    #    right FINGERS drooped downward and stabbed into the left palm even with the wrist
    #    held high -- "the fingers are angled downwards a lot, they intersect at a great
    #    height." -58 levels the whole hand into a flat horizontal plate whose fingers
    #    point FORWARD, parallel to the left's, so nothing dips into the left.
    #  * SMALL GAP. Because the plate is now level & parallel to the (also level) left
    #    palm, the two never interpenetrate even held close -- so raise -34 keeps them a
    #    slight gap apart (palms "rubbing"), not the big -43 float that leveling would
    #    otherwise force. FORWARD 90 rolls the palm DOWN (back to camera).
    # The circle is walked by UP (yaw 77..91 -> left/right) + a SMALL bend swing
    # (-50..-58 -> tiny up/down); kept small so the gap stays slight all the way round.
    return {
        # raise -29 (lowered from -34): drops the right plate until the two palms
        # read as just TOUCHING at the circle's low point, while the level/parallel
        # plates still keep a hair of clearance so the fingers never intersect.
        "RightUpperArm": [{"axis": "RIGHT", "angle": -29}, {"axis": "UP", "angle": up}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": bend}],
        "RightWrist": [{"axis": "FORWARD", "angle": 90}, {"axis": "RIGHT", "angle": -58}],
        "curl_right": FLAT,
    }
# Circle quadrature points over the left palm: right / top / left / bottom. Bend swing
# kept tight (-50..-58) so the level plate keeps only a slight gap the whole way round.
_NONE_R = _none_right(91, -54)   # 3 o'clock
_NONE_T = _none_right(84, -58)   # 12 o'clock (highest -- a hair more gap)
_NONE_L = _none_right(77, -54)   # 9 o'clock
_NONE_B = _none_right(84, -50)   # 6 o'clock (lowest -- still a slight positive gap, no clip)
NONE_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.10, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_R},  # come together, start circle
    {"t": 0.20, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_T},
    {"t": 0.30, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_L},
    {"t": 0.40, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_B},
    {"t": 0.50, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_R},  # (circle 2)
    {"t": 0.60, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_T},
    {"t": 0.70, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_L},
    {"t": 0.80, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_B},
    {"t": 0.90, **NEUTRAL_POSE, **_NONE_LEFT, **_NONE_R},  # close loop, then retract
    {"t": 1.0, **NEUTRAL_POSE},
]

# SORRY: a closed fist rubbed in a small CIRCLE over the centre of the chest --
# the "hand over the heart" apology (fist, palm to the chest, circular rub).
# Authored from the standard ISL/ASL form (no ISLRTC reference video for SORRY was
# available), validated in-engine, NOT against a signed reference. Default face =
# SAD (remorseful) via the gloss layer (_WORD_DEFAULT_EMOTION); the sad emotion also
# droops the head and slows the timing (see SignDirector._emotion_head_delta /
# _speed_factor), so the geometry keeps the head NEUTRAL and lets the emotion layer
# carry the remorse -- baking a head bow here too would double it.
#
# The rub is a FRONTAL-PLANE circle traced at CONSTANT depth against the chest
# (Probe-solved, radius ~4 cm, centre hand ~(0.0, 1.35, 0.17)). Getting the fist LOW
# (mid-chest) AND CLOSE to the body needs a LOW elbow: the upper arm stays barely
# raised (elbow hangs low + out, a natural hand-on-heart pose) with a big forearm
# fold bringing the hand up to the chest. A RAISED elbow would force the hand either
# high-at-the-face or low-but-far-forward off the chest (the "low+close needs a low
# elbow" trap -- see DRINK/PLEASE). Each circle point moves only what it must, so the
# gap against the chest stays constant all the way round: upper-arm RIGHT walks the
# hand UP/DOWN (no depth change), upper-arm UP walks it LEFT/RIGHT (its depth coupling
# is cancelled by an opposing lower-arm UP), lower-arm fold held at RIGHT -99. Fist
# orientation is inherited from the forearm (NO wrist delta, like BAD) -- from the
# shipped ~19deg-off camera the back of the fist faces the viewer, with the thumb
# resting UP the radial side (see FIST_A) so the closed fist reads properly.
#
# SMOOTHNESS: the circle is walked as EIGHT points per loop, not four. With four
# points the LINEAR-per-segment interpolation (see SignDirector._sample_word) traces a
# SQUARE -- the hand changed direction hard at each of the four corners and the motion
# visibly "broke"/stopped. Eight points make an octagon that reads as a continuous
# circle. Two full loops are traced, entered at the BOTTOM (so the rise from the hip
# flows straight into the loop) going counter-clockwise. The sad emotion slows the
# whole word (~1.45x), so the rub reads as deliberate and heavy.
def _sorry_key(up_right, up_up, lo_up):
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": up_right}, {"axis": "UP", "angle": up_up}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -99}, {"axis": "UP", "angle": lo_up}],
        "curl_right": FIST_A,
    }
# Eight points around the rub circle, (up_right, up_up, lo_up) each, Probe-verified
# (radius ~4 cm, constant depth z~0.17). Ordered from the BOTTOM going CLOCKWISE from
# the viewer's perspective (bottom -> left -> top -> right), so the rise from the hip
# flows into the loop. (An earlier version ran counter-clockwise -- reversed per user.)
# hand (x,y) at each point noted for reference:
_SORRY_CIRCLE = [
    (11.5, 80.0, 57.0),   # bottom       (-0.020, 1.311)
    (8.7,  71.9, 64.1),   # bottom-left  (-0.042, 1.323)
    (2.0,  68.6, 67.1),   # left         (-0.043, 1.350)
    (-4.7, 71.9, 64.1),   # top-left     (-0.025, 1.377)
    (-7.5, 80.0, 57.0),   # top          ( 0.006, 1.390)
    (-4.7, 88.1, 49.9),   # top-right    ( 0.033, 1.378)
    (2.0,  91.4, 46.9),   # right        ( 0.037, 1.349)
    (8.7,  88.1, 49.9),   # bottom-right ( 0.014, 1.321)
]
def _build_sorry():
    kfs = [{"t": 0.0, **NEUTRAL_POSE}]
    t0, t1 = 0.13, 0.87                 # circle spans t0..t1
    pts = len(_SORRY_CIRCLE) * 2 + 1    # 2 loops + a closing return to the entry point
    for i in range(pts):
        t = t0 + (t1 - t0) * i / (pts - 1)
        ur, uu, lu = _SORRY_CIRCLE[i % len(_SORRY_CIRCLE)]
        kfs.append({"t": round(t, 4), **NEUTRAL_POSE, **_sorry_key(ur, uu, lu)})
    kfs.append({"t": 1.0, **NEUTRAL_POSE})
    return kfs
SORRY_SIGN = _build_sorry()

# I / ME: the signer points at their OWN chest -- the exact mirror of YOU (same
# index-finger POINT), aimed INWARD at the sternum instead of forward at the
# addressee, tapping the centre of the chest once or twice. No ISLRTC reference
# video was in hand, so (like SORRY) this is authored from the standard, widely
# documented form the user described and validated in-engine, NOT against a signed
# reference. Emotion is left NEUTRAL (pointing at yourself carries none), so there
# is deliberately no _WORD_DEFAULT_EMOTION entry for it.
#
# Geometry (Probe/PoseLab-solved, verified from FRONT + both SIDE profiles so the
# fingertip touches the chest and never sinks INTO it):
#  * HOLD THE HAND FORWARD, then POINT BACK. The make-or-break lesson: do NOT jam the
#    hand flat against the chest. An early version folded the forearm nearly vertical
#    so the hand pressed on the sternum and the fully-extended index (~15 cm of reach)
#    drove straight THROUGH the torso (tip at z~0.08, ~7 cm inside the body -- it read
#    as the finger literally buried in the chest). Instead the hand is held ~12 cm in
#    FRONT of the chest (wrist ~(0.00, 1.28, 0.27), a less-folded forearm off a low,
#    slightly-forward elbow) and the index points BACK toward the sternum, so the whole
#    finger is visible reaching in and the TIP STOPS AT THE SURFACE (~z 0.15). Same
#    idea as YOU (an extended-arm point) but folded inward at the body instead of out.
#  * AIMING THE FINGER AT THE CHEST needs a WRIST delta. With none, the POINT index
#    points ACROSS the body (out to the avatar's left). A world-axis roll of ~90 deg
#    swings the tip back-and-up onto the sternum, dead centre: tip ~(0.00, 1.36, 0.15),
#    just kissing the chest (NOT through it). A pure world-UP (yaw) roll does NOT
#    work: it swings the finger toward the camera instead.
#  * ROLL, separately from AIM: a plain cross-product aim solve (rotate natural-hand-X
#    onto the target direction by the SHORTEST path) leaves the roll about that pointing
#    axis wherever the minimal rotation happens to drop it -- for this arm that put the
#    palm facing OUT TO THE SIDE, so the wrist read as bending toward the EDGE of the
#    fist (ulnar/radial deviation) instead of toward the palm -- the "unnatural bend"
#    the user first flagged. The fix keeps the AIM identical (so the touch point doesn't
#    move) but explicitly SOLVES for roll too: a full-orientation delta (target_basis *
#    natural_basis^-1, both orthonormal, not just an aim cross-product) that pins natural
#    local-X to the SAME world direction as before AND pins natural local-Y (the palm
#    normal) to a chosen world direction. Because local-X (the pointing axis) is
#    unchanged, the fingertip position is provably unmoved by ANY choice of local-Y
#    target (verified each time: re-applying the delta to the natural basis reproduces
#    the old tip to sub-mm) -- only the hand's roll about that axis changes. Two
#    corrections landed here: local-Y first pinned to world-DOWN (palm down, rejected --
#    "unnatural bend"), then to world +X thinking "right" meant SCREEN-right (rejected --
#    the user meant the CHARACTER's own right, and this rig's right arm/hand rests at
#    world -X in the neutral pose, i.e. NEGATIVE X is the character's right side, the
#    mirror of what "RIGHT"-named axes elsewhere in this file mean as a rotation AXIS).
#    Final: local-Y pinned to world -X -- same touch point, palm now facing the
#    character's own right side, confirmed by a side-by-side render against both
#    rejected versions (this one reads as a distinct extended index with the fist
#    trailing below it; the world+X version read as a blobby fist with little finger
#    definition).
# The TAP is a small, natural UP-BOB (~3.5 cm): the fingertip lifts up-and-just-off the
# chest and comes back down. It bobs UP (not in/out) because the shipped camera is
# near-frontal -- an in/out (z) lift is foreshortened to nothing and the taps vanish,
# but a vertical (y) bob shows fully (screen-Y ~ world-Y). The lift RAISES the upper
# arm only ~6 deg (RIGHT -12 -> -18), so the ELBOW barely moves, so it reads as a light
# fingertip tap, NOT an arm pump (an earlier ~6 cm whole-arm bob looked like pumping).
# curl + wrist are the contact's, unchanged, so only the tip's height moves.
_ME_WRIST = [{"axis": [0.4608, 0.8836, 0.0832], "angle": 115.55}]
_ME_TOUCH = {   # index fingertip TOUCHING the centre of the chest   tip ~(0.00, 1.36, 0.15)
    "RightUpperArm": [{"axis": "RIGHT", "angle": -12}, {"axis": "UP", "angle": 66}],
    "RightLowerArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 44}],
    "RightWrist": _ME_WRIST,
    "curl_right": POINT,
}
_ME_LIFT = {    # fingertip bobbed ~3.5 cm UP off the chest (the tap gap)   tip ~(0.00, 1.40, 0.16)
    "RightUpperArm": [{"axis": "RIGHT", "angle": -18}, {"axis": "UP", "angle": 66}],
    "RightLowerArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 44}],
    "RightWrist": _ME_WRIST,
    "curl_right": POINT,
}
ME_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.34, **NEUTRAL_POSE, **_ME_TOUCH},   # rise, form the point, first tap on the chest
    {"t": 0.48, **NEUTRAL_POSE, **_ME_LIFT},    # lift up-off the chest (tap gap)
    {"t": 0.62, **NEUTRAL_POSE, **_ME_TOUCH},   # second tap
    {"t": 0.80, **NEUTRAL_POSE, **_ME_TOUCH},   # hold "me" on the chest so the point reads
    {"t": 1.0, **NEUTRAL_POSE},
]

WORD_SIGNS = {
    # I / ME: index point tapping the centre of the chest (see ME_SIGN).
    "i": ME_SIGN,
    "me": ME_SIGN,
    # YOU: index finger points at the addressee, arm raised and extended
    # forward at shoulder height. Re-derived: the old version only yawed the
    # upper arm (no forward raise at all), so the hand barely rose above
    # chest height -- it now has a real RIGHT-axis raise as well.
    "you": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.5, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -68}, {"axis": "UP", "angle": 52}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -5}],
            "curl_right": POINT},
        {"t": 0.8, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -68}, {"axis": "UP", "angle": 52}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -5}],
            "curl_right": POINT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # DRINK: a fist with the THUMB extended (an "A" hand, the thumb = spout) rises
    # to the mouth; the thumb TIP touches the lips, then the hand RISES together
    # with the head as it tips back to drink, and finally lowers back to rest.
    #
    # Two things make this read right, both hard-won (see CLAUDE.md):
    #  * THUMB VISIBILITY. A plain palm-to-face roll (wrist UP -90 alone) turns the
    #    BACK of the fist to the camera and hides the thumb behind it. Adding a
    #    FORWARD -35 tilt to the wrist presents the thumb (radial) side to the
    #    camera, so the spout reads as a distinct digit with its tip at the lips
    #    (verified by zooming the hand from the real camera).
    #  * THE RISE'S ARM PATH is a diagonal sweep (four waypoints, t 0.26/0.33/0.41/
    #    0.46) chosen so the hand's HEIGHT and CENTERING both increase monotonically
    #    from rest to contact -- never swinging further out than the resting arm
    #    before coming in. An early version let the hand overshoot laterally past rest
    #    before centering, which read as the arm "coming up, then bending sideways."
    #  * THE WRIST is a perfectly LINEAR-IN-TIME ramp (UP = 10 - 200*t, FORWARD =
    #    -20 - 30*t) from a low-pose-appropriate orientation at t=0 to the exact
    #    contact orientation at t=0.50. Holding the wrist at one CONSTANT value
    #    during the rise does NOT stop it from visually rotating -- the wrist delta
    #    composes with the forearm's own (large) rotation as the arm swings, so a
    #    fixed delta still appears to twist on screen. The only way to avoid both a
    #    late "sudden correction" AND a visible early twist is to make the correction
    #    happen at a perfectly uniform rate the WHOLE way (every segment rotates at
    #    the identical rate -- verified none is faster than any other), so it reads
    #    as continuous micro-adjustment rather than a rigid hold plus a jump.
    # The descent keeps the wrist rolled (thumb visible) high, then unrolls it
    # GRADUALLY as the hand drops down the front, relaxing open near the waist so
    # the turn-over reads as natural relaxation, never a twist.
    "drink": [
        {"t": 0.0, **NEUTRAL_POSE, "RightWrist": [{"axis": "UP", "angle": 10.0}, {"axis": "FORWARD", "angle": -20.0}]},
        {"t": 0.26, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -4}, {"axis": "UP", "angle": 42}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -68}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "UP", "angle": -42.0}, {"axis": "FORWARD", "angle": -27.8}],
            "curl_right": THUMB_OUT},
        {"t": 0.33, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -16}, {"axis": "UP", "angle": 48}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -88}, {"axis": "UP", "angle": 38}],
            "RightWrist": [{"axis": "UP", "angle": -56.0}, {"axis": "FORWARD", "angle": -29.9}],
            "curl_right": THUMB_OUT},
        {"t": 0.41, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 64}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 50}],
            "RightWrist": [{"axis": "UP", "angle": -72.0}, {"axis": "FORWARD", "angle": -32.3}],
            "curl_right": THUMB_OUT},
        {"t": 0.46, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -34}, {"axis": "UP", "angle": 78}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -103}, {"axis": "UP", "angle": 60}],
            "RightWrist": [{"axis": "UP", "angle": -82.0}, {"axis": "FORWARD", "angle": -33.8}],
            "curl_right": THUMB_OUT},
        # Contact: thumb TIP at the lips AND visible. Two coupled tricks:
        #  * FORWARD -35 on the wrist (on top of the UP -90 roll) turns the thumb
        #    (radial) side to the camera so the spout is VISIBLE; a plain UP -90 roll
        #    shows the back of the fist and hides the thumb (the "thumb hidden" bug).
        #  * That tilt alone pushes the thumb tip OUT to the cheek (~x-0.09), off the
        #    lips. OPENING THE ELBOW (LowerArm -105 instead of -125) walks the tip back
        #    IN to the lip centre (~x-0.02) -- more UP-swing does NOT (it jams the hand
        #    into the face). Net tip ~(-0.02,1.63,0.08), touching the lips, thumb shown.
        {"t": 0.50, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -42}, {"axis": "UP", "angle": 88}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -105}, {"axis": "UP", "angle": 66}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "FORWARD", "angle": -35}],
            "Head": {"axis": "RIGHT", "angle": -5},
            "curl_right": THUMB_OUT},
        # DRINK: the head tips BACK (chin up) and the hand RISES WITH IT. Tipping the
        # head lifts the lips, so the arm raises (RIGHT -42 -> -52) to keep the thumb ON
        # the lips -- verified at head -20 the tip re-lands on the raised lips at
        # ~(-0.05,1.65,0.06). Raising MORE carries the thumb past the lips up to the eye
        # (a bug an earlier version had); this raise TRACKS the lips. The visible rise +
        # the head tilt together read as the drinking motion.
        {"t": 0.60, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -52}, {"axis": "UP", "angle": 89}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -107}, {"axis": "UP", "angle": 67}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "FORWARD", "angle": -35}],
            "Head": {"axis": "RIGHT", "angle": -20},
            "curl_right": THUMB_OUT},
        # Descent: lower the fist down the FRONT of the body, keeping the wrist rolled
        # (thumb visible) while high and unrolling it GRADUALLY as the hand drops, so the
        # turn-over reads as relaxation, never a twist. Fingers open progressively; head
        # returns in step with the hand.
        {"t": 0.74, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -28}, {"axis": "UP", "angle": 80}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -108}, {"axis": "UP", "angle": 68}],
            "RightWrist": [{"axis": "UP", "angle": -82}, {"axis": "FORWARD", "angle": -30}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": THUMB_OUT},
        {"t": 0.86, **NEUTRAL_POSE,          # at chest: wrist relaxing, fingers begin opening
            "RightUpperArm": [{"axis": "RIGHT", "angle": -8}, {"axis": "UP", "angle": 66}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}, {"axis": "UP", "angle": 62}],
            "RightWrist": [{"axis": "UP", "angle": -58}, {"axis": "FORWARD", "angle": -18}],
            "Head": {"axis": "RIGHT", "angle": -3},
            "curl_right": {"Thumb": 0.05, "Index": 0.7, "Middle": 0.7, "Ring": 0.7, "Little": 0.7}},
        {"t": 0.94, **NEUTRAL_POSE,          # low at the waist: hand relaxing open, wrist rolling out
            "RightUpperArm": [{"axis": "FORWARD", "angle": -30}, {"axis": "UP", "angle": 30}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -45}, {"axis": "UP", "angle": 30}],
            "RightWrist": [{"axis": "UP", "angle": -30}, {"axis": "FORWARD", "angle": -8}],
            "Head": {"axis": "RIGHT", "angle": 0},
            "curl_right": {"Thumb": 0.1, "Index": 0.4, "Middle": 0.4, "Ring": 0.4, "Little": 0.4}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # GOOD (Sign 2): a clean thumbs-up held in front of the right shoulder. The
    # forearm stands upright (an UP component on the LowerArm bend keeps it from
    # reaching forward -- the old [RIGHT -92]-only bend threw the hand out in front
    # with the palm facing the camera). The wrist carries UP -90 PLUS a RIGHT 40
    # roll, which twists the hand toward the CHARACTER'S LEFT so the palm faces left
    # and the thumb stands straight UP -- NOT palm-to-camera, and with no forward
    # wrist-bend (a FORWARD tilt made the wrist look twisted/bent). Held.
    "good": [
        {"t": 0.0, **NEUTRAL_POSE},
        # GOOD_THUMB: like THUMB_OUT but the thumb is EXTENDED extra-straight -- a
        # slightly negative curl about BACK straightens the thumb along its length so it
        # points cleanly straight up (about UP or RIGHT it would just swing sideways;
        # BACK extends it). good-specific so the shared THUMB_OUT is untouched.
        {"t": 0.32, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -108}, {"axis": "UP", "angle": 56}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 40}],
            "curl_right": {"Thumb": -0.5, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}},
        {"t": 0.75, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -108}, {"axis": "UP", "angle": 56}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 40}],
            "curl_right": {"Thumb": -0.5, "_thumb_axis": "BACK", "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # BAD (Sign 2): a fist with ONLY the little finger extended (PINKY) snaps UP near the
    # CHEEK, then comes STRAIGHT DOWN to the chest with the ELBOW HELD CONSTANT (a fixed
    # pivot) and NO left-right sway, matching the ISLRTC reference (Bad_(Sign_2).mp4).
    # The RightUpperArm is IDENTICAL at every key ([RIGHT -46, UP 67]) so the elbow world
    # position never moves (Relbow = (-0.156,1.295,0.221)); the descent is the FOREARM
    # swinging about that fixed elbow. A plain unfold would swing the hand INWARD to centre,
    # so each descent key adds a world-UP roll to the LowerArm to steer it back OUT, keeping
    # x ~-0.18 the whole way (Probe-solved, no sway). The mid key is an explicit control
    # point so the SLERP can't bow the descent. Fist orientation is inherited from the
    # forearm (no RightWrist). Default face = angry (gloss layer, _WORD_DEFAULT_EMOTION).
    #   cheek  LowerArm [RIGHT -106, UP 16] -> hand (-0.179, 1.534, 0.346)
    #   mid    LowerArm [RIGHT -65,  UP -25] -> hand (-0.184, 1.388, 0.474)
    #   chest  LowerArm [RIGHT -32,  UP -44] -> hand (-0.177, 1.232, 0.484)
    "bad": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.16, **NEUTRAL_POSE,           # snap the pinky-fist up, near the cheek
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 67}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}, {"axis": "UP", "angle": 16}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.30, **NEUTRAL_POSE,           # brief hold at the cheek
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 67}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}, {"axis": "UP", "angle": 16}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.50, **NEUTRAL_POSE,           # mid-descent (Probe-pinned so x stays ~-0.18)
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 67}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -65}, {"axis": "UP", "angle": -25}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.66, **NEUTRAL_POSE,           # chest: forearm ~horizontal, hand straight below the cheek
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 67}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -32}, {"axis": "UP", "angle": -44}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.82, **NEUTRAL_POSE,           # hold at the chest
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 67}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -32}, {"axis": "UP", "angle": -44}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # YES: closed fist raised to shoulder height with the PALM turned to face
    # DOWNWARD -- a base wrist roll of UP -90, then a forward flex (RIGHT) so the
    # palm points at the floor. The fist "nods" at the wrist twice, bobbing
    # between RIGHT 47 (up) and RIGHT 92 (down, palm fully down), like a head
    # nodding. The raise lands DIRECTLY at the up extreme (RIGHT 47), and the
    # settle returns to it too, so the FIRST nod is already full range -- an
    # earlier version raised to an intermediate RIGHT 80, which made the first
    # nod a tiny 80->92 before the later 47<->92 swings grew, reading as "starts
    # small, then bigger." Each wrist value is a LIST composed world-space (see
    # SignDirector._bone_delta_basis): the UP -90 roll, then the RIGHT flex/nod on
    # top. The wrapped-thumb fist stays a proper fist throughout.
    # A subtle HEAD nod is layered in sync: the chin dips (Head RIGHT +7) on each
    # fist-down beat and lifts slightly (RIGHT -2) on the up beats.
    "yes": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.2, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 47}],
            "Head": {"axis": "RIGHT", "angle": -2},  # chin lifts slightly
            "curl_right": FIST_TIGHT},
        {"t": 0.38, **NEUTRAL_POSE,           # nod DOWN (palm tips down)
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 92}],
            "Head": {"axis": "RIGHT", "angle": 7},   # chin dips with the nod
            "curl_right": FIST_TIGHT},
        {"t": 0.54, **NEUTRAL_POSE,           # back UP
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 47}],
            "Head": {"axis": "RIGHT", "angle": -2},  # chin lifts slightly
            "curl_right": FIST_TIGHT},
        {"t": 0.7, **NEUTRAL_POSE,            # nod DOWN again
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 92}],
            "Head": {"axis": "RIGHT", "angle": 7},   # chin dips with the nod
            "curl_right": FIST_TIGHT},
        {"t": 0.85, **NEUTRAL_POSE,           # settle, palm still to viewer
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 47}],
            "Head": {"axis": "RIGHT", "angle": -2},  # chin lifts slightly
            "curl_right": FIST_TIGHT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # HELLO: a salute -- flat hand rises to sit at the brow, centered in front of
    # the forehead with the elbow out at shoulder height and the palm angled
    # down/forward (FORWARD wrist roll), held, then flicks outward-down away from
    # the head. Arm angles from the Probe sweep (pose "P": hand ~1.58 at the brow).
    "hello": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.30, **NEUTRAL_POSE,           # flat hand up to the FOREHEAD, fingers up (salute).
            # Upper arm swings up so the elbow sits OUT at shoulder height (elbow x more
            # negative than the shoulder -- it does NOT tuck across the chest); the forearm
            # folds the flat hand in to the BROW. Raised from the temple/nose (y~1.54) up to
            # the forehead (hand y~1.61) by lifting the elbow via a bigger upper-arm swing.
            "RightUpperArm": [{"axis": "RIGHT", "angle": -90}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -94}, {"axis": "UP", "angle": 88}],
            "RightWrist": {"axis": "UP", "angle": -90},
            "curl_right": FLAT},
        {"t": 0.56, **NEUTRAL_POSE,           # hold the salute at the forehead
            "RightUpperArm": [{"axis": "RIGHT", "angle": -90}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -94}, {"axis": "UP", "angle": 88}],
            "RightWrist": {"axis": "UP", "angle": -90},
            "curl_right": FLAT},
        {"t": 0.80, **NEUTRAL_POSE,           # move the hand AWAY from the forehead (out + down)
            "RightUpperArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 25}],
            "RightWrist": {"axis": "UP", "angle": -90},
            "curl_right": FLAT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # PLEASE: five fingertips drawn to a point -- an upward "flower-bud" CONE (see
    # the CONE handshape + "_converge") -- raised to the CHIN, then drawn DOWN and
    # forward (off the torso) to a CENTRED chest-height position, held at each end.
    # Getting the bud TO THE FACE (chin) is what makes the sign read, so the start is
    # CENTRED at the chin; on this rig centring at the face forces a RAISED elbow (a
    # low+centred hand doesn't exist -- see the DRINK note), an accepted trade.
    # KEY TRICK (2026-07 rework): the chin key's wrist aims the bud UP + toward the
    # camera with a raw [x,y,z] axis (33 deg) composed with a world-UP -50 roll (so the
    # pinched, OPEN fingers face the viewer, not the back of the hand). The down key
    # REUSES THE IDENTICAL WRIST -- not a re-solved counter-rotation. An earlier version
    # forced the bud dead-vertical at the down too; because the forearm rotates ~90 deg
    # between the keys, that needed a ~132 deg wrist that read as a broken, hyperextended
    # bend (the "weird elbow/wrist" bug). Sharing one wrist lets the bud tilt GENTLY
    # forward with the forearm as it lowers -- natural, no crank -- and the down is
    # routed CENTRED-and-forward, not swung out to the side (old x -0.27). Each position
    # is held briefly (a beat at the face, a beat at the chest) so the travel reads.
    "please": [
        {"t": 0.0, **NEUTRAL_POSE},
        # bud rises to the CHIN, centred, fingertips up (wrist ~y1.50, tip at mouth)
        {"t": 0.30, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -50}],
            "curl_right": CONE},
        {"t": 0.42, **NEUTRAL_POSE,          # beat at the chin
            "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -50}],
            "curl_right": CONE},
        # drawn DOWN and forward (off the torso so it never clips the chest/stomach) to
        # a CENTRED chest-height position. Same wrist as the chin key (NOT re-solved), so
        # the bud tilts gently forward with the forearm as it lowers -- no 132-deg crank.
        {"t": 0.74, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -16}, {"axis": "UP", "angle": 74}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -80}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -50}],
            "curl_right": CONE},
        {"t": 0.88, **NEUTRAL_POSE,          # beat at the down-forward end
            "RightUpperArm": [{"axis": "RIGHT", "angle": -16}, {"axis": "UP", "angle": 74}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -80}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -50}],
            "curl_right": CONE},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # NONE / NOTHING / EMPTY share one two-handed brush-off sign (see NONE_SIGN).
    "none": NONE_SIGN,
    "nothing": NONE_SIGN,
    "empty": NONE_SIGN,
    # SORRY: closed fist circled over the heart (see SORRY_SIGN). Default face = sad.
    "sorry": SORRY_SIGN,
    # TEACHER: both hands make an index-point ("1", thumb closed) and the WRISTS CROSS at
    # the wrist, one on top of the other, both index fingers pointing UP in a V, tapping
    # twice. This pass is FRAMED FOR THE SHIPPED CAMERA (which sits ~19deg to the avatar's
    # left) -- it's posed so THAT view reads like the ISLRTC reference, per user direction.
    # The camera geometry drove the solution (many prior passes failed): from the shipped
    # camera screen-X ~ world-X and screen-Y ~ world-Y, so:
    #  * The two WRISTS are placed at nearly the SAME world x AND height, differing only in
    #    DEPTH (RightShoulder FORWARD +8 puts the right ~5cm in front). On screen they thus
    #    OVERLAP -> read as crossed at the wrist, right on top, and never intersect. (Left
    #    shoulder left alone -- rotating it back drove the elbow through the torso before.)
    #  * The two FINGERTIPS are splayed to OPPOSITE world-x (a FORWARD +/-20 V on each
    #    wrist) so on screen they separate -> BOTH fingers read as an upward V above the
    #    crossed wrists. Elbows sit wide, so the forearms diverge DOWN (they only meet at
    #    the wrist, not along their length -- fixing the "whole forearms intersecting" look).
    #  * ONE handshape, thumb CLOSED about BACK. TAP = small UP-swing oscillation (103->107).
    # Because this is camera-framed, it looks its best from the shipped view; other angles
    # show the small depth offset but still read fine.
    "teacher": [
        {"t": 0.0, **NEUTRAL_POSE},
        # rise: the two forearms SCISSOR into an X that crosses AT THE WRIST, with
        # the two index fingers slanting up to opposite corners so the cross reads.
        # The make-or-break lever is a FORWARD-roll ABDUCTION on each UpperArm
        # (right +24 / left -24): it swings each elbow WIDE and DOWN to its own
        # side while the UP-swing keeps the wrist near centre -- so the forearms
        # form the wide lower half of the X and only meet at the wrist (they never
        # overlap along their length, the old "forearms intersecting" bug). A depth
        # offset (RightShoulder FORWARD +8 -> right wrist ~5cm in front) makes them
        # read as crossed-one-on-top without colliding in 3-D. The wrist FORWARD
        # +-20 splays each index finger ACROSS to the opposite side (right->screen
        # right, left->screen left) so the fingers are the slanted upper half of the
        # X. ONE keeps the thumb closed (BACK). Framed for the shipped camera.
        {"t": 0.26, **NEUTRAL_POSE,
            "RightShoulder": [{"axis": "FORWARD", "angle": 8}],
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 95}, {"axis": "FORWARD", "angle": 24}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "RightWrist": [{"axis": [-0.7908, 0.0, 0.6121], "angle": 38.7}, {"axis": "FORWARD", "angle": 20}],
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -30}, {"axis": "UP", "angle": -95}, {"axis": "FORWARD", "angle": -24}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "LeftWrist": [{"axis": [-0.8060, 0.0, -0.5918], "angle": 30.7}, {"axis": "FORWARD", "angle": -20}],
            "curl_left": ONE},
        # tap (1): small UP-swing bob at the crossing
        {"t": 0.44, **NEUTRAL_POSE,
            "RightShoulder": [{"axis": "FORWARD", "angle": 8}],
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 99}, {"axis": "FORWARD", "angle": 24}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "RightWrist": [{"axis": [-0.7908, 0.0, 0.6121], "angle": 38.7}, {"axis": "FORWARD", "angle": 20}],
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -30}, {"axis": "UP", "angle": -99}, {"axis": "FORWARD", "angle": -24}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "LeftWrist": [{"axis": [-0.8060, 0.0, -0.5918], "angle": 30.7}, {"axis": "FORWARD", "angle": -20}],
            "curl_left": ONE},
        # part (back to hold)
        {"t": 0.60, **NEUTRAL_POSE,
            "RightShoulder": [{"axis": "FORWARD", "angle": 8}],
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 95}, {"axis": "FORWARD", "angle": 24}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "RightWrist": [{"axis": [-0.7908, 0.0, 0.6121], "angle": 38.7}, {"axis": "FORWARD", "angle": 20}],
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -30}, {"axis": "UP", "angle": -95}, {"axis": "FORWARD", "angle": -24}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "LeftWrist": [{"axis": [-0.8060, 0.0, -0.5918], "angle": 30.7}, {"axis": "FORWARD", "angle": -20}],
            "curl_left": ONE},
        # tap (2)
        {"t": 0.76, **NEUTRAL_POSE,
            "RightShoulder": [{"axis": "FORWARD", "angle": 8}],
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 99}, {"axis": "FORWARD", "angle": 24}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "RightWrist": [{"axis": [-0.7908, 0.0, 0.6121], "angle": 38.7}, {"axis": "FORWARD", "angle": 20}],
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -30}, {"axis": "UP", "angle": -99}, {"axis": "FORWARD", "angle": -24}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "LeftWrist": [{"axis": [-0.8060, 0.0, -0.5918], "angle": 30.7}, {"axis": "FORWARD", "angle": -20}],
            "curl_left": ONE},
        # settle (hold) then release
        {"t": 0.90, **NEUTRAL_POSE,
            "RightShoulder": [{"axis": "FORWARD", "angle": 8}],
            "RightUpperArm": [{"axis": "RIGHT", "angle": -22}, {"axis": "UP", "angle": 95}, {"axis": "FORWARD", "angle": 24}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "RightWrist": [{"axis": [-0.7908, 0.0, 0.6121], "angle": 38.7}, {"axis": "FORWARD", "angle": 20}],
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -30}, {"axis": "UP", "angle": -95}, {"axis": "FORWARD", "angle": -24}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -106}],
            "LeftWrist": [{"axis": [-0.8060, 0.0, -0.5918], "angle": 30.7}, {"axis": "FORWARD", "angle": -20}],
            "curl_left": ONE},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # GO: decoded frame-by-frame at 25fps from the ISLRTC reference
    # (ISL_dictionary/Go.mp4) -- an earlier pass (raise beside the head + a small
    # wrist flick, arm FIXED between the two keys) was WRONG on rewatch; don't
    # revert to it. The real sign is ONE continuous motion with the hand near the
    # NECK/CHIN (elbow already out to the side, palm facing INWARD toward the
    # neck -- so the BACK of the hand faces the camera) that then both TWISTS
    # (a forearm roll, not a wrist flex) AND SWEEPS through a semicircular arc
    # outward/upward, ending with the hand up beside the head, palm facing
    # diagonally outward-and-down. The arm/orientation genuinely change together
    # across the whole motion -- it is NOT a fixed arm with a wrist-only flick.
    # This rig has no separate forearm-twist bone (RightLowerArm's bend is just
    # the elbow hinge), so the twist is implemented via RightWrist -- the only
    # bone representing hand-relative-to-forearm orientation here; a world-UP-axis
    # roll on it, empirically, is what swings the palm (found by testing named
    # axes in PoseLab and comparing renders to the reference frames): UP 140 at
    # the START arm gives the edge-on/back-of-hand look, UP -70 at the END arm
    # gives palm-diagonal-out-and-down (the "same nominal axis, opposite-feeling
    # sign convention" between the two arm configs is just this rig's coupling of
    # wrist delta to whatever the current forearm orientation is -- Basis.slerp
    # between the two keyframes' actual 3-D orientations is what matters, not the
    # two angle numbers matching up arithmetically).
    # The reference clip's final arm-drop back to the side (~h_042-046 in a 25fps
    # extraction) is the actor relaxing after the sign is already complete, NOT
    # part of the sign -- do not encode that as a third pose; go straight from
    # the END hold back to NEUTRAL_POSE like every other sign here.
    "go": [
        {"t": 0.0, **NEUTRAL_POSE},
        # START: hand tucked right against the jaw/cheek (elbow raised, NOT flared
        # out low -- a face-height hand needs a raised elbow on this rig, same
        # lesson as DRINK/PLEASE/HELLO; an earlier pass put the hand ~0.32 units
        # IN FRONT of the head bone (whose own z is ~0.008), which floated it way
        # out from the face instead of tucked against it -- don't repeat that,
        # always sanity-check a face-height target against the actual Head bone
        # position, not just eyeballed plausibility). Probe-solved to
        # (-0.167, 1.577, 0.111), right at jaw height and within ~10cm of the head.
        {"t": 0.26, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -104}, {"axis": "UP", "angle": 86}],
            "RightWrist": {"axis": "UP", "angle": 120},
            "curl_right": FLAT},
        {"t": 0.38, **NEUTRAL_POSE,          # brief hold at the jaw before the twist+arc
            "RightUpperArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -104}, {"axis": "UP", "angle": 86}],
            "RightWrist": {"axis": "UP", "angle": 120},
            "curl_right": FLAT},
        # END: forearm twists + the arm sweeps a semicircular arc outward/upward --
        # hand ends up beside the head (~(-0.25, 1.63, 0.14)), palm diagonally
        # outward-and-down. Both arm bones AND the wrist change together here.
        {"t": 0.62, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -80}, {"axis": "UP", "angle": 10}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}, {"axis": "UP", "angle": 66}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": FLAT},
        {"t": 0.80, **NEUTRAL_POSE,          # hold the end position so the arc reads
            "RightUpperArm": [{"axis": "RIGHT", "angle": -80}, {"axis": "UP", "angle": 10}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}, {"axis": "UP", "angle": 66}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": FLAT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Non-lexical function words (never played by the fixed gloss; kept so the
    # dataset is complete for export_word_signs.py).
    "are": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "going": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "to": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
}
