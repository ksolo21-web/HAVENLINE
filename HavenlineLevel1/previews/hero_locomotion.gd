extends RefCounted
## Optional opening: play only the three clips already embedded in Character1.
## CharacterBody remains the sole owner of movement. No animation root motion
## is applied to the actor, and the imported scene/clip resources are untouched.
const LOOP_LIBRARY := &"l1_hero_preview"
const SOURCE_KEYS := {"idle": "presetbipedidle", "walk": "presetbipedwalk", "run": "presetbipedrun"}
const MOVE_MIN := 0.08
const RUN_ENTER := 3.0
const RUN_EXIT := 2.65
const BLEND_SECONDS := 0.10

var player: AnimationPlayer
var current := ""

func bind(visual: Node3D) -> bool:
	if not is_instance_valid(visual) or is_instance_valid(player):
		return false
	var matches := visual.find_children("*", "AnimationPlayer", true, false)
	if matches.size() != 1:
		return false
	var imported := matches[0] as AnimationPlayer
	if imported.has_animation_library(LOOP_LIBRARY):
		return false
	var clips := {}
	for animation_name: StringName in imported.get_animation_list():
		# glTF/scene import may sanitize colon separators, but no substring or
		# first-match fallback is allowed, and duplicate matches fail closed.
		var full := String(animation_name)
		var leaf := full.get_slice("/", full.get_slice_count("/") - 1)
		var key := leaf.to_lower().replace(":", "").replace("_", "").replace(" ", "")
		for state: String in SOURCE_KEYS:
			if key != SOURCE_KEYS[state]:
				continue
			if clips.has(state):
				return false
			clips[state] = imported.get_animation(animation_name)
	if clips.size() != SOURCE_KEYS.size():
		return false
	var local := AnimationLibrary.new()
	for state: String in SOURCE_KEYS:
		var source := clips.get(state) as Animation
		if source == null or not is_finite(source.length) or source.length <= 0.0:
			return false
		var loop := source.duplicate() as Animation
		if loop == null:
			return false
		loop.loop_mode = Animation.LOOP_LINEAR
		if local.add_animation(StringName(state), loop) != OK:
			return false
	if imported.add_animation_library(LOOP_LIBRARY, local) != OK:
		return false
	player = imported
	_play("idle")
	return true

func observe(planar_speed: float, grounded: bool) -> void:
	if not is_instance_valid(player):
		return
	if not grounded or not is_finite(planar_speed) or planar_speed < MOVE_MIN:
		_play("idle")
		return
	var threshold := RUN_EXIT if current == "run" else RUN_ENTER
	_play("run" if planar_speed >= threshold else "walk")

func _play(state: String) -> void:
	if state == current:
		return
	var clip := StringName(String(LOOP_LIBRARY) + "/" + state)
	if not player.has_animation(clip):
		return
	player.play(clip, 0.0 if current.is_empty() else BLEND_SECONDS)
	current = state
