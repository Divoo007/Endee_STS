extends Node3D
const ArmRig = preload("res://scripts/arm_rig.gd")
const HandRig = preload("res://scripts/hand_rig.gd")
const FaceExpressions = preload("res://scripts/face_expressions.gd")
const SignDir = preload("res://scripts/SignDirector.gd")
const AX := {"RIGHT": Vector3.RIGHT, "UP": Vector3.UP, "FORWARD": Vector3.FORWARD}
var _sk: Skeleton3D
var _mesh: MeshInstance3D
var _arm := ArmRig.new()
var _hand := HandRig.new()
var _idx := {}
var _cfg := {}
var _bmap := {}

func _ready():
	_sk = _first(self, "Skeleton3D")
	if _sk.find_bone("Bip01 L UpperArm") != -1:
		var ap = _first(self, "AnimationPlayer")
		if ap: ap.stop(); ap.active = false
		_sk.clear_bones_global_pose_override(); _sk.reset_bone_poses(); _sk.force_update_all_bone_transforms()
		for bn in SignDir.BIPED_MAP: _bmap[SignDir.BIPED_MAP[bn]] = bn
		_arm.set_name_map(_bmap); _hand.set_name_map(_bmap)
	_mesh = _first_mesh(self)
	_idx = FaceExpressions.index_shapes(_mesh.mesh)
	_arm.build(_sk); _hand.build(_sk)
	_cfg = _read_cfg()
	var fax = _axis(_cfg.get("finger_axis", ""), SignDir.BIPED_FINGER_CURL_AXIS)
	var tax = _axis(_cfg.get("thumb_axis", ""), fax)
	_hand.set_finger_curl_axis(fax, fax, tax, float(_cfg.get("thumb_scale", 1.0)))
	_frame(); _apply()

var _dumped := false
func _process(_dt):
	_apply()
	# Print positions only after a few frames, once the pose is stable -- reading
	# in _ready races the AnimationPlayer and can report the neutral pose instead.
	if not _dumped and Engine.get_process_frames() >= 3:
		_dumped = true
		_dump_positions()

func _dump_positions():
	var li := _sk.find_bone(_bmap.get("LeftHand", "LeftHand"))
	var ri := _sk.find_bone(_bmap.get("RightHand", "RightHand"))
	if li != -1: print("POS Left=", _sk.get_bone_global_pose(li).origin)
	if ri != -1: print("POS Right=", _sk.get_bone_global_pose(ri).origin)
	# Thumb tip + head, so DRINK-type mouth-contact signs can be tuned by number.
	# Fingertips too, so beak/cone orientation can be solved numerically: the
	# vector (MiddleDistal - RightHand) IS the direction the fingers point.
	for bn in ["RightThumbDistal", "RightIndexDistal", "RightMiddleDistal", "RightRingDistal", "RightLittleDistal", "LeftHand", "LeftIndexDistal", "LeftThumbMetacarpal", "LeftThumbProximal", "LeftThumbDistal", "Head", "LeftLowerArm", "RightLowerArm"]:
		var bi := _sk.find_bone(_bmap.get(bn, bn))
		if bi != -1: print("POS %s=%s" % [bn, _sk.get_bone_global_pose(bi).origin])
	# Full RightHand global basis (post-wrist), so a wrist can be SOLVED to match
	# another pose's exact hand orientation (not just its finger direction) -- kills
	# the beak "twist" between two keys at different forearm angles.
	var rh := _sk.find_bone(_bmap.get("RightHand", "RightHand"))
	if rh != -1:
		var b := _sk.get_bone_global_pose(rh).basis
		print("BASIS Right x=%s y=%s z=%s" % [b.x, b.y, b.z])

func _apply():
	var deltas := {}
	for b in ArmRig.POSE_ORDER: deltas[b] = Basis.IDENTITY
	for b in _cfg.get("bones", {}): deltas[b] = _compose(_cfg["bones"][b])
	# Mirror SignDirector._sample_word's elbow-hinge conjugation (see there for
	# the derivation) so PoseLab previews match the real in-game result.
	for side in ["Left", "Right"]:
		var upper: Basis = deltas[side + "UpperArm"]
		var lower_raw: Basis = deltas[side + "LowerArm"]
		deltas[side + "LowerArm"] = upper * lower_raw * upper.inverse()
	_arm.apply(deltas, 0.0)
	var conv: float = float(_cfg.get("converge", 0.0))
	# Base-only bend (KNOW): read "_base_bend" from each curl dict (as the sign data
	# carries it), so the four fingers fold ~90deg at the base knuckle only.
	var bb := {"Left": _base_bend(_cfg.get("curl_left", {})), "Right": _base_bend(_cfg.get("curl_right", {}))}
	var pb := {"Left": _pip_bend(_cfg.get("curl_left", {})), "Right": _pip_bend(_cfg.get("curl_right", {}))}
	_hand.apply_fingers({"Left": _curl(_cfg.get("curl_left", {})), "Right": _curl(_cfg.get("curl_right", {}))},
		0.0, {"Left": _wrist(_cfg.get("wrist_left", {})), "Right": _wrist(_cfg.get("wrist_right", {}))},
		{}, {"Left": conv, "Right": conv}, bb, pb)
	FaceExpressions.apply(_mesh, _idx, _cfg.get("emotion", "relaxed"))

