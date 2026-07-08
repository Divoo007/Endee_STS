extends Node3D
## Sign-language prototype. Two entry points into the exact same animation
## code (see _perform() below):
##
## 1. CLI/video mode (render_signs.py): reads a JSON config (`-- --config
##    <path>`) with one sentence already tokenized into words, a per-word
##    keyframe list, and a single emotion; renders and quits (see _run()).
## 2. Web mode (index.html running the Web export): a JS bridge lets the
##    page call perform_web(sentence, emotion) with a *live* sentence typed
##    by the user; words are looked up in the same keyframe data, now
##    bundled at res://data/word_signs.json instead of arriving via
##    --config, and the avatar keeps running afterward waiting for the next
##    submission instead of quitting.
##
## Either way, per-word keyframe data comes from ../../sign_words.py (see
## export_word_signs.py for how it becomes data/word_signs.json) and the
## sampling/posing math below is untouched between the two modes.

const FaceExpressions = preload("res://scripts/face_expressions.gd")
const HandRig = preload("res://scripts/hand_rig.gd")
const ArmRig = preload("res://scripts/arm_rig.gd")

const DEFAULT_SECONDS_PER_WORD := 1.6
const EMOTIONS := ["happy", "sad", "angry", "surprised", "relaxed"]

const AXES := {
	"RIGHT": Vector3.RIGHT,
	"UP": Vector3.UP,
	"FORWARD": Vector3.FORWARD,
}

var _skeleton: Skeleton3D
var _mesh: MeshInstance3D
var _face_shape_indices := {}
var _hand_rig := HandRig.new()
var _arm_rig := ArmRig.new()
var _idle_t := 0.0
var _word_signs_data := {}  # loaded lazily from res://data/word_signs.json
var _run_id := 0            # bumped on every perform_web() call so a new
                             # submission cancels whichever one is still playing
var _js_perform_callback  # must be kept alive (JavaScriptBridge.create_callback
                           # result is refcounted) for as long as JS can call it --
                           # a local var here would be GC'd as soon as _ready() returns


func _ready() -> void:
	_skeleton = $Avatar/GeneralSkeleton
	_mesh = _skeleton.get_node("body")
	_face_shape_indices = FaceExpressions.index_shapes(_mesh.mesh)
	_hand_rig.build(_skeleton)
	_arm_rig.build(_skeleton)
	_frame_camera()
	if OS.has_feature("web"):
		_setup_web_bridge()
	else:
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
	cam.global_position = focus + Vector3(0, 0.02, 1.35)
	cam.look_at(focus, Vector3.UP)


func _bone_delta_basis(kf: Dictionary, bone_name: String) -> Basis:
	if kf.has(bone_name):
		var p: Dictionary = kf[bone_name]
		var axis: Vector3 = AXES.get(p.get("axis", "RIGHT"), Vector3.RIGHT)
		return Basis(axis, deg_to_rad(float(p.get("angle", 0.0))))
	return Basis.IDENTITY


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
	return result


