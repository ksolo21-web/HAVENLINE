extends "res://previews/integrated_opening.gd"
## This opt-in scene exercises an ephemeral input-to-intent path only. It never
## binds a default action, awards anything, or reads/writes a real receipt.
const Intent = preload("res://previews/manual_fishing_intent.gd")
const FixtureRiver = preload("res://river_geometry.gd")
const FIXTURE_BANK := Vector2(4.8, -2.9553380834572076)
const FIXTURE_KEY := KEY_G
const CAST_PROMPT := "Cast [G]"
const CAST_ACK := "Input noted"
const CAST_EDGE := 14.0
const CAST_BUTTON_HEIGHT := 54.0
var cast_button: Button
var last_cast_intent: Dictionary = {}
var cast_intent_count := 0
var _casting := Intent.new()
var _bound_cast := false
var _cast_owner := ""
var _cast_touch := -1
var _cast_touch_device := 0
var _cast_sequence := 0
var _was_eligible := false
var _cast_slot_fits := false

func _ready() -> void:
	super._ready()
	if not bound:
		return
	var terrain_at_bank := Terrain.sample(FIXTURE_BANK)
	if not terrain_at_bank.get("valid", false):
		return
	var fixture_aim := FIXTURE_BANK.lerp(FixtureRiver.center_at_x(FIXTURE_BANK.x), .66)
	# Reuse the isolated intent fixture's exact parameters, not gameplay tuning.
	# This binding exists only when this specifically named opt-in scene is loaded.
	_bound_cast = _casting.bind({
		"admitted":true, "spot_id":"shore-intent-fixture", "bank_xz":FIXTURE_BANK, "aim_xz":fixture_aim,
		"bank_side":bank_side, "foot_radius":float(layout.actor_radius),
		"stand_tolerance":.14, "height_tolerance":.10,
		"cast_range":Vector3(FIXTURE_BANK.x, float(terrain_at_bank.height), FIXTURE_BANK.y).distance_to(
			Vector3(fixture_aim.x, FixtureRiver.WATER_Y, fixture_aim.y)) + .2,
		"min_facing_dot":.75, "keycode":int(FIXTURE_KEY)
	})
	if not _bound_cast:
		return
	cast_button = opening_hud._button()
	cast_button.name = "OptInCastActionOnly"
	cast_button.text = CAST_PROMPT
	cast_button.add_theme_font_size_override("font_size", 19)
	cast_button.add_theme_stylebox_override("normal", opening_hud._plate_style(Color("#264662"), Color("#86b5cc")))
	var skin := cast_button.get_theme_stylebox("normal") as StyleBoxFlat
	skin.content_margin_left = 8.0
	skin.content_margin_right = 8.0
	get_viewport().size_changed.connect(_layout_cast)
	_layout_cast()

func _layout_cast() -> void:
	if not is_instance_valid(cast_button):
		return
	var visible_size := get_viewport().get_visible_rect().size
	var left_gap := minf(gate_button.position.x, tree_button.position.x) - CAST_EDGE - 10.0
	var width := minf(136.0, left_gap)
	var font := cast_button.get_theme_font("font")
	var sz := cast_button.get_theme_font_size("font_size")
	var required := maxf(font.get_string_size(CAST_PROMPT, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x,
		font.get_string_size(CAST_ACK, HORIZONTAL_ALIGNMENT_LEFT, -1, sz).x) + 16.0
	_cast_slot_fits = visible_size.y >= CAST_BUTTON_HEIGHT + 2.0 * CAST_EDGE and width >= required
	cast_button.position = Vector2(CAST_EDGE, maxf(CAST_EDGE, visible_size.y - CAST_EDGE - CAST_BUTTON_HEIGHT))
	cast_button.size = Vector2(maxf(1.0, width), CAST_BUTTON_HEIGHT)
	_refresh_cast()

func _refresh_cast() -> void:
	if not is_instance_valid(cast_button):
		return
	var eligible := bound and _casting.eligibility(self, actor, camera) == "eligible"
	if not eligible or not _was_eligible:
		cast_button.text = CAST_PROMPT
	_was_eligible = eligible
	cast_button.visible = eligible and _cast_slot_fits

func _physics_process(dt: float) -> void:
	super._physics_process(dt)
	_refresh_cast()

func _submit_cast(event: InputEventKey) -> void:
	_cast_sequence += 1
	var intent := _casting.capture(event, _cast_sequence, self, actor, camera)
	if intent.get("status") == "intent":
		last_cast_intent = intent
		cast_intent_count += 1
		cast_button.text = CAST_ACK

func _submit_touch_edge(pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = FIXTURE_KEY
	event.pressed = pressed
	_submit_cast(event)

func _input(event: InputEvent) -> void:
	if not _bound_cast or not bound:
		super._input(event)
		return

	var key := event as InputEventKey
	var is_cast_key := key != null and key.physical_keycode == FIXTURE_KEY
	var is_screen_pointer := event is InputEventScreenTouch or event is InputEventScreenDrag
	# Reject emulation before it can claim or release ownership.
	if event.device == InputEvent.DEVICE_ID_EMULATION and (is_cast_key or is_screen_pointer):
		return

	if is_cast_key:
		if key.pressed:
			if touch_id >= 0:
				return
			if not key.echo and _cast_owner.is_empty():
				_cast_owner = "keyboard"
			if _cast_owner == "keyboard":
				_submit_cast(key)
		elif _cast_owner == "keyboard":
			_submit_cast(key)
			_cast_owner = ""
		return

	var pointer: Variant = event
	if is_screen_pointer and _cast_owner == "touch" and pointer.index == _cast_touch:
		# Ignore coincident foreign fingerprints before the base index-only
		# handler can mistake them for an ordinary pointer release/drag.
		if event.device != _cast_touch_device:
			return
		if event is InputEventScreenTouch and not event.pressed:
			_submit_touch_edge(false)
			_cast_owner = ""
			_cast_touch = -1
			_cast_touch_device = 0
		return

	if event is InputEventScreenTouch:
		# Preserve inherited gate and tree priority for genuine touches.
		if event.pressed and cast_button.is_visible_in_tree() and cast_button.get_global_rect().has_point(event.position):
			if touches_gate_button(event.position) or touches_tree_button(event.position):
				super._input(event)
			elif _cast_owner.is_empty() and touch_id < 0:
				_cast_owner = "touch"
				_cast_touch = event.index
				_cast_touch_device = event.device
				_submit_touch_edge(true)
			return

	super._input(event)
