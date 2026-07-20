extends RefCounted
## Shared finger/hand articulation logic used by both Director.gd (emotion
## demo, same uniform curl on both hands via apply()) and SignDirector.gd
## (sign-language demo, distinct per-finger handshapes via apply_fingers()).
##
## Fingers hang off LeftHand/RightHand, which are themselves *not* directly
## posed by the arm-pose systems -- their global pose already inherits the
## forearm's rotation automatically via normal skeleton forward-kinematics.
## Finger curl deltas are expressed LOCAL to each bone's own rest frame and
## composed against the hand's ACTUAL current orientation, so a "curl" always
## closes toward the palm regardless of how the arm is posed.
##
## The four fingers and the thumb are oriented differently, so they get
## separate curl axes (set_finger_curl_axis). The VRM uses RIGHT for both;
## the realistic Biped uses different axes -- SignDirector configures it.

const FINGER_NAMES := ["Thumb", "Index", "Middle", "Ring", "Little"]
const FINGER_CURL_MAX_DEG := {
	"Proximal": 70.0, "Intermediate": 85.0, "Distal": 55.0, "Metacarpal": 20.0,
}
const FINGER_CURL_AXIS := Vector3.RIGHT  # local to each finger bone's own rest frame
const HAND_WIGGLE_AXIS := Vector3.RIGHT  # local to each hand bone's own rest frame

# --- Finger CONVERGENCE (adduction), for cone/"flower-bud" handshapes (PLEASE) --
# The curl model only flexes fingers toward the palm; it can't draw the fingertips
# TOGETHER laterally, so a pursed cone never forms. "converge" (0..1) adds a base-
# joint ADDUCTION that fans the four fingers inward toward the middle finger's line
# so their tips meet at a point, and lifts+opposes the thumb to join them. Gated
# behind an opt-in value, so every existing (non-converging) handshape is untouched.
# Adduction is applied ONLY at the base joint (Proximal for fingers, Metacarpal for
# the thumb) -- the whole finger swings from its knuckle, the way real adduction does.
const FINGER_ADDUCT_AXIS := Vector3.UP        # local base-joint axis fingers fan about
const THUMB_OPPOSE_AXIS := Vector3.RIGHT      # local axis that lifts the thumb to oppose
# Per-finger fan direction toward the middle finger (right-hand sense; left mirrors).
# Outer fingers need more swing to reach the centre; middle is the anchor (~0).
const FINGER_CONVERGE_DIR := {"Index": 1.0, "Middle": 0.2, "Ring": -1.1, "Little": -2.0}
const FINGER_ADDUCT_MAX_DEG := 20.0
const THUMB_OPPOSE_MAX_DEG := 45.0

var _skeleton: Skeleton3D
var _relative_order: Array = []  # ["LeftHand","RightHand"] + finger tiers, parent-before-child
var _finger_bone_role := {}      # bone name -> "Proximal"/"Intermediate"/"Distal"/"Metacarpal"
var _finger_side := {}           # bone name -> "Left"/"Right"
var _finger_name := {}           # bone name -> "Thumb"/"Index"/"Middle"/"Ring"/"Little"
# Local axes a "curl" rotates about. Defaults (RIGHT) are correct for the VRM;
# other rigs (e.g. a 3ds-Max Biped) orient their finger bones differently and
# need different axes -- and the THUMB usually needs a different axis than the
# other four fingers. SignDirector sets these per-avatar.
var _finger_curl_axis: Vector3 = FINGER_CURL_AXIS
var _thumb_curl_axis: Vector3 = FINGER_CURL_AXIS
var _thumb_curl_scale: float = 1.0   # thumbs often need a gentler curl than fingers
var _hand_wiggle_axis: Vector3 = HAND_WIGGLE_AXIS
# Optional {our_name: actual_bone_name} translation (see arm_rig.gd). The skin
# binds by bone name, so we translate at lookup rather than rename bones.
var _name_map := {}


func set_name_map(m: Dictionary) -> void:
	_name_map = m


## Set the local-frame axes about which finger curl (and the hand wiggle)
## rotates. thumb_axis defaults to the finger axis; thumb_scale scales the
## thumb's curl amount (thumbs usually shouldn't close as far as fingers).
func set_finger_curl_axis(curl_axis: Vector3, wiggle_axis: Vector3 = curl_axis,
		thumb_axis: Vector3 = curl_axis, thumb_scale: float = 1.0) -> void:
	_finger_curl_axis = curl_axis
	_hand_wiggle_axis = wiggle_axis
	_thumb_curl_axis = thumb_axis
	_thumb_curl_scale = thumb_scale


## The rig's default thumb curl axis (used when a handshape doesn't override it).
func get_thumb_curl_axis() -> Vector3:
	return _thumb_curl_axis


