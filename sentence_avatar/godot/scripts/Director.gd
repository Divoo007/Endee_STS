extends Node3D
## Sequences (sentence, emotion) segments read from a JSON config passed via
## `-- --config <path>` on the Godot command line. Each segment holds a
## facial expression (see FaceExpressions), a body-language pose -- arms/
## torso/head, via ArmRig -- and articulated fingers (see HandRig) for a
## fixed duration, with continuous small motion layered on top so nothing
## sits frozen, updates the on-screen caption, then advances.

const FaceExpressions = preload("res://scripts/face_expressions.gd")
const HandRig = preload("res://scripts/hand_rig.gd")
const ArmRig = preload("res://scripts/arm_rig.gd")

const DEFAULT_SECONDS_PER_SEGMENT := 3.5
const POSE_EASE_SECONDS := 0.4

# Held body pose per emotion: bone name -> rotation applied LOCAL to that
# bone's own rest frame, composed against its ACTUAL current parent (see
# ArmRig) -- so, unlike a plain global-axis rotation, "raise the shoulder"
# and "bend the elbow" genuinely compose into one arm instead of each
# being computed as if the other joint hadn't moved.
#
# Rest pose is a T-pose (arms horizontal). FORWARD is the bend axis for
# both UpperArm and LowerArm: positive angle raises the right arm (swings
# it up from horizontal) and lowers the left, so most poses use opposite
# signs L/R for a mirrored pose. LowerArm's angle is *additional* rotation
# on top of wherever UpperArm's actual pose ended up, so e.g. happy's
# LowerArm continues curling the same direction UpperArm already raised
# it, producing a visible elbow bend rather than one rigid segment.
const BODY_PRESETS := {
	"happy": {
		"RightUpperArm": {"axis": Vector3.FORWARD, "angle": 65},
		"LeftUpperArm": {"axis": Vector3.FORWARD, "angle": -65},
		"RightLowerArm": {"axis": Vector3.FORWARD, "angle": 40},
		"LeftLowerArm": {"axis": Vector3.FORWARD, "angle": -40},
		"Head": {"axis": Vector3.RIGHT, "angle": -8},
	},
	"sad": {
		"Spine": {"axis": Vector3.RIGHT, "angle": 14},
		"Chest": {"axis": Vector3.RIGHT, "angle": 8},
		"RightUpperArm": {"axis": Vector3.FORWARD, "angle": -75},
		"LeftUpperArm": {"axis": Vector3.FORWARD, "angle": 75},
		"RightLowerArm": {"axis": Vector3.FORWARD, "angle": -20},
		"LeftLowerArm": {"axis": Vector3.FORWARD, "angle": 20},
		"Head": {"axis": Vector3.RIGHT, "angle": 26},
	},
	"angry": {
		"Spine": {"axis": Vector3.RIGHT, "angle": -4},
		"Chest": {"axis": Vector3.RIGHT, "angle": -6},
		"RightUpperArm": {"axis": Vector3.FORWARD, "angle": 10},
		"LeftUpperArm": {"axis": Vector3.FORWARD, "angle": -10},
		"RightLowerArm": {"axis": Vector3.FORWARD, "angle": 35},
		"LeftLowerArm": {"axis": Vector3.FORWARD, "angle": -35},
		"Head": {"axis": Vector3.RIGHT, "angle": -10},
	},
	"surprised": {
		"Spine": {"axis": Vector3.RIGHT, "angle": -6},
		"RightUpperArm": {"axis": Vector3.FORWARD, "angle": 65},
		"LeftUpperArm": {"axis": Vector3.FORWARD, "angle": -65},
		"RightLowerArm": {"axis": Vector3.FORWARD, "angle": 15},
		"LeftLowerArm": {"axis": Vector3.FORWARD, "angle": -15},
		"Head": {"axis": Vector3.RIGHT, "angle": -12},
	},
	"relaxed": {
		"RightUpperArm": {"axis": Vector3.FORWARD, "angle": -70},
		"LeftUpperArm": {"axis": Vector3.FORWARD, "angle": 70},
		"RightLowerArm": {"axis": Vector3.FORWARD, "angle": -15},
		"LeftLowerArm": {"axis": Vector3.FORWARD, "angle": 15},
		"Head": {"axis": Vector3.RIGHT, "angle": 3},
	},
}

# 0.0 = fingers open/flat, 1.0 = full fist -- same curl on both hands here;
# SignDirector.gd drives left/right independently for one-handed signs.
const FINGER_CURL_PRESETS := {
	"happy": 0.15,
	"sad": 0.55,
	"angry": 1.0,
	"surprised": 0.0,
	"relaxed": 0.35,
}
const HAND_WIGGLE_DEG := 12.0
const FINGER_FIDGET_AMPLITUDE := 0.12  # fraction of full curl range

