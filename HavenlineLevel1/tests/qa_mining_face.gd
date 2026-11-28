extends "res://tests/field_route.gd"
## A real thumbstick path reproduces the first-hit stall beside the northern pine.
## The reference capture runs this same route with the production camera.
const Session := preload("res://tests/lifecycle_test_profile.gd")
var mine
var clock := 0
var counts := {}
var milestones := {}
var assertions := {}
var images := OS.get_environment("MINING_CAPTURE")
var film := OS.get_environment("MINING_FRAMES")
var previous := 0
var first_release := -1
var baseline := OS.get_environment("MINING_BASELINE") == "1"
var photographed := {}
var stone_ids := []
var initial_stock := 0
var visual_at_release := {}

func image_pair(label: String) -> void:
	if images.is_empty() or photographed.has(label):return
	photographed[label] = true
	for zoom:float in [1.,2.]:
		field.set_zoom_ratio(zoom)
		RenderingServer.force_draw(false, 1./60.)
		root.get_texture().get_image().save_jpg(images.path_join(label+"-"+str(int(zoom))+"x.jpg"),.93)
	field.set_zoom_ratio(1.)

func step_mine() -> void:
	await physics_frame
	clock += 1
	if not film.is_empty() and clock % 5 == 0:
		RenderingServer.force_draw(false, 1./60.)
		root.get_texture().get_image().save_jpg(film.path_join("frame-%05d.jpg"%int(clock/5)),.91)
	var total_before := int(counts.get("deplete_stone",0))
	counts.clear()
	for evt in field.events:
		if Vector2(evt.x,evt.z).distance_to(Vector2(mine.position.x,mine.position.z)) > .04: continue
		counts[evt.event] = counts.get(evt.event,0)+1
	if mine.strikes != previous and mine.strikes in [1,2]:
		var tag := "contact-"+str(mine.strikes)
		milestones[tag] = clock
		assertions[tag+" grants no stone"] = typed_drops().is_empty() and int(field.inventory.carried.stone) == initial_stock
		image_pair(tag)
	if int(counts.get("deplete_stone",0)) > total_before and first_release < 0:
		first_release = clock
		stone_ids = typed_drops()
		milestones["break"] = clock
		var lo: AABB = mine._mesh.mesh.get_aabb()
		visual_at_release={"source_visible":mine._mesh.is_visible_in_tree(),"collision_layer":mine.bank_body.collision_layer,"bounds":str(lo),"spawned_ids":stone_ids}
		if not baseline:
			visual_at_release["cut_chunks"]=mine.fracture.shards.size()
		image_pair("release")
	if first_release != -1:
		if clock == first_release+7: image_pair("fracture")
		if clock == first_release+32: image_pair("spent")
		if mine.phase=="seated" and not milestones.has("return"):
			milestones["return"]=clock
			image_pair("return")
	previous=mine.strikes

func typed_drops() -> Array:
	var ids:=[]
	for token in field.drops:
		var d:Dictionary=field.drops[token]
		if d.kind=="stone" and d.at.distance_to(mine.position)<2.0: ids.append(token)
	ids.sort()
	return ids

func walk_to(goal:Vector2) -> void:
	for step in 360:
		var reached:=move_to([goal.x,goal.y],.075)
		await step_mine()
		if reached:break
	steer(Vector2.ZERO)

func run() -> void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.size.x*.28,root.size.y*.70)
	mine=field.resource_rock
	initial_stock=field.inventory.carried.stone
	for step in 8: await step_mine()
	var at:=Vector2(mine.position.x,mine.position.z)
	await walk_to(at+Vector2.from_angle(-1.57)*2.75)
	image_pair("working-face")
	var settled:Vector3=field.actor.position
	for i in 225:
		await step_mine()
		if first_release>=0 and clock>=first_release+33:break
	var broken := first_release>=0
	var expected_yield := 3 if baseline else 6
	if not broken:image_pair("stalled")
	assertions["three strikes from the original northern approach"]=broken and counts.get("impact_stone",0)==3
	assertions["one physical break creates the full stone yield"]=broken and stone_ids.size()==expected_yield and counts.get("deplete_stone",0)==1
	if broken:
		assertions["visible boulder and walking collision clear together"]=not visual_at_release.source_visible and visual_at_release.collision_layer==0
		if not baseline:assertions["four pieces cut from the original bank separate"]=visual_at_release.cut_chunks==4
		await walk_to(at)
		for i in 24:await step_mine()
		assertions["walking over the actual drops banks each stone once"]=field.inventory.carried.stone-initial_stock==expected_yield and stone_ids.all(func(key):return field.inventory.collected.get(key)=="stone")
		image_pair("collected")
		await walk_to(at+Vector2(0,4.25))
		while clock<first_release+304:await step_mine()
		assertions["bank reopens after 300 physical ticks"]=milestones.get("return",-1)-first_release==300
		assertions["no second grant or retained collision during cooldown"]=counts.get("deplete_stone",0)==1 and typed_drops().is_empty() and field.inventory.carried.stone-initial_stock==expected_yield
	var record={"checks":assertions,"ticks":milestones,"source_id":mine.get_meta("field_source_id"),"at":[mine.position.x,mine.position.z],"working_position":[settled.x,settled.z],"source_at_release":visual_at_release,"events":counts,"inventory":field.inventory.carried,"renderer":RenderingServer.get_video_adapter_name(),"display_size":str(root.size),"frozen_reference":"25b4ec6/Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/02-stone.png"}
	print("MINING_REPLAY ",JSON.stringify(record))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(0 if baseline or false not in assertions.values() else 1)
