extends "res://tests/field_route.gd"

# The automation drives ordinary touchscreen controls; runtime fields are read back for evidence.
var harvest_body: Node3D
var clip_enabled := OS.get_environment("WORLD_ROUTE_MOVIE")=="1"
var clip_current := ""
var clip_curtain: ColorRect
var blackout_frame := -1
var last_approach := Vector3.ZERO
var accepted_boss := false
var plate_enabled := OS.get_environment("WORLD_ROUTE_PLATES")=="1"
var plate_names := {}
var plate_pending := false
var complete_log: Array[Dictionary] = []
var tick_events: Array[Dictionary] = []
var event_cursor: Dictionary = {}
var observed_triggers := {}
var event_clip := ""
var event_clip_end := 0
var last_seen := {}
var stage_entered := {}
var renewal_seen := -1
var recovery_leg := -1

var token_last := -1
var token_totals := {}
var track_counts := {}
var last_track_tick := -120

func _initialize() -> void:
	OS.set_environment("FIELD_QA_SCENE",String(ProjectSettings.get_setting("application/run/main_scene")))
	super._initialize()

func read_field() -> Dictionary:
	var state := super.read_field()
	state.erase("world")
	state.erase("world_state")
	if token_last!=field.inventory.collected.size():
		token_last=field.inventory.collected.size()
		token_totals=field.Inventory.EMPTY.duplicate()
		for kind in field.inventory.collected.values():token_totals[kind]+=1
	state["unique_token_counts"]=token_totals.duplicate()
	state.erase("collected")
	state.erase("loose")
	state.erase("vis_items")
	state["stage_number"]=field.field_env.perimeter_stage
	state["orbit_active"]=field.character_kit.active
	state["visible_heads"]=0
	for slot in field.character_kit.slots:
		if slot.axe.visible or slot.pickaxe.visible:state.visible_heads+=1
	if field.field_env.has_method("is_inside_camp"):
		state["inside"] = field.field_env.is_inside_camp(field.actor.position)
	state["perimeter"] = field.layout.camp_rect_xz.duplicate()
	state["gate_centers"] = {}
	for gate in field.gates:
		state.gate_centers[gate.gate_id] = pt(gate.global_position)
	state["wolves"] = []
	for wolf in field.enemies:
		if is_instance_valid(wolf) and wolf.hp>0:
			state.wolves.append([wolf.spawn_id,wolf.is_boss,wolf.hp,wolf.state,pt(wolf.global_position)])
	state["wave"] = field.encounters.wave if "encounters" in field else 0
	state["tower_active"] = field.defense_tower.active
	state["tower_flights"] = field.defense_tower.flights.size()
	state["cooling"] = field.lifecycle.cooling.duplicate()
	if field.world_landscape:
		state["terrain_chunks"]=field.world_landscape.chunks.size()
		state["terrain_cell"]=[field.world_landscape.center_chunk.x,field.world_landscape.center_chunk.y]
	if "tracks" in field and field.tracks:
		state["tracks"]=field.tracks.total
		if tick-last_track_tick>=60:
			last_track_tick=tick
			track_counts={"boots":0,"paws":0,"inside":0,"large_paws":0}
			for chunk in field.tracks.chunks.values():
				for mark in chunk.marks:
					track_counts["paws" if mark.wolf else "boots"]+=1
					if mark.wolf and mark.extent.y>.40:track_counts.large_paws+=1
					if field.field_env.is_inside_camp(mark.p):track_counts.inside+=1
		state["stamp_sample"]=track_counts.duplicate()
		state["stamp_tick"]=last_track_tick
	return state

func advance() -> void:
	harvest_body=null
	super.advance()
	if finished:
		if clip_enabled:_set_clip("")
		var log_file:=FileAccess.open(out_dir.path_join("world-events-complete.json"),FileAccess.WRITE)
		log_file.store_string(JSON.stringify(complete_log))
		log_file.close()

func _set_clip(id: String) -> void:
	if not clip_curtain:
		var overlay := CanvasLayer.new()
		overlay.layer=240
		root.add_child(overlay)
		clip_curtain=ColorRect.new()
		clip_curtain.color=Color.BLACK
		clip_curtain.mouse_filter=Control.MOUSE_FILTER_IGNORE
		overlay.add_child(clip_curtain)
		clip_curtain.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		clip_current="boot"
	if id!=clip_current:
		var frame:=Engine.get_process_frames()
		if clip_current!="" and clip_current!="boot":event("clip_end",{"clip":clip_current,"frame":frame,"physics":tick})
		clip_current=id
		clip_curtain.visible=id==""
		RenderingServer.set_render_loop_enabled(true)
		blackout_frame=frame+2 if id=="" else -1
		if id!="":event("clip_start",{"clip":id,"frame":frame,"physics":tick})
	elif blackout_frame>=0 and Engine.get_process_frames()>=blackout_frame:
		RenderingServer.set_render_loop_enabled(false)
		blackout_frame=-1

