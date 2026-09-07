class_name HavenlineNativeRenderPolicy
extends RefCounted

const UHD := Vector2i(3840, 2160)

static func dimensions(logical_size: Vector2, review := false) -> Vector2i:
	var aspect := maxf(1.0, logical_size.x / maxf(1.0, logical_size.y))
	var minimum := Vector2i(1280, 720) if review else UHD
	# Both dimensions, not merely 8.29 million pixels. No hidden upscaling.
	var height := maxi(minimum.y, int(ceil(float(minimum.x) / aspect)))
	var width := maxi(minimum.x, int(ceil(height * aspect)))
	return Vector2i(width + width % 2, height + height % 2)

static func frame_target(refresh: float) -> int:
	if not is_finite(refresh): return 60
	if refresh >= 119.0: return 120
	if refresh >= 89.0: return 90
	return 60

static func logical_safe_rect(logical_size: Vector2, window_size: Vector2i, safe: Rect2i) -> Rect2:
	if window_size.x <= 0 or window_size.y <= 0:
		return Rect2(Vector2.ZERO, logical_size)
	var bounds := Rect2i(Vector2i.ZERO, window_size)
	var clipped := safe.intersection(bounds)
	if clipped.size.x <= 0 or clipped.size.y <= 0: clipped = bounds
	var scale := logical_size / Vector2(window_size)
	return Rect2(Vector2(clipped.position) * scale, Vector2(clipped.size) * scale)
