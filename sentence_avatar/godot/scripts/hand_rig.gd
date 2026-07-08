extends RefCounted
## Shared finger/hand articulation logic used by both Director.gd (emotion
## demo, same uniform curl on both hands via apply()) and SignDirector.gd
## (sign-language demo, distinct per-finger handshapes via apply_fingers()).
##
## Fingers hang off LeftHand/RightHand, which are themselves *not* directly
## posed by the arm-pose systems above -- their global pose already inherits
## the forearm's rotation automatically via normal skeleton forward-
## kinematics. Because the hand can be rotated quite far from its bind pose
## by whatever arm pose is active, finger curl deltas are expressed LOCAL to
## each bone's own rest frame and composed against the hand's ACTUAL current
## orientation (not its stale bind-pose rest), so a "curl" always closes
## toward the palm regardless of how the arm is posed. See apply_fingers().

const FINGER_NAMES := ["Thumb", "Index", "Middle", "Ring", "Little"]
const FINGER_CURL_MAX_DEG := {
	"Proximal": 70.0, "Intermediate": 85.0, "Distal": 55.0, "Metacarpal": 20.0,
}
const FINGER_CURL_AXIS := Vector3.RIGHT  # local to each finger bone's own rest frame
const HAND_WIGGLE_AXIS := Vector3.RIGHT  # local to each hand bone's own rest frame

var _skeleton: Skeleton3D
var _relative_order: Array = []  # ["LeftHand","RightHand"] + finger tiers, parent-before-child
var _finger_bone_role := {}      # bone name -> "Proximal"/"Intermediate"/"Distal"/"Metacarpal"
var _finger_side := {}           # bone name -> "Left"/"Right"
var _finger_name := {}           # bone name -> "Thumb"/"Index"/"Middle"/"Ring"/"Little"


func build(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
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


## Convenience wrapper for a uniform handshape (same curl across every
## finger, both hands) -- what the emotion demo uses. curl_left/curl_right:
## 0.0 (open hand) - 1.0 (full fist). wiggle_deg: small continuous wrist
## rotation to layer on top so hands aren't perfectly frozen.
func apply(curl_left: float, curl_right: float, wiggle_deg: float = 0.0) -> void:
	var uniform_left := {}
	var uniform_right := {}
	for finger in FINGER_NAMES:
		uniform_left[finger] = curl_left
		uniform_right[finger] = curl_right
	apply_fingers({"Left": uniform_left, "Right": uniform_right}, wiggle_deg)


## finger_curls: {"Left": {"Thumb": 0-1, "Index": 0-1, "Middle": 0-1, "Ring":
## 0-1, "Little": 0-1}, "Right": {...}} -- 0.0 (that finger open/straight) -
## 1.0 (that finger fully curled). Lets a handshape differ per finger, e.g.
## "Index": 0.0 with the rest at 1.0 for a pointing hand. A finger/side
## missing from the dict defaults to 0.0 (open). wiggle_deg: small
## continuous wrist rotation layered on top so hands aren't perfectly frozen
## -- used only when wrist_deltas has no entry for that side. wrist_deltas:
## optional {"Left": Basis, "Right": Basis}, a GLOBAL-space rotation (same
## convention as ArmRig.apply()'s bone_deltas) that REPLACES the wiggle for
## that side. This is a deliberately separate knob from finger curl: curling
## fingers can only close them toward the palm, it can never change which
## way the hand/palm itself is aimed. Aiming the hand (e.g. so a pointing
## gesture's extended finger reaches toward the camera instead of wherever
## the forearm happens to leave it) needs an actual wrist rotation, which is
## what this does -- without touching the elbow/shoulder pose that puts the
## hand where it is.
func apply_fingers(finger_curls: Dictionary, wiggle_deg: float = 0.0, wrist_deltas: Dictionary = {}) -> void:
	for bone_name in _relative_order:
		var idx := _skeleton.find_bone(bone_name)
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
				var delta_local := Basis(HAND_WIGGLE_AXIS, deg_to_rad(wiggle_deg))
				final_global_basis = parent_global.basis * (local_rest.basis * delta_local)
		else:
			var role: String = _finger_bone_role.get(bone_name, "Proximal")
			var side: String = _finger_side.get(bone_name, "Left")
			var finger: String = _finger_name.get(bone_name, "Index")
			var side_curls: Dictionary = finger_curls.get(side, {})
			var curl: float = side_curls.get(finger, 0.0)
			var angle_deg: float = curl * FINGER_CURL_MAX_DEG.get(role, 60.0)
			var delta_local := Basis(FINGER_CURL_AXIS, deg_to_rad(angle_deg))
			final_global_basis = parent_global.basis * (local_rest.basis * delta_local)
		var final_global_origin: Vector3 = parent_global * local_rest.origin
		_skeleton.set_bone_global_pose_override(idx, Transform3D(final_global_basis, final_global_origin), 1.0, true)
		_skeleton.force_update_all_bone_transforms()