var _skeleton: Skeleton3D
var _mesh: MeshInstance3D
var _face_shape_indices := {}   # friendly name -> blend shape index
var _hand_rig := HandRig.new()
var _arm_rig := ArmRig.new()
var _target_deltas := {}        # bone name -> Basis (local delta), current ease target
var _from_deltas := {}          # bone name -> Basis, ease start point
var _current_curl_target := 0.0
var _pose_elapsed := 0.0
var _idle_t := 0.0


func _ready() -> void:
	_skeleton = $Avatar/GeneralSkeleton
	_mesh = _skeleton.get_node("body")
	_face_shape_indices = FaceExpressions.index_shapes(_mesh.mesh)
	_hand_rig.build(_skeleton)
	_arm_rig.build(_skeleton)
	_frame_camera()
	_run()


func _frame_camera() -> void:
	var head_idx := _skeleton.find_bone("Head")
	var chest_idx := _skeleton.find_bone("Chest")
	if head_idx == -1 or chest_idx == -1:
		return
	var head_pos: Vector3 = _skeleton.global_transform * _skeleton.get_bone_global_pose(head_idx).origin
	var chest_pos: Vector3 = _skeleton.global_transform * _skeleton.get_bone_global_pose(chest_idx).origin
	var cam: Camera3D = $Camera3D
	var focus := head_pos.lerp(chest_pos, 0.55)
	# dead-on front view, pulled back slightly so raised/spread arms and
	# hands stay inside frame
	cam.global_position = focus + Vector3(0, 0.02, 1.35)
	cam.look_at(focus, Vector3.UP)


func _process(delta: float) -> void:
	_idle_t += delta
	_apply_arm_pose(delta)
	var wiggle := sin(_idle_t * 2.2) * HAND_WIGGLE_DEG
	var fidget := sin(_idle_t * 3.1) * FINGER_FIDGET_AMPLITUDE
	var curl := clampf(_current_curl_target + fidget, 0.0, 1.0)
	_hand_rig.apply(curl, curl, wiggle)


func _apply_arm_pose(delta: float) -> void:
	if _target_deltas.is_empty():
		return
	_pose_elapsed = min(_pose_elapsed + delta, POSE_EASE_SECONDS)
	var t := 1.0 if POSE_EASE_SECONDS <= 0.0 else _pose_elapsed / POSE_EASE_SECONDS
	t = ease(t, -2.0)  # ease-out
	var blended := {}
	for bone_name in ArmRig.POSE_ORDER:
		var target: Basis = _target_deltas.get(bone_name, Basis.IDENTITY)
		var from_basis: Basis = _from_deltas.get(bone_name, target)
		blended[bone_name] = from_basis.slerp(target, t)
	var bob := sin(_idle_t * 1.6) * 0.01
	_arm_rig.apply(blended, bob)


func _set_body_pose(emotion: String) -> void:
	var preset: Dictionary = BODY_PRESETS.get(emotion, {})
	var new_target := {}
	for bone_name in ArmRig.POSE_ORDER:
		if preset.has(bone_name):
			var p: Dictionary = preset[bone_name]
			new_target[bone_name] = Basis(p["axis"], deg_to_rad(p["angle"]))
		else:
			new_target[bone_name] = Basis.IDENTITY
	var from := {}
	for bone_name in ArmRig.POSE_ORDER:
		from[bone_name] = _target_deltas.get(bone_name, new_target[bone_name])
	_from_deltas = from
	_pose_elapsed = 0.0
	_target_deltas = new_target
	_current_curl_target = FINGER_CURL_PRESETS.get(emotion, 0.2)


func _read_config() -> Dictionary:
	var args := OS.get_cmdline_user_args()
	var config_path := ""
	for i in range(args.size()):
		if args[i] == "--config" and i + 1 < args.size():
			config_path = args[i + 1]
	if config_path.is_empty():
		push_error("Director: no --config path passed after --")
		return {}
	var f := FileAccess.open(config_path, FileAccess.READ)
	if f == null:
		push_error("Director: could not open config at %s" % config_path)
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Director: config JSON is not an object")
		return {}
	return parsed


func _run() -> void:
	var config := _read_config()
	var sentences: Array = config.get("sentences", ["(no sentence provided)"])
	var emotions: Array = config.get("emotions", ["relaxed"])
	var seconds_per_segment: float = config.get("seconds_per_segment", DEFAULT_SECONDS_PER_SEGMENT)

	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel

	for i in range(emotions.size()):
		var emotion: String = emotions[i]
		var sentence: String = sentences[i % sentences.size()]
		sentence_label.text = "\"%s\"" % sentence
		emotion_label.text = emotion.to_upper()
		FaceExpressions.apply(_mesh, _face_shape_indices, emotion)
		_set_body_pose(emotion)
		await get_tree().create_timer(seconds_per_segment).timeout

	get_tree().quit()
