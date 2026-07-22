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
# Open spread "5" hand (WHY): all five fingers extended and clearly SPLAYED apart,
# palm open -- the loose questioning/upturned open hand. None of the other shapes
# spread the fingers: FLAT holds them TOGETHER (a B-hand). The spread is produced by
# driving the SAME convergence machinery CONE uses (hand_rig.gd), but NEGATIVE: a
# negative "_converge" REVERSES the base-joint adduction so the four fingers fan
# OUTWARD instead of toward a point, and reverses the thumb opposition so the thumb
# abducts away to the side (an open palm, not a tucked one). Curl is kept very light
# (~0.1, nearly straight) so it reads as an open hand, not a claw. Thumb about BACK
# (like the fists) so at this light curl it lies naturally along the radial side.
FIVE = {"Thumb": 0.0, "Index": 0.1, "Middle": 0.1, "Ring": 0.1, "Little": 0.1,
        "_thumb_axis": "BACK", "_converge": -0.7}
# NAME_HAND: palm held FLAT-FORWARD (its area vector points at the viewer -- see NAME's
# per-key wrist solve), with BOTH the INDEX and the THUMB bent at their BASE joints so they
# point FORWARD out of the palm (toward the viewer, ~parallel to the palm normal), and
# middle/ring/pinky closed into a fist. Both use a PER-FINGER base-bend
# ("_base_bend":["Index","Thumb"]): each folds only at its base joint and stays STRAIGHT,
# sticking out, while the other three curl NORMALLY into the fist. A plain curl can't do
# this -- it folds a digit INTO the palm (just a fist); with the palm facing the viewer a
# digit can only point along the normal by base-bending, not by curling (curling lays it
# flat across the palm). Per-finger base-bend was added to the rig for exactly this
# (hand_rig._base_bends; value = bool for all four, KNOW, OR a list of names, here).
#  * INDEX 0.8 -- base-bent ~76deg (a touch under a right angle so it stands slightly more
#    upright than a full 90). Bends about the FINGER curl axis.
#  * THUMB 1.0 -- base-bent at its Metacarpal about a SOLVED raw axis [0.7,-0.47,0.0] so the
#    straight thumb points FORWARD/DOWN more directly AT the viewer, roughly parallel to the
#    index. (Tuned from the earlier forward-aim [0.7,-0.15,0.7]: twisted ~53deg toward the
#    camera, then ~10deg toward the avatar's RIGHT (-x) per request.) The thumb's base joint
#    frame differs from the fingers', so no named axis aims it -- tuned empirically (PoseLab).
NAME_HAND = {"Thumb": 1.0, "Index": 0.8, "Middle": 1.0, "Ring": 1.0, "Little": 1.0,
             "_base_bend": ["Index", "Thumb"], "_thumb_axis": [0.7, -0.47, 0.0]}

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

