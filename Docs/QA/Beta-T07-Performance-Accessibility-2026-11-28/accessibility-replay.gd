extends "res://tests/qa_snow_truck.gd"

class ProbedHUD extends "res://field_hud.gd":
	var emulated_density:=1.
	var emulated_insets:=Vector4.ZERO

	func _pixels_per_dp() -> float:
		return emulated_density

	func _platform_safe_area() -> Rect2:
		if emulated_insets==Vector4.ZERO: return Rect2()
		return Rect2(get_window().position,get_window().size).grow_individual(
			-emulated_insets.x,-emulated_insets.y,-emulated_insets.z,-emulated_insets.w)

class ProbedOpening extends "res://field_opening.gd":
	func create_opening_hud() -> OpeningHUD:
		return ProbedHUD.new()

var records := {}
var capture_native := OS.get_environment("T07_A11Y_NATIVE")=="1"
var suite_path := OS.get_environment("T07_A11Y_DIR")

func _initialize() -> void:
	run.call_deferred()

func tap(point: Vector2) -> void:
	touch(17,point,true)
	await process_frame
	touch(17,point,false)
	for _i in 3: await process_frame

func press_item(dock: Control, id: String) -> void:
	for _page in 6:
		for pair in dock.commands:
			if str(pair[1])==id:
				await tap(pair[0].get_global_rect().get_center())
				return
		var next: Button
		for pair in dock.commands:
			if str(pair[1])=="list_next": next=pair[0]
		if next==null: break
		await tap(next.get_global_rect().get_center())
	_assert("reachable menu command "+id,false)

func pixels_per_canvas() -> Vector2:
	return root.get_stretch_transform().get_scale().abs()

func touch_dimensions(target: Control) -> Vector2:
	return target.get_global_rect().size*pixels_per_canvas()/field.opening_hud._pixels_per_dp()


func capture(name: String) -> void:
	if not capture_native: return
	await process_frame
	RenderingServer.force_draw(false)
	var image := root.get_texture().get_image()
	_assert("native screenshot "+name,image.save_jpg(suite_path.path_join(name+".jpg"),.82)==OK)

func layout_fit(hud: Control, id: String) -> void:
	var dock: Control=hud.camp_dock
	var safe: Rect2=hud._safe_rect()
	var targets: Array[Control]=[hud.quality,dock.pack_button,dock.build]
	for button: Button in dock.tabs.values(): targets.append(button)
	if dock.sheet.visible:
		targets.append(dock.close)
		for pair in dock.commands: targets.append(pair[0])
	var measurements := {}
	var min_touch:=INF
	var inside:=true
	for target in targets:
		var dimensions:=touch_dimensions(target)
		min_touch=minf(min_touch,minf(dimensions.x,dimensions.y))
		var box:=target.get_global_rect()
		inside=inside and safe.grow(.25).encloses(box)
		measurements[String(target.accessibility_name) if not target.accessibility_name.is_empty() else target.name]=[dimensions.x,dimensions.y]
	if dock.sheet.visible:
		for key: String in dock.tabs:
			inside=inside and not dock.sheet.get_global_rect().intersects(dock.tabs[key].get_global_rect())
		inside=inside and not dock.sheet.get_global_rect().intersects(dock.build.get_global_rect())
	var clipping: bool=safe.encloses(hud.objective.get_global_rect()) and (not dock.sheet.visible or safe.grow(.25).encloses(dock.sheet.get_global_rect()))
	_assert(id+" visible touch targets meet the design 48 dp",min_touch>=47.99)
	_assert(id+" menu and HUD fit the tested safe canvas",inside and clipping)
	records[id]={"raster":[root.size.x,root.size.y],"viewport":str(root.get_visible_rect().size),
		"emulated_pixels_per_dp":hud._pixels_per_dp(),"emulated_insets":str(hud.emulated_insets),"canvas_scale":str(pixels_per_canvas()),"min_target_dp":min_touch,"targets":measurements,"safe_targets":inside,"hud_contained":clipping}

