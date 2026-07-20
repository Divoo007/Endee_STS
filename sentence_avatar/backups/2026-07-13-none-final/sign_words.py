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

The demo plays a fixed ISL gloss (TOMORROW TEA YOU DRINK) for all three sample
sentences; only those four words' signs matter (are/going/to are non-lexical).
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
# CONE / true flower-bud (PLEASE): fingertips drawn to a POINT. Two things make the
# pinch read: (1) "_converge" fans them together laterally + opposes the thumb -- a
# hand-rig capability the plain curl model lacks (no adduction), so the five tips
# actually meet; see hand_rig.gd's convergence note. (2) GRADUATED curl -- the middle
# finger is the LONGEST, so with equal curl its tip towers above the others and the
# shape reads as a raised finger, not a pinch; curling the long fingers MORE (middle
# most, then index/ring, little least) lands all four tips at the same point. The
# thumb curls about BACK to join them from the front. Absent (off) on every other
# handshape, so nothing else changes.
CONE = {"Thumb": 0.45, "Index": 0.5, "Middle": 0.65, "Ring": 0.55, "Little": 0.4,
        "_thumb_axis": "BACK", "_converge": 1.2}
# Index only extended, others (incl. thumb) closed -- a clean pointing "1"
# (TEACHER's two crossed pointers; YOU points with this too via POINT).
ONE = {"Thumb": 0.85, "Index": 0.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}

SENTENCE = "You are drinking tea tomorrow."

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
    "curl_left": FLAT,
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
        "RightUpperArm": [{"axis": "RIGHT", "angle": -34}, {"axis": "UP", "angle": up}],
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

# BACKUP of the PLEASE sign as of the "fingers behind the palm" version -- kept per
# user request before a follow-up tweak that turns each wrist a further UP -30 toward
# the camera so the pinched fingertips are visible (the live "please" in WORD_SIGNS
# is that tweaked version). To REVERT the wrist turn: WORD_SIGNS["please"] =
# PLEASE_BACKUP_FINGERS_HIDDEN. Everything else (elbow, arm, CONE handshape) is
# identical between the two -- ONLY the RightWrist values differ.
PLEASE_BACKUP_FINGERS_HIDDEN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.30, **NEUTRAL_POSE,
        "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
        "RightWrist": {"axis": [0.8967, 0.0, 0.4427], "angle": 33.24},
        "curl_right": CONE},
    {"t": 0.42, **NEUTRAL_POSE,
        "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
        "RightWrist": {"axis": [0.8967, 0.0, 0.4427], "angle": 33.24},
        "curl_right": CONE},
    {"t": 0.74, **NEUTRAL_POSE,
        "RightUpperArm": [{"axis": "RIGHT", "angle": 4}, {"axis": "UP", "angle": 54}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -66}],
        "RightWrist": {"axis": [-0.0270, 0.5416, 0.8402], "angle": 131.70},
        "curl_right": CONE},
    {"t": 0.88, **NEUTRAL_POSE,
        "RightUpperArm": [{"axis": "RIGHT", "angle": 4}, {"axis": "UP", "angle": 54}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -66}],
        "RightWrist": {"axis": [-0.0270, 0.5416, 0.8402], "angle": 131.70},
        "curl_right": CONE},
    {"t": 1.0, **NEUTRAL_POSE},
]