# HELP: a "thumbs-up served on a plate", decoded from the ISLRTC reference
# (ISL_dictionary/Help.mp4). The RIGHT hand makes a thumbs-up (GOOD's handshape)
# RESTING ON the upturned LEFT palm (a flat, level plate); the joined two-hand set
# traces a SEMICIRCULAR ARC that moves AWAY from the body -- from close in at the
# lower chest, UP-and-FORWARD to an apex, then DOWN-and-FORWARD, ending low and
# FARTHEST OUT (presented away) -- then returns to rest. Both hands move TOGETHER,
# keeping the stack. The path never comes back toward the body: forward reach (z)
# increases MONOTONICALLY at every key (0.17 -> 0.28), while height rises to the
# apex then falls. On this rig the elbow is pinned back (z~0.17), so reaching FAR
# forward forces the hand LOW -- hence the apex is up-but-near and the end is
# low-but-far, which is exactly "up+forward then down+forward". (On the shipped
# near-frontal camera the vertical rise/fall reads most; the forward travel reads
# as the arms visibly extending away.)
#
# Two-handed stacking (Probe/PoseLab-solved, verified zoomed on the shipped camera
# at all five keys):
#  * LEFT flat plate: palm UP, fingers pointing FORWARD and LEVEL so the fist sits
#    ON it. Like NONE's plate, a plain FORWARD-90 palm-up roll leaves the fingers
#    pointing UP (into the fist); a RIGHT 95 pitch levels the palm across ALL the
#    arm poses, so ONE constant LeftWrist works for the whole arc.
#  * RIGHT thumbs-up, thumb held WORLD-UP at every key. GOOD's fixed wrist points
#    the thumb up only when the forearm is folded upright as in GOOD; across this
#    arc the forearm angle changes, so that same wrist would swing the thumb
#    forward/sideways. Instead each key's RightWrist is SOLVED: a raw axis-angle
#    PREFIX (from Probe, with GOOD's canonical thumbs-up marked as the orientation
#    TARGET -- full_rel = good_natural * key_natural^-1) makes the hand's world
#    orientation MATCH GOOD's at that key, then GOOD's own [UP -90, RIGHT 40] suffix
#    builds the thumbs-up on top. The thumb points up the whole way through.
#  * RESTS ON THE PALM CENTRE, no float, no clip: the LEFT wrist sits at a CONSTANT
#    world offset from the RIGHT fist bottom (RightLittleDistal) at EVERY key --
#    left_wrist = fist + (-0.0165, -0.025, -0.048). That offset was solved SURFACE-
#    first, not bone-first: an earlier version placed the left wrist a fixed drop
#    UNDER the fist BONE (RightLittleDistal, which is curled INTO the palm, ~2cm
#    above the true fist mesh bottom) and a fixed z, which parked the fist over the
#    palm HEEL/wrist ~2cm BEHIND the palm centre AND actually intersecting at the low
#    keys -- and it only LOOKED fine because it was checked on the near-frontal
#    shipped camera, which compresses depth and hides both errors. The current offset
#    was dialled from a SIDE + BELOW camera (which reveal z/contact) so the fist sits
#    lightly ON the palm CENTRE, centred at x~0, no sink. Because BOTH hands hold a
#    constant world orientation across the arc (right thumb-up matched to GOOD per
#    key, left plate a constant LeftWrist), one constant wrist offset keeps the fist
#    on the same palm spot the whole way -- so the offset is the RIGID relative pose.
#    Left arm angles per key were Newton-solved (K4 Jacobian) to hold this offset to
#    +-1mm across all 9 keys; verify a change from SIDE/BELOW, never the shipped cam.
# RANGE: this is the "prominent" arc -- height sweeps ~1.14 -> ~1.43 (apex, upper
# chest) -> ~1.10, and forward reach ~0.14 -> ~0.29 (the rig's centred max; the
# elbow is pinned back so it can't reach further while staying centred). NOTE ON
# CAMERA: on the near-frontal telephoto shipped camera the big up/down reads
# strongly, but "forward" is the camera's depth axis and shows mostly as the ARM
# EXTENDING toward the viewer (forearm foreshortening, fold->straight from START to
# END) + the hand growing ~10%; a literal on-screen forward TRANSLATION is not
# possible from a frontal camera (see the projection analysis in the chat log).
# HELP carries NO default emotion (informational, like most words); the caller/LLM
# can still tag it per utterance.
_HELP_THUMB = {"Thumb": -0.5, "_thumb_axis": "BACK",  # GOOD's extra-straight thumbs-up
               "Index": 1.0, "Middle": 1.0, "Ring": 1.0, "Little": 1.0}
_HELP_LWRIST = [{"axis": "FORWARD", "angle": 90}, {"axis": "RIGHT", "angle": 95}]  # flat palm-up plate
def _help_key(r_up, r_lo, wrist_axis, wrist_ang, l_up, l_lo):
    # r_up/l_up = (RIGHT elevation, UP yaw-to-centre) of the upper arm; r_lo/l_lo =
    # (RIGHT fold, UP steer) of the forearm. wrist_axis/wrist_ang = the Probe-solved
    # per-key orientation prefix; the [UP -90, RIGHT 40] suffix is GOOD's own wrist.
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": r_up[0]}, {"axis": "UP", "angle": r_up[1]}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": r_lo[0]}, {"axis": "UP", "angle": r_lo[1]}],
        "RightWrist": [{"axis": wrist_axis, "angle": wrist_ang},
                       {"axis": "UP", "angle": -90}, {"axis": "RIGHT", "angle": 40}],
        "curl_right": _HELP_THUMB,
        "LeftUpperArm": [{"axis": "RIGHT", "angle": l_up[0]}, {"axis": "UP", "angle": l_up[1]}],
        "LeftLowerArm": [{"axis": "RIGHT", "angle": l_lo[0]}, {"axis": "UP", "angle": l_lo[1]}],
        "LeftWrist": _HELP_LWRIST,
        "curl_left": FLAT,
    }