func run() -> void:
	field=ProbedOpening.new()
	field.name="HavenlineFieldOpening"
	root.add_child(field)
	camera=field.camera
	truck=field.snow_truck
	for _i in 12: await physics_frame
	field.encounters.remaining=900.
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	var hud: Control=field.opening_hud
	var dock: Control=hud.camp_dock
	var compass: Control=hud.get_node("HomeCompass")
	var states := [
		["phone_16_9",Vector2i(1920,1080),2.5,Vector4.ZERO],
		["phone_20_9",Vector2i(2400,1080),3.,Vector4(94.,30.,38.,24.)],
		["tablet_16_10",Vector2i(2560,1600),2.,Vector4.ZERO],
		["tablet_4_3",Vector2i(2732,2048),2.,Vector4.ZERO],
		["foldable_outer",Vector2i(2520,1080),3.,Vector4.ZERO],
		["foldable_inner",Vector2i(2208,1768),2.5,Vector4.ZERO],
		["portrait_cover",Vector2i(540,1260),1.5,Vector4.ZERO]
	]
	if capture_native:
		states=[["portrait_cover",Vector2i(540,1260),1.5,Vector4.ZERO],["foldable_unfolded_portrait",Vector2i(840,942),2.,Vector4.ZERO]]
	for state in states:
		dock.dismiss()
		hud.emulated_density=state[2]
		hud.emulated_insets=state[3]
		root.size=state[1]
		for _i in 5: await process_frame
		hud.reflow()
		await tap(dock.tabs.Camp.get_global_rect().get_center())
		_assert(state[0]+" open Camp with touch",dock.tab=="Camp")
		await press_item(dock,"accessibility")
		_assert(state[0]+" open Accessibility with touch",dock.tab=="Accessibility")
		layout_fit(hud,state[0])
		_assert(state[0]+" no compass covers Accessibility",not compass.visible)
		await capture(state[0]+"-standard")
		var original_scale:=root.content_scale_factor
		await press_item(dock,"access:large_ui")
		_assert(state[0]+" large HUD changes actual stretch scale",root.content_scale_factor>original_scale)
		var after:=pixels_per_canvas()
		layout_fit(hud,state[0]+"_large")
		await capture(state[0]+"-large")
		await press_item(dock,"access:large_ui")
		_assert(state[0]+" restore standard HUD",is_equal_approx(root.content_scale_factor,original_scale))
		records[state[0]+"_large"]["actual_canvas_scale"]=str(after)
		await tap(dock.close.get_global_rect().get_center())
		_assert(state[0]+" can close the Accessibility sheet",dock.tab.is_empty())
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	await press_item(dock,"accessibility")
	for key in ["reduced_motion","captions","right_stick"]:
		await press_item(dock,"access:"+key)
		_assert("toggled "+key+" through visible menu",field.access.values[key])
	var settings=preload("res://field_accessibility.gd").new()
	settings.load_preferences()
	_assert("preferences reload independently of camp save",settings.values==field.access.values)
	await tap(dock.close.get_global_rect().get_center())
	for _i in 5: await process_frame
	var stick: Control=hud.get_node("MovementThumbstick")
	_assert("configured resting stick is reachable on the right",stick.position.x>hud._safe_rect().get_center().x)
	origin=stick.position
	var actor_before: Vector3=field.actor.global_position
	steer(_heading(Vector3.BACK))
	for _i in 22: await physics_frame
	steer(Vector2.ZERO)
	_assert("actual right-thumb movement starts and releases cleanly",actor_before.distance_to(field.actor.global_position)>.5 and field.touch_id<0)
	var sound_bus:=AudioServer.get_bus_index("Master")
	var original_mute:=AudioServer.is_bus_mute(sound_bus)
	AudioServer.set_bus_mute(sound_bus,true)
	field._event("raid_warning",field.actor.global_position,"boss_arrival")
	_assert("raid caption visible with sound muted",hud.event_caption.visible and hud.event_caption.text=="Raid approaching")
	var health: int=field.player_hp
	field._player_hit(1)
	_assert("damage remains clear without strobe",field.player_hp==health-1 and is_zero_approx(field.flash.color.a) and hud.event_caption.text=="You took damage")
	await capture("muted-damage-caption")
	AudioServer.set_bus_mute(sound_bus,original_mute)
	_assert("reduced-motion build can be funded",_fund("center_hearth"))
	for _i in 20: await physics_frame
	_assert("reduced-motion reveals hearth without optional tween",field.camp_active and (not field.field_env.reveal_tween or not field.field_env.reveal_tween.is_running()))
	await repair_with_touch(hud,dock)
	await check_live_build_controls(hud,dock)
	await check_graphics_presets(hud)
	print("T07_A11Y ",JSON.stringify({"checks":checks,"layouts":records,"scope":{"controller":"The Level 1 trial targets touch and keyboard","raster_emulation":true,"physical_certification":false}}))
	await _close_field()
	quit(int(checks.values().has(false)))

