extends RefCounted
## Shared arm/torso/head posing logic used by both Director.gd (emotion
## demo) and SignDirector.gd (sign-language demo).
##
## Each bone's rotation is a delta in GLOBAL/world space (so a "raise the
## arm" rotation means the same thing regardless of which bone it's applied
## to, and matches the axis behavior discovered by testing each bone's
## actual rest-pose response), applied on top of where that bone's rest
## orientation ACTUALLY ends up given its parent's current pose -- not the
## bone's own stale global bind-pose rest. Concretely: for a bone whose
## parent is itself posed (e.g. LowerArm once UpperArm has been raised),
## the "rest orientation to rotate from" is parent_actual_global * local_rest,
## not the bone's independent global rest.
##
## Two earlier versions got parts of this wrong:
## - Composing every bone's delta against its own independent GLOBAL REST
##   (ignoring the parent's actual pose) doesn't accumulate the way a real
##   skeleton does: shoulder-raise and elbow-bend don't compose into a
##   genuine bend, they read as one rigid segment, because the forearm's
##   target was computed from a frame that never accounted for the upper
##   arm's actual new pose.
## - Composing the delta LOCAL to the bone's own rest frame (the same
##   pattern hand_rig.gd correctly uses for finger curls) fixed the
##   chaining, but silently changed what the axis constants meant: a local
##   axis is whatever direction that bone's own idiosyncratic rest
##   orientation happens to point, not world space, so the same
##   Vector3.FORWARD that reliably raised an arm in isolation could swing a
##   different bone sideways once actually chained. Fingers get away with a
##   fixed local axis because every finger bone shares a consistent rest
##   convention; the arm bones don't.
## apply() below composes the delta as a GLOBAL rotation on top of the
## bone's actual (parent-relative) rest, getting both right at once.

# Parent-before-child order: a bone's origin/parent-relative composition
# depends on its parent already being committed this frame.
const POSE_ORDER := [
	"Spine", "Chest", "LeftShoulder", "RightShoulder",
	"LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "Head",
]

var _skeleton: Skeleton3D
# Optional {our_name: actual_bone_name} translation for rigs whose bones are
# named differently (e.g. the realistic Biped avatar). Empty = names match
# (the VRM). Renaming the skeleton's bones is NOT an option because the mesh
# skin binds to bones BY NAME, so we translate at lookup instead.
var _name_map := {}


func build(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton


func set_name_map(m: Dictionary) -> void:
	_name_map = m


## bone_deltas: bone_name -> Basis, a GLOBAL-space rotation applied on top
## of that bone's actual (parent-relative) rest orientation (identity =
## stay at rest). Bones in POSE_ORDER not present in bone_deltas are left
## at rest. bob_offset: small vertical origin offset (idle breathing)
## applied at bob_bone, which propagates to its children via the normal
## hierarchical composition below.
func apply(bone_deltas: Dictionary, bob_offset: float = 0.0, bob_bone: String = "Spine") -> void:
	for bone_name in POSE_ORDER:
		var idx := _skeleton.find_bone(_name_map.get(bone_name, bone_name))
		if idx == -1:
			continue
		var delta_global: Basis = bone_deltas.get(bone_name, Basis.IDENTITY)
		var local_rest := _skeleton.get_bone_rest(idx)
		var parent_idx := _skeleton.get_bone_parent(idx)
		var parent_global := Transform3D.IDENTITY
		if parent_idx != -1:
			parent_global = _skeleton.get_bone_global_pose(parent_idx)
		var actual_rest_basis: Basis = parent_global.basis * local_rest.basis
		var final_global_basis: Basis = delta_global * actual_rest_basis
		var local_origin := local_rest.origin
		if bone_name == bob_bone:
			local_origin += Vector3(0, bob_offset, 0)
		var origin: Vector3 = parent_global * local_origin
		_skeleton.set_bone_global_pose_override(idx, Transform3D(final_global_basis, origin), 1.0, true)
		_skeleton.force_update_all_bone_transforms()
