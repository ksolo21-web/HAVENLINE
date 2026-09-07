extends PanelContainer
# Visible on-device measurement, not a synthetic FPS score. Explicitly reports
# submission timing separately from externally verified display/thermal evidence.
const Record = preload("res://scripts/performance_record.gd")
const DURATION := 1800.0
const WARMUP := 30.0
const REPORT_PATH := "user://environment-device-benchmark.json"
var game: Control
var samples = Record.new()
var warmed := 0.0
var elapsed := 0.0
var previous := 0
var ui_clock := 0.0
var interruptions := 0
var running := true
var native_ok := true
var stats: Label
var stop: Button
var message := ""

func configure(owner_game: Control):
	game = owner_game
	set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	position = Vector2(game.size.x-470, game.size.y-290)
	size = Vector2(438, 200)
	var padding := MarginContainer.new()
	for side in ["left","right","top","bottom"]: padding.add_theme_constant_override("margin_"+side,16)
	add_child(padding)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",10)
	padding.add_child(column)
	stats = Label.new()
	stats.add_theme_font_size_override("font_size",20)
	stats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stats.custom_minimum_size.x = 396
	column.add_child(stats)
	stop = Button.new()
	stop.text = "Stop and save measurements"
	stop.custom_minimum_size.y = 48
	column.add_child(stop)
	stop.pressed.connect(func(): finish(false) if running else queue_free())
	RenderingServer.frame_post_draw.connect(after_draw)
	update_label()

func after_draw():
	if not running or not is_instance_valid(game): return
	var now := Time.get_ticks_usec()
	if game.paused:
		previous = 0
		return
	if previous == 0:
		previous = now
		return
	var milliseconds := float(now-previous)/1000.0
	previous = now
	if milliseconds <= 0 or not is_finite(milliseconds): return
	if warmed < WARMUP:
		warmed += milliseconds / 1000.0
	else:
		var resolution: Vector2i = game.scene_view.size
		samples.resolution(resolution)
		native_ok = native_ok and resolution.x >= 3840 and resolution.y >= 2160 and is_equal_approx(game.scene_view.scaling_3d_scale,1.0)
		samples.sample(milliseconds)
		elapsed += milliseconds / 1000.0
	ui_clock += milliseconds / 1000.0
	if ui_clock >= 1.0:
		ui_clock = 0.0
		update_label()
	if elapsed >= DURATION:
		finish.call_deferred(true)
		running = false

func update_label():
	if not is_instance_valid(stats): return
	position = Vector2(maxf(16,game.size.x-470),maxf(100,game.size.y-290))
	var measured: float = minf(elapsed,DURATION)
	var percent := int(measured / DURATION * 100.0)
	var fps: float = 1000.0*samples.count/samples.sum_ms if samples.sum_ms > 0 else 0.0
	var resolution: Vector2i = game.scene_view.size
	var stage := "Warm-up %d / 30 s" % int(minf(warmed,WARMUP)) if warmed < WARMUP else "Measured %02d:%02d / 30:00 · %d%%" % [int(measured)/60,int(measured)%60,percent]
	stats.text = "NATIVE FRAME TEST · %d × %d\n%s\nAverage submission rate: %.1f FPS\nRender scale %.2f · interruptions %d\nNot a display/thermal certificate." % [resolution.x,resolution.y,stage,fps,game.scene_view.scaling_3d_scale,interruptions]

func finish(completed: bool):
	running = false
	if RenderingServer.frame_post_draw.is_connected(after_draw): RenderingServer.frame_post_draw.disconnect(after_draw)
	var report: Dictionary = samples.report()
	report["completed_thirty_minutes"] = completed and elapsed >= DURATION
	report["warmup_seconds"] = warmed
	report["active_seconds"] = elapsed
	report["interruptions"] = interruptions
	report["native_dimensions_and_scale_maintained"] = native_ok and samples.count > 0
	report["platform"] = OS.get_name()
	report["model"] = OS.get_model_name()
	report["gpu"] = RenderingServer.get_video_adapter_name()
	report["renderer"] = RenderingServer.get_current_rendering_method()
	report["engine"] = Engine.get_version_info().string
	report["environment_revision"] = game.ENVIRONMENT_REVISION
	report["display_presentation_verified"] = false
	report["physical_device_validated"] = false
	report["thermal_validated"] = false
	report["sustained_4k60_certified"] = false
	report["limitations"] = ["Measured engine submission intervals, not presented-frame timestamps.","Device identity is reported, not independently attested.","External sustained presentation and thermal evidence are still required.","Only currently implemented and visible game content was measured."]
	var file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(report,"\t"))
		file.close()
		message = "Measurements saved on this device."
	else: message = "Report could not be saved: error %d" % FileAccess.get_open_error()
	stats.text = "%s\n%.1f FPS average · P99 %.2f ms\n%d × %d · %.0f s measured\n%s\nDisplay/thermal approval still pending." % ["30-minute test completed" if report.completed_thirty_minutes else "Test stopped — not completed",report.average_engine_fps,report.p99_ms,game.scene_view.size.x,game.scene_view.size.y,elapsed,message]
	stop.text = "Close measurements"

func _notification(what: int):
	if what == NOTIFICATION_APPLICATION_PAUSED:
		if running: interruptions += 1
		previous = 0
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		previous = 0

func _exit_tree():
	if RenderingServer.frame_post_draw.is_connected(after_draw): RenderingServer.frame_post_draw.disconnect(after_draw)