func repair_with_touch(hud: Control, dock: Control) -> void:
	var raid=field.encounters.raids
	var id: String="gate-east"
	raid.clock.condition[id]=raid.clock.hp(id)-6
	var bill: Dictionary=raid.clock.repair_bill(id)
	_assert("damaged gate available for repair fixture",not bill.is_empty())
	for kind: String in bill:
		for bundle in int(bill[kind]):
			field.inventory.collect("c11-repair-%s-%d"%[kind,bundle],kind)
	field.actor.global_position=raid.sites.repair_position(id)
	field.previous_dry_position=field.actor.global_position
	raid.sites.update_notice(.016)
	for _i in 3: await process_frame
	var notice: Control=raid.sites.notice
	_assert("live repair is visible and funded",is_instance_valid(notice) and notice.repair.is_visible_in_tree() and not notice.repair.disabled)
	if not is_instance_valid(notice) or not notice.repair.is_visible_in_tree(): return
	var target: Rect2=notice.repair.get_global_rect()
	var dp:=touch_dimensions(notice.repair)
	_assert("repair touch target meets 48 dp and clears dock",minf(dp.x,dp.y)>=47.99 and not target.intersects(dock.build.get_global_rect()) and not target.intersects(dock.tabs.Camp.get_global_rect()))
	var prior: Dictionary=field.inventory.carried.duplicate()
	await tap(target.position+Vector2(target.size.x*.5,-3.))
	_assert("outside the repair target has no charge",field.inventory.carried==prior and not raid.clock.repair_bill(id).is_empty())
	await tap(target.position+Vector2(target.size.x*.5,3.))
	_assert("the repair accepts touch near the top edge and consumes the exact bill",
		raid.clock.repair_bill(id).is_empty() and bill.keys().all(func(kind: String)->bool: return field.inventory.carried[kind]==prior[kind]-bill[kind]))

func check_live_build_controls(hud: Control, dock: Control) -> void:
	await tap(dock.tabs.Camp.get_global_rect().get_center())
	await press_item(dock,"move")
	var controls: Control=field.camp_layout.overlay
	var dimensions:=touch_dimensions(controls.done)
	_assert("Move equipment opens layout with a reachable Done button",
		field.camp_layout.active and controls.done.is_visible_in_tree() and minf(dimensions.x,dimensions.y)>=47.99)
	await tap(controls.done.get_global_rect().get_center())
	_assert("Done closes placement with touch",not field.camp_layout.active)

func check_graphics_presets(hud: Control) -> void:
	var profiles: Array[String]=["Ultra","High","Low","Ultra"]
	var samples: Array[int]=[Viewport.MSAA_4X,Viewport.MSAA_2X,Viewport.MSAA_DISABLED,Viewport.MSAA_4X]
	var scales: Array[float]=[1.,1.,.75,1.]
	for i in profiles.size():
		if i>0: await tap(hud.quality.get_global_rect().get_center())
		var title: String=profiles[i]
		_assert("gear selects "+title+" step "+str(i),field.graphics.preset_name()==title and hud.quality.accessibility_name.contains(title))
		_assert(title+" sampling and render scale step "+str(i),root.msaa_3d==samples[i] and is_equal_approx(root.scaling_3d_scale,scales[i]))