# NINE keys along the away-arc. Two things make the two-hand group hold together:
#  (1) RIGID RELATIVE POSE. The left wrist sits at a CONSTANT offset from the RIGHT
#      FIST BOTTOM at EVERY key -- left_wrist = fist(RightLittleDistal) +
#      (-0.0165, -0.025, -0.048) -- Newton-solved (K4 Jacobian) so the measured
#      offset holds to +-1mm across all 9 keys, instead of a per-key target that
#      drifted ~3cm (the left visibly slid vs the right = "left moving faster").
#      With a fixed offset (and both hands' world orientation held constant -- the
#      right thumb-up matched to GOOD per key, the left plate a constant LeftWrist),
#      the fist keeps the same spot on the palm centre the whole way.
#  (2) DENSITY. Interpolation is LINEAR-per-segment (SignDirector._sample_word), so
#      even with a fixed offset AT the keys the two hands trace slightly different
#      curves BETWEEN them and can separate mid-segment. Nine closely-spaced keys
#      (~0.09 apart) keep that between-key drift tiny -- verified on between-key
#      frames, the fist rests on the palm throughout (not just at the keys). This
#      also gives the fluid, corner-free curve.
# The offset was tuned by render so the fist rests JUST ON TOP of the palm centre
# (~1-2cm, no float, no intersection). Right-fist world pos noted per key. z
# (forward) rises ~0.15->0.24 (K8 farthest, presented away); y rises to the apex
# (~1.42, upper chest) then falls to a RAISED low end (~1.20, not the waist).
_HELP_K0 = _help_key((10, 80), (-70, 55), [0.1027, -0.343, 0.9337], 66.1, (5.9, -82.4), (-54, -48.2))    # (-0.005,1.217,0.147) near+low
_HELP_K1 = _help_key((6, 80), (-86, 55), [-0.0107, -0.4887, 0.8724], 51, (9.0, -81.8), (-78, -46.3))    # (0.003,1.291,0.162) rising
_HELP_K2 = _help_key((-2, 80), (-102, 55), [-0.1562, -0.7529, 0.6394], 36.59, (2.3, -83.4), (-94, -43.2))  # (-0.004,1.374,0.187)
_HELP_K3 = _help_key((-10, 80), (-102, 55), [-0.0771, -0.8616, 0.5018], 31.89, (-0.1, -84.5), (-102, -44.7))  # (0.001,1.408,0.188)
_HELP_K4 = _help_key((-18, 80), (-94, 45), [0.0177, -0.7395, 0.6729], 21.42, (-4.0, -80.9), (-102, -40.2))  # (0.017,1.425,0.22) apex (upper chest)
_HELP_K5 = _help_key((-2, 80), (-102, 45), [-0.2686, -0.5965, 0.7564], 29.79, (-3.4, -81.6), (-86, -34.1))  # (-0.009,1.375,0.228)
_HELP_K6 = _help_key((2, 80), (-87, 40), [-0.1044, -0.2481, 0.9631], 41.08, (11.2, -87.0), (-86, -27.6))  # (0.006,1.311,0.232) descending
_HELP_K7 = _help_key((6, 80), (-78, 35), [-0.0641, -0.0777, 0.9949], 51.81, (9.4, -87.7), (-70, -22.1))  # (-0.001,1.262,0.246)
_HELP_K8 = _help_key((6, 80), (-60, 35), [0.0547, -0.0169, 0.9984], 68.14, (-7.3, -74.2), (-30, -40.7))  # (0,1.197,0.241) raised-low + farthest out
# Even ~0.09 spacing -> steady speed; the single global ease (SignDirector
# ._ease_progress) accelerates from and decelerates to rest, so no per-key stops.
HELP_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.09, **NEUTRAL_POSE, **_HELP_K0},   # hands meet, near the body + low
    {"t": 0.18, **NEUTRAL_POSE, **_HELP_K1},   # rising, forward
    {"t": 0.27, **NEUTRAL_POSE, **_HELP_K2},
    {"t": 0.36, **NEUTRAL_POSE, **_HELP_K3},
    {"t": 0.45, **NEUTRAL_POSE, **_HELP_K4},   # apex: up and forward
    {"t": 0.54, **NEUTRAL_POSE, **_HELP_K5},
    {"t": 0.63, **NEUTRAL_POSE, **_HELP_K6},   # descending, still forward
    {"t": 0.72, **NEUTRAL_POSE, **_HELP_K7},
    {"t": 0.80, **NEUTRAL_POSE, **_HELP_K8},   # end: raised-low + farthest out (presented away)
    {"t": 0.88, **NEUTRAL_POSE, **_HELP_K8},   # brief hold on the offer
    {"t": 1.0, **NEUTRAL_POSE},
]

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
#
# TUNING PASSES (v1 snapshot kept in backups/2026-07-21-me-v1/):
#  - v2 "very slightly reduce the wrist bend + point the finger a touch down": rotate
#    the AIM only (local-X target), then re-solve the same palm->-X roll -- unfold ~6 deg
#    toward the forearm and pitch the tip down ~8 deg (delta 115.55 -> 107.59).
#  - v3 "index slightly more down": pitch the aim a further ~5 deg down and re-solve the
#    palm->-X roll again (delta -> 104.57). Bend stays ~86 deg (unchanged look); the tip
#    ends a touch lower and nearer the chest.
#  - v3 thumb: the shared POINT thumb (curl 0.6 about the default UP axis) read as a
#    BROKEN half-curled stub laid across the dorsum. Fixed with a ME-LOCAL handshape
#    (_ME_POINT, so YOU's shared POINT is untouched). Curl 0 = the thumb's NATURAL REST
#    (undeflected) -- it sits straight and stands up alongside the index, which is the
#    "straight thumb" the user wanted. A first attempt over-corrected with a strong
#    negative curl (~-0.9): that EXTENDS the thumb past straight and HYPEREXTENDS it
#    backward off the dorsum (bent too far the OTHER way). So the thumb is left at 0 --
#    dead straight, no bend in either direction. Four fingers unchanged: index straight
#    (the point), other three closed. (_thumb_axis is a no-op at curl 0, so it's dropped.)
_ME_WRIST = [{"axis": [0.4507, 0.8927, -0.0011], "angle": 104.57}]
_ME_POINT = {"Thumb": 0.0, "Index": 0.0, "Middle": 0.95, "Ring": 0.95, "Little": 0.95}
_ME_TOUCH = {   # index fingertip TOUCHING the centre of the chest   tip ~(0.03, 1.35, 0.15)
    "RightUpperArm": [{"axis": "RIGHT", "angle": -12}, {"axis": "UP", "angle": 66}],
    "RightLowerArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 44}],
    "RightWrist": _ME_WRIST,
    "curl_right": _ME_POINT,
}
_ME_LIFT = {    # fingertip bobbed ~3.5 cm UP off the chest (the tap gap)   tip ~(0.00, 1.39, 0.16)
    "RightUpperArm": [{"axis": "RIGHT", "angle": -18}, {"axis": "UP", "angle": 66}],
    "RightLowerArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 44}],
    "RightWrist": _ME_WRIST,
    "curl_right": _ME_POINT,
}
ME_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.34, **NEUTRAL_POSE, **_ME_TOUCH},   # rise, form the point, first tap on the chest
    {"t": 0.48, **NEUTRAL_POSE, **_ME_LIFT},    # lift up-off the chest (tap gap)
    {"t": 0.62, **NEUTRAL_POSE, **_ME_TOUCH},   # second tap
    {"t": 0.80, **NEUTRAL_POSE, **_ME_TOUCH},   # hold "me" on the chest so the point reads
    {"t": 1.0, **NEUTRAL_POSE},
]

