extends Control
const Surface = preload("res://scripts/outpost_surface.gd")
var simulation
var camera: Camera3D
var view: SubViewport
var descriptor: Dictionary = {}
var anchor := Vector2.ZERO
var toast := ""
var toast_time := 0.0

static func describe(sim) -> Dictionary:
	if sim.action.is_empty(): return {}
	var kind: String = sim.action.kind
	var id: String = str(sim.action.id)
	var seconds := 0.5
	match kind:
		"gather":
			for r in sim.resources:
				if r.id == id: seconds = float(sim.tuning.gatherSecondsPerUnit[r.kind])
		"deposit": seconds = sim.tuning.furnaceDepositSecondsPerUnit
		"rescue": seconds = sim.tuning.survivorRescueSeconds
		"build": seconds = sim.tuning.playerConstructionSecondsPerUnit
		"repair", "defense_repair": seconds = sim.tuning.furnaceRepairSecondsPerUnit
		"enemy": seconds = sim.tuning.wolf.playerHitSeconds
		_: return {}
	var key := kind + ":" + id
	return {"kind":kind, "position":sim.action.position, "duration":seconds,
		"progress":clampf(float(sim.action_clocks.get(key,0.0))/seconds,0.0,1.0),
		"paused_by_movement":sim.velocity.length() >= 0.2}

func configure(sim, cam: Camera3D, viewport: SubViewport):
	simulation=sim; camera=cam; view=viewport
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func refresh(dt: float, paused: bool):
	if not paused: toast_time=maxf(0.0,toast_time-dt)
	descriptor=describe(simulation)
	if not descriptor.is_empty():
		var p: Vector2=descriptor.position
		var world_point:=Vector3(p.x,Surface.height_at(p)+.13,p.y)
		anchor=camera.unproject_position(world_point)/Vector2(view.size)*size
		# Keep the indicator away from the permanent top HUD and screen edges.
		anchor=anchor.clamp(Vector2(44,128),size-Vector2(44,108))
	visible=not paused
	queue_redraw()

func consume(events: Array):
	for event in events:
		if event.type == "upgrade":
			toast="FURNACE LEVEL %d  ·  WARMTH EXPANDED" % event.level
			toast_time=3.2
		elif event.type == "wave_clear":
			toast="OUTPOST SAFE  ·  FRONTIER UNLOCKED"; toast_time=3.2

func _draw():
	if not descriptor.is_empty():
		var tint:=Color("ffaa5b") if not descriptor.paused_by_movement else Color("afc8d9")
		draw_arc(anchor,25,0,TAU,56,Color(.05,.11,.19,.6),6,true)
		if descriptor.progress > .001:
			draw_arc(anchor,25,-PI/2,-PI/2+TAU*descriptor.progress,56,tint,4,true)
		draw_circle(anchor,3,tint)
	if toast_time > 0.0:
		var font:=ThemeDB.fallback_font
		var extent:=font.get_string_size(toast,HORIZONTAL_ALIGNMENT_LEFT,-1,22)
		var origin:=Vector2((size.x-extent.x)/2,145)
		draw_string(font,origin+Vector2(1,2),toast,HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color(.03,.06,.10,.9))
		draw_string(font,origin,toast,HORIZONTAL_ALIGNMENT_LEFT,-1,22,Color("ffe1b7"))
