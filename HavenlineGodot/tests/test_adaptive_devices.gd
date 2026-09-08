extends SceneTree
const Layout = preload("res://scripts/adaptive_layout.gd")
const RenderPolicy = preload("res://scripts/render_policy.gd")
const Main = preload("res://scripts/main.gd")
var checks: Array = []
var failures: Array = []
func check(label: String, value: bool):
	checks.append({"name":label, "passed":value})
	if not value: failures.append(label)
func _initialize(): call_deferred("run")
func buttons_in(node: Node) -> Array:
	var result: Array = []
	for child in node.get_children():
		if child is Button: result.append(child.text)
		result.append_array(buttons_in(child))
	return result
func run():
	# Layout fixtures, NOT emulated or physically certified Android devices.
	var fixtures := [
		["phone_16_9", Vector2(1920,1080), 420.0, Rect2(0,0,1920,1080)],
		["phone_ultrawide_cutout", Vector2(2400,1080), 440.0, Rect2(80,0,2320,1020)],
		["phone_small", Vector2(1280,720), 320.0, Rect2(0,0,1280,680)],
		["tablet_16_10", Vector2(2560,1600), 280.0, Rect2(0,0,2560,1520)],
		["tablet_4_3", Vector2(2048,1536), 264.0, Rect2(0,0,2048,1536)],
		["tablet_3_2", Vector2(2400,1600), 240.0, Rect2(0,0,2400,1536)],
		["fold_outer", Vector2(2520,1080), 420.0, Rect2(64,0,2456,1020)],
		["fold_inner", Vector2(2208,1840), 360.0, Rect2(0,0,2208,1760)],
		["resized_window", Vector2(1280,800), 160.0, Rect2(120,80,1280,760), Vector2(120,80)]
	]
	for f in fixtures:
		var p: Vector2 = f[1]
		var logical := p * maxf(1920.0 / p.x, 1080.0 / p.y)
		var safe := Layout.safe_rect(logical, p, f[3], f[4] if f.size() > 4 else Vector2.ZERO)
		var scale := Layout.density_scale(logical, p, f[2])
		var layout := Layout.plan(safe, scale)
		check(f[0]+": positive safe area", safe.has_area() and Rect2(Vector2.ZERO,logical).encloses(safe))
		for key in layout.rects:
			check(f[0]+": "+key+" within safe bounds", safe.grow(.02).encloses(layout.rects[key]))
		var menu := Rect2(layout.menu_position, layout.menu_size * scale)
		check(f[0]+": menu inside safe bounds", safe.grow(.02).encloses(menu))
		check(f[0]+": Camp touch target at least 48dp", layout.rects.camp.size.y / scale >= 48 - 0.0001)
		check(f[0]+": native dimensions unchanged by UI scale", RenderPolicy.internal_size(p.x/p.y).x>=3840 and RenderPolicy.internal_size(p.x/p.y).y>=2160)
		check(f[0]+": required layout size supported", layout.minimum_window_supported)
	check("Invalid safe area uses usable window, not empty controls", Layout.safe_rect(Vector2(960,540),Vector2(1920,1080),Rect2()).size==Vector2(960,540))
	check("Unavailable density is handled without NaN", Layout.density_scale(Vector2(960,540),Vector2(1920,1080),NAN)==1.0)
	check("Zero pixel size is safe", Layout.density_scale(Vector2(960,540),Vector2.ZERO,320)==1.0)
	check("Project expands aspect without stretching UI", ProjectSettings.get_setting("display/window/stretch/aspect")=="expand")
	var game := Main.new()
	game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory="user://adaptive-layout-regression"
	game.size=Vector2(1280,720)
	root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	await process_frame
	var original := JSON.stringify(game.sim.snapshot())
	for dims in [Vector2(960,540),Vector2(640,360),Vector2(960,720),Vector2(780,400)]:
		game.size=dims
		game.resize_render()
		game.apply_hud_layout(Rect2(Vector2(12,12),dims-Vector2(24,24)),1.0)
		game.menu.visible=true
		for i in 5: await process_frame
		var safe: Rect2 = game.hud_safe_rect
		check("Sticky return control fits "+str(dims), game.menu.get_global_rect().encloses(game.menu_return_button.get_global_rect()))
		check("Runtime menu fits "+str(dims), safe.grow(.1).encloses(Rect2(game.menu.position,game.menu.size*game.menu.scale)))
		check("Runtime menu is vertically scrollable "+str(dims),game.menu_scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED)
		check("Runtime resize retains game state "+str(dims),JSON.stringify(game.sim.snapshot())==original)
	game.joystick_id=5;game.joystick_origin=Vector2(20,30)
	game.resize_render()
	check("Resize cancels stale touch ownership",game.joystick_id==-1 and game.joystick_origin==Vector2.ZERO)
	game.qa_mode=false
	game.rebuild_menu()
	var normal_labels:=buttons_in(game.menu)
	game.qa_mode=true
	check("Player menu does not ask the player to benchmark",not str(normal_labels).contains("Measure native"))
	game.rebuild_menu()
	check("Explicit QA mode retains measurement instrument",str(buttons_in(game.menu)).contains("QA · Measure native"))
	game.outpost_audio.stop_all()
	await create_timer(.35).timeout
	game.free()
	await process_frame
	print(JSON.stringify({"suite":"adaptive_devices","passed":failures.is_empty(),"checks":checks,"failures":failures,"physical_device_certified":false,"visual_critic_approval":false}))
	quit(0 if failures.is_empty() else 1)
