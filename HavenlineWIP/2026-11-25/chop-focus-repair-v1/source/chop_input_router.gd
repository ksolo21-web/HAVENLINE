extends RefCounted
## Detached input adapter; opening integration shown only in temporary replay.
const Impact = preload("res://chop_impact_bridge.gd")
var _impact: Impact
var _authority: RefCounted
var _admit_ticket: Callable
var _touch_owner := -1
var _touch_ticket: RefCounted
var _key_held := false
var _mouse_held := false
var _touch_device := -1
var _key_device := -1
var _mouse_device := -1
var _app_focused := true
var _window_focused := true
var _latest_ticket: RefCounted
var _retire_ticket: Callable

func configure(impact: Impact, marker_authority: RefCounted, on_ticket: Callable) -> bool:
	if _impact != null or impact == null or marker_authority == null or not on_ticket.is_valid():
		return false
	_impact = impact
	_authority = marker_authority
	_admit_ticket = on_ticket
	# The existing owner-capability endpoint validates ticket identity and
	# cannot produce a marker strike or retire a different live request.
	_retire_ticket = func(ticket: RefCounted) -> bool: return impact.finish_or_cancel(marker_authority,ticket)
	return true

func focused() -> bool:
	return _app_focused and _window_focused

func notify_focus(is_application: bool, has_focus: bool) -> void:
	var was_focused := focused()
	if is_application:
		_app_focused = has_focus
	else:
		_window_focused = has_focus
	if not was_focused or focused() or _impact == null:
		return
	var prior := _latest_ticket
	_latest_ticket = null
	_touch_ticket = null
	_touch_owner = -1
	_touch_device = -1
	_key_device = -1
	_mouse_device = -1
	_key_held = false
	_mouse_held = false
	for channel: StringName in [&"key_f", &"mouse_primary", &"touch_tree"]:
		_impact.release(channel)
	if prior != null:
		_retire_ticket.call(prior)

## Run before any press hit test. Release is about origin, not where the
## user lifted. On normal release retain the independent playback request.
func release_only(event: InputEvent) -> bool:
	if _impact == null or not focused() or event.device == InputEvent.DEVICE_ID_EMULATION:
		return false
	if event is InputEventScreenTouch and (event.canceled or not event.pressed) and event.index == _touch_owner and event.device == _touch_device and _touch_owner >= 0:
		var prior := _touch_ticket
		_touch_owner = -1
		_touch_ticket = null
		_touch_device = -1
		_impact.release(&"touch_tree")
		if event.canceled and prior != null:
			_impact.finish_or_cancel(_authority,prior)
		return true
	if event is InputEventKey and not event.pressed and not event.echo and event.physical_keycode == KEY_F and _key_held and event.device == _key_device:
		_key_held = false
		_key_device = -1
		_impact.release(&"key_f")
		return true
	if event is InputEventMouseButton and not event.pressed and event.button_index == MOUSE_BUTTON_LEFT and _mouse_held and event.device == _mouse_device:
		_mouse_held = false
		_mouse_device = -1
		_impact.release(&"mouse_primary")
		return true
	return false

## Caller must have resolved original button/keyboard precedence already.
## Non-admitted busy presses still own their physical release, preventing
## a held press from queueing a later swing. No drag ever initiates chop.
func capture_press(event: InputEvent, move_touch: int = -1) -> void:
	if _impact == null or not focused() or event.device == InputEvent.DEVICE_ID_EMULATION or not event.is_pressed():
		return
	var channel := StringName()
	if event is InputEventKey and not event.echo and event.physical_keycode == KEY_F and not _key_held:
		_key_held = true
		_key_device = event.device
		channel = &"key_f"
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and not _mouse_held:
		_mouse_held = true
		_mouse_device = event.device
		channel = &"mouse_primary"
	elif event is InputEventScreenTouch and not event.canceled and event.index >= 0 and event.index != move_touch and _touch_owner < 0:
		_touch_owner = event.index
		_touch_device = event.device
		channel = &"touch_tree"
	if channel == StringName():
		return
	var ticket := _impact.press(channel)
	if channel == &"touch_tree":
		_touch_ticket = ticket
	if ticket != null:
		_latest_ticket = ticket
		_admit_ticket.call(ticket)
