extends Node3D
## Sign-language prototype (hard-coded 3-sentence demo).
##
## Input is a single sentence that ENDS in a bracketed emotion, e.g.
##   "You are drinking tea tomorrow. (Happy)"
##   "Why are you drinking tea tomorrow? (Question)"
## The English word order is ignored: every supported sentence maps to the
## same ISL gloss -- TOMORROW TEA YOU DRINK -- played in gloss order, with the
## bracketed emotion held on the face/head. Parsing lives in _parse_request()
## so the web app and the CLI renderer share one implementation.
##
## Two entry points into the same animation code (_perform):
## 1. CLI/video (render_signs.py): a JSON config (`-- --config <path>`) carries
##    the raw sentence + the full per-word keyframe table; renders and quits.
## 2. Web (index.html): a JS bridge calls perform_web(rawSentence) with the
##    live text typed by the user; keyframes come from res://data/word_signs.json.
##
## Per-word keyframe data (the hand signs) comes from ../../sign_words.py and is
## NOT changed here -- the gloss only selects/reorders which signs play.

const FaceExpressions = preload("res://scripts/face_expressions.gd")
const HandRig = preload("res://scripts/hand_rig.gd")
const ArmRig = preload("res://scripts/arm_rig.gd")

const DEFAULT_SECONDS_PER_WORD := 2.8  # slow for now; real pace will be driven by speaking intensity later

# --- Hard-coded demo scope: 3 sample sentences -> one ISL gloss + a bracketed
# emotion. Every supported sentence maps to the SAME gloss (the English order
# is dropped, ISL reorders to TOMORROW TEA YOU DRINK and drops "are"/"why").
const SUPPORTED_EMOTIONS := ["question", "happy", "angry"]
const GLOSS := ["tomorrow", "tea", "you", "drink"]
const KNOWN_SENTENCES := {
	"why are you drinking tea tomorrow": GLOSS,
	"you are drinking tea tomorrow": GLOSS,
}

const AXES := {
	"RIGHT": Vector3.RIGHT,
	"UP": Vector3.UP,
	"FORWARD": Vector3.FORWARD,
	"BACK": Vector3.BACK,
}

# --- Realistic (Rocketbox) avatar support --------------------------------
# The Rocketbox FBX uses a 3ds-Max Biped skeleton. We rename its bones to our
# VRM convention at load (see _adapt_skeleton) so arm_rig/hand_rig/this script
# drive it with ZERO changes to the sign logic. Only the finger-curl axis and
# the camera framing differ, handled below.
const BIPED_MAP := {
	"Bip01 Pelvis": "Hips", "Bip01 Spine": "Spine", "Bip01 Spine1": "Chest",
	"Bip01 Spine2": "UpperChest", "Bip01 Neck": "Neck", "Bip01 Head": "Head",
	"Bip01 L Clavicle": "LeftShoulder", "Bip01 R Clavicle": "RightShoulder",
	"Bip01 L UpperArm": "LeftUpperArm", "Bip01 R UpperArm": "RightUpperArm",
	"Bip01 L Forearm": "LeftLowerArm", "Bip01 R Forearm": "RightLowerArm",
	"Bip01 L Hand": "LeftHand", "Bip01 R Hand": "RightHand",
	"Bip01 L Finger0": "LeftThumbMetacarpal", "Bip01 L Finger01": "LeftThumbProximal", "Bip01 L Finger02": "LeftThumbDistal",
	"Bip01 L Finger1": "LeftIndexProximal", "Bip01 L Finger11": "LeftIndexIntermediate", "Bip01 L Finger12": "LeftIndexDistal",
	"Bip01 L Finger2": "LeftMiddleProximal", "Bip01 L Finger21": "LeftMiddleIntermediate", "Bip01 L Finger22": "LeftMiddleDistal",
	"Bip01 L Finger3": "LeftRingProximal", "Bip01 L Finger31": "LeftRingIntermediate", "Bip01 L Finger32": "LeftRingDistal",
	"Bip01 L Finger4": "LeftLittleProximal", "Bip01 L Finger41": "LeftLittleIntermediate", "Bip01 L Finger42": "LeftLittleDistal",
	"Bip01 R Finger0": "RightThumbMetacarpal", "Bip01 R Finger01": "RightThumbProximal", "Bip01 R Finger02": "RightThumbDistal",
	"Bip01 R Finger1": "RightIndexProximal", "Bip01 R Finger11": "RightIndexIntermediate", "Bip01 R Finger12": "RightIndexDistal",
	"Bip01 R Finger2": "RightMiddleProximal", "Bip01 R Finger21": "RightMiddleIntermediate", "Bip01 R Finger22": "RightMiddleDistal",
	"Bip01 R Finger3": "RightRingProximal", "Bip01 R Finger31": "RightRingIntermediate", "Bip01 R Finger32": "RightRingDistal",
	"Bip01 R Finger4": "RightLittleProximal", "Bip01 R Finger41": "RightLittleIntermediate", "Bip01 R Finger42": "RightLittleDistal",
}
# Local axes a "curl" rotates about on the Biped rig (found by axis sweep;
# VRM default is RIGHT). The four fingers flex toward the palm about BACK
# (-Z); the thumb is oriented differently and tucks across the palm about UP.
# (+Z/FORWARD only splays the fingers straight -- it does NOT make a fist.)
const BIPED_FINGER_CURL_AXIS := Vector3.BACK
# UP curls the thumb TOWARD the fingers/index -- correct for pinch/ring shapes
# (tea's OK, please's PURSE). A fist needs the thumb tucked the OTHER way ACROSS
# the palm, which is a NEGATIVE thumb curl (rotate about -UP); see the FIST_*
# handshapes in sign_words.py. So the direction lives in the curl sign, per
# handshape, not in this global axis.
const BIPED_THUMB_CURL_AXIS := Vector3.UP