# TODAY: the dominant hand makes an index-point ("1", other fingers + thumb closed)
# held in front of the chest with the INDEX POINTING STRAIGHT DOWN, bobbing UP-AND-DOWN
# a couple of times ("this day / right now, here"), per the ISLRTC reference
# (ISL_dictionary/Today.mp4, decoded frame-by-frame): the hand rises to mid-chest, the
# index points down at the torso, and taps down twice.
# GEOMETRY (PoseLab-solved): the arm reaches OUT slightly DIAGONALLY (per user) -- the
# upper arm swings out (UP 56, down from 66) and the elbow is opened (LowerArm RIGHT -46,
# from -58), so the hand sits out to the avatar's right + forward instead of tucked at
# centre-chest. The index in that pose naturally points ACROSS the body (+x), so the wrist
# rolls FORWARD 90 to rotate the whole hand DOWN (index at the floor), THEN adds a world
# UP +30 TWIST -- an anticlockwise turn seen from ABOVE (right-hand rule about +Y) -- to
# roll the hand as the user asked. (An earlier "solved palmar-flexion" wrist, raw axis
# ~112 deg, read WORSE and was reverted -- keep the FORWARD-90-plus-UP-twist form. The
# pre-twist / pre-extend version is snapshotted in backups/2026-07-21-today-v1/.)
# The BOB is driven ENTIRELY by the upper-arm RIGHT angle (more negative = higher on this
# rig): high -37 (hand y~1.39) <-> low -20 (hand y~1.28), ~10cm, in the mid/upper-chest
# region (raised ~4.5cm per user "slightly up"). Forearm fold + wrist held CONSTANT across
# every key, so the index keeps pointing straight down through the whole bob (verified both
# extremes: IndexDistal ~14cm below the wrist). Handshape = ONE (thumb closed about BACK).
_TODAY_WRIST = [{"axis": "FORWARD", "angle": 90}, {"axis": "UP", "angle": 30}]
def _today_key(up_right):
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": up_right}, {"axis": "UP", "angle": 56}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -46}, {"axis": "UP", "angle": 44}],
        "RightWrist": _TODAY_WRIST,
        "curl_right": ONE,
    }
TODAY_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.26, **NEUTRAL_POSE, **_today_key(-37)},   # rise, form the point: index down at the chest (high)
    {"t": 0.40, **NEUTRAL_POSE, **_today_key(-20)},   # tap DOWN
    {"t": 0.54, **NEUTRAL_POSE, **_today_key(-37)},   # back up
    {"t": 0.68, **NEUTRAL_POSE, **_today_key(-20)},   # tap DOWN again
    {"t": 0.82, **NEUTRAL_POSE, **_today_key(-37)},   # settle (up)
    {"t": 1.0, **NEUTRAL_POSE},
]

