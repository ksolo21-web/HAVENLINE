extends RefCounted

# The recovered scene has an orthographic span of 13.0 at its authored angle.
const NORMAL_SPAN := 13.0
const MAX_ZOOM := 2.0
var zoom_ratio := 1.0
var fingers: Dictionary = {}
var pair: Array = []
var pinching := false
var start_span := 0.0
var start_ratio := 1.0

func set_ratio(camera: Camera3D, value: float) -> void:
	if not is_finite(value):
		return
	zoom_ratio = clampf(value, 1.0, MAX_ZOOM)
	camera.size = NORMAL_SPAN / zoom_ratio

func reset_gesture() -> void:
	fingers.clear()
	pair.clear()
	pinching = false

func select_pair() -> void:
	pair = fingers.keys().slice(0, 2)
	if pair.size() == 2:
		start_span = fingers[pair[0]].distance_to(fingers[pair[1]])
		start_ratio = zoom_ratio

# Return true when a touch belongs to the zoom recognizer. After a pinch,
# the remaining finger cannot turn into a movement drag until all fingers lift.
func consume(event: InputEvent, camera: Camera3D) -> bool:
	if event is InputEventScreenTouch:
		if event.canceled or not event.pressed:
			if not fingers.has(event.index):
				return true
			var consumed := pinching
			fingers.erase(event.index)
			if fingers.is_empty():
				reset_gesture()
			elif pair.has(event.index):
				select_pair()
			return consumed
		if fingers.has(event.index):
			return true
		fingers[event.index] = event.position
		if fingers.size() == 2:
			pinching = true
			select_pair()
		return pinching
	if event is InputEventScreenDrag:
		if not fingers.has(event.index):
			return true
		fingers[event.index] = event.position
		if pinching and pair.size() == 2 and pair.has(event.index):
			var span: float = fingers[pair[0]].distance_to(fingers[pair[1]])
			if start_span < 2.0:
				select_pair()
			else:
				set_ratio(camera, start_ratio * span / start_span)
		return pinching
	return false
