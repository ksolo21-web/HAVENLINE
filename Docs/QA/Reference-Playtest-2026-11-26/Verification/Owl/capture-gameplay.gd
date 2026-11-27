extends SceneTree
var w
var wolf
var out="/tmp/hl-ref5/owl/gameplay"
var rows=[]
var pics=[]
func _initialize():call_deferred("run")
func shoot(label: String):
	var cam: Camera3D=w.camera
	for zoom in [1.,2.]:
		w.set_zoom_ratio(zoom)
		await process_frame
		RenderingServer.force_draw()
		var im:=root.get_texture().get_image()
		var center: Vector3=w.owl.art.to_global(Vector3(0,.34,0))
		var location:=cam.unproject_position(center)
		var tag="%s-%dx"%[label,int(zoom)]
		im.save_jpg(out.path_join(tag+".jpg"),.96)
		pics.append({"id":tag,"owl_screen":[location.x,location.y],"pixels":[im.get_width(),im.get_height()],"hero":[w.actor.position.x,w.actor.position.z],"state":w.owl.state,"receipts":w.inventory.settlement.owl_hits,"scene":w.scene_file_path,"cam_size":cam.size})
func run():
	w=load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(w)
	for i in 4: await physics_frame
	w.set_physics_process(false)
	w.set_process(false)
	if not w.field_ready or w.persist_blocked: push_error("isolated field did not open");quit(1);return
	for j in int(w.inventory.costs.center_hearth.wood):
		w.inventory.collect("owl-game-hearth-"+str(j),"wood")
		w.inventory.payment("center_hearth","wood",false)
	w._finish_purchase("center_hearth")
	w._apply_hearth(true,false)
	w.actor.position=w.settlement_loop.works.PLOT_AT
	for j in w.inventory.survivor_cost:w.inventory.collect("owl-game-award-"+str(j),"wood")
	w.carry.sync(true)
	for j in range(w.inventory.survivor_cost*36):
		w.settlement_loop.works.advance(1./60.)
		w.carry.advance(1./60.)
	if not w.inventory.settlement.survivor_paid: push_error("award failed");quit(2);return
	var perch: Vector3 = w.owl._perch()
	var player:=Vector3(perch.x+1.85,0,perch.z*.78)
	w.actor.position=player
	w.camera.position=player+w.camera_follow_offset
	for i in 150:w.owl.advance(1./60.)
	w._refresh_field()
	w._refresh_hud_field(false)
	await shoot("paid-perch")
	w.actor.position=Vector3(perch.x-2.05,0,perch.z*.81)
	w.camera.position=w.actor.position+w.camera_follow_offset
	for i in 140:w.owl.advance(1./60.)
	w._refresh_hud_field(false)
	await shoot("perch-turn")
	for j in range(1,w.enemies.size()):
		w.enemies[j].active=false; w.enemies[j].hide()
	wolf=w.enemies[0]
	w.actor.position=Vector3(7.3,0,-1.4)
	w.camera.position=w.actor.position+w.camera_follow_offset
	wolf.position=Vector3(13.5,0,.35);wolf.home=wolf.position
	var saved={}
	var hit=-1
	for i in 175:
		w._physics_process(1./60.)
		var s: String=w.owl.state
		rows.append({"tick":i,"phase":s,"life":wolf.hp if is_instance_valid(wolf) else 0,"receipts":w.inventory.settlement.owl_hits,"reach":w.owl.talon_weights.y,"grip":w.owl.talon_weights.z})
		var tag=""
		if s=="windup" and w.owl.age>.11: tag="windup"
		if s=="dive" and w.owl.talon_weights.y>.76: tag="reach"
		if s=="strike" and hit<0:hit=i;tag="contact"
		if s=="strike" and w.owl.age>.115:tag="rake"
		if s=="recover" and w.owl.age>.2:tag="recover"
		if tag!="" and not saved.has(tag):
			await shoot(tag)
			saved[tag]=true
		else:
			await process_frame
		if hit>=0 and i>hit+29:break
	var f:=FileAccess.open(out.path_join("field-telemetry.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"hit_tick":hit,"scene":w.scene_file_path,"fixed_physics_hz":60,"camera":"native gameplay camera, both game zoom stops","gates":"paid camp and paid survivor; eligible moving wolf","samples":rows,"shots":pics},"  "));f.close()
	if hit<0:push_error("missed field strike")
	w._close_field()