# YESTERDAY: one hand raised beside the CHEEK with the index finger pointing UP (ONE
# handshape); the finger then BENDS/HOOKS down to close into a FIST in place -- "the day
# behind." Decoded frame-by-frame from the ISLRTC reference (ISL_dictionary/Yesterday.mp4):
# the hand rises to the cheek with the index up, the index curls down into a closed fist
# and straightens back up, hooking down TWICE (two up-and-down bends) before it lowers.
# The hand does NOT travel during the curl -- only the
# fingers close (like TODAY's fixed-hand bob) -- so the arm pose is IDENTICAL at every held
# key and ONLY curl_right changes (ONE -> FIST_TIGHT). Because both shapes fold the thumb
# the same way (curl 1.1 about BACK), the thumb stays closed throughout and just the index
# hooks from straight (0) to closed (1), which reads as the finger bending down.
# GEOMETRY (Probe/PoseLab-solved): cheek anchor RightUpperArm [RIGHT -52, UP 86] +
# RightLowerArm [RIGHT -120, UP 30] -> hand ~(-0.10, 1.56, 0.28) beside the cheek, the ONE
# index pointing straight UP (tip ~(-0.14, 1.71, 0.31), ~14 cm above the hand). No wrist
# delta: fist/finger orientation is inherited from the forearm, and from the shipped
# ~19deg-off camera the back of the hand faces the viewer (verified in PoseLab). Emotion
# NEUTRAL (a temporal word carries none, like TODAY) -- no _WORD_DEFAULT_EMOTION entry.
def _yesterday_key(curl):
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": -52}, {"axis": "UP", "angle": 86}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -120}, {"axis": "UP", "angle": 30}],
        "curl_right": curl,
    }
YESTERDAY_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.20, **NEUTRAL_POSE, **_yesterday_key(ONE)},         # rise: index up beside the cheek
    {"t": 0.32, **NEUTRAL_POSE, **_yesterday_key(ONE)},         # hold the index up
    {"t": 0.48, **NEUTRAL_POSE, **_yesterday_key(FIST_TIGHT)},  # index HOOKS down into a fist (bend 1)
    {"t": 0.62, **NEUTRAL_POSE, **_yesterday_key(ONE)},         # index straightens back UP
    {"t": 0.78, **NEUTRAL_POSE, **_yesterday_key(FIST_TIGHT)},  # index HOOKS down again (bend 2)
    {"t": 0.88, **NEUTRAL_POSE, **_yesterday_key(FIST_TIGHT)},  # hold the fist at the cheek
    {"t": 1.0, **NEUTRAL_POSE},
]

# KNOW: a FLAT four-finger hand whose fingertips TAP the TEMPLE -- "it's in my head."
# Matches the ISLRTC reference (ISL_dictionary/Know.mp4): a flat B-hand (ALL FOUR fingers
# extended and together, NOT a fist, NOT a single index) raised to the side of the
# forehead, the fingertips touching the temple, with a small in/out tap; the hand then
# withdraws with the fingers still extended (it does NOT close into a fist).
# (REWRITTEN 2026-07-22, twice. v1 was a four-finger "bent-B" edge-on hand -- read as a
# fist floating beside the head, never touching. v2 corrected to a single index point
# (ONE) with a lateral tap -- but that was ALSO wrong on two counts the user caught:
# (a) it's NOT just the index, all four fingers point at the head; (b) the "tap" swung the
# UPPER arm, which flaps the ELBOW sideways instead of moving the HAND toward/away from the
# head. Don't revert to either -- not the bent-B/_base_bend machinery, not the ONE handshape,
# not an upper-arm/elbow-sway tap.)
#  * HANDSHAPE = FLAT (all four fingers straight at 0.0, together; thumb 0.15). A forearm
#    TWIST -- a world-UP RightWrist roll of -60 -- turns the flat hand so the PALM faces the
#    SIDE OF THE FACE (palm toward the head), the hand lying flat against the temple. The
#    fingertips sit at the temple; fingers stay FLAT the whole time, including the withdrawal
#    (never fisted).
#  * PLACE = the hand sits at the SIDE of the face at temple height (wrist below the temple,
#    at cheek/eye level) so the up-pointing fingertips land on the temple/outer brow. Same
#    trap as HELLO/DRINK: getting the tips TO the temple needs the wrist BELOW it -- a
#    forearm that puts the WRIST at forehead height sends the fingers up OVER the head.
#  * THE TAP moves the HAND toward/away from the head, NOT the elbow. It's driven by the
#    LOWER arm's UP yaw (upper arm FIXED, so the elbow stays put): TOUCH 86 presses the
#    fingertips to the temple, LIFT 79 swings the forearm so the hand lifts ~2-3 cm
#    out/forward off the temple, then back. (Probe-confirmed: across lower-arm UP the elbow
#    stays at (-0.211,1.407,0.260) while the hand moves in/out -- the earlier upper-arm tap
#    instead flapped the elbow sideways, which read as a wrong "elbow sway".)
# GEOMETRY (Probe/PoseLab-solved): RightUpperArm [RIGHT -82, UP 46] (fixed), RightLowerArm
# [RIGHT -98, UP 86 touch / 79 lift], RightWrist roll UP -60 (the forearm twist that turns
# the palm to face the side of the face). TOUCH lands the wrist at ~(-0.170,1.600,0.074) with
# the flat fingertips on the temple. Emotion NEUTRAL (informational, like TODAY/YESTERDAY)
# -- no _WORD_DEFAULT_EMOTION entry.
_KNOW_FLAT = {"Thumb": 0.15, "Index": 0.0, "Middle": 0.0, "Ring": 0.0, "Little": 0.0}
def _know_key(lo_yaw):
    # lo_yaw is the LOWER-arm UP yaw: 86 = fingertips ON the temple, 79 = lifted off.
    # The upper arm is FIXED so the elbow does not move -- only the hand travels in/out.
    # RightWrist UP -60 twists the forearm so the PALM faces the SIDE OF THE FACE.
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": -82}, {"axis": "UP", "angle": 46}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": lo_yaw}],
        "RightWrist": [{"axis": "UP", "angle": -60}],
        "curl_right": _KNOW_FLAT,
    }
