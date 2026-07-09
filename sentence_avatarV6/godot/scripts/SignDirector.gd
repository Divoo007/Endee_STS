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

const DEFAULT_SECONDS_PER_WORD := 1.8

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
}

var _skeleton: Skeleton3D
var _mesh: MeshInstance3D
var _face_shape_indices := {}
var _hand_rig := HandRig.new()
var _arm_rig := ArmRig.new()
var _idle_t := 0.0
var _current_emotion := "relaxed"  # set per performance; drives emotion head motion
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
	# Signing-space framing. Rather than move the lens in close (which shrinks
	# nothing but badly foreshortens signs that reach *toward* the viewer --
	# you/drink/tomorrow -- and risks clipping the forward hand), we keep a
	# normal working distance and narrow the FOV (telephoto): that enlarges
	# the upper body to fill the frame AND flattens perspective so a forward
	# point reads as a point instead of collapsing into the hand. A small
	# sideways offset gives a gentle near-frontal 3/4 so forward reach still
	# shows some depth, while staying frontal enough to read as signing.
	cam.fov = 41.0
	var focus := head_pos.lerp(chest_pos, 0.4)
	cam.global_position = focus + Vector3(0.55, 0.08, 1.4)
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
	for wrist_bone in ["LeftWrist", "RightWrist"]:
		var basis_a := _bone_delta_basis(a, wrist_bone)
		var basis_b := _bone_delta_basis(b, wrist_bone)
		sample[wrist_bone] = basis_a.slerp(basis_b, local_t)
	sample["curl_left"] = _lerp_finger_curls(_finger_curls(a, "Left"), _finger_curls(b, "Left"), local_t)
	sample["curl_right"] = _lerp_finger_curls(_finger_curls(a, "Right"), _finger_curls(b, "Right"), local_t)
	return sample


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
	_hand_rig.apply_fingers({"Left": sample["curl_left"], "Right": sample["curl_right"]}, 0.0, wrist_deltas)


# Interim, current-avatar emotion HEAD motion. On the realistic avatar this is
# replaced/augmented by finer face controls (one-brow raise, cheek lift, eye
# narrow). Angry needs no head motion (the furrow carries it via the blend
# shape); Happy nods gently; Question cocks the head (stand-in for a raised brow).
func _emotion_head_delta() -> Basis:
	match _current_emotion:
		"happy":
			return Basis(Vector3.RIGHT, deg_to_rad(sin(_idle_t * 3.0) * 5.0))
		"question":
			return Basis(Vector3.FORWARD, deg_to_rad(11.0))
		_:
			return Basis.IDENTITY


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


## Core playback loop shared by both entry points. Plays the gloss `words` in
## order, each looked up in keyframes_by_word, holding `emotion` on the face.
func _perform(sentence: String, emotion: String, words: Array, keyframes_by_word: Dictionary,
		seconds_per_word: float, quit_when_done: bool) -> void:
	_run_id += 1
	var my_run_id := _run_id

	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel

	sentence_label.text = "\"%s\"" % sentence
	emotion_label.text = emotion.to_upper()
	_current_emotion = emotion
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
	var raw: String = config.get("sentence", "")
	var all_keyframes: Dictionary = config.get("keyframes", {})
	var seconds_per_word: float = config.get("seconds_per_word", DEFAULT_SECONDS_PER_WORD)
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


func _setup_web_bridge() -> void:
	var word_label: Label = $CaptionLayer/WordLabel
	var sentence_label: Label = $CaptionLayer/SentenceLabel
	var emotion_label: Label = $CaptionLayer/EmotionLabel
	word_label.text = "READY"
	sentence_label.text = "Type a sentence ending in (Question), (Happy) or (Angry), then press Perform"
	emotion_label.text = ""
	_js_perform_callback = JavaScriptBridge.create_callback(_on_web_perform)
	var window := JavaScriptBridge.get_interface("window")
	window.godotPerform = _js_perform_callback
	JavaScriptBridge.eval("window.godotReady = true; if (window.onGodotReady) window.onGodotReady();", true)
