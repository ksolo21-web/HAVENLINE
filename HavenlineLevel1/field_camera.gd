extends RefCounted
## The perspective and lens stay fixed. Composition translates the camera along
## the ground, respecting the actual viewport and the visible HUD panels.

const FOLLOW_RATE := 8.6
const VELOCITY_RATE := 10.0
const LEAD_SECONDS := .35
const MAX_LEAD_METRES := 2.1
const FOLLOW_SPEED_LIMIT := 10.5
const DISCONTINUITY_METRES := 4.5
const TARGET_RANGE := 6.8

var previous_feet := Vector3.INF
var travel := Vector3.ZERO

static func view_span(short_span: float, size: Vector2) -> Vector2:
	if not size.is_finite() or size.x <= 0.0 or size.y <= 0.0: return Vector2.ONE*short_span
	var aspect := size.x / size.y
	return short_span * Vector2(maxf(aspect,1.0),maxf(1.0/aspect,1.0))

static func screen_offset(value: Vector3, basis: Basis) -> Vector2:
	return Vector2(value.dot(basis.x),-value.dot(basis.y))

static func _screen_rect(area: Rect2, canvas: Rect2, span: Vector2) -> Rect2:
	return Rect2(((area.position-canvas.position)/canvas.size-Vector2(.5,.5))*span,area.size/canvas.size*span)

static func _limits(subject: Rect2, window: Rect2) -> Rect2:
	var least := subject.end-window.end
	var most := subject.position-window.position
	return Rect2(least,most-least)

static func _box(at: Vector3, feet: Vector3, basis: Basis, margin: Vector2) -> Rect2:
	return Rect2(screen_offset(at-feet,basis)-margin,margin*2.0)

func _context(world, feet: Vector3, basis: Basis) -> Array[Rect2]:
	var tracked: Vector3 = world.opening_hud.camp_dock.tracked_point()
	if tracked.is_finite() and feet.distance_to(tracked) <= TARGET_RANGE:
		return [_box(tracked,feet,basis,Vector2(.52,.35))]
	var counter = world.counter
	if counter.active and not counter.queue.is_empty() and world.field_env.is_inside_camp(feet):
		if feet.distance_to(counter.service_point.global_position) <= 3.8:
			var result: Array[Rect2] = [_box(counter.food_rest.global_position,feet,basis,Vector2(.48,.26))]
			var waiting: Array[Rect2] = []
			for item in counter.queue:
				var customer: Node3D = item.body
				if not is_instance_valid(customer): continue
				var sides := Vector2(.37,.075)
				var guest := _box(customer.global_position,feet,basis,sides).merge(_box(customer.global_position+Vector3.UP*1.59,feet,basis,sides))
				var order: Node3D = item.request
				if is_instance_valid(order) and order.visible:
					guest = guest.merge(_box(order.global_position+Vector3.UP*.31,feet,basis,Vector2(.40,.22)))
					result.append(guest)
				else:
					result.append(_box(customer.global_position+Vector3.UP*1.35,feet,basis,Vector2(.34,.27)))
					waiting.append(guest)
			result.append_array(waiting)
			return result
	var project: Node3D = world.carry.receivers.get(world.next_project)
	if is_instance_valid(project) and project.is_visible_in_tree() and feet.distance_to(project.global_position) <= TARGET_RANGE:
		var center := screen_offset(project.global_position-feet,basis)
		var outline := Rect2(center,Vector2.ZERO)
		var border := project.get_node_or_null("Brackets") as MeshInstance3D
		if border and border.mesh:
			var box := border.get_aabb()
			for x in [box.position.x,box.end.x]:
				for z in [box.position.z,box.end.z]:
					outline = outline.expand(screen_offset(border.to_global(Vector3(x,box.end.y,z))-feet,basis))
		return [outline.grow(.17)]
	var entrance := Vector3.INF
	var distance := 3.35
	for gate in world.gates:
		if not gate.active: continue
		var at: Vector3 = gate.global_position
		var reach := feet.distance_to(at)
		if reach < distance:
			entrance = at+Vector3.UP*.64
			distance = reach
	if entrance.is_finite(): return [_box(entrance,feet,basis,Vector2(.68,.44))]
	return []

static func quality_plate(button: Button) -> Rect2:
	var rect := button.get_global_rect()
	var skin := button.get_theme_stylebox("normal") as StyleBoxFlat
	# The hit box is deliberately larger than the painted settings tile.
	if skin:
		rect = rect.grow_individual(skin.expand_margin_left,skin.expand_margin_top,skin.expand_margin_right,skin.expand_margin_bottom)
	return rect.grow(4.0)

static func _panel_rects(hud, canvas: Rect2, span: Vector2) -> Array[Rect2]:
	var controls := [hud.plate,hud.objective,hud.camp_dock.nav,hud.camp_dock.build,
		hud.level_continue,hud.get_node_or_null("HomeCompass")]
	var result: Array[Rect2] = [_screen_rect(hud.counts_area.grow(7.0),canvas,span)]
	for control in controls:
		if is_instance_valid(control) and control.visible:
			result.append(_screen_rect(control.get_global_rect().grow(7.0),canvas,span))
	if is_instance_valid(hud.quality) and hud.quality.visible:
		result.append(_screen_rect(quality_plate(hud.quality),canvas,span))
	return result