# Axis from a named string ("RIGHT"/"-UP"/...), a raw [x,y,z] array, or "" (fallback).
func _axis(v, fallback: Vector3) -> Vector3:
	if v is Array and v.size() == 3:
		return Vector3(float(v[0]), float(v[1]), float(v[2])).normalized()
	if v is String and v != "":
		var neg: bool = v.begins_with("-")
		var key: String = v.substr(1) if neg else v
		if AX.has(key):
			return -AX[key] if neg else AX[key]
	return fallback
func _compose(v):
	var db := Basis.IDENTITY
	if v is Array:
		for p in v: db = Basis(AX.get(p.get("axis","RIGHT"), Vector3.RIGHT), deg_to_rad(float(p.get("angle",0)))) * db
	else:
		db = Basis(AX.get(v.get("axis","RIGHT"), Vector3.RIGHT), deg_to_rad(float(v.get("angle",0))))
	return db
func _wrist(d):
	# A wrist value is either a single {axis,angle} or a LIST of them composed in
	# order (world-space, pre-multiplied) -- mirrors SignDirector._bone_delta_basis
	# so a base roll + a nod tip can be layered (see "yes").
	if d is Array:
		var b := Basis.IDENTITY
		for q in d: b = Basis(_axis(q.get("axis","UP"), Vector3.UP), deg_to_rad(float(q.get("angle",0)))) * b
		return b
	if d is Dictionary and d.has("axis"): return Basis(_axis(d["axis"], Vector3.UP), deg_to_rad(float(d.get("angle",0))))
	return Basis.IDENTITY
func _curl(raw):
	var r := {}
	for f in HandRig.FINGER_NAMES: r[f] = float(raw.get(f, 0.0)) if typeof(raw) == TYPE_DICTIONARY else float(raw)
	return r
func _base_bend(raw):
	# bool (all four fingers) OR Array of finger names (only those base-bend). Passed
	# straight to hand_rig, which interprets both (see HandRig._base_bends).
	if typeof(raw) == TYPE_DICTIONARY:
		return raw.get("_base_bend", false)
	return false
func _pip_bend(raw):
	# Array of finger names to fold at the PIP (Intermediate) instead of the base knuckle.
	if typeof(raw) == TYPE_DICTIONARY:
		return raw.get("_pip_bend", false)
	return false
func _frame():
	var cam: Camera3D = $Camera3D
	if _cfg.get("real_camera", false):
		var head_idx := _sk.find_bone(_bmap.get("Head", "Head"))
		var chest_idx := _sk.find_bone(_bmap.get("Chest", "Chest"))
		var head_pos: Vector3 = _sk.global_transform * _sk.get_bone_global_pose(head_idx).origin
		var chest_pos: Vector3 = _sk.global_transform * _sk.get_bone_global_pose(chest_idx).origin
		cam.fov = 40.0
		var focus_b := head_pos.lerp(chest_pos, 0.5)
		cam.global_position = focus_b + Vector3(0.55, 0.04, 1.62)
		cam.look_at(focus_b, Vector3.UP)
		return
	var c = _cfg.get("camera", {})
	var pos = c.get("pos", [0.0, 1.35, 1.5]); var look = c.get("look", [0.0, 1.3, 0.0])
	cam.fov = float(c.get("fov", 38.0))
	cam.global_position = Vector3(pos[0], pos[1], pos[2]); cam.look_at(Vector3(look[0], look[1], look[2]), Vector3.UP)
func _read_cfg():
	var a = OS.get_cmdline_user_args()
	for i in range(a.size()):
		if a[i] == "--config" and i+1 < a.size():
			var f = FileAccess.open(a[i+1], FileAccess.READ)
			if f: return JSON.parse_string(f.get_as_text())
	return {}
func _first(n, cls):
	if n.is_class(cls): return n
	for c in n.get_children():
		var r = _first(c, cls)
		if r: return r
	return null
func _first_mesh(n):
	var best = null; var bn = -1; var st = [n]
	while not st.is_empty():
		var x = st.pop_back()
		if x is MeshInstance3D and x.mesh and x.mesh.get_blend_shape_count() > bn: bn = x.mesh.get_blend_shape_count(); best = x
		for c in x.get_children(): st.append(c)
	return best
