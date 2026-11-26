extends SceneTree
var w
var seen:={}
var out:=OS.get_environment("FINISH_AUDIT_OUT")
func _initialize(): call_deferred("run")
func aim(at:Vector3, z:float=1.0):
	w.actor.position=at
	w.previous_dry_position=at
	w.actor.velocity=Vector3.ZERO
	w.camera.position=at+Vector3(7,11,11)
	w.set_zoom_ratio(z)
func fund(id:String):
	for kind:String in w.inventory.remaining(id):
		for i in range(int(w.inventory.remaining(id)[kind])):
			assert(w.inventory.collect("audit-"+id+kind+str(i),kind))
			assert(w.inventory.payment(id,kind,false))
	w._finish_purchase(id)
func snap(k:String, target:Node3D=null):
	if seen.has(k): return
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(out+"/"+k+".jpg",.94)
	seen[k]={"viewport":str(root.size),"camera":str(w.camera.global_transform),"zoom":w.trial_camera.zoom_ratio,"source_in_camera":null if target==null else str(w.camera.unproject_position(target.global_position)),"owl_state":w.owl.state,"worker_state":w.survivor.phase,"worker_contacts":w.survivor.contacts,"hud_text":w.opening_hud.prompt.text,"player":str(w.actor.global_position),"furnace_paid":w.camp_active}
func tick(n:int):
	for i in n:await physics_frame
func run():
	w=load("res://field_opening.tscn").instantiate()
	root.add_child(w)
	await tick(10);w.persist_requested=false;snap("01-hud-before")
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2"]:
		fund(id)
		await tick(2)
	w.inventory.settlement.survivor_paid=true
	w.inventory.settlement.survivor_wood=2
	aim(w.survivor.RESCUE)
	await tick(2)
	snap("02-survivor",w.survivor.actor)
	aim(Vector3(-.15,0,9.70))
	for i in 1050:
		await physics_frame
		var s=w.survivor
		if s.phase=="chopping" and s.swing_time>.19:
			snap("03-working",s.actor)
		if s.contacts==1 and s.phase=="chopping" and s.swing_time>.41:
			w.set_zoom_ratio(2.)
			snap("04-worker-hit-pinch",s.actor)
			w.set_zoom_ratio(1.)
		if s.contacts>0:
			snap("04-worker-hit",s.actor)
		if s.phase=="carrying":
			snap("05-worker-cargo",s.actor)
			break
	aim(w.gates[0].position-Vector3(0,0,1.3))
	await tick(275)
	snap("06-owl-perch",w.owl)
	# An exterior attention point and a regular simulated wolf let the normal owl behaviour drive the encounter.
	aim(Vector3(3.20,0,11.2))
	var wolf=w.encounters._add(Vector3(6.3,0,13.8),true,8765,Vector3(6.3,0,13.8))
	if wolf==null and not w.enemies.is_empty():
		wolf=w.enemies[0];wolf.position=w.actor.position+Vector3(4.3,0,-1.)
	for i in 820:
		await physics_frame
		var screen_at:Vector2=w.camera.unproject_position(w.owl.global_position)
		if w.owl.state in ["follow","bank","dive","recover"] and w.owl.visible and Rect2(Vector2(0,0),Vector2(root.size)).grow(-35).has_point(screen_at):
			snap("07-owl-"+w.owl.state,w.owl)
		if seen.has("07-owl-recover") and seen.has("07-owl-dive"):break
	w.carry.pickup("art-audit-log","wood",w.actor.position);w.carry.pickup("art-audit-stone","stone",w.actor.position);w.carry.pickup("art-audit-meat","meat",w.actor.position)
	await tick(36)
	for kind in ["wood","stone","cooker"]:
		var p:Vector3=w.lakeshore.APRON if kind=="cooker" else w.processors.APRONS[kind]
		aim(p);await tick(22);snap("08-"+kind+"-1x",w.lakeshore.cooker if kind=="cooker" else w.processors.wheels[kind])
		aim(p,2.);await tick(29);snap("08-"+kind+"-2x",w.lakeshore.cooker if kind=="cooker" else w.processors.wheels[kind])
		await tick(75)
	aim(w.counter.service_point.global_position);await tick(4);snap("09-counter-approach",w.counter)
	for i in 120:
		await physics_frame
		if i in [16,28,42,60]:snap("09-counter-%03d"%i,w.counter)
		if i==45:
			w.set_zoom_ratio(2.)
			snap("09-counter-pinch",w.counter)
			w.set_zoom_ratio(1.)
	# Inspect the actual responsive HUD with all three minerals and both processing balances present.
	for kind in ["slate","metal","coal"]:
		w.carry.pickup("audit-ui-"+kind,kind,w.actor.position)
	await tick(30);snap("10-stocked-hud")
	var hud=w.opening_hud
	var layout:={}
	for key in ["plate","chapter","row","mineral_row","workshop_stock","health_text","health_bar","purse","prompt","operation","gate","level_continue"]:
		var c:Control=hud.get(key)
		var rect:=c.get_global_rect()
		layout[key]={"visible":c.is_visible_in_tree(),"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y]}
	var meta=FileAccess.open(out+"/hud.json",FileAccess.WRITE)
	meta.store_string(JSON.stringify({"physical_window":str(root.size),"logical_canvas":str(hud.get_viewport_rect().size),"stocked_hud":layout},"  "))
	meta.close()
	var f=FileAccess.open(out+"/observations.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(seen,"  "));f.close()
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,w)
	w.queue_free()
	for i in 5:await process_frame
	quit()
