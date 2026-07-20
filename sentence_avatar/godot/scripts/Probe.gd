extends Node3D
## Headless arm-pose position probe. Applies a LIST of candidate arm poses and
## prints the resulting LeftHand/RightHand global positions -- no rendering, so
## it runs fast under --headless and lets me sweep many candidates in one pass
## to find arm angles that land a hand at a target chest/mouth position.
const ArmRig = preload("res://scripts/arm_rig.gd")
const SignDir = preload("res://scripts/SignDirector.gd")
const AX := {"RIGHT": Vector3.RIGHT, "UP": Vector3.UP, "FORWARD": Vector3.FORWARD}
var _sk: Skeleton3D
var _arm := ArmRig.new()
var _bmap := {}

func _ready():
	_sk = _first(self, "Skeleton3D")
	var ap = _first(self, "AnimationPlayer")
	if ap: ap.stop(); ap.active = false
	_sk.clear_bones_global_pose_override(); _sk.reset_bone_poses(); _sk.force_update_all_bone_transforms()
	for bn in SignDir.BIPED_MAP: _bmap[SignDir.BIPED_MAP[bn]] = bn
	_arm.set_name_map(_bmap); _arm.build(_sk)
	var cfg = _read_cfg()
	var top_basis: Basis = Basis.IDENTITY
	var have_top := false
	var blend: float = cfg.get("blend", 1.0)
	for cand in cfg.get("candidates", []):
		var deltas := {}
		for b in ArmRig.POSE_ORDER: deltas[b] = Basis.IDENTITY
		for b in cand.get("bones", {}): deltas[b] = _compose(cand["bones"][b])
		for side in ["Left", "Right"]:
			var upper: Basis = deltas[side + "UpperArm"]
			var lower_raw: Basis = deltas[side + "LowerArm"]
			deltas[side + "LowerArm"] = upper * lower_raw * upper.inverse()
		_arm.apply(deltas, 0.0)
		var l := _pos("LeftHand")
		var r := _pos("RightHand")
		var le := _pos("LeftLowerArm"); var re := _pos("RightLowerArm")
		print("CAND %s | L=(%.3f,%.3f,%.3f) R=(%.3f,%.3f,%.3f) | Lelbow=(%.3f,%.3f,%.3f) Relbow=(%.3f,%.3f,%.3f) | dist=%.3f" % [
			cand.get("name", "?"), l.x, l.y, l.z, r.x, r.y, r.z, le.x, le.y, le.z, re.x, re.y, re.z, l.distance_to(r)])
		# Wrist-orientation solve: compute the NATURAL (no-wrist-delta) global
		# basis of RightHand -- i.e. parent_global(RightLowerArm) * local_rest(RightHand)
		# -- which is exactly what hand_rig.gd calls actual_rest_basis when it later
		# applies a RightWrist delta as final = wrist_delta * actual_rest_basis. If the
		# FIRST candidate is flagged "top": true, its natural Hand basis becomes the
		# target; every later candidate then gets the wrist delta needed to rotate its
		# own actual_rest_basis to (partially) match that target, printed as a raw
		# axis-angle (degrees) usable directly as a RightWrist config value. `blend`
		# (0..1, default 1.0 = full compensation) lets us dial back from a fully rigid
		# match if the required rotation is extreme.
		var hand_idx := _sk.find_bone(_bmap.get("RightHand", "RightHand"))
		if hand_idx != -1:
			var lower_idx := _sk.find_bone(_bmap.get("RightLowerArm", "RightLowerArm"))
			var parent_global: Transform3D = _sk.get_bone_global_pose(lower_idx)
			var local_rest: Transform3D = _sk.get_bone_rest(hand_idx)
			var actual_rest_basis: Basis = parent_global.basis * local_rest.basis
			if cand.get("top", false) or not have_top:
				top_basis = actual_rest_basis
				have_top = true
				print("  natural Hand basis (TOP/target) quat=%s" % [actual_rest_basis.get_rotation_quaternion()])
			else:
				var full_rel: Basis = top_basis * actual_rest_basis.inverse()
				var q: Quaternion = full_rel.get_rotation_quaternion()
				var blended := Quaternion.IDENTITY.slerp(q, blend)
				var axis := blended.get_axis()
				var ang := rad_to_deg(blended.get_angle())
				print("  natural Hand basis quat=%s | full_rel angle=%.2f axis=(%.4f,%.4f,%.4f) | BLENDED(%.2f) angle=%.2f axis=(%.4f,%.4f,%.4f)" % [
					actual_rest_basis.get_rotation_quaternion(), rad_to_deg(q.get_angle()), q.get_axis().x, q.get_axis().y, q.get_axis().z,
					blend, ang, axis.x, axis.y, axis.z])
	get_tree().quit()

func _pos(name: String) -> Vector3:
	var idx := _sk.find_bone(_bmap.get(name, name))
	if idx == -1: return Vector3.ZERO
	return _sk.get_bone_global_pose(idx).origin

func _compose(v):
	var db := Basis.IDENTITY
	if v is Array:
		for p in v: db = Basis(AX.get(p.get("axis","RIGHT"), Vector3.RIGHT), deg_to_rad(float(p.get("angle",0)))) * db
	else:
		db = Basis(AX.get(v.get("axis","RIGHT"), Vector3.RIGHT), deg_to_rad(float(v.get("angle",0))))
	return db

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