# --- Rig-adaptive resting neutral ----------------------------------------
# The arms-at-rest neutral baked into word_signs.json (sign_words.py's
# NEUTRAL_POSE) is authored for the Biped rig, whose IMPORT pose is already an
# A-pose -- so a modest FORWARD ~50 deg lowers the arms to the sides. The VRM
# ships a full T-POSE rest, so those same numbers leave its arms sticking out
# ~45 deg (and the raw import pose is worse: straight out). When driving the VRM
# we therefore SUBSTITUTE a deeper arms-down neutral (dialed in via PoseLabVRM)
# wherever a keyframe sits exactly at the Biped neutral -- fixing the resting
# stance AND the non-signing arm mid-sign, with the Biped avatar left untouched.
# Mirror of sign_words.py NEUTRAL_POSE's arm values -- kept in sync so the VRM
# substitution below can recognise a bone sitting at the Biped rest.
const BIPED_ARM_NEUTRAL := {
	"RightUpperArm": {"axis": "FORWARD", "angle": -44},
	"LeftUpperArm": {"axis": "FORWARD", "angle": 44},
	"RightLowerArm": {"axis": "FORWARD", "angle": 0},
	"LeftLowerArm": {"axis": "FORWARD", "angle": 0},
}
const VRM_ARM_NEUTRAL := {
	"RightUpperArm": [{"axis": "FORWARD", "angle": -82}, {"axis": "RIGHT", "angle": -8}],
	"LeftUpperArm": [{"axis": "FORWARD", "angle": 82}, {"axis": "RIGHT", "angle": -8}],
	"RightLowerArm": [{"axis": "FORWARD", "angle": -12}, {"axis": "RIGHT", "angle": -10}],
	"LeftLowerArm": [{"axis": "FORWARD", "angle": 12}, {"axis": "RIGHT", "angle": -10}],
}
const BIPED_NEUTRAL_CURL := 0.15
const VRM_NEUTRAL_CURL := 0.3

var _skeleton: Skeleton3D
var _mesh: MeshInstance3D
var _face_shape_indices := {}
var _hand_rig := HandRig.new()
var _arm_rig := ArmRig.new()
var _idle_t := 0.0
var _current_emotion := "relaxed"  # set per WORD; drives emotion head motion
var _current_intensity := 1.0      # 0..1 "degree" of the current word's emotion
var _is_biped := false             # true when driving the realistic Rocketbox avatar
var _bmap := {}                    # our-name -> actual bone name (Biped); empty for the VRM
var _word_signs_data := {}  # loaded lazily from res://data/word_signs.json
var _run_id := 0            # bumped on every perform_web() call so a new
                             # submission cancels whichever one is still playing
var _js_perform_callback  # must be kept alive (JavaScriptBridge.create_callback
                           # result is refcounted) for as long as JS can call it --
                           # a local var here would be GC'd as soon as _ready() returns
var _js_perform_gloss_callback  # kept alive for window.godotPerformGloss (see above)


func _ready() -> void:
	_skeleton = _find_skeleton()
	_adapt_skeleton()   # rename Biped bones -> our convention if this is the realistic avatar
	_mesh = _find_face_mesh()
	_face_shape_indices = FaceExpressions.index_shapes(_mesh.mesh)
	_hand_rig.build(_skeleton)
	_arm_rig.build(_skeleton)
	_frame_camera()
	if OS.has_feature("web"):
		_setup_web_bridge()
	else:
		_run()


# --- Avatar detection / adaptation ---------------------------------------

func _find_skeleton() -> Skeleton3D:
	var s := get_node_or_null("Avatar/GeneralSkeleton")
	if s is Skeleton3D:
		return s
	return _first_of_type(get_node("Avatar"), "Skeleton3D")


func _first_of_type(n: Node, cls: String) -> Node:
	if n == null:
		return null
	if n.is_class(cls):
		return n
	for c in n.get_children():
		var r := _first_of_type(c, cls)
		if r != null:
			return r
	return null


func _find_face_mesh() -> MeshInstance3D:
	var b := _skeleton.get_node_or_null("body")
	if b is MeshInstance3D:
		return b
	# else pick the MeshInstance3D carrying the most blend shapes (the face)
	var best: MeshInstance3D = null
	var best_n := -1
	var stack: Array = [get_node("Avatar")]
	while not stack.is_empty():
		var node = stack.pop_back()
		if node is MeshInstance3D and node.mesh != null and node.mesh.get_blend_shape_count() > best_n:
			best_n = node.mesh.get_blend_shape_count()
			best = node
		for c in node.get_children():
			stack.append(c)
	return best