func _plate(id:String) -> void:
	if not plate_enabled or plate_names.has(id) or plate_pending:return
	plate_names[id]=true
	plate_pending=true
	await process_frame
	RenderingServer.force_draw(false,1./24.)
	var im:Image=root.get_texture().get_image()
	var requested:=root.size
	assert(im.get_size()==requested and root.scaling_3d_scale==1.)
	im.convert(Image.FORMAT_RGB8)
	im.save_png(out_dir.path_join(id+".png"))
	event("world_plate",{"id":id,"width":im.get_width(),"height":im.get_height(),"pos":pt(field.actor.position),"hud":field.opening_hud.prompt.text,"state":read_field(),"native_scale":root.scaling_3d_scale,"camera":str(root.get_camera_3d().get_path()),"physics_tick":tick})
	plate_pending=false

func _discover(row:Dictionary) -> void:
	if not plate_enabled and not clip_enabled:return
	if index==0 and tick>=25:_plate("01-unpaid")
	if row.get("target","")=="starter-renewal" and renewal_seen>=0 and tick-renewal_seen>15:_plate("renewed-"+String(row.kind))
	if row.action=="farm" and row.kind=="wood" and field.resource_tree.strikes==1:_plate("02-tree")
	if row.action=="farm" and row.kind=="stone" and field.resource_rock.strikes==1:_plate("03-mine")
	if row.action=="buy":
		var receipt:Dictionary=field.inventory.paid[row.id]
		var partially_paid:bool=receipt.values().any(func(n):return n>0)
		if partially_paid and not field.inventory.complete(row.id): _plate("pay-"+String(row.id))
	if row.has("plate") and tick-stage_tick>=int(row.get("at_tick",22)):
		if row.plate!="05-built" or field.camp_active and float(field.field_env.snow.get_shader_parameter("reveal"))>=.995:_plate(row.plate)
	for wolf in field.enemies:
		if not is_instance_valid(wolf) or wolf.hp<=0:continue
		var gap:float=wolf.position.distance_to(field.actor.position)
		if gap<4.2 and wolf.state in ["windup","lunge","stagger"]:
			_plate("04-boss" if wolf.is_boss else "04-wolf")
			_trigger_clip("Alpha wolf encounter" if wolf.is_boss else "Wild wolf encounter",3.0)
	for e in tick_events:
		if e.event=="tower_fire" and field.actor.position.distance_to(field.defense_tower.position)<6.5:
			_plate("tower-fire")
			_trigger_clip("Watchtower bolts at the eastern threat",2.0)
		if e.event=="tower_hit" and field.actor.position.distance_to(Vector3(e.x,0,e.z))<8.:
			_plate("tower-hit")

func _trigger_clip(id:String,seconds:float) -> void:
	if observed_triggers.has(id):return
	observed_triggers[id]=true
	event_clip=id
	event_clip_end=tick+int(60.*seconds)

func observe_clip(row: Dictionary) -> void:
	_discover(row)
	if not clip_enabled: return
	var inc := float(tick-stage_tick)/60.0
	var clip: String = row.get("shot","")
	if inc<float(row.get("offset",0.0)) or inc>float(row.get("length",3.0)):
		clip=""
	if row.get("target","")=="starter-renewal" and field.lifecycle.cooling.has(row.source_id) and field.lifecycle.cooling[row.source_id]<1.0:
		_trigger_clip(String(row.kind).capitalize()+" regrows in the field",2.2)
	if tick<event_clip_end:clip=event_clip
	_set_clip(clip)

func steer(direction: Vector2) -> void:
	# Recovery discards the prior touch. A human starts a new drag on regaining control.
	if field and touch_held and field.touch_id<0:
		touch_held=false
		last_input=Vector2.ZERO
	super.steer(direction)

func _in_patch(pos: Vector3, row: Dictionary) -> bool:
	if not row.has("region"): return true
	var b:Array=row.region
	return pos.x>=b[0] and pos.z>=b[1] and pos.x<=b[2] and pos.z<=b[3]