func _lerp_finger_curls(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var result := {}
	for finger in HandRig.FINGER_NAMES:
		result[finger] = lerpf(float(a.get(finger, 0.0)), float(b.get(finger, 0.0)), t)
	return result


## Samples a word's keyframe list at fraction (0-1) of that word's duration,
## returning {bone_name: delta Basis, "curl_left": per-finger dict,
## "curl_right": per-finger dict}.
func _sample_word(keyframes: Array, frac: float) -> Dictionary:
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
	var sample := {}
	for bone_name in ArmRig.POSE_ORDER:
		var basis_a := _bone_delta_basis(a, bone_name)
		var basis_b := _bone_delta_basis(b, bone_name)
		sample[bone_name] = basis_a.slerp(basis_b, local_t)
	sample["curl_left"] = _lerp_finger_curls(_finger_curls(a, "Left"), _finger_curls(b, "Left"), local_t)
	sample["curl_right"] = _lerp_finger_curls(_finger_curls(a, "Right"), _finger_curls(b, "Right"), local_t)
	return sample


func _apply_sample(sample: Dictionary) -> void:
	var bob := sin(_idle_t * 1.6) * 0.01
	_arm_rig.apply(sample, bob)
	_hand_rig.apply_fingers({"Left": sample["curl_left"], "Right": sample["curl_right"]}, 0.0)


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


## Core playback loop shared by both entry points -- CLI/video mode and web
## mode differ only in where (sentence, emotion, words, keyframes_by_word)
## come from and whether the scene quits when done. The per-word sampling/
## posing itself (_sample_word/_apply_sample) is identical either way.
func _perform(sentence: String, emotion: String, words: Array, keyframes_by_word: Dictionary,
		seconds_per_word: float, quit_when_done: bool) -> void:
	_run_id += 1
	var my_run_id := _run_id

	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel

	sentence_label.text = "\"%s\"" % sentence
	emotion_label.text = emotion.to_upper()
	FaceExpressions.apply(_mesh, _face_shape_indices, emotion)

	for word_v in words:
		if my_run_id != _run_id:
			return  # superseded by a newer web submission
		var word: String = word_v
		word_label.text = word.to_upper()
		var keyframes: Array = keyframes_by_word.get(word, [])
		if keyframes.is_empty():
			await get_tree().create_timer(seconds_per_word).timeout
			continue
		var elapsed := 0.0
		while elapsed < seconds_per_word:
			if my_run_id != _run_id:
				return
			_idle_t += get_process_delta_time()
			var frac := clampf(elapsed / seconds_per_word, 0.0, 1.0)
			_apply_sample(_sample_word(keyframes, frac))
			await get_tree().process_frame
			elapsed += get_process_delta_time()
		_apply_sample(_sample_word(keyframes, 1.0))

	if my_run_id == _run_id:
		word_label.text = "DONE"

	if quit_when_done:
		get_tree().quit()


func _run() -> void:
	var config := _read_config()
	var sentence: String = config.get("sentence", "")
	var emotion: String = config.get("emotion", "relaxed")
	var words: Array = config.get("words", [])
	var keyframes_by_word: Dictionary = config.get("keyframes", {})
	var seconds_per_word: float = config.get("seconds_per_word", DEFAULT_SECONDS_PER_WORD)
	_perform(sentence, emotion, words, keyframes_by_word, seconds_per_word, true)


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
	return _word_signs_data


func _tokenize(sentence: String) -> Array:
	var lower := sentence.to_lower()
	var words: Array = []
	var current := ""
	for i in range(lower.length()):
		var c := lower[i]
		if c >= "a" and c <= "z":
			current += c
		elif current != "":
			words.append(current)
			current = ""
	if current != "":
		words.append(current)
	return words


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


## Called from the browser via the window.godotPerform JS bridge (see
## _setup_web_bridge) with a live, user-typed sentence.
func perform_web(sentence: String, emotion: String) -> void:
	if not EMOTIONS.has(emotion):
		emotion = "relaxed"
	var words := _tokenize(sentence)
	if words.is_empty():
		_report_web_error("Enter a sentence to sign.")
		return
	var data := _load_word_signs()
	var unknown: Array = []
	for w in words:
		if not data.has(w):
			unknown.append(w)
	if not unknown.is_empty():
		_report_web_error("No sign data for: %s" % ", ".join(unknown))
		return
	var keyframes_by_word := {}
	for w in words:
		keyframes_by_word[w] = data[w]
	_perform(sentence, emotion, words, keyframes_by_word, DEFAULT_SECONDS_PER_WORD, false)


func _on_web_perform(args: Array) -> void:
	var sentence: String = String(args[0]) if args.size() > 0 else ""
	var emotion: String = String(args[1]) if args.size() > 1 else "relaxed"
	perform_web(sentence, emotion)


func _setup_web_bridge() -> void:
	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel
	word_label.text = "READY"
	sentence_label.text = "Enter a sentence and emotion, then press Perform"
	emotion_label.text = ""
	_js_perform_callback = JavaScriptBridge.create_callback(_on_web_perform)
	var window := JavaScriptBridge.get_interface("window")
	window.godotPerform = _js_perform_callback
	JavaScriptBridge.eval("window.godotReady = true; if (window.onGodotReady) window.onGodotReady();", true)