_KNOW_TOUCH = _know_key(86)   # flat fingertips ON the temple
_KNOW_LIFT = _know_key(79)    # hand lifted ~2-3 cm out/forward off the temple (elbow fixed)
KNOW_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.24, **NEUTRAL_POSE, **_KNOW_TOUCH},   # rise, fingertips to the temple (touch 1)
    {"t": 0.40, **NEUTRAL_POSE, **_KNOW_LIFT},    # fingertips lift off (hand moves out, elbow still)
    {"t": 0.54, **NEUTRAL_POSE, **_KNOW_TOUCH},   # press back to the temple (touch 2)
    {"t": 0.72, **NEUTRAL_POSE, **_KNOW_TOUCH},   # brief hold
    {"t": 1.0, **NEUTRAL_POSE},
]

# NAME: the hand held PALM-FLAT-FORWARD (palm area vector at the viewer) with the INDEX
# bent forward + the THUMB base-bent forward (NAME_HAND, other three fisted), drawn
# HORIZONTALLY across the FULL width of the body, from the avatar's LEFT to its RIGHT --
# like highlighting a line of text / drawing the top edge of a text-box. AUTHORED FROM THE
# USER'S DESCRIPTION of this ISL variant, NOT decoded from a reference video: the
# ISL_dictionary clip in hand ("Name (Sign 2)") shows a DIFFERENT form (an index+thumb
# hook raised to the temple then drawn down), so this is a distinct, reference-text-based
# sign (like SORRY / I-ME).
# MOTION (per the user): (1) QUICKLY raise the right hand across to the avatar's LEFT,
# forming the handshape; (2) SLOWLY drag it LEFT->RIGHT across the whole body; (3) drop
# back to rest. The slow drag gets the bulk of the time so the "highlight" reads.
# GEOMETRY (Probe/PoseLab-solved): the drag is mostly an UPPER-ARM YAW at CONSTANT
# elevation (RIGHT -19), with the elbow fold OPENING as the hand crosses to the avatar's
# left and TIGHTENING as it reaches to the right -- so HEIGHT stays ~flat (y 1.34 -> 1.39)
# the whole way, the horizontal line the sign needs. UP yaw 115 -> 40 (fold -66 -> -82)
# walks the hand x +0.20 -> -0.32 (~0.51 m, the widest cross-body reach the right arm can
# make at chest height while STAYING FORWARD OF THE CHEST -- reaching further to the
# avatar's left drives the hand behind the chest plane, z<0.1, and it clips the torso).
# The forward reach (z) naturally arcs 0.16 (left) -> 0.39 (right); on the near-frontal
# shipped camera that depth arc barely shows, so it still reads as a horizontal drag.
# WRIST -- SOLVED PER KEYFRAME: keeping the palm flat-forward while the upper arm yaws needs
# a DIFFERENT wrist at every key (a single fixed world-wrist would rotate the palm away from
# forward as the arm swings, since the palm-forward orientation is NOT invariant under the
# yaw). Each key's raw [x,y,z] axis-angle maps that pose's natural hand basis to
# (fingers->up, palm normal->+z at the viewer), computed from the measured natural basis at
# each pose (PoseLab). SignDirector slerps between them; consecutive solves share a near-
# identical axis so the palm stays ~forward the whole drag. Emotion NEUTRAL (naming carries
# none) -- no _WORD_DEFAULT_EMOTION entry.
def _name_key(up, fold, wax, wang):
    return {
        "RightUpperArm": [{"axis": "RIGHT", "angle": -19}, {"axis": "UP", "angle": up}],
        "RightLowerArm": [{"axis": "RIGHT", "angle": fold}, {"axis": "UP", "angle": 10}],
        "RightWrist": {"axis": wax, "angle": wang},
        "curl_right": NAME_HAND,
    }
