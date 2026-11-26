extends SceneTree
## Exercise the trial through the viewport input path with real touch IDs.
var checks := {}
var world
func _initialize() -> void:
	call_deferred("run")

func touch(id: int, point: Vector2, pressed: bool, canceled := false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = id
	event.pressed = pressed
	event.canceled = canceled
	event.position = point
	root.push_input(event, true)

func drag(id: int, point: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = id
	event.position = point
	root.push_input(event, true)

func run() -> void:
	world = preload("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await process_frame
	var basis: Basis = world.camera.global_basis
	var mouse_area := root.get_visible_rect().size * Vector2(.48,.7)
	var a := mouse_area
	var b := a + Vector2(120,0)
	checks["default authored angle and normal span"] = world.camera.size == 13.0 and world.get_zoom_ratio() == 1.0
	checks["Ultra enabled at native resolution and 4x MSAA"] = world.graphics.ultra and root.msaa_3d == Viewport.MSAA_4X and is_equal_approx(root.scaling_3d_scale, minf(1.0,minf(3840.0 / maxf(root.size.x,root.size.y),2160.0 / minf(root.size.x,root.size.y))))
	checks["textured scene materials use anisotropic filtering"] = not world.graphics.originals.is_empty() and world.graphics.originals.keys().all(func(m): return m.texture_filter == BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC)
	touch(17,a,true)
	drag(17,a+Vector2(20,0))
	drag(81,a)
	checks["one finger moves and an unrelated drag leaves it owned"] = world.touch_id == 17 and world.touch_origin.distance_to(world.touch_now) > 5
	var first: Vector2 = world.touch_now
	touch(3,b,true)
	checks["second finger releases movement stick"] = world.touch_id == -1
	drag(3,first + (b-first) * 1.5)
	checks["span ratio drives proportional zoom"] = is_equal_approx(world.get_zoom_ratio(), 1.5)
	drag(3,first + (b-first) * 3)
	checks["pinch clamps at two times"] = is_equal_approx(world.get_zoom_ratio(),2) and world.camera.size == 6.5
	touch(5,b+Vector2(0,50),true)
	drag(5,b+Vector2(11,70))
	checks["third finger does not disturb active pinch"] = world.get_zoom_ratio() == 2
	touch(3,b,false,true)
	var spare := b+Vector2(11,70)
	drag(5,spare)
	checks["replacement finger rebases without zoom jump"] = world.get_zoom_ratio() == 2 and world.touch_id < 0
	drag(5,first + (spare-first)*.2)
	checks["pinch clamps at authored normal view"] = world.get_zoom_ratio() == 1.0 and basis.is_equal_approx(world.camera.global_basis)
	touch(5,spare,false)
	drag(17,a+Vector2(50,0))
	checks["surviving finger cannot take over movement"] = world.touch_id < 0
	touch(17,a,false)
	touch(9,a,true)
	drag(9,b)
	checks["new single-finger gesture acquires movement"] = world.touch_id == 9
	touch(9,b,false,true)
	checks["canceled movement clears held input"] = world.touch_id < 0 and world.trial_camera.fingers.is_empty()
	var button: Vector2 = world.graphics.quality_button.get_global_rect().get_center()
	touch(8,button,true)
	touch(8,button,false)
	checks["graphics control selects standard without movement"] = not world.graphics.ultra and world.touch_id < 0 and root.msaa_3d == Viewport.MSAA_DISABLED
	touch(12,button,true)
	touch(12,button,false)
	checks["graphics control restores Ultra"] = world.graphics.ultra and root.msaa_3d == Viewport.MSAA_4X
	touch(2,a,true)
	touch(6,b,true)
	root.focus_exited.emit()
	drag(2,b)
	checks["focus loss cancels stick and pinch ownership"] = world.touch_id < 0 and world.trial_camera.fingers.is_empty()
	var hud = world.opening_hud
	var opening_layout = {"width": hud.plate.size.x, "height": hud.plate.size.y, "gate_height": hud.gate.size.y, "new_required_chapter_and_hp":hud.chapter.visible and hud.health_text.visible}
	print("FIELD_HUD ",JSON.stringify(opening_layout))
	checks["trial canvas fills the window"] = root.content_scale_aspect == Window.CONTENT_SCALE_ASPECT_EXPAND and root.get_screen_transform().origin.length() < 2
	checks["camera uses the short axis"] = world.camera.keep_aspect == (Camera3D.KEEP_WIDTH if root.size.y > root.size.x else Camera3D.KEEP_HEIGHT)
	checks["Ultra preserves visible ground inside shadows"] = is_equal_approx(world.graphics.lights[0].shadow_opacity, .74)
	var values := {"suite":"orbit_camera","checks":checks,"renderer":RenderingServer.get_current_rendering_method(),"framebuffer":str(root.size),"scene_draw_scale":root.scaling_3d_scale,"quality":world.graphics.quality_button.text,"filtered_materials":world.graphics.originals.size()}
	print(JSON.stringify(values))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for i in 5: await process_frame
	quit(1 if checks.values().has(false) else 0)