WORD_SIGNS = {
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
    # TEA: one delicate pinch (thumb+index, holding a tiny cup) sipped at the
    # mouth, twice, with a small head tilt. Re-derived from the ISLRTC reference:
    # real ISL mimes sipping a small cup one-handed -- NOT the old two-handed
    # "stationary cup + stirring hand" that was never validated (see CLAUDE.md).
    "tea": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.32, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -42}, {"axis": "UP", "angle": 46}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 34}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": OK},
        {"t": 0.55, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -44}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -75}, {"axis": "UP", "angle": 42}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "Head": {"axis": "RIGHT", "angle": -8},
            "curl_right": OK},
        {"t": 0.72, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -42}, {"axis": "UP", "angle": 48}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -70}, {"axis": "UP", "angle": 38}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": OK},
        {"t": 0.86, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -44}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -75}, {"axis": "UP", "angle": 42}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "Head": {"axis": "RIGHT", "angle": -8},
            "curl_right": OK},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # TOMORROW: index raised high near the head (clearly distinct from YOU's
    # shoulder-height forward point), forearm rolls forward slightly across
    # keyframes for a small "day ahead" push motion.
    # TOMORROW: index raised near the head, and the whole hand makes ONE COMPLETE
    # forward rotation (a "day turning over / day ahead" roll). The roll is
    # authored in ~90-degree steps so the slerp between keyframes traces the full
    # 360 instead of collapsing to identity.
    "tomorrow": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.18, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -88}, {"axis": "UP", "angle": 45}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -38}],
            "RightWrist": {"axis": "RIGHT", "angle": 0},
            "Head": {"axis": "RIGHT", "angle": -4},
            "curl_right": POINT},
        {"t": 0.38, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -88}, {"axis": "UP", "angle": 45}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -38}],
            "RightWrist": {"axis": "RIGHT", "angle": 120},
            "Head": {"axis": "RIGHT", "angle": -4},
            "curl_right": POINT},
        {"t": 0.58, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -88}, {"axis": "UP", "angle": 45}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -38}],
            "RightWrist": {"axis": "RIGHT", "angle": 240},
            "Head": {"axis": "RIGHT", "angle": -4},
            "curl_right": POINT},
        {"t": 0.78, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -88}, {"axis": "UP", "angle": 45}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -38}],
            "RightWrist": {"axis": "RIGHT", "angle": 355},
            "Head": {"axis": "RIGHT", "angle": -4},
            "curl_right": POINT},
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
    # BAD (Sign 2): a fist with ONLY the little finger extended (PINKY) starts up
    # at the face (forearm vertical, hand by the cheek), then the ELBOW EXTENDS,
    # dropping the fist STRAIGHT DOWN (a near-vertical hand path -- constant world x/z)
    # to end with the forearm horizontal in front of the body. Displeased face at
    # sentence level. Arm angles from the Probe (START: hand at the cheek ~1.50;
    # END E6: hand ~1.22 directly below the start, x/z held constant).
    "bad": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.26, **NEUTRAL_POSE,           # snap the pinky-fist up to the face (mouth level)
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 56}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -88}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.40, **NEUTRAL_POSE,           # brief hold at the face
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 56}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -88}],
            "Head": {"axis": "RIGHT", "angle": -10},
            "curl_right": PINKY},
        {"t": 0.68, **NEUTRAL_POSE,           # the elbow drops the fist STRAIGHT DOWN
            # From the face the hand descends on a near-vertical line (same world x/z,
            # y ~1.50 -> ~1.22), ending with the forearm horizontal in front of the body.
            # The OLD end swung the hand INWARD across the body (x -0.25 -> 0.00) -- that
            # sideways sweep read as the "curved path". No wrist roll now: the POSITIVE-
            # thumb fist (see PINKY) tucks correctly in any orientation, so palm-down is fine.
            "RightUpperArm": [{"axis": "RIGHT", "angle": -15}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -42}],
            "curl_right": PINKY},
        {"t": 0.86, **NEUTRAL_POSE,           # hold: fist down, forearm horizontal in front
            "RightUpperArm": [{"axis": "RIGHT", "angle": -15}, {"axis": "UP", "angle": 50}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -42}],
            "curl_right": PINKY},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # YES: closed fist raised to shoulder height with the PALM turned to face
    # DOWNWARD -- a base wrist roll of UP -90, then a forward flex (RIGHT ~80) so
    # the palm points at the floor. The fist "nods" at the wrist twice, bobbing
    # between RIGHT 62 (up) and RIGHT 90 (down, palm fully down), like a head
    # nodding. Each wrist value is a LIST composed world-space (see
    # SignDirector._bone_delta_basis): the UP -90 roll, then the RIGHT flex/nod on
    # top. The wrapped-thumb fist stays a proper fist throughout.
    "yes": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.2, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 80}],
            "curl_right": FIST_TIGHT},
        {"t": 0.38, **NEUTRAL_POSE,           # nod DOWN (palm tips down)
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 90}],
            "curl_right": FIST_TIGHT},
        {"t": 0.54, **NEUTRAL_POSE,           # back UP
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 62}],
            "curl_right": FIST_TIGHT},
        {"t": 0.7, **NEUTRAL_POSE,            # nod DOWN again
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 90}],
            "curl_right": FIST_TIGHT},
        {"t": 0.85, **NEUTRAL_POSE,           # settle, palm still to viewer
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 60}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -95}],
            "RightWrist": [{"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 80}],
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
    # THANK YOU (Sign 2): flat hand rises so the fingertips are at the forehead
    # (palm angled in/down), then arcs DOWN and FORWARD away from the face, palm
    # rotating up -- the classic "thank you" release, started high at the brow.
    "thank_you": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.32, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -80}, {"axis": "UP", "angle": 52}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -108}],
            "RightWrist": {"axis": "RIGHT", "angle": -35},
            "curl_right": FLAT},
        {"t": 0.62, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -38}, {"axis": "UP", "angle": 40}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -48}],
            "RightWrist": {"axis": "RIGHT", "angle": 18},
            "curl_right": FLAT},
        {"t": 0.82, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -38}, {"axis": "UP", "angle": 40}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -48}],
            "RightWrist": {"axis": "RIGHT", "angle": 18},
            "curl_right": FLAT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # PLEASE: five fingertips drawn to a point -- an upward "flower-bud" CONE (see
    # the CONE handshape + "_converge") -- raised to the CHIN, then drawn DOWN and
    # AWAY diagonally (forward + down, off the torso) and held, the bud pointing UP
    # the whole way. Getting the bud TO THE FACE (chin) is what makes the sign read,
    # so the start is CENTRED at the chin; on this rig centring at the face forces a
    # RAISED elbow (a low+centred hand doesn't exist -- see the DRINK note), an
    # accepted trade. The down leg travels FORWARD as it drops so the hand clears the
    # chest/stomach (an earlier straight-down-the-midline version clipped the torso).
    # KEY TRICK: the arm poses alone point the fingers up-and-BACK into the face
    # (they'd occlude), so the bud is aimed cleanly UP by a WRIST delta with a raw
    # [x,y,z] axis, solved numerically in PoseLab. The chin key's wrist maps its
    # finger direction onto world-up (33 deg); the down key's wrist is solved to
    # reproduce the chin key's EXACT hand orientation (~132 deg about a solved axis),
    # not merely "point up" -- otherwise the bud visibly TWISTS as it descends. Both
    # keys thus hold an identical, steady vertical bud; only its height changes. Each
    # position is held briefly (a beat at the face, a beat at the chest) so the
    # face->down travel reads as a deliberate gesture, not a single smear.
    # Finally, each wrist carries an extra world-UP -30 (the composed second entry in
    # the RightWrist list) that turns the bud slightly TOWARD THE CAMERA so the pinched
    # fingertips face the viewer instead of hiding behind the back of the hand. Same
    # roll on both keys, so the orientation match is preserved. The un-turned version
    # (fingers behind the palm) is saved as PLEASE_BACKUP_FINGERS_HIDDEN above.
    "please": [
        {"t": 0.0, **NEUTRAL_POSE},
        # bud rises to the CHIN, centred, fingertips up (wrist ~y1.50, tip at mouth)
        {"t": 0.30, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -30}],
            "curl_right": CONE},
        {"t": 0.42, **NEUTRAL_POSE,          # beat at the chin
            "RightUpperArm": [{"axis": "RIGHT", "angle": -26}, {"axis": "UP", "angle": 86}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -116}, {"axis": "UP", "angle": 64}],
            "RightWrist": [{"axis": [0.8967, 0.0, 0.4427], "angle": 33.24}, {"axis": "UP", "angle": -30}],
            "curl_right": CONE},
        # drawn DOWN and AWAY (diagonally forward, off the torso so it never clips
        # the chest/stomach), the bud still pointing up (wrist orientation matched to
        # the chin key so the bud doesn't twist as it travels)
        {"t": 0.74, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": 4}, {"axis": "UP", "angle": 54}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -66}],
            "RightWrist": [{"axis": [-0.0270, 0.5416, 0.8402], "angle": 131.70}, {"axis": "UP", "angle": -30}],
            "curl_right": CONE},
        {"t": 0.88, **NEUTRAL_POSE,          # beat at the down-away end
            "RightUpperArm": [{"axis": "RIGHT", "angle": 4}, {"axis": "UP", "angle": 54}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -66}],
            "RightWrist": [{"axis": [-0.0270, 0.5416, 0.8402], "angle": 131.70}, {"axis": "UP", "angle": -30}],
            "curl_right": CONE},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # NO (Sign 2): index+middle extended (a "V") at face height; the two fingers
    # swing OUTWARD to the side and back, twice (a flicking "no"). The outward
    # swing is a wrist yaw so the fingertips sweep away from centre.
    "no": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.22, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 66}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -96}],
            "RightWrist": {"axis": "UP", "angle": 0},
            "curl_right": TWO_OPEN},
        {"t": 0.42, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 66}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -96}],
            "RightWrist": {"axis": "UP", "angle": -55},
            "curl_right": TWO_OPEN},
        {"t": 0.6, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 66}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -96}],
            "RightWrist": {"axis": "UP", "angle": 0},
            "curl_right": TWO_OPEN},
        {"t": 0.78, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 66}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -96}],
            "RightWrist": {"axis": "UP", "angle": -55},
            "curl_right": TWO_OPEN},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # NONE / NOTHING / EMPTY share one two-handed brush-off sign (see NONE_SIGN).
    "none": NONE_SIGN,
    "nothing": NONE_SIGN,
    "empty": NONE_SIGN,
    # TEACHER: both hands make an index-point ("1"); the forearms CROSS at centre
    # chest (right over to the left, left over to the right) and TAP together
    # twice. (Re-derived per user correction: crossed pointing hands tapping.)
    "teacher": [
        {"t": 0.0, **NEUTRAL_POSE},
        {"t": 0.28, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": 96}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "RightWrist": {"axis": "FORWARD", "angle": 60},
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": -96}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "LeftWrist": {"axis": "FORWARD", "angle": -60},
            "curl_left": ONE},
        {"t": 0.48, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": 112}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "RightWrist": {"axis": "FORWARD", "angle": 60},
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": -112}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "LeftWrist": {"axis": "FORWARD", "angle": -60},
            "curl_left": ONE},
        {"t": 0.66, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": 96}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "RightWrist": {"axis": "FORWARD", "angle": 60},
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": -96}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "LeftWrist": {"axis": "FORWARD", "angle": -60},
            "curl_left": ONE},
        {"t": 0.84, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": 112}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "RightWrist": {"axis": "FORWARD", "angle": 60},
            "curl_right": ONE,
            "LeftUpperArm": [{"axis": "RIGHT", "angle": -35}, {"axis": "UP", "angle": -112}],
            "LeftLowerArm": [{"axis": "RIGHT", "angle": -74}],
            "LeftWrist": {"axis": "FORWARD", "angle": -60},
            "curl_left": ONE},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Non-lexical function words (never played by the fixed gloss; kept so the
    # dataset is complete for export_word_signs.py).
    "are": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "going": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "to": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
}