func build(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
	if not _relative_order.is_empty():
		return
	_relative_order.append("LeftHand")
	_relative_order.append("RightHand")
	# Thumb has one fewer segment (Metacarpal/Proximal/Distal) than the other
	# four fingers (Proximal/Intermediate/Distal); tiers pair them up so both
	# walk parent-before-child together.
	var tiers := [
		["Proximal", "Metacarpal"],
		["Intermediate", "Proximal"],
		["Distal", "Distal"],
	]
	for tier in tiers:
		var finger_role: String = tier[0]
		var thumb_role: String = tier[1]
		for side_v in ["Left", "Right"]:
			var side: String = side_v
			for finger_v in ["Index", "Middle", "Ring", "Little"]:
				var finger: String = finger_v
				var bone_name: String = side + finger + finger_role
				_relative_order.append(bone_name)
				_finger_bone_role[bone_name] = finger_role
				_finger_side[bone_name] = side
				_finger_name[bone_name] = finger
			var thumb_bone: String = side + "Thumb" + thumb_role
			_relative_order.append(thumb_bone)
			_finger_bone_role[thumb_bone] = thumb_role
			_finger_side[thumb_bone] = side
			_finger_name[thumb_bone] = "Thumb"


## Convenience wrapper for a uniform handshape (same curl across every finger,
## both hands) -- what the emotion demo uses.
func apply(curl_left: float, curl_right: float, wiggle_deg: float = 0.0) -> void:
	var uniform_left := {}
	var uniform_right := {}
	for finger in FINGER_NAMES:
		uniform_left[finger] = curl_left
		uniform_right[finger] = curl_right
	apply_fingers({"Left": uniform_left, "Right": uniform_right}, wiggle_deg)


## finger_curls: {"Left": {"Thumb": 0-1, ...}, "Right": {...}} per-finger curl
## (0 open .. 1 fully curled). wrist_deltas: optional {"Left"/"Right": Basis}
## global-space hand rotation that REPLACES the idle wiggle for that side.
## thumb_axes: optional {"Left"/"Right": Vector3} overriding the thumb curl axis
## for that hand (fists fold the thumb about BACK to carry it across the PALM;
## the default _thumb_curl_axis -- UP on the Biped -- suits pinch shapes). Fingers
## other than the thumb are unaffected.
func apply_fingers(finger_curls: Dictionary, wiggle_deg: float = 0.0, wrist_deltas: Dictionary = {}, thumb_axes: Dictionary = {}, converge: Dictionary = {}) -> void:
	for bone_name in _relative_order:
		var idx := _skeleton.find_bone(_name_map.get(bone_name, bone_name))
		if idx == -1:
			continue
		var parent_idx := _skeleton.get_bone_parent(idx)
		var parent_global := Transform3D.IDENTITY
		if parent_idx != -1:
			parent_global = _skeleton.get_bone_global_pose(parent_idx)
		var local_rest := _skeleton.get_bone_rest(idx)
		var final_global_basis: Basis
		if bone_name.ends_with("Hand"):
			var side: String = "Left" if bone_name.begins_with("Left") else "Right"
			if wrist_deltas.has(side):
				var actual_rest_basis: Basis = parent_global.basis * local_rest.basis
				final_global_basis = (wrist_deltas[side] as Basis) * actual_rest_basis
			else:
				var delta_local := Basis(_hand_wiggle_axis, deg_to_rad(wiggle_deg))
				final_global_basis = parent_global.basis * (local_rest.basis * delta_local)
		else:
			var role: String = _finger_bone_role.get(bone_name, "Proximal")
			var side: String = _finger_side.get(bone_name, "Left")
			var finger: String = _finger_name.get(bone_name, "Index")
			var is_thumb: bool = finger == "Thumb"
			var side_curls: Dictionary = finger_curls.get(side, {})
			var curl: float = side_curls.get(finger, 0.0)
			var angle_deg: float = curl * FINGER_CURL_MAX_DEG.get(role, 60.0)
			if is_thumb:
				angle_deg *= _thumb_curl_scale
			var axis: Vector3
			if is_thumb:
				axis = thumb_axes.get(side, _thumb_curl_axis)
			else:
				axis = _finger_curl_axis
			var delta_local := Basis(axis, deg_to_rad(angle_deg))
			# Convergence (opt-in): a base-joint adduction that fans fingertips to a
			# point + opposes the thumb, composed BEFORE the curl so curl still closes
			# toward the palm in the already-fanned frame. Base joint only.
			var conv: float = float(converge.get(side, 0.0))
			var is_base: bool = role == "Proximal" or (is_thumb and role == "Metacarpal")
			if conv != 0.0 and is_base:
				var add_deg: float
				var add_axis: Vector3
				if is_thumb:
					add_deg = conv * THUMB_OPPOSE_MAX_DEG
					add_axis = THUMB_OPPOSE_AXIS
				else:
					add_deg = conv * FINGER_ADDUCT_MAX_DEG * float(FINGER_CONVERGE_DIR.get(finger, 0.0))
					add_axis = FINGER_ADDUCT_AXIS
				if side == "Left":
					add_deg = -add_deg
				delta_local = delta_local * Basis(add_axis, deg_to_rad(add_deg))
			final_global_basis = parent_global.basis * (local_rest.basis * delta_local)
		var final_global_origin: Vector3 = parent_global * local_rest.origin
		_skeleton.set_bone_global_pose_override(idx, Transform3D(final_global_basis, final_global_origin), 1.0, true)
		_skeleton.force_update_all_bone_transforms()