static func _subtract(choices: Array[Vector2], start: float, end: float) -> Array[Vector2]:
	var remaining: Array[Vector2] = []
	for interval in choices:
		if start > interval.x: remaining.append(Vector2(interval.x,minf(interval.y,start)))
		if end < interval.y: remaining.append(Vector2(maxf(interval.x,end),interval.y))
	return remaining

static func _horizontal(subject: Rect2, view: Rect2, y: float, choices: Array[Vector2], panels: Array[Rect2]) -> Array[Vector2]:
	var edges := _limits(subject,view)
	var result: Array[Vector2] = []
	if y < edges.position.y-.001 or y > edges.end.y+.001: return result
	for interval in choices:
		var fit := Vector2(maxf(interval.x,edges.position.x),minf(interval.y,edges.end.x))
		if fit.x <= fit.y: result.append(fit)
	for panel in panels:
		if panel.position.y < subject.end.y-y-.001 and panel.end.y > subject.position.y-y+.001:
			result = _subtract(result,subject.position.x-panel.end.x,subject.end.x-panel.position.x)
			if result.is_empty(): break
	return result

static func _compose(subjects: Array[Rect2], view: Rect2, panels: Array[Rect2], wish: Vector2) -> Vector2:
	# For a fixed height, every subject leaves one or more horizontal ranges.
	# The optimal height is the preferred one or an edge of a subject/panel.
	var first := _limits(subjects[0],view.grow(-.04))
	if not first.has_area(): return wish
	var heights := PackedFloat32Array([clampf(wish.y,first.position.y,first.end.y),first.position.y,first.end.y])
	for subject in subjects:
		var available := _limits(subject,view)
		for edge in [available.position.y,available.end.y]:
			if edge > first.position.y and edge < first.end.y: heights.append(edge)
		for panel in panels:
			for edge in [subject.end.y-panel.position.y,subject.position.y-panel.end.y]:
				if edge > first.position.y and edge < first.end.y: heights.append(edge)
	var best := wish.clamp(first.position,first.end)
	var highest := 0
	var closest := INF
	var full := (1 << subjects.size())-1
	for y in heights:
		if highest==full and (y-wish.y)*(y-wish.y)>=closest: continue
		var ranges: Array[Vector2] = [Vector2(first.position.x,first.end.x)]
		var score := 0
		for i in subjects.size():
			var allowed := _horizontal(subjects[i],view,y,ranges,panels)
			if allowed.is_empty():
				if i==0: break
				continue
			ranges = allowed
			score |= 1 << (subjects.size()-1-i)
		if score < highest or score==0: continue
		for interval in ranges:
			var point := Vector2(clampf(wish.x,interval.x,interval.y),y)
			var distance := point.distance_squared_to(wish)
			if score>highest or distance<closest:
				best = point
				highest = score
				closest = distance
	return best

func update(world, dt: float) -> void:
	var feet: Vector3 = world.actor.global_position
	var camera: Camera3D = world.camera
	var canvas := camera.get_viewport().get_visible_rect()
	if not feet.is_finite() or not is_finite(dt) or dt<=0.0 or not canvas.has_area() or not canvas.size.is_finite() or not is_finite(camera.size) or camera.size<=0.0: return
	var basis := camera.global_basis
	var ground_up := basis.y.slide(Vector3.UP)
	if ground_up.length_squared() < .01: return
	var span := view_span(camera.size,canvas.size)
	var hud = world.opening_hud
	var inset := minf(canvas.size.x,canvas.size.y)*.027
	var view := _screen_rect(hud._safe_rect().intersection(canvas).grow(-inset),canvas,span)
	var warp := not previous_feet.is_finite() or feet.distance_squared_to(previous_feet)>DISCONTINUITY_METRES*DISCONTINUITY_METRES
	var measured := Vector3.ZERO if warp else ((feet-previous_feet).slide(Vector3.UP)/dt).limit_length(8.0)
	var time := minf(dt,.1)
	travel = Vector3.ZERO if warp else travel.lerp(measured,1.0-exp(-VELOCITY_RATE*time))
	previous_feet = feet
	var head := float(world.layout.actor_height)*basis.y.y
	var lead := Rect2(Vector2(-.51,-head-.105),Vector2(1.02,head+.205))
	if world.snow_truck.mounted: lead = Rect2(Vector2(-1.15,-1.7),Vector2(2.30,1.98))
	var wish := screen_offset((travel*LEAD_SECONDS).limit_length(MAX_LEAD_METRES),basis)
	wish.y -= minf(span.y*.05,camera.size*.13)
	var subjects: Array[Rect2] = [lead]
	var context := _context(world,feet,basis)
	if not context.is_empty():
		wish += (context[0].get_center()*.23).limit_length(camera.size*.17)
	subjects.append_array(context)
	var desired := _compose(subjects,view,_panel_rects(hud,canvas,span),wish)
	var base: Vector3 = feet+world.camera_follow_offset
	var from := screen_offset(camera.global_position-base,basis)
	var shift := desired if warp or not from.is_finite() else from.lerp(desired,1.0-exp(-FOLLOW_RATE*time))
	var permitted := _limits(lead,view)
	if permitted.has_area(): shift = shift.clamp(permitted.position,permitted.end)
	var next := base + basis.x*shift.x - ground_up*(shift.y/ground_up.length_squared())
	camera.global_position = next if warp else camera.global_position.move_toward(next,FOLLOW_SPEED_LIMIT*time)
