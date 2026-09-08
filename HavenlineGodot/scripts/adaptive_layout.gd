extends RefCounted
# Pure layout calculations; no device-name switch or manual phone/tablet mode.
# Window-local safe areas are kept separate from the native 3D render target.

static func safe_rect(logical: Vector2, pixels: Vector2, screen_area: Rect2,
		window_origin: Vector2 = Vector2.ZERO) -> Rect2:
	var full := Rect2(Vector2.ZERO, logical)
	if not logical.is_finite() or logical.x <= 0 or logical.y <= 0:
		return Rect2()
	if not pixels.is_finite() or pixels.x <= 0 or pixels.y <= 0:
		return full
	if screen_area.size.x <= 0 or screen_area.size.y <= 0:
		return full
	var local := Rect2(screen_area.position - window_origin, screen_area.size)
	local = local.intersection(Rect2(Vector2.ZERO, pixels))
	if not local.has_area(): return full
	return Rect2(local.position * logical / pixels, local.size * logical / pixels)

static func density_scale(logical: Vector2, pixels: Vector2, dpi: float) -> float:
	if not pixels.is_finite() or pixels.x <= 0 or pixels.y <= 0: return 1.0
	if not is_finite(dpi) or dpi < 72 or dpi > 1200: return 1.0
	# UI coordinates per Android density-independent pixel, not 3D render scale.
	return maxf(logical.x / pixels.x, logical.y / pixels.y) * dpi / 160.0

static func plan(safe: Rect2, ui_scale: float = 1.0) -> Dictionary:
	var s := ui_scale if is_finite(ui_scale) and ui_scale > 0 else 1.0
	var available := safe.size / s
	var margin := 16.0
	var width := maxf(1.0, available.x - 2 * margin)
	var camp_width := minf(112.0, width * 0.3)
	var menu_size := Vector2(minf(780.0, width), maxf(1.0, minf(620.0, available.y - 2 * margin)))
	var compact := available.x < 1100.0
	var objective_width := width if compact else minf(620.0, width - 520.0)
	var objective_x := margin if compact else (available.x - objective_width) / 2.0
	var objective_y := 106.0 if compact else 20.0
	var rects := {
		"status": Rect2(margin, margin, maxf(1.0, width - camp_width - 16), 30),
		"climate": Rect2(margin, 52, maxf(1.0, width - camp_width - 16), 46),
		"objective": Rect2(objective_x, objective_y, objective_width, 54),
		"hint": Rect2(margin, maxf(0.0, available.y - 44), width, 28),
		"camp": Rect2(available.x - margin - camp_width, margin, camp_width, 48)
	}
	for key in rects:
		var r: Rect2 = rects[key]
		rects[key] = Rect2(safe.position + r.position * s, r.size * s)
	return {"scale":s, "safe":safe, "compact":compact, "rects":rects,
		"menu_size":menu_size, "menu_position":safe.get_center() - menu_size * s / 2,
		"joystick_radius":64 * s, "minimum_window_supported":available.x >= 320 and available.y >= 240}
