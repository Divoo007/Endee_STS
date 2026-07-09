extends RefCounted
## Shared facial-expression logic used by both Director.gd (emotion demo)
## and SignDirector.gd (sign-language demo), so the avatar's blend-shape
## mapping is defined once.

# Friendly face-shape name -> substring to match against the mesh's actual
# blend shape names. Matching by substring keeps this working across avatars
# that name shapes slightly differently, as long as they follow either the
# VRM/VRChat viseme convention (vrc_v_aa, ...) or plain VRM preset naming
# (_A, _Joy, _Angry, ...) -- the current avatar uses the latter and ships
# full VRM mood blend shapes (joy/angry/sorrow/fun).
const FACE_SHAPE_ALIASES := {
	"aa": "_A",
	"oh": "_O",
	"blink": "_Blink",
	"joy": "_Joy",
	"angry": "_Angry",
	"sorrow": "_Sorrow",
	"fun": "_Furious",  # this avatar's author named the "fun" preset shape "_Furious"
}

# Held facial weights per emotion (0.0-1.0 per named shape).
const FACE_PRESETS := {
	"happy": {"joy": 1.0},
	"sad": {"sorrow": 1.0},
	"angry": {"angry": 1.0, "blink": 0.0},
	"surprised": {"aa": 0.0, "oh": 0.85, "blink": 0.0},
	"relaxed": {},
}


static func index_shapes(mesh: ArrayMesh) -> Dictionary:
	var indices := {}
	for i in range(mesh.get_blend_shape_count()):
		var shape_name: String = mesh.get_blend_shape_name(i)
		for alias in FACE_SHAPE_ALIASES.keys():
			if shape_name.find(FACE_SHAPE_ALIASES[alias]) != -1:
				indices[alias] = i
	return indices


static func apply(mesh_instance: MeshInstance3D, shape_indices: Dictionary, emotion: String) -> void:
	var preset: Dictionary = FACE_PRESETS.get(emotion, {})
	for alias in shape_indices.keys():
		var weight: float = preset.get(alias, 0.0)
		mesh_instance.set_blend_shape_value(shape_indices[alias], weight)
