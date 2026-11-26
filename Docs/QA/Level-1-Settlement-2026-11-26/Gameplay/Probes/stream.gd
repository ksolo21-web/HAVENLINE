extends "res://tests/world_house_route.gd"

var channel := StreamPeerTCP.new()
var mix := AudioEffectCapture.new()
var master := -1
var last_sample_count := 0
var native := false
var current_shot := ""
var video_frame := 0
var shot_table: Dictionary = {}
var arm_bus := false
var shade: ColorRect
var out_fps:=float(OS.get_environment("HL_OUTPUT_FPS"))
var dark := true
var effect_chapter := ""
var effect_until := -1
var once_events:Dictionary={}
var worker_trail:Array[Vector3]=[]
var exit_legs:Array=[]
var exit_phase := -1
var suppress_default_release:=false

func steer(direction:Vector2) -> void:
	if suppress_default_release and direction.is_zero_approx():return
	super.steer(direction)

func _initialize() -> void:
	native = OS.get_environment("HL_RECORD") == "1"
	if native:
		var err := channel.connect_to_host("127.0.0.1", int(OS.get_environment("HL_STREAM_PORT")))
		if err: push_error("Local encoder connection failed");quit(11);return
		while channel.get_status()==StreamPeerTCP.STATUS_CONNECTING:
			channel.poll()
			OS.delay_usec(100)
		if channel.get_status()!=StreamPeerTCP.STATUS_CONNECTED:quit(12);return
		mix.buffer_length=2.
		master=AudioServer.get_bus_index("Master")
		AudioServer.add_bus_effect(master,mix)
		process_frame.connect(_on_capture)
	super._initialize()

func send_bytes(header:Dictionary,data:PackedByteArray=PackedByteArray()) -> void:
	var meta := JSON.stringify(header).to_utf8_buffer()
	channel.big_endian = true
	channel.put_u32(meta.size())
	channel.put_u32(data.size())
	channel.put_data(meta)
	if not data.is_empty():channel.put_data(data)

func _on_capture() -> void:
	var n := mix.get_frames_available()
	if n:
		var values := mix.get_buffer(n)
		send_bytes({"type":"audio","offset":last_sample_count,"samples":n},values.to_byte_array())
		last_sample_count += n
	if not field or not is_instance_valid(field) or finished or tick<2:return
	if not shade:
		var overlay:=CanvasLayer.new()
		overlay.layer=244
		root.add_child(overlay)
		shade=ColorRect.new()
		shade.color=Color.BLACK
		shade.mouse_filter=Control.MOUSE_FILTER_IGNORE
		overlay.add_child(shade)
		shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		shade.hide()
	if not current_shot.is_empty():
		shade.hide()
		RenderingServer.force_draw(false,1./out_fps)
		var image := root.get_texture().get_image()
		var pframe := Engine.get_process_frames()
		var sample := {"type":"picture","chapter":current_shot,"engine_frame":pframe,"physics_tick":tick,"audio_start":last_sample_count,"image_size":[image.get_width(),image.get_height()],"render_scale":root.scaling_3d_scale,"camera":str(root.get_camera_3d().get_path())}
		send_bytes(sample,image.save_jpg_to_buffer(.93))
		video_frame += 1
		dark = false
	elif not dark:
		shade.show()
		RenderingServer.force_draw(false,1./out_fps)
		dark=true

func observe_clip(row: Dictionary) -> void:
	current_shot = ""
	var seconds := (tick-stage_tick)/60.
	if row.has("proof_shot") and seconds>=float(row.get("from",0)) and seconds<float(row.get("to",1)):
		current_shot = row.proof_shot
	if field.owl and field.owl.state == "dive" and not once_events.has("owl_hit"):
		current_shot="Owl talons strike a live wolf"
	var effects:={"owl_hit":["Owl talons strike a live wolf",68],"process_wood":["Working carried wood at the sawmill",68],"process_stone":["Working carried stone at the drill",68],"survivor_rescued":["The survivor joins camp",70],"worker_pickup":["The helper collects real timber",65],"worker_delivery":["Timber arrives at the storehouse",70],"cooker_start":["The lakeshore kitchen starts",85],"meal_ready":["The cooked meal is ready",55],"meal_served":["The customer pays",65],"next_level":["Next-level checkpoint selected",80]}
	for e in tick_events:
		if effects.has(e.event) and not once_events.has(e.event):
			once_events[e.event]=true
			effect_chapter=effects[e.event][0]
			effect_until=tick+int(effects[e.event][1])
	if tick<effect_until:current_shot=effect_chapter