# (up_yaw, fold, wrist_axis, wrist_angle) per key, avatar-LEFT -> avatar-RIGHT.
_NAME_L = (115, -66, [-0.5958, -0.8006,  0.0632], 165.63)  # left end (avatar's left)
_NAME_2 = (100, -68, [-0.5979, -0.8012, -0.0232], 154.20)
_NAME_C = ( 85, -71, [-0.5866, -0.8019, -0.1135], 142.88)  # centre
_NAME_4 = ( 66, -74, [-0.5673, -0.7919, -0.2263], 128.21)
_NAME_R = ( 40, -82, [-0.4856, -0.7833, -0.3882], 108.28)  # right end (avatar's right)
NAME_SIGN = [
    {"t": 0.0, **NEUTRAL_POSE},
    {"t": 0.16, **NEUTRAL_POSE, **_name_key(*_NAME_L)},  # QUICK: swing across to the avatar's LEFT, hand formed
    {"t": 0.24, **NEUTRAL_POSE, **_name_key(*_NAME_L)},  # brief beat at the left end
    {"t": 0.40, **NEUTRAL_POSE, **_name_key(*_NAME_2)},  # SLOW drag left -> right ...
    {"t": 0.54, **NEUTRAL_POSE, **_name_key(*_NAME_C)},
    {"t": 0.68, **NEUTRAL_POSE, **_name_key(*_NAME_4)},
    {"t": 0.82, **NEUTRAL_POSE, **_name_key(*_NAME_R)},  # ... to the avatar's RIGHT end
    {"t": 0.88, **NEUTRAL_POSE, **_name_key(*_NAME_R)},  # brief beat at the right end
    {"t": 1.0, **NEUTRAL_POSE},                          # back down to rest
]

