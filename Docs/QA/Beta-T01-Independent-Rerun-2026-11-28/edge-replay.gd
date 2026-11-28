extends "../Beta-T07-Performance-Accessibility-2026-11-28/accessibility-replay.gd"

class FieldProbe extends ProbedOpening:
	var movement_request := Vector2.ZERO

	func move_actor(input: Vector2, dt: float) -> float:
		movement_request=input
		return super(input,dt)

var exercises := {}

func input_touch(index: int, at: Vector2, pressed: bool, cancelled:=false) -> void:
	var event:=InputEventScreenTouch.new()
	event.index=index
	event.position=at
	event.pressed=pressed
	event.canceled=cancelled
	root.push_input(event,true)

func input_drag(index: int, at: Vector2, relative: Vector2) -> void:
	var event:=InputEventScreenDrag.new()
	event.index=index
	event.position=at
	event.relative=relative
	root.push_input(event,true)

func reports_fit(stick: Control, safe: Rect2) -> bool:
	var rim:=Rect2(stick.position-Vector2.ONE*52.,Vector2.ONE*104.)
	var thumb:Vector2=stick.position+stick.offset+Vector2(0.,1.)
	var knob:=Rect2(thumb-Vector2.ONE*22.,Vector2.ONE*44.)
	return stick.is_visible_in_tree() and safe.grow(.01).encloses(rim) and safe.grow(.01).encloses(knob)

func world_contact_on_edge(hud: Control, edge: String) -> Dictionary:
	var safe: Rect2=hud._safe_rect()
	var dock: Control=hud.camp_dock
	var blockers:Array[Control]=[hud.quality,dock.pack_button,dock.build,hud.level_continue]
	for button:Control in dock.tabs.values(): blockers.append(button)
	var step:Vector2={"left":Vector2.RIGHT,"right":Vector2.LEFT,"top":Vector2.DOWN,"bottom":Vector2.UP}[edge]
	for relative in [.50,.28,.72,.18,.82,.10,.90,.03,.97]:
		var point:Vector2
		match edge:
			"left": point=Vector2(safe.position.x+2.,safe.position.y+safe.size.y*relative)
			"right": point=Vector2(safe.end.x-2.,safe.position.y+safe.size.y*relative)
			"top": point=Vector2(safe.position.x+safe.size.x*relative,safe.position.y+2.)
			"bottom": point=Vector2(safe.position.x+safe.size.x*relative,safe.end.y-2.)
		if blockers.all(func(node:Control):return not node.is_visible_in_tree() or not node.get_global_rect().grow(2.).has_point(point)):
			return {"origin":point,"step":step}
	return {}

func exercise(label: String, edge: String) -> void:
	var hud:Control=field.opening_hud
	var stick:Control=hud.get_node("MovementThumbstick")
	var found:=world_contact_on_edge(hud,edge)
	if found.is_empty():
		exercises[label+" "+edge]={"covered_by_hud":true}
		return
	var at:Vector2=found.origin
	var step:Vector2=found.step*82.
	var safe:Rect2=hud._safe_rect()
	field.actor.global_position=Vector3(.4,.008,14.6)
	field.actor.velocity=Vector3.ZERO
	field.previous_dry_position=field.actor.global_position
	for i in 5: await physics_frame
	var initial:Vector3=field.actor.global_position
	input_touch(11,at,true)
	await process_frame
	await process_frame
	var acquired:bool=field.touch_id==11 and field.touch_origin.distance_to(at)<.01
	var press_visible:=reports_fit(stick,safe)
	input_drag(11,at+step,step)
	for i in 15: await physics_frame
	for i in 2: await process_frame
	var heading_and_speed:bool=field.movement_request.is_equal_approx(step/82.) and field.touch_origin.distance_to(at)<.01
	var moved:float=initial.distance_to(field.actor.global_position)
	exercises[label+" "+edge]={"acquired":acquired,"pressed_visible":press_visible,"drag_visible":reports_fit(stick,safe),
		"input_preserved":heading_and_speed,"distance_travelled":moved,"safe_rect":str(safe),"draw_center":str(stick.position),"logical_origin":str(at)}
	_assert(label+" "+edge+" accepts a gameplay touch and preserves movement",acquired and heading_and_speed and moved>.20)
	_assert(label+" "+edge+" indicator remains inside the safe area",press_visible and reports_fit(stick,safe))
	if capture_native and edge=="left": await capture(label+"-left-edge")
	input_touch(11,at+step,false,true)
	for i in 5: await physics_frame
	_assert(label+" "+edge+" cancellation clears movement",field.touch_id<0 and field.movement_request.is_zero_approx())

func run() -> void:
	field=FieldProbe.new()
	root.add_child(field)
	for i in 14: await physics_frame
	field.encounters.remaining=900.
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	field.access.values.right_stick=true
	field.access.values.large_ui=true
	field._apply_hud_scale()
	var states := [
		["phone_16_9",Vector2i(1920,1080),2.5,Vector4.ZERO],
		["phone_20_9_inset",Vector2i(2400,1080),3.,Vector4(94.,30.,38.,24.)],
		["tablet_16_10",Vector2i(2560,1600),2.,Vector4.ZERO],
		["tablet_4_3",Vector2i(2732,2048),2.,Vector4.ZERO],
		["fold_outer_landscape",Vector2i(2520,1080),3.,Vector4.ZERO],
		["fold_inner_landscape",Vector2i(2208,1768),2.5,Vector4.ZERO],
		["fold_cover_portrait",Vector2i(540,1260),1.5,Vector4(12.,25.,8.,14.)],
	]
	if capture_native:
		states=[["fold_cover_portrait",Vector2i(540,1260),1.5,Vector4(12.,25.,8.,14.)],
			["fold_unfolded",Vector2i(840,942),2.,Vector4.ZERO]]
	var hud:Control=field.opening_hud
	for state in states:
		hud.emulated_density=state[2]
		hud.emulated_insets=state[3]
		root.size=state[1]
		for i in 8: await process_frame
		hud.reflow()
		for edge: String in ["left","right","top","bottom"]:
			await exercise(state[0], edge)
		_assert(state[0]+" left and right world margins were reachable",not exercises[state[0]+" left"].has("covered_by_hud") and not exercises[state[0]+" right"].has("covered_by_hud"))
	print("T01_EDGE ",JSON.stringify({"checks":checks,"exercises":exercises,
		"thumbstick_sha256":FileAccess.get_sha256("res://field_thumbstick.gd")}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(int(checks.values().has(false)))
