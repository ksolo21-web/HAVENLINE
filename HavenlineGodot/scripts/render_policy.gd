extends RefCounted

static func internal_size(aspect: float, review: bool = false) -> Vector2i:
	if not is_finite(aspect) or aspect < 1.0: aspect = 1.0
	if review:
		var h := int(ceil(sqrt(float(1280 * 720) / aspect)))
		return Vector2i(int(ceil(h * aspect)), h)
	# Native 4K means BOTH dimensions, not merely an equivalent pixel count.
	var h := maxi(2160, int(ceil(3840.0 / aspect)))
	return Vector2i(int(ceil(h * aspect)), h)