func _adapt_skeleton() -> void:
	if _skeleton.find_bone("Bip01 L UpperArm") == -1:
		return  # already VRM-named (stylized avatar) -- nothing to adapt
	_is_biped = true
	# stop the imported take so it doesn't fight our pose/blend-shape overrides,
	# and put the skeleton at its rest pose so arm_rig's composition (which reads
	# each parent's live global pose) starts from the same frame the skin binds to
	var ap := _first_of_type(get_node("Avatar"), "AnimationPlayer")
	if ap != null:
		(ap as AnimationPlayer).stop()
		(ap as AnimationPlayer).active = false
	_skeleton.clear_bones_global_pose_override()
	_skeleton.reset_bone_poses()
	_skeleton.force_update_all_bone_transforms()
	# Do NOT rename bones: the mesh skin binds to bones BY NAME. Instead give the
	# rigs a VRM->Biped translation so they drive it with our sign logic unchanged.
	for biped_name in BIPED_MAP:
		_bmap[BIPED_MAP[biped_name]] = biped_name
	_arm_rig.set_name_map(_bmap)
	_hand_rig.set_name_map(_bmap)
	# Biped finger bones orient differently from the VRM -> fingers curl about
	# FORWARD, thumb tucks across the palm about UP.
	_hand_rig.set_finger_curl_axis(BIPED_FINGER_CURL_AXIS, BIPED_FINGER_CURL_AXIS, BIPED_THUMB_CURL_AXIS)


func _frame_camera() -> void:
	var head_idx := _skeleton.find_bone(_bmap.get("Head", "Head"))
	var chest_idx := _skeleton.find_bone(_bmap.get("Chest", "Chest"))
	if head_idx == -1 or chest_idx == -1:
		return
	var head_pos: Vector3 = _skeleton.global_transform * _skeleton.get_bone_global_pose(head_idx).origin
	var chest_pos: Vector3 = _skeleton.global_transform * _skeleton.get_bone_global_pose(chest_idx).origin
	var cam: Camera3D = $Camera3D
	# Signing-space framing. Rather than move the lens in close (which shrinks
	# nothing but badly foreshortens signs that reach *toward* the viewer --
	# you/drink/tomorrow -- and risks clipping the forward hand), we keep a
	# normal working distance and narrow the FOV (telephoto): that enlarges
	# the upper body to fill the frame AND flattens perspective so a forward
	# point reads as a point instead of collapsing into the hand. A small
	# sideways offset gives a gentle near-frontal 3/4 so forward reach still
	# shows some depth, while staying frontal enough to read as signing.
	# The realistic (Biped) avatar is taller and its signs range from the waist
	# up to above the head, so it needs a lower focus + a wider/further framing
	# than the stylized avatar.
	if _is_biped:
		cam.fov = 40.0
		var focus_b := head_pos.lerp(chest_pos, 0.5)
		cam.global_position = focus_b + Vector3(0.55, 0.04, 1.62)
		cam.look_at(focus_b, Vector3.UP)
	else:
		cam.fov = 41.0
		var focus := head_pos.lerp(chest_pos, 0.4)
		cam.global_position = focus + Vector3(0.55, 0.08, 1.4)
		cam.look_at(focus, Vector3.UP)


# Resolve a rotation axis that is EITHER a named axis string ("RIGHT"/"UP"/
# "FORWARD"/"BACK") or a raw [x,y,z] vector. The raw form lets a wrist aim the
# hand along an arbitrary solved direction (e.g. pointing a pursed cone straight
# up when the forearm sits at an odd angle -- see PLEASE).
func _resolve_axis(v, fallback: Vector3 = Vector3.RIGHT) -> Vector3:
	if v is Array and v.size() == 3:
		return Vector3(float(v[0]), float(v[1]), float(v[2])).normalized()
	if v is String:
		return AXES.get(v, fallback)
	return fallback


func _bone_delta_basis(kf: Dictionary, bone_name: String) -> Basis:
	if not kf.has(bone_name):
		return Basis.IDENTITY
	var p = kf[bone_name]
	# A bone value may be a single {axis, angle} rotation, or an ARRAY of them
	# composed in order (world-space, each pre-multiplied) -- needed on the
	# realistic Biped rig, where reaching e.g. the mouth requires raising AND
	# swinging the arm inward (two rotations on one bone).
	if p is Array:
		var db := Basis.IDENTITY
		for q in p:
			db = Basis(_resolve_axis(q.get("axis", "RIGHT")), deg_to_rad(float(q.get("angle", 0.0)))) * db
		return db
	var axis: Vector3 = _resolve_axis(p.get("axis", "RIGHT"))
	return Basis(axis, deg_to_rad(float(p.get("angle", 0.0))))


## Reads one hand's per-finger curl dict out of a keyframe ({"Thumb": 0-1,
## "Index": 0-1, "Middle": 0-1, "Ring": 0-1, "Little": 0-1}), defaulting
## missing fingers to 0.0 (open). Also accepts a plain number for
## backward-compatible "same curl on every finger" keyframes.
func _finger_curls(kf: Dictionary, side: String) -> Dictionary:
	var raw = kf.get("curl_left" if side == "Left" else "curl_right", {})
	var result := {}
	for finger in HandRig.FINGER_NAMES:
		if typeof(raw) == TYPE_DICTIONARY:
			result[finger] = float(raw.get(finger, 0.0))
		else:
			result[finger] = float(raw)
	# Optional per-handshape thumb curl axis (e.g. fists fold the thumb about BACK
	# to bring it across the PALM, while the global default UP suits pinch shapes).
	# Carried alongside the finger scalars so it flows through interpolation/apply.
	if typeof(raw) == TYPE_DICTIONARY and raw.has("_thumb_axis"):
		result["_thumb_axis"] = raw["_thumb_axis"]
	# Optional convergence (0..1): fans the fingertips to a point + opposes the
	# thumb, for pursed cone shapes (PLEASE). Carried alongside the curl scalars
	# so it flows through interpolation/apply like the thumb axis does.
	if typeof(raw) == TYPE_DICTIONARY and raw.has("_converge"):
		result["_converge"] = float(raw["_converge"])
	return result