func read_field() -> Dictionary:
	var result := super.read_field()
	if "settlement" in field.inventory:
		result["settlement"] = field.inventory.settlement.duplicate()
		if "settlement_loop" in field and field.settlement_loop:
			var panel=field.opening_hud.level_continue
			result["finish_ui"]={"text":panel.text,"visible":panel.is_visible_in_tree(),"ready":field.settlement_loop.ready()}
			if field.survivor and "actor" in field.survivor and field.survivor.actor:
				result["survivor_position"]=pt(field.survivor.actor.global_position)
				if "phase" in field.survivor:result["survivor_phase"]=field.survivor.phase
			if field.lakeshore:
				result["kitchen_active"]=field.lakeshore.working
			if field.owl:
				result["owl_state"]=field.owl.state
			if field.settlement_loop.works:
				result["worksite"]=field.settlement_loop.works.active
			if field.counter:
				result["serving_counter"]={"order":field.counter.sale_order,"committed":field.counter.sale_committed,"cash_visible":is_instance_valid(field.counter.cash),"meal_visible":is_instance_valid(field.counter.meal),"queue_length":field.counter.queue.size(),"leaving":field.counter.leaving.size()}
	return result

func advance() -> void:
	if phases[index].has("checkpoint"):
		var name:String=phases[index].checkpoint
		var live_path:String=field.field_save.directory.path_join(field.field_save.PRIMARY)
		var contents:=FileAccess.get_file_as_bytes(live_path)
		if contents.is_empty():push_error("Missing game-created checkpoint "+name);quit(9);return
		var copy:=FileAccess.open(out_dir.path_join(name+".save.json"),FileAccess.WRITE)
		copy.store_buffer(contents)
		copy.close()
		event("earned_checkpoint",{"name":name,"file_sha256":FileAccess.get_sha256(live_path),"state":read_field()})
	if index==phases.size()-1 and native:
		send_bytes({"type":"finish","frames":video_frame,"samples_before_tail":last_sample_count,"lost":mix.get_discarded_frames(),"mix_hz":AudioServer.get_mix_rate()})
	super.advance()

func execute(row:Dictionary) -> void:
	var action := String(row.action)
	if action not in ["wait_settlement", "press_continue", "leave_south", "enter_south", "owl_encounter"]:
		super.execute(row)
		return
	var idle:=row.duplicate()
	idle.action="hold"
	idle.s=100000.
	suppress_default_release=action in ["leave_south","enter_south","owl_encounter"] or (row.get("key","")=="worker_deliveries" and not String(field.inventory.settlement.worker_carry_token).is_empty())
	super.execute(idle)
	suppress_default_release=false
	if finished:return
	if action=="wait_settlement":
		var state:Dictionary=field.inventory.settlement
		if int(state[row.key])>=int(row.value):
			steer(Vector2.ZERO)
			advance()
		elif row.key=="worker_deliveries" and not String(state.worker_carry_token).is_empty() and field.survivor and field.survivor.actor:
			var w:Vector3=field.survivor.actor.global_position
			if worker_trail.is_empty() or worker_trail.back().distance_to(w)>.52:worker_trail.append(w)
			if worker_trail.size()>3:
				var next:Vector3=worker_trail.front()
				if move_to([next.x,next.z],.44):worker_trail.pop_front()
	elif action=="owl_encounter":
		if int(field.inventory.settlement.owl_hits)>0:
			steer(Vector2.ZERO);advance();return
		var closest=null
		var nearest:=INF
		for wolf in field.enemies:
			if is_instance_valid(wolf) and wolf.hp>0:
				var dist:float=wolf.global_position.distance_squared_to(field.actor.position)
				if dist<nearest:nearest=dist;closest=wolf
		if closest:
			if nearest>22.:move_to([closest.position.x,closest.position.z],3.2)
			else:circle_around(closest.position,3.9,1.)
		else:move_to([10.8,8.6],.30)
	elif action=="enter_south":
		if exit_phase!=index:
			exit_phase=index
			exit_legs=[] if field.field_env.is_inside_camp(field.actor.position) else [[0.,7.45],[0.,3.7]]
			exit_legs.append([-2.65,2.6]);exit_legs.append([-2.5,.30])
		if exit_legs.is_empty():steer(Vector2.ZERO);advance()
		elif move_to(exit_legs.front(),.25):exit_legs.pop_front()
	elif action=="leave_south":
		if exit_phase!=index:
			exit_phase=index
			exit_legs=[[-2.55,2.7],[0.,3.8],[0.,7.45]] if field.field_env.is_inside_camp(field.actor.position) else []
		if exit_legs.is_empty():advance()
		elif move_to(exit_legs.front(),.24):exit_legs.pop_front()
	elif action=="press_continue":
		if int(field.inventory.settlement.level)>=2:
			advance()
			return
		if tick-stage_tick<30 or goal_tap_sent:return
		var buttons:=root.find_children("*","Button",true,false)
		for item:Button in buttons:
			if item.is_visible_in_tree() and not item.disabled and ("continue" in item.text.to_lower() or "level 2" in item.text.to_lower() or "next level" in item.text.to_lower()):
				var pos:=item.get_global_rect().get_center()
				event("continuation_tap",{"label":item.text,"path":str(item.get_path()),"canvas_position":[pos.x,pos.y],"settlement":field.inventory.settlement.duplicate()})
				touch(8,pos,true)
				touch(8,pos,false)
				goal_tap_sent=true
				break