func _loot_target(kind: String, row: Dictionary) -> Variant:
	var found = null
	var nearest := INF
	for d in field.drops.values():
		if d.kind!=kind or d.get("claimed",false) or not _in_patch(d.at,row): continue
		if field.field_env.is_inside_camp(d.at) or field.actor.position.distance_squared_to(d.at)>64.:continue
		var distance:float=field.actor.position.distance_squared_to(d.at)
		if distance<nearest:
			nearest=distance
			found=d
	return found

func _farm(row: Dictionary) -> void:
	var kind: String=row.kind
	if field.inventory.carried[kind]>=int(row.count):
		steer(Vector2.ZERO)
		if field.carry.flights.is_empty():advance()
		return
	var drop=_loot_target(kind,row)
	if drop!=null:
		move_to([drop.at.x,drop.at.z],.26)
		return
	if kind=="meat":
		var victim=null
		var nearest:=INF
		for wolf in field.enemies:
			if is_instance_valid(wolf) and wolf.hp>0:
				var distance:float=wolf.position.distance_squared_to(field.actor.position)
				if distance<nearest:
					nearest=distance
					victim=wolf
		if victim:
			if nearest>11.0:move_to([victim.position.x,victim.position.z],2.41)
			else:circle_around(victim.position,2.45,1.)
		else:move_to(row.get("p",[12.,5.]),.25)
		return
	var body=field.resource_tree if kind=="wood" else field.resource_rock
	if row.get("choose_nearest",false):
		var sources:Array=field.trees if kind=="wood" else field.rocks
		if not is_instance_valid(harvest_body) or harvest_body.phase not in ["rooted","seated","falling","ready_to_credit"]:
			var best:=INF
			harvest_body=null
			for item in sources:
				if not is_instance_valid(item) or item.phase not in ["rooted","seated"] or not _in_patch(item.position,row):continue
				var d:float=field.actor.position.distance_squared_to(item.position)
				if d<best:
					best=d
					harvest_body=item
		if is_instance_valid(harvest_body):body=harvest_body
	if body.phase=="falling":
		if not body.sweep_clear(field.actor.position,.31):move_to([body.position.x+2.1,body.position.z+1.6],.18)
		else:steer(Vector2.ZERO)
	elif body.phase in ["credited","mined","ready_to_credit"]:
		move_to([body.position.x+.7,body.position.z+2.5],.19)
	elif field.actor.position.distance_squared_to(body.position)>12.2:
		var delta:Vector3=(field.actor.position-body.position).normalized()*2.55
		move_to([body.position.x+delta.x,body.position.z+delta.z],.25)
	else:
		circle_around(body.position,2.60,1.)

func execute(row: Dictionary) -> void:
	tick_events.clear()
	var cursor:int=field.events.size()-1
	while cursor>=0 and not is_same(field.events[cursor],event_cursor):
		cursor-=1
	for j in range(cursor+1,field.events.size()):
		var newest:Dictionary=field.events[j]
		complete_log.append(newest)
		tick_events.append(newest)
		event_cursor=newest
	observe_clip(row)
	if tick_events.any(func(e):return e.event=="reset") and row.get("far_travel",false):recovery_leg=0
	if recovery_leg>=0:
		var retreat=[[0.,7.7],[13.,7.7],[13.,-.2]]
		if move_to(retreat[recovery_leg],.25):
			recovery_leg+=1
			if recovery_leg==retreat.size():recovery_leg=-1
		return
	if tick-stage_tick>int(row.get("timeout",35))*60:
		event("timeout",snapshot());finished=true;quit(4);return
	match String(row.action):
		"gate":
			steer(Vector2.ZERO)
			var gate=field.nearest_gate
			if gate and gate.gate_id==row.gate:
				if gate.target_open and gate.angle>=PI*.49:
					advance()
				elif not gate.target_open and field.gate_button.visible and not goal_tap_sent:
					var center:Vector2=field.gate_button.get_global_rect().get_center()
					touch(3,center,true);touch(3,center,false);goal_tap_sent=true
		"farm":_farm(row)
		"buy":
			var id:String=row.id
			var pos:Vector3=field.carry.receivers[id].global_position
			if field.inventory.complete(id) and field.carry.flights.is_empty():
				steer(Vector2.ZERO);advance()
			else:move_to([pos.x,pos.z],.18)
		"renew":
			steer(Vector2.ZERO)
			if not field.lifecycle.cooling.has(row.source_id):
				if renewal_seen<0:renewal_seen=tick
				if tick-renewal_seen>72:
					renewal_seen=-1
					advance()
		"wait_event":
			steer(Vector2.ZERO)
			for e in field.events:
				if e.event==row.id:advance();return
		_:
			super.execute(row)