func _lerp_finger_curls(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var result := {}
	for finger in HandRig.FINGER_NAMES:
		result[finger] = lerpf(float(a.get(finger, 0.0)), float(b.get(finger, 0.0)), t)
	# The thumb axis is a discrete choice, not a lerp-able value: snap to whichever
	# keyframe we're closer to (defaulting to the incoming one) so a handshape that
	# specifies BACK keeps it across the whole hold.
	var axis = b.get("_thumb_axis", a.get("_thumb_axis", null)) if t >= 0.5 else a.get("_thumb_axis", b.get("_thumb_axis", null))
	if axis != null:
		result["_thumb_axis"] = axis
	# Convergence IS lerp-able (a scalar) -- interpolate it so the cone forms
	# gradually as the hand rises and relaxes as it lowers back to the open bookend.
	result["_converge"] = lerpf(float(a.get("_converge", 0.0)), float(b.get("_converge", 0.0)), t)
	return result


## Samples a word's keyframe list at fraction (0-1) of that word's duration,
## returning {bone_name: delta Basis, "curl_left": per-finger dict,
## "curl_right": per-finger dict}.
func _sample_word(keyframes: Array, frac: float, sharpness: float = 0.0) -> Dictionary:
	var a: Dictionary = keyframes[0]
	var b: Dictionary = keyframes[0]
	var local_t := 0.0
	var last: Dictionary = keyframes[keyframes.size() - 1]
	if frac <= float(a.get("t", 0.0)):
		a = keyframes[0]
		b = a
	elif frac >= float(last.get("t", 1.0)):
		a = last
		b = last
	else:
		for i in range(keyframes.size() - 1):
			var ka: Dictionary = keyframes[i]
			var kb: Dictionary = keyframes[i + 1]
			var ta: float = float(ka.get("t", 0.0))
			var tb: float = float(kb.get("t", 1.0))
			if ta <= frac and frac <= tb:
				a = ka
				b = kb
				var span := tb - ta
				local_t = 0.0 if span <= 0.0 else (frac - ta) / span
				break
	# Interpolation WITHIN a segment is LINEAR (no per-segment easing). Easing is
	# applied ONCE to the whole word's progress in _perform_items (_ease_progress).
	# Easing each segment separately drove the pose to ZERO velocity at every
	# keyframe, so a multi-keyframe sign visibly stopped-and-restarted at each one
	# ("breaks" / non-constant speed). Linear per segment + one global ease keeps
	# the motion continuous. (sharpness is kept in the signature for callers but
	# is now folded into the global ease instead of applied here.)
	var sample := {}
	for bone_name in ArmRig.POSE_ORDER:
		var basis_a := _bone_delta_basis(a, bone_name)
		var basis_b := _bone_delta_basis(b, bone_name)
		sample[bone_name] = basis_a.slerp(basis_b, local_t)
	# The elbow is a hinge fixed to the UPPER arm's own orientation, not to a
	# world-space axis. Keyframes author each LowerArm bend as a world-axis
	# rotation (e.g. "RIGHT 60"), which only bends like a real elbow when the
	# upper arm is near its rest orientation -- once a sign swings the upper
	# arm through a large compound rotation (e.g. TEA's cup arm), that same
	# world axis no longer lines up with the forearm's hinge and the elbow
	# visibly bends the wrong way. Fix: conjugate the authored bend by the
	# upper arm's own delta so the hinge axis is carried along with the arm
	# instead of staying fixed in world space (derivation: this is the unique
	# delta_global that reproduces "bend at rest, THEN rotate rigidly with the
	# upper arm" through arm_rig's parent-relative composition).
	for side in ["Left", "Right"]:
		var upper: Basis = sample[side + "UpperArm"]
		var lower_raw: Basis = sample[side + "LowerArm"]
		sample[side + "LowerArm"] = upper * lower_raw * upper.inverse()
	for wrist_bone in ["LeftWrist", "RightWrist"]:
		var basis_a := _bone_delta_basis(a, wrist_bone)
		var basis_b := _bone_delta_basis(b, wrist_bone)
		sample[wrist_bone] = basis_a.slerp(basis_b, local_t)
	sample["curl_left"] = _lerp_finger_curls(_finger_curls(a, "Left"), _finger_curls(b, "Left"), local_t)
	sample["curl_right"] = _lerp_finger_curls(_finger_curls(a, "Right"), _finger_curls(b, "Right"), local_t)
	return sample


## Blend two whole pose samples (as returned by _sample_word) at t in 0..1:
## slerp every bone/wrist Basis, lerp the finger-curl dicts. Used to flow the END
## of one sign directly into the START of the next, without dipping to neutral.
func _lerp_samples(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var out := {}
	for key in a:
		var av = a[key]
		var bv = b.get(key, av)
		if key == "curl_left" or key == "curl_right":
			out[key] = _lerp_finger_curls(av, bv, t)
		elif av is Basis:
			out[key] = (av as Basis).slerp(bv, t)
		else:
			out[key] = bv
	return out


## True when a keyframe rotation spec `a` is exactly the single-rotation Biped
## neutral `b` (so we can tell "this arm is at rest" from "this arm is signing").
## The baked neutral is always a single {axis,angle} dict; an authored sign pose
## is either a different single rotation or a multi-rotation Array (never equal).
func _rot_eq(a, b) -> bool:
	if typeof(a) != TYPE_DICTIONARY or typeof(b) != TYPE_DICTIONARY:
		return false
	return String(a.get("axis", "")) == String(b.get("axis", "")) \
		and abs(float(a.get("angle", 0.0)) - float(b.get("angle", 0.0))) < 0.01


## Rewrite a loaded keyframe table in place for the current rig. Only the VRM
## needs it: wherever an arm bone / curl sits at the Biped resting neutral, swap
## in the VRM's deeper arms-down neutral so it hangs its arms naturally at rest
## and for the non-signing arm during a sign. Biped keyframes pass through
## unchanged (they were authored for that rig).
func _adapt_keyframes_for_rig(data: Dictionary) -> void:
	if _is_biped:
		return
	for word in data.keys():
		var kfs = data[word]
		if not (kfs is Array):
			continue
		for kf in kfs:
			if not (kf is Dictionary):
				continue
			for bone in BIPED_ARM_NEUTRAL:
				if kf.has(bone) and _rot_eq(kf[bone], BIPED_ARM_NEUTRAL[bone]):
					kf[bone] = (VRM_ARM_NEUTRAL[bone] as Array).duplicate(true)
			for curl_key in ["curl_left", "curl_right"]:
				var c = kf.get(curl_key, null)
				if typeof(c) != TYPE_DICTIONARY and c != null \
						and abs(float(c) - BIPED_NEUTRAL_CURL) < 0.001:
					kf[curl_key] = VRM_NEUTRAL_CURL


## Pose the avatar in its resting neutral immediately, so it isn't frozen in its
## raw import pose (a full T-pose on the VRM) while idle/waiting for input. Any
## word's first keyframe (t=0) is that neutral, already rig-adapted on load.
func _apply_rest_pose() -> void:
	var data := _load_word_signs()
	for word in data.keys():
		var kfs = data[word]
		if kfs is Array and not (kfs as Array).is_empty():
			_current_emotion = "relaxed"
			_current_intensity = 1.0
			_apply_sample(_sample_word(kfs, 0.0, 0.0))
			return


func _apply_sample(sample: Dictionary) -> void:
	var bob := sin(_idle_t * 1.6) * 0.01
	# Layer emotion-driven HEAD motion on top of the sign's own head pose. Head
	# is a bone (not a blend shape), so this carries to ANY humanoid rig -- and
	# on the current avatar it's the main way Question/Happy read at all, since
	# this avatar has no isolated brow/cheek blend shapes (see _perform note).
	var head_extra := _emotion_head_delta()
	if head_extra != Basis.IDENTITY:
		sample["Head"] = head_extra * (sample["Head"] as Basis)
	_arm_rig.apply(sample, bob)
	var wrist_deltas := {"Left": sample["LeftWrist"], "Right": sample["RightWrist"]}
	# Per-handshape thumb curl axis (fists carry "_thumb_axis": "BACK"); default to
	# the rig's global thumb axis for hands that don't specify one.
	var thumb_axes := {}
	var converge := {}
	for side in ["Left", "Right"]:
		var c = sample["curl_left" if side == "Left" else "curl_right"]
		if typeof(c) == TYPE_DICTIONARY and c.has("_thumb_axis"):
			thumb_axes[side] = AXES.get(String(c["_thumb_axis"]), _hand_rig.get_thumb_curl_axis())
		if typeof(c) == TYPE_DICTIONARY and c.has("_converge"):
			converge[side] = float(c["_converge"])
	_hand_rig.apply_fingers({"Left": sample["curl_left"], "Right": sample["curl_right"]}, 0.0, wrist_deltas, thumb_axes, converge)


# Emotion-driven HEAD motion, scaled by the current word's intensity (0..1) so a
# stronger "degree" of emotion reads as more head movement. Happy nods gently;
# Question cocks the head (stand-in for a raised brow); Angry gives a sharp,
# faster downward jut at high intensity; Sad droops; Surprised lifts/recoils.
func _emotion_head_delta() -> Basis:
	var i := clampf(_current_intensity, 0.0, 1.0)
	match _current_emotion:
		"happy":
			return Basis(Vector3.RIGHT, deg_to_rad(sin(_idle_t * 3.0) * 5.0 * i))
		"question":
			return Basis(Vector3.FORWARD, deg_to_rad(11.0 * (0.4 + 0.6 * i)))
		"angry":
			# sharp, quick assertive jut down; more intensity -> deeper and faster
			return Basis(Vector3.RIGHT, deg_to_rad((3.0 + 6.0 * i) * (0.5 + 0.5 * sin(_idle_t * (5.0 + 4.0 * i)))))
		"sad":
			return Basis(Vector3.RIGHT, deg_to_rad(9.0 * i))       # head droops down
		"surprised":
			return Basis(Vector3.RIGHT, deg_to_rad(-7.0 * i))      # head lifts back
		"sarcasm":
			# lazy sideways head cock with a slow sway -- the "oh, sure" tilt
			return Basis(Vector3.FORWARD, deg_to_rad((6.0 + 3.0 * sin(_idle_t * 1.4)) * (0.4 + 0.6 * i)))
		"pleading":
			# head tips gently forward/down -- the imploring "please" bow, deeper
			# with intensity, with a faint slow beg-nod
			return Basis(Vector3.RIGHT, deg_to_rad((5.0 + 5.0 * i) + 2.0 * sin(_idle_t * 1.8)))
		_:
			return Basis.IDENTITY


# --- Per-word emotion dynamics ------------------------------------------------
# Map the pipeline's "neutral" to the relaxed (expressionless) face preset.
func _face_emotion(e: String) -> String:
	return "relaxed" if e == "neutral" else e


# How the emotion + its intensity scale a word's DURATION. Angry/surprised get
# faster and sharper as intensity rises; sad slows down; others tighten mildly.
# Returned factor multiplies the base seconds-per-word (smaller = quicker).
func _speed_factor(emotion: String, intensity: float) -> float:
	var i := clampf(intensity, 0.0, 1.0)
	match emotion:
		"angry":
			return 1.1 - 0.45 * i        # 1.1 .. 0.65  (snappy when very angry)
		"surprised":
			return 1.05 - 0.35 * i
		"happy", "question":
			return 1.05 - 0.2 * i
		"sad":
			return 1.1 + 0.5 * i         # 1.1 .. 1.6   (slow, heavy)
		"sarcasm":
			return 1.15 + 0.35 * i       # 1.15 .. 1.5  (drawn-out, exaggerated)
		"pleading":
			return 1.1 + 0.3 * i         # 1.1 .. 1.4   (slow, imploring)
		_:
			return 1.0


# Eased interpolation for keyframe transitions. sharp (0..1, from intensity)
# biases toward a snappier arrival-and-hold; 0 = plain smoothstep.
func _ease(t: float, sharp: float) -> float:
	var s := clampf(t, 0.0, 1.0)
	var smooth := s * s * (3.0 - 2.0 * s)              # smoothstep
	var snappy := 1.0 - pow(1.0 - s, 2.0 + 2.0 * sharp)  # ease-out, sharpens with `sharp`
	return lerpf(smooth, snappy, clampf(sharp, 0.0, 1.0))


# Maps a word's LINEAR time progress (0..1) to eased progress with a CONSTANT-SPEED
# middle and smoothly ramped ends -- a trapezoidal velocity profile. This is applied
# once across the whole word (not per keyframe segment), so the hand accelerates
# once at the start, travels at a steady speed through all the intermediate
# keyframes WITHOUT stopping at any of them, then decelerates once at the end. That
# is what makes a multi-keyframe sign read as one continuous, fluid motion instead
# of a series of little stop-start hops. `sharp` (from intensity, for angry/surprised)
# blends toward a snappy ease-out so those emotions still land hard.
func _ease_progress(t: float, sharp: float) -> float:
	t = clampf(t, 0.0, 1.0)
	var r := 0.12   # fraction of the word spent ramping speed up / down at each end
	                # (small = closer to constant speed with only a gentle start/stop)
	var eased: float
	if r <= 0.0:
		eased = t
	else:
		var v := 1.0 / (1.0 - r)   # plateau speed so total displacement integrates to 1
		if t < r:
			eased = v * t * t / (2.0 * r)            # ramp up (constant accel)
		elif t <= 1.0 - r:
			eased = v * (r * 0.5 + (t - r))           # constant speed
		else:
			var u := 1.0 - t
			eased = 1.0 - v * u * u / (2.0 * r)       # ramp down
	if sharp > 0.0:
		var snappy := 1.0 - pow(1.0 - t, 2.0 + 2.0 * sharp)
		eased = lerpf(eased, snappy, clampf(sharp, 0.0, 1.0))
	return eased


func _read_config() -> Dictionary:
	var args := OS.get_cmdline_user_args()
	var config_path := ""
	for i in range(args.size()):
		if args[i] == "--config" and i + 1 < args.size():
			config_path = args[i + 1]
	if config_path.is_empty():
		push_error("SignDirector: no --config path passed after --")
		return {}
	var f := FileAccess.open(config_path, FileAccess.READ)
	if f == null:
		push_error("SignDirector: could not open config at %s" % config_path)
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("SignDirector: config JSON is not an object")
		return {}
	return parsed


## Backward-compatible wrapper: a uniform emotion held across every word (the
## hard-coded demo + old web sentence path). Delegates to _perform_items.
func _perform(sentence: String, emotion: String, words: Array, keyframes_by_word: Dictionary,
		seconds_per_word: float, quit_when_done: bool) -> void:
	var items: Array = []
	for w in words:
		items.append({"word": String(w), "emotion": emotion, "intensity": 0.85})
	_perform_items(sentence, items, keyframes_by_word, seconds_per_word, emotion, 0.85, quit_when_done)


## Core playback loop. Plays each gloss ITEM ({word, emotion, intensity}) in
## order: the word's sign from keyframes_by_word, its own emotion held on the
## face (weighted by intensity), with duration/head-motion/easing all scaled by
## that per-word emotion + intensity so the "degree" of feeling reads visually.
func _perform_items(caption: String, items: Array, keyframes_by_word: Dictionary,
		base_seconds_per_word: float, overall_emotion: String, overall_intensity: float,
		quit_when_done: bool) -> void:
	_run_id += 1
	var my_run_id := _run_id

	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel

	sentence_label.text = "\"%s\"" % caption
	emotion_label.text = overall_emotion.to_upper()

	# Pose the previous sign ended on, so the next sign can flow straight out of it
	# instead of dropping back to a neutral rest between every word.
	var last_sample := {}
	for idx in range(items.size()):
		if my_run_id != _run_id:
			return  # superseded by a newer submission
		var item: Dictionary = items[idx]
		var word: String = String(item.get("word", ""))
		var emotion: String = String(item.get("emotion", overall_emotion))
		var intensity: float = clampf(float(item.get("intensity", overall_intensity)), 0.0, 1.0)
		var sharp: float = intensity if (emotion == "angry" or emotion == "surprised") else 0.0

		_current_emotion = emotion
		_current_intensity = intensity
		FaceExpressions.apply(_mesh, _face_shape_indices, _face_emotion(emotion), intensity)
		emotion_label.text = "%s  %d%%" % [emotion.to_upper(), int(round(intensity * 100.0))]
		word_label.text = word.to_upper()

		var duration: float = base_seconds_per_word * _speed_factor(emotion, intensity)
		var keyframes: Array = keyframes_by_word.get(word, [])
		if keyframes.is_empty():
			await get_tree().create_timer(duration).timeout
			continue

		# Skip the neutral rest bookends BETWEEN signs so they flow into one another:
		# only the very first sign rises from rest, only the very last returns to it.
		# By convention keyframes[0] and keyframes[-1] are the neutral bookends.
		var is_first: bool = idx == 0
		var is_last: bool = idx == items.size() - 1
		var frac_lo: float = 0.0 if is_first else float((keyframes[1] as Dictionary).get("t", 0.0))
		var frac_hi: float = 1.0 if is_last else float((keyframes[keyframes.size() - 2] as Dictionary).get("t", 1.0))
		var span: float = maxf(0.0, frac_hi - frac_lo)

		# Blend straight from the previous sign's ending pose into this sign's start
		# pose (no dip to neutral). Nothing to blend from for the first sign.
		if not last_sample.is_empty():
			var target := _sample_word(keyframes, frac_lo, sharp)
			var blend_dur: float = minf(0.45, duration * 0.5)
			var bt := 0.0
			while bt < blend_dur:
				if my_run_id != _run_id:
					return
				_idle_t += get_process_delta_time()
				_apply_sample(_lerp_samples(last_sample, target, _ease(bt / blend_dur, 0.0)))
				await get_tree().process_frame
				bt += get_process_delta_time()

		var elapsed := 0.0
		while elapsed < duration:
			if my_run_id != _run_id:
				return
			_idle_t += get_process_delta_time()
			var prog: float = _ease_progress(clampf(elapsed / duration, 0.0, 1.0), sharp)
			var frac: float = frac_lo + prog * span
			_apply_sample(_sample_word(keyframes, frac, sharp))
			await get_tree().process_frame
			elapsed += get_process_delta_time()
		last_sample = _sample_word(keyframes, frac_hi, sharp)
		_apply_sample(last_sample)

	if my_run_id == _run_id:
		word_label.text = "DONE"

	if quit_when_done:
		get_tree().quit()


func _normalize(s: String) -> String:
	var low := s.to_lower()
	var out := ""
	for i in range(low.length()):
		var c := low[i]
		if (c >= "a" and c <= "z") or c == " ":
			out += c
	while out.find("  ") != -1:
		out = out.replace("  ", " ")
	return out.strip_edges()


## Parses a raw demo input like "You are drinking tea tomorrow. (Happy)" into
## {ok, err, base, emotion, gloss}. Emotion is the trailing "(...)"; the
## sentence (minus the bracket) must be one of KNOWN_SENTENCES; the gloss is
## the fixed ISL reordering. Hard-coded 3-sentence demo scope.
func _parse_request(raw: String) -> Dictionary:
	var emotion := ""
	var base := raw
	var open_i := raw.rfind("(")
	var close_i := raw.rfind(")")
	if open_i != -1 and close_i > open_i:
		emotion = raw.substr(open_i + 1, close_i - open_i - 1).strip_edges().to_lower()
		base = raw.substr(0, open_i)
	if not SUPPORTED_EMOTIONS.has(emotion):
		return {"ok": false, "err": "End the sentence with an emotion in brackets: (Question), (Happy) or (Angry)."}
	var norm := _normalize(base)
	if not KNOWN_SENTENCES.has(norm):
		return {"ok": false, "err": "This demo is hard-coded for the 3 sample sentences."}
	return {"ok": true, "err": "", "base": base.strip_edges(), "emotion": emotion, "gloss": KNOWN_SENTENCES[norm]}


func _run() -> void:
	var config := _read_config()
	var all_keyframes: Dictionary = config.get("keyframes", {})
	_adapt_keyframes_for_rig(all_keyframes)  # deepen the neutral for the VRM
	var seconds_per_word: float = config.get("seconds_per_word", DEFAULT_SECONDS_PER_WORD)
	# Direct-gloss path: a config carrying an explicit "gloss" array (+ optional
	# "emotion" and "caption") plays exactly those words, bypassing the hard-coded
	# KNOWN_SENTENCES lookup. Used by the single-word dev previews and, going
	# forward, by the speech pipeline that hands gloss+emotion in already-computed.
	var gloss_v = config.get("gloss", null)
	if gloss_v is Array and not (gloss_v as Array).is_empty():
		var emotion: String = String(config.get("emotion", "neutral"))
		var intensity: float = float(config.get("intensity", 0.8))
		var res := _resolve_gloss(gloss_v, all_keyframes, emotion, intensity)
		if not res["ok"]:
			push_error("SignDirector: " + str(res["err"]))
			get_tree().quit()
			return
		var words: Array = []
		for it in res["items"]:
			words.append(it["word"])
		var caption: String = String(config.get("caption", " ".join(PackedStringArray(words))))
		_perform_items(caption, res["items"], res["kbw"], seconds_per_word, emotion, intensity, true)
		return
	var raw: String = config.get("sentence", "")
	var req := _parse_request(raw)
	if not req["ok"]:
		push_error("SignDirector: " + str(req["err"]))
		get_tree().quit()
		return
	var keyframes_by_word := {}
	for w in req["gloss"]:
		keyframes_by_word[w] = all_keyframes.get(w, [])
	_perform(req["base"], req["emotion"], req["gloss"], keyframes_by_word, seconds_per_word, true)


# --- Web mode -------------------------------------------------------------

func _load_word_signs() -> Dictionary:
	if not _word_signs_data.is_empty():
		return _word_signs_data
	var f := FileAccess.open("res://data/word_signs.json", FileAccess.READ)
	if f == null:
		push_error("SignDirector: could not open res://data/word_signs.json")
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) == TYPE_DICTIONARY:
		_word_signs_data = parsed
		_adapt_keyframes_for_rig(_word_signs_data)  # deepen the neutral for the VRM
	return _word_signs_data


func _report_web_error(message: String) -> void:
	_run_id += 1  # cancel anything in flight
	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	word_label.text = "..."
	sentence_label.text = message
	if OS.has_feature("web"):
		JavaScriptBridge.eval(
			"if (window.onGodotError) window.onGodotError(%s);" % JSON.stringify(message), true
		)


## Called from the browser via the window.godotPerform JS bridge with a live,
## user-typed sentence that ends in a bracketed emotion, e.g.
## "You are drinking tea tomorrow. (Happy)".
func perform_web(raw: String) -> void:
	var req := _parse_request(raw)
	if not req["ok"]:
		_report_web_error(str(req["err"]))
		return
	var data := _load_word_signs()
	var keyframes_by_word := {}
	for w in req["gloss"]:
		if not data.has(w):
			_report_web_error("No sign data for: %s" % w)
			return
		keyframes_by_word[w] = data[w]
	_perform(req["base"], req["emotion"], req["gloss"], keyframes_by_word, DEFAULT_SECONDS_PER_WORD, false)


func _on_web_perform(args: Array) -> void:
	var raw: String = String(args[0]) if args.size() > 0 else ""
	perform_web(raw)


## Normalize a gloss array whose elements are EITHER a plain word string OR a
## {word, emotion, intensity} dict into performable items + a keyframe lookup,
## validating that every word has sign data. Returns {ok, err, items, kbw}.
func _resolve_gloss(gloss: Array, data: Dictionary, default_emotion: String, default_intensity: float) -> Dictionary:
	var items: Array = []
	var kbw := {}
	for g in gloss:
		var word := ""
		var emotion := default_emotion
		var intensity := default_intensity
		if typeof(g) == TYPE_DICTIONARY:
			word = String(g.get("word", ""))
			emotion = String(g.get("emotion", default_emotion))
			intensity = float(g.get("intensity", default_intensity))
		else:
			word = String(g)
		if word.is_empty():
			continue
		if not data.has(word):
			return {"ok": false, "err": "No sign data for: %s" % word}
		kbw[word] = data[word]
		items.append({"word": word, "emotion": emotion, "intensity": intensity})
	if items.is_empty():
		return {"ok": false, "err": "Empty gloss."}
	return {"ok": true, "err": "", "items": items, "kbw": kbw}


## New primary web entry point: the browser hands in an already-computed
## performance request (from the speech/text -> LLM pipeline) as a JSON string:
##   {"caption": "...", "gloss": [{"word","emotion","intensity"}, ...],
##    "overall_emotion": "...", "overall_intensity": 0..1}
## Gloss + emotion are NOT re-derived here -- the LLM produced them upstream.
func perform_web_gloss(raw_json: String) -> void:
	var parsed = JSON.parse_string(raw_json)
	if typeof(parsed) != TYPE_DICTIONARY:
		_report_web_error("Malformed performance request.")
		return
	var gloss = parsed.get("gloss", [])
	if not (gloss is Array) or (gloss as Array).is_empty():
		_report_web_error("Performance request had no gloss.")
		return
	var overall_emotion := String(parsed.get("overall_emotion", "neutral"))
	var overall_intensity := float(parsed.get("overall_intensity", 0.7))
	var data := _load_word_signs()
	var res := _resolve_gloss(gloss, data, overall_emotion, overall_intensity)
	if not res["ok"]:
		_report_web_error(str(res["err"]))
		return
	var words: Array = []
	for it in res["items"]:
		words.append(it["word"])
	var caption := String(parsed.get("caption", " ".join(PackedStringArray(words))))
	_perform_items(caption, res["items"], res["kbw"], DEFAULT_SECONDS_PER_WORD,
		overall_emotion, overall_intensity, false)


func _on_web_perform_gloss(args: Array) -> void:
	var raw: String = String(args[0]) if args.size() > 0 else ""
	perform_web_gloss(raw)


func _setup_web_bridge() -> void:
	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel
	word_label.text = "READY"
	sentence_label.text = "Type or speak a sentence, then Perform"
	emotion_label.text = ""
	_apply_rest_pose()  # stand naturally on load instead of the raw import (T-)pose
	_js_perform_callback = JavaScriptBridge.create_callback(_on_web_perform)
	_js_perform_gloss_callback = JavaScriptBridge.create_callback(_on_web_perform_gloss)
	var window := JavaScriptBridge.get_interface("window")
	window.godotPerform = _js_perform_callback
	window.godotPerformGloss = _js_perform_gloss_callback
	JavaScriptBridge.eval("window.godotReady = true; if (window.onGodotReady) window.onGodotReady();", true)
