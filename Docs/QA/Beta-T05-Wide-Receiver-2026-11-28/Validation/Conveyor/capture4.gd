extends "res://tests/field_route.gd"
const Session=preload("res://tests/lifecycle_test_profile.gd")
var output:=OS.get_environment("HAVENLINE_PATCH_EVIDENCE")
var rows:=[]
var b
var j:Dictionary
var net
var field_meat_added:=0
var frames:=0
func _initialize():run.call_deferred()
func snap(label:String, zoom:float) -> void:
	field.set_zoom_ratio(zoom)
	camera.global_position=field.actor.global_position+field.camera_follow_offset
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	root.get_texture().get_image().save_jpg(output.path_join(label+".jpg"),.93)
	var feet:=Vector2(field.actor.global_position.x,field.actor.global_position.z)
	var public_floor:bool=net.aisles._body_clear(feet,.31) and net.aisles.disc_clear(feet,.31)
	if not public_floor:push_error("camera witness is not on actual working floor "+label)
	var active:={}
	for lane:String in b.LANES:
		if not b.goods[lane].visible:continue
		var m:Node3D=b.goods[lane]
		var p:=camera.unproject_position(m.global_position)
		active[lane]={"xz":str(m.global_position),"screen":[p.x,p.y],"scale":m.global_basis.x.length()}
	var parked:=[]
	for item:Node3D in field.counter.public_piles.get("meal",[]):
		if item.visible:
			var p:=camera.unproject_position(item.global_position)
			parked.append({"xz":str(item.global_position),"screen":[p.x,p.y]})
	var exchange:={}
	if field.counter.sale_order and is_instance_valid(field.counter.meal):
		var dish:Node3D=field.counter.meal
		var guest:Dictionary=field.counter.queue[0]
		var mitt:Vector3=field.counter._guest_palm(guest,"right")+(guest.body as Node3D).global_basis*Vector3(-.15,.01,.04)
		exchange={"meal":str(dish.global_position),"hand":str(mitt),"distance_m":dish.global_position.distance_to(mitt),"sale_seconds":field.counter.sale_elapsed}
	rows.append({"solid_foot":public_floor,"exchange":exchange,"label":label,"zoom":zoom,"camera":str(camera.global_position),"feet":str(field.actor.global_position),"active":active,"stock":parked,"served":j.served,"counter_stock":j.counter_stock,"red":net.red_lamp.visible,"green":net.green_lamp.visible})
func run():
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field);current_scene=field;camera=field.camera
	field.set_physics_process(false)
	field.actor.global_position=Vector3(2.82,0,-5.45)
	field.previous_dry_position=field.actor.global_position
	field.counter.arrival_clock=180.
	var loop=field.settlement_loop
	b=loop.conveyors;b.refresh_paths();net=b.network;j=field.inventory.settlement
	var stored:bool=OS.get_environment("HL_RECEIVING_SEED").contains("serial-upgrade")
	var stream:="stored_meal" if stored else "meal"
	if not net.receiver:
		push_error("Expected paid broad receiver on this save");quit(2);return
	if not stored:
		# Exercise a real wolf defeat, both grounded pickup tokens and the
		# public store before production. Inventory is never set by this driver.
		if field.enemies.is_empty():field.encounters._add(Vector3(14.8,0.,1.5),false,740,Vector3(14.8,0.,1.5))
		var wolf=field.enemies[0]
		field.actor.global_position=wolf.global_position
		for turn_id in 14:
			if wolf.hp<=0:break
			wolf.take_swirl_hit(9000+turn_id)
		for token in field.drops.keys():
			if not field.drops.has(token) or field.drops[token].kind!="meat":continue
			field.actor.global_position=field.drops[token].at
			field._step_drops(.36)
		for i in 45:field.carry.advance(1./60.)
		field.actor.global_position=field.depot.bins.meat.global_position
		var before:int=field.inventory.stored.meat
		for i in 130:
			field.carry.deposit_storage("meat")
			field.carry.advance(1./60.)
		field_meat_added=field.inventory.stored.meat-before
		print("EARNED RAW ",field_meat_added)
	var observer:=Vector3(2.65,0,-5.25)
	field.actor.global_position=observer
	field.previous_dry_position=observer
	var seen:={}
	var initial_stock:int=j.counter_stock
	var sales:int=j.served
	var first:=true
	var stage:=0
	for tick in 5000:
		loop.advance_unattended(1./60.)
		field.counter.show_goods(j)
		if b.goods[stream].visible:
			var at:Vector3=b.goods[stream].global_position
			var along:float=net.receiver.along(at)
			var label:=""
			if along>=.62 and along<=1.05:label="High-intake"
			elif along>=1.5 and along<=1.78:label="Down-slope"
			if label!="" and not seen.has(label):
				seen[label]=true
				await snap(stream+"-"+label+"-1x",1.)
				await snap(stream+"-"+label+"-2x",2.)
			if stage==0 and along>=-.05 and along<=1.05:stage=1
		if stage==1 and tick%5==0:
			field.set_zoom_ratio(1.)
			camera.global_position=observer+field.camera_follow_offset
			await process_frame
			RenderingServer.force_draw(false,1./60.)
			root.get_texture().get_image().save_jpg(output.path_join("travel-%03d.jpg"%frames),.83)
			frames+=1
		if stage==1 and j.counter_stock>initial_stock:stage=2
		if j.counter_stock==2 and first:
			await snap("Paired-2x",2.)
			first=false
		if j.counter_stock>=b.buffer_capacity() or stored and j.counter_stock>initial_stock:
			await snap("Stocked-1x",1.)
			field.actor.global_position=Vector3(5.64,0,-5.01)
			await snap("Stocked-2x",2.)
			break
	if not stored and j.counter_stock<8:
		push_error("Source stock remained below eight: %d, raw earned %d"%[j.counter_stock,field_meat_added])
	field.actor.global_position=Vector3(5.1,0,-8.4)
	field.counter.arrival_clock=0.
	var sale_shot:=false
	var hand_shot:=false
	var sale_frames:=0
	for tick in 1000:
		loop.advance(1./60.)
		if field.counter.sale_order!=0 and tick%4==0:
			field.set_zoom_ratio(1.)
			camera.global_position=field.actor.global_position+field.camera_follow_offset
			await process_frame
			RenderingServer.force_draw(false,1./60.)
			root.get_texture().get_image().save_jpg(output.path_join("sale-%03d.jpg"%sale_frames),.82)
			sale_frames+=1
		if not hand_shot and field.counter.sale_committed and field.counter.sale_elapsed>.64 and field.counter.sale_elapsed<.75:
			await snap("Counter-presentation-1x",1.)
			hand_shot=true
		if not sale_shot and field.counter.sale_committed and is_instance_valid(field.counter.meal) and field.counter.sale_elapsed>1.05:
			await snap("Paid-collection-2x",2.)
			sale_shot=true
		if j.served>sales and field.counter.sale_order==0:break
	var file:=FileAccess.open(output.path_join("Receiver.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"source_fixture":OS.get_environment("HL_RECEIVING_SEED"),"views":rows,"served_start":sales,"served_end":j.served,"sale":j.served>sales,"field_meat_added":field_meat_added,"frames":frames,"renderer":RenderingServer.get_video_adapter_name()}," "))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 3:await process_frame
	quit(int(not sale_shot))
