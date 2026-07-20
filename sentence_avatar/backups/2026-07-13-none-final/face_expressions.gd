extends RefCounted
## Shared facial-expression logic used by both Director.gd (emotion demo) and
## SignDirector.gd (sign-language demo), so the avatar's blend-shape mapping is
## defined once.
##
## Works across two very different avatars by matching blend shapes by NAME
## SUBSTRING (index_shapes): the stylized VRM ships coarse VRM-preset shapes
## (_Joy/_Angry/_Sorrow...), while the realistic Rocketbox avatar ships a full
## ARKit/FACS set (MouthSmileLeft, BrowOuterUpLeft, BrowDownLeft, EyeSquint...).
## Each emotion preset below lists targets for BOTH; whichever aliases don't
## exist on the current mesh simply aren't indexed and are skipped -- so one
## preset table drives either avatar. The ARKit set is what finally makes fine
## grammar like a single raised eyebrow ("question") faithful.

# Friendly alias -> substring matched against the mesh's blend shape names.
const FACE_SHAPE_ALIASES := {
	# VRM (stylized avatar)
	"aa": "_A", "oh": "_O", "blink": "_Blink",
	"joy": "_Joy", "angry": "_Angry", "sorrow": "_Sorrow", "fun": "_Furious",
	# ARKit / FACS (realistic Rocketbox avatar). Substrings are unique within
	# that avatar's shape names (e.g. "blendShape1.AK_44_MouthSmileLeft"). The
	# shapes are gentle at weight 1.0, so each emotion STACKS the ARKit (AK_)
	# blendshape with its matching FACS action unit (AU_) for a stronger read.
	"browUpL": "BrowOuterUpLeft", "browUpR": "BrowOuterUpRight", "browInner": "BrowInnerUp",
	"outBrowL": "L_OuterBrowRaiser", "outBrowR": "R_OuterBrowRaiser", "innerBrow": "InnerBrowRaiser",
	"browDownL": "BrowDownLeft", "browDownR": "BrowDownRight", "browLow": "BrowLowerer",
	"smileL": "MouthSmileLeft", "smileR": "MouthSmileRight",
	"pullL": "L_LipCornerPuller", "pullR": "R_LipCornerPuller",
	"cheekL": "CheekSquintLeft", "cheekR": "CheekSquintRight",
	"cheekRaiseL": "L_CheekRaiser", "cheekRaiseR": "R_CheekRaiser",
	"eyeSqL": "EyeSquintLeft", "eyeSqR": "EyeSquintRight", "lidTight": "LidTightener",
	"sneerL": "NoseSneerLeft", "sneerR": "NoseSneerRight", "noseWrinkle": "NoseWrinkler",
	"frownL": "MouthFrownLeft", "frownR": "MouthFrownRight",
	"jawOpen": "JawOpen", "lidUpL": "L_UpperLidRaiser", "lidUpR": "R_UpperLidRaiser",
}

# Held facial weights per emotion (0.0-1.0 per named alias). Lists both VRM and
# ARKit targets; only those present on the current mesh take effect. Values are
# pushed hard (and AK+AU stacked) because the realistic shapes are subtle.
const FACE_PRESETS := {
	"happy": {
		"joy": 1.0,                                            # VRM
		"smileL": 1.0, "smileR": 1.0, "pullL": 1.0, "pullR": 1.0,   # broad smile (AK+AU)
		"cheekL": 0.9, "cheekR": 0.9, "cheekRaiseL": 0.8, "cheekRaiseR": 0.8,  # lifted cheeks
		"browInner": 0.25, "lidUpL": 0.2, "lidUpR": 0.2,       # open, engaged eyes
	},
	"angry": {
		"angry": 1.0, "blink": 0.0,                            # VRM
		"browDownL": 1.0, "browDownR": 1.0, "browLow": 1.0,    # furrowed/lowered brows (AK+AU)
		"eyeSqL": 0.85, "eyeSqR": 0.85, "lidTight": 0.8,       # narrowed, tightened eyes
		"sneerL": 0.6, "sneerR": 0.6, "noseWrinkle": 0.6,      # nose sneer/wrinkle
	},
	"question": {
		"browUpL": 1.0, "outBrowL": 1.0,                       # ONE eyebrow strongly raised (AK+AU)
		"innerBrow": 0.5, "browInner": 0.4, "lidUpL": 0.4,     # quizzical, wider that eye
	},
	"sad": {"sorrow": 1.0, "frownL": 0.7, "frownR": 0.7},
	"surprised": {"oh": 0.85, "jawOpen": 0.4, "browUpL": 0.8, "browUpR": 0.8, "innerBrow": 0.6, "blink": 0.0},
	# Sarcasm reads through ASYMMETRY: a one-sided smirk (left corner only) under
	# the OPPOSITE brow cocked up, with half-lidded, unimpressed eyes and a faint
	# sneer. Deliberately lopsided -- a symmetric smile would read as genuine.
	"sarcasm": {
		"joy": 0.4,                                            # VRM: faint amusement
		"smileL": 0.9, "pullL": 1.0,                           # smirk: left corner only
		"browUpR": 0.85, "outBrowR": 0.75,                     # opposite (right) brow cocked
		"eyeSqL": 0.4, "eyeSqR": 0.4, "lidTight": 0.4,         # half-lidded, unimpressed
		"sneerL": 0.4, "cheekRaiseL": 0.5,                     # faint one-sided sneer/cheek
	},
	# Pleading / begging: the inner brows pulled UP hard (the tell-tale "puppy"
	# arch), a gentle downturned mouth (asking, not smiling) and eyes opened a
	# touch for a soft, imploring look. Symmetric -- unlike sarcasm -- because a
	# sincere plea reads as earnest, not lopsided.
	"pleading": {
		"sorrow": 0.55,                                        # VRM: soft plaintive base
		"browInner": 1.0, "innerBrow": 1.0,                    # inner brows raised hard (AK+AU) --
		                                                       # OUTER brows left DOWN on purpose: the
		                                                       # inner-up/outer-down oblique is what
		                                                       # reads as pleading, not surprise.
		"frownL": 0.6, "frownR": 0.6,                          # gentle downturned, begging mouth
		"lidUpL": 0.2, "lidUpR": 0.2,                          # eyes opened a touch -- soft, imploring
	},
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


## intensity (0..1) scales every blend-shape weight, so a "degree of anger"
## coming from the speech pipeline reads as a proportionally stronger/weaker
## face. "neutral" is treated as "relaxed" (a flat, expressionless face).
static func apply(mesh_instance: MeshInstance3D, shape_indices: Dictionary, emotion: String, intensity: float = 1.0) -> void:
	var key := "relaxed" if emotion == "neutral" else emotion
	var preset: Dictionary = FACE_PRESETS.get(key, {})
	var scale: float = clampf(intensity, 0.0, 1.0)
	for alias in shape_indices.keys():
		var weight: float = preset.get(alias, 0.0) * scale
		mesh_instance.set_blend_shape_value(shape_indices[alias], weight)