WORD_SIGNS = {
    # NAME: palm-forward hand, index bent forward + thumb base-bent forward, drawn
    # horizontally across the body left->right (see NAME_SIGN).
    "name": NAME_SIGN,
    # KNOW: a flat four-finger hand tapping the temple -- "it's in my head" (see KNOW_SIGN).
    "know": KNOW_SIGN,
    # TODAY: index-point bobbed down at the chest (see TODAY_SIGN).
    "today": TODAY_SIGN,
    # YESTERDAY: index-up at the cheek, then hooked closed into a fist (see YESTERDAY_SIGN).
    "yesterday": YESTERDAY_SIGN,
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
    # HELP: thumbs-up (right) served on the upturned left palm, scooped up-and-forward
    # (see HELP_SIGN).
    "help": HELP_SIGN,
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
    # (ISL_dictionary/Go.mp4). Reworked 2026-07-21 -- the previous pass (raise
    # beside the head, then a semicircular twist-and-arc to a palm-out-and-down
    # hold beside the head) did NOT match the reference; don't revert to it.
    # The real sign is a flat open hand (FLAT/B-hand) that reads in THREE beats:
    #   1. START -- hand raised to the face (chin/cheek), fingers pointing UP.
    #      Same raised-elbow-for-a-face-height-hand lesson as DRINK/PLEASE/HELLO;
    #      Probe-solved to (-0.167, 1.577, 0.111), jaw height, ~10cm from the head.
    #   2. DIP -- the hand drops to a CENTRED mid-chest point (~(-0.27, 1.21, 0.28))
    #      and the wrist rotates so the fingers point DOWN/forward, palm down. This
    #      is the bottom of the arc, not a pause -- the whole thing is one swoop.
    #   3. THRUST OUT -- the arm sweeps UP-and-OUT to the side, ending extended on
    #      a diagonal (hand above the shoulder, ~(-0.66, 1.63, 0.11)), palm facing
    #      FORWARD/away, fingers pointing up-and-out -- the "away you go" gesture.
    # The wrist FLIP from DIP (palm-down, fingers-down) to OUT (palm-forward,
    # fingers-up) is what sells it and happens across the up-and-out sweep. The rig
    # has no forearm-twist bone (RightLowerArm is just the elbow hinge), so the roll
    # is a world-UP-axis RightWrist delta whose *feel* depends on the current
    # forearm orientation (Basis.slerp between the keyframes' real 3-D orientations
    # is what matters, not the raw angle numbers): UP 120 at the START arm reads as
    # fingers-up-at-the-face; UP 0 at the DIP arm as fingers-down; UP -70 at the OUT
    # arm as palm-forward/fingers-up-out. All Probe-solved for positions +
    # PoseLab-verified for orientation, then rendered full-motion vs the reference.
    "go": [
        {"t": 0.0, **NEUTRAL_POSE},
        # 1. START: flat hand raised to the face, fingers up, palm facing BACK
        # toward the avatar's own face. The wrist roll is kept MODERATE (UP 40, not
        # the earlier 120) -- past ~60 the palm keeps rotating out to the avatar's
        # right and the wrist reads as an unnatural cocked-back hyperextension; UP 40
        # is the most roll that still leaves the palm facing the face (2026-07-21).
        {"t": 0.22, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -104}, {"axis": "UP", "angle": 86}],
            "RightWrist": {"axis": "UP", "angle": 40},
            "curl_right": FLAT},
        {"t": 0.34, **NEUTRAL_POSE,          # brief settle at the face before the swoop
            "RightUpperArm": [{"axis": "RIGHT", "angle": -66}, {"axis": "UP", "angle": 44}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -104}, {"axis": "UP", "angle": 86}],
            "RightWrist": {"axis": "UP", "angle": 40},
            "curl_right": FLAT},
        # 2. DIP: hand drops to centred mid-chest, wrist rotates fingers DOWN/forward.
        {"t": 0.50, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": 12}, {"axis": "UP", "angle": 30}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -70}, {"axis": "UP", "angle": 40}],
            "RightWrist": {"axis": "UP", "angle": 0},
            "curl_right": FLAT},
        # 3. THRUST OUT -> stop pointing FORWARD (2026-07-22, per user): instead of
        # flinging the arm up-and-out to the SIDE, the outward move stops when the
        # forearm/hand points FORWARD -- the direction the avatar faces, perpendicular
        # to the body -- with the upper arm (bicep) raised/extended outward. The hand
        # ends out in front at ~shoulder height (~(-0.30, 1.50, 0.43)), palm turned
        # FORWARD (same way the avatar faces). The wrist's flip (fingers-down at the
        # DIP -> palm-forward) completes over this leg and holds. (Earlier versions
        # ended out to the side: fully lateral ~(-0.66,1.63,0.11), then a toned-down
        # out-and-slightly-forward ~(-0.58,1.61,0.24) -- both replaced.)
        {"t": 0.66, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 30}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -45}, {"axis": "UP", "angle": 18}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": FLAT},
        {"t": 0.82, **NEUTRAL_POSE,          # hold the forward-pointing end so it reads
            "RightUpperArm": [{"axis": "RIGHT", "angle": -58}, {"axis": "UP", "angle": 30}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -45}, {"axis": "UP", "angle": 18}],
            "RightWrist": {"axis": "UP", "angle": -70},
            "curl_right": FLAT},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # WHY (Sign 2): the open, upturned questioning hand (ISL_dictionary/Why_(Sign_2).mp4).
    # An open SPREAD "5" hand (FIVE) is raised to in front of the chest, palm turned UP
    # and toward the signer with the fingers pointing UP-and-out and clearly splayed, and
    # given a small side-to-side questioning SHAKE, then lowered. It reads together with a
    # questioning FACE (the LLM tags the emotion; a question word normally lands "question").
    #
    # Two things had to come together (see the decode notes in CLAUDE.md):
    #  * THE HANDSHAPE HAD TO SPREAD. Every existing shape holds the fingers together or
    #    curls them; FIVE fans them apart with a NEGATIVE "_converge" (the CONE machinery
    #    run backwards -- see the FIVE comment). Light curl (~0.1) keeps it an open hand.
    #  * PALM-UP *AND* FINGERS-UP AT A LOW, CENTRED HAND is the "low+centred doesn't exist"
    #    trap (see DRINK): a vertical forearm (fingers naturally up) throws the hand out to
    #    the shoulder, while a low centred hand leaves the forearm pointing FORWARD (fingers
    #    forward, not up). The fix is a low forward-forearm pose (RightUpperArm FORWARD -26/
    #    UP 18, RightLowerArm RIGHT -98/UP 32 -> hand ~(-0.33, 1.25, 0.27), MID-CHEST, elbow
    #    tucked low by the side, slightly to the signer's right -- matching the reference,
    #    which holds the hand low and in front, NOT up at the shoulder) PLUS a wrist that
    #    both rolls the palm UP (FORWARD -90) and FLEXES the fingertips up (RIGHT -15): the
    #    fingertips ride ~6 cm above the wrist (Probe/PoseLab-solved, verified palm-up +
    #    fingers-up from the shipped camera). The SHAKE is a small UP-yaw oscillation of the
    #    upper arm (~+-4 deg) paired with a tiny wrist-roll wobble, so the whole open hand
    #    jiggles side-to-side in place while held -- the questioning tremble, not a travel path.
    "why": [
        {"t": 0.0, **NEUTRAL_POSE},
        # Rise to the open palm-up questioning hand, low and in front of the chest.
        {"t": 0.28, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 18}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -15}],
            "curl_right": FIVE},
        # Questioning shake: a WIDE side-to-side swing (upper-arm UP +-10, wrist roll
        # +-7) so the open hand rocks clearly left-and-right -- a bigger, more emphatic
        # "why?!" than the earlier subtle +-4 tremble.
        {"t": 0.40, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 28}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -22}],
            "curl_right": FIVE},
        {"t": 0.52, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 8}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -8}],
            "curl_right": FIVE},
        {"t": 0.64, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 28}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -22}],
            "curl_right": FIVE},
        {"t": 0.76, **NEUTRAL_POSE,
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 9}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -9}],
            "curl_right": FIVE},
        {"t": 0.86, **NEUTRAL_POSE,          # settle back to the base hold before lowering
            "RightUpperArm": [{"axis": "FORWARD", "angle": -26}, {"axis": "UP", "angle": 18}],
            "RightLowerArm": [{"axis": "RIGHT", "angle": -98}, {"axis": "UP", "angle": 32}],
            "RightWrist": [{"axis": "FORWARD", "angle": -90}, {"axis": "RIGHT", "angle": -15}],
            "curl_right": FIVE},
        {"t": 1.0, **NEUTRAL_POSE},
    ],
    # Non-lexical function words (never played by the fixed gloss; kept so the
    # dataset is complete for export_word_signs.py).
    "are": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "going": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
    "to": [{"t": 0.0, **NEUTRAL_POSE}, {"t": 1.0, **NEUTRAL_POSE}],
}
