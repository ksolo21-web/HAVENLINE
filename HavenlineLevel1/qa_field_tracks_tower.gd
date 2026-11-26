extends SceneTree
const Tracks=preload("res://field_snow_tracks.gd")
const Tower=preload("res://field_tower_art.gd")
const Wolf=preload("res://field_enemy.gd")
var checks:={}
var results:={}
var save_dir:=OS.get_environment("TRACK_TOWER_EVIDENCE")
func _initialize(): call_deferred("run")
func record(key:String,val:bool): checks[key]=val
func plate(name_:String):
	if DisplayServer.get_name()=="headless" or save_dir.is_empty():return
	RenderingServer.force_draw(false)
	root.get_texture().get_image().save_jpg(save_dir.path_join(name_+".jpg"),.95)
func run():
	var arena:=Node3D.new();root.add_child(arena)
	var mask_warm: Array=[false]
	var t:=Tracks.new();arena.add_child(t);t.set_physics_process(false)
	t.configure(func(p:Vector3):return p.z<3.0 and (not mask_warm[0] or p.x>10.0))
	var human:=Node3D.new()
	human.add_to_group(Tracks.SURVIVOR_GROUP)
	arena.add_child(human)
	var prop:=Node3D.new()
	arena.add_child(prop)
	record("new survivor automatically discovered", t.living.has(human))
	for i in 90:
		prop.position.z+=.03
		t._physics_process(1./60)
	record("moving prop and stationary survivor leave no tracks", not t.living.has(prop) and t.total==0)
	for i in 90:
		human.position.x+=.03;t._physics_process(1./60)
	record("unrigged survivor leaves alternating soles",t.total>=4 and t.living[human].step>=4)
	var count:=t.total
	for i in 60:t._physics_process(1./60)
	record("standing still creates no impressions",t.total==count)
	human.position=Vector3(50,0,5);t._physics_process(.016);human.position.x+=.7;t._physics_process(.1)
	record("teleport and non-snow omitted",t.total==count)
	mask_warm[0]=true;t.refresh_surface()
	record("warm expansion clears old tracks immediately",t.total==0)
	t.configure(func(_p:Vector3):return true)
	for i in 1150:
		t._emit_mark(Vector3(i*.12,0,0),0,i%3==0,false,1.)
	record("bounded batching",t.total<=Tracks.MAX_MARKS and t.chunks.size()<20)
	t._physics_process(Tracks.LIFE+.5)
	record("prints fade and chunks retire",t.total==0 and t.chunks.is_empty())
	human.queue_free();await process_frame
	record("freed actor unregistered",t.living.is_empty())
	arena.free()

	var game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	var tracker=game.tracks
	var h=game.actor
	h.position=Vector3(-1.8,0,12)
	tracker.reset_actor(h)
	var input:=Vector2(.84,0)
	game.touch_id=7;game.touch_origin=Vector2(500,420);game.touch_now=game.touch_origin+input*82.
	for i in 140: await physics_frame
	game.touch_id=-1
	var hp:=0
	var sides:={}
	for chunk in tracker.chunks.values():
		for m in chunk.marks:
			if not m.wolf:hp+=1;sides[m.right]=true
	results.human_marks=hp;results.sole_sides=sides.size()
	results.sole_bones=tracker.living[h].feet.size()
	record("integrated hero rig produces both planted boot tracks",hp>=3 and sides.size()==2 and results.sole_bones==2)
	# Normal walk action with deterministic player-relative lanes for comparison of paw geometry.
	game.set_physics_process(false)
	for enemy in game.enemies: enemy.hide()
	var clear:Vector3=h.position
	var test_actors: Array=[]
	for boss in [false,true]:
		var animal=Wolf.new();animal.is_boss=boss;game.add_child(animal)
		animal.position=clear+Vector3(2.55 if boss else .82,0,-3.55)
		animal.configure(h);tracker.register_actor(animal,"wolf",animal.size_factor())
		animal._play("Walk");animal.animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		test_actors.append(animal)
	for i in 140:
		for animal in test_actors:
			animal.position.z+=.0196;animal.animator.advance(1./60)
		await physics_frame
	var paws:={}
	for animal in test_actors:
		var placements:=0
		for foot in tracker.living[animal].feet:
			if (foot.last as Vector3).is_finite():placements+=1
		paws["boss" if animal.is_boss else "wolf"]=placements
	var sizes:={}
	for chunk in tracker.chunks.values():
		for m in chunk.marks:
			if m.wolf:sizes[str(snappedf(m.extent.x,.001))]=true
	results.paw_bones_with_landings=paws;results.paw_widths=sizes.keys()
	record("four ordinary and four boss paws plant",paws.wolf==4 and paws.boss==4)
	record("boss paws larger",sizes.size()>=2)
	game.camera.position=clear+Vector3(.45,0,-.8)+Vector3(7,11,11);game.set_zoom_ratio(2.0)
	plate("Snow-tracks-gameplay-2x")
	tracker.set_physics_process(false)
	if DisplayServer.get_name()!="headless" and not save_dir.is_empty():
		var fade_frames: Array[Image]=[]
		fade_frames.append(root.get_texture().get_image())
		var mark:Dictionary={}
		var best:=INF
		for chunk in tracker.chunks.values():
			for m in chunk.marks:
				var dist:float=m.p.distance_to(clear-Vector3(2.,0,0))
				if not m.wolf and dist<best:
					best=dist;mark=m
		var fresh_age:float=tracker.clock-mark.time
		results.fade_fresh_age=fresh_age
		tracker._physics_process(Tracks.LIFE*.74-fresh_age)
		await process_frame;RenderingServer.force_draw(false)
		fade_frames.append(root.get_texture().get_image())
		tracker._physics_process(Tracks.LIFE)
		await process_frame;RenderingServer.force_draw(false)
		fade_frames.append(root.get_texture().get_image())
		var left:Vector2=game.camera.unproject_position(mark.p)
		var rect:=Rect2i(Vector2i(left)-Vector2i(37,32),Vector2i(74,64))
		rect=rect.intersection(Rect2i(Vector2i.ZERO,fade_frames[0].get_size()))
		var strip:=Image.create_empty(rect.size.x*3,rect.size.y,false,Image.FORMAT_RGB8)
		for i in 3:
			var frame:=fade_frames[i].get_region(rect)
			frame.convert(Image.FORMAT_RGB8)
			strip.blit_rect(frame,Rect2i(Vector2i.ZERO,rect.size),Vector2i(rect.size.x*i,0))
		strip.save_png(save_dir.path_join("Track-fade-three-times.png"))
	for animal in test_actors:
		animal.hp=0;animal.position.x+=.25
	tracker._physics_process(.016)
	var cleared:=true
	for animal in test_actors:
		for foot in tracker.living[animal].feet:
			if (foot.last as Vector3).is_finite():cleared=false
	record("dead actors cease planting",cleared)
	for animal in test_actors:animal.hide()
	h.position=Vector3(8.1,0,-1.2)
	game._apply_hearth(true,false)
	var tower=game.defense_tower.art
	tower.show();tower.set_build_progress(1.)
	tower.aim_at_world(Vector3(13,0,6))
	var bolt=tower.projectile();game.add_child(bolt)
	record("separate modeled bolt and world launch anchor",bolt.find_children("*","MeshInstance3D",true,false).size()>0 and tower.muzzle_global_position().y>1.85)
	bolt.queue_free()
	tower.set_build_progress(.35);record("frame builds before roof",not tower.frame.find_child("SlateRoof",true,false).visible)
	tower.set_build_progress(1.);record("completed roof visible",tower.frame.find_child("SlateRoof",true,false).visible)
	game.camera.position=tower.global_position+Vector3(7,11,11);game.set_zoom_ratio(2.)
	await process_frame;plate("Eastern-watchtower-gameplay-2x")
	if DisplayServer.get_name()!="headless":
		h.hide()
		game.opening_hud.get_parent().hide()
		var c=game.camera;c.keep_aspect=Camera3D.KEEP_HEIGHT;c.size=4.35;c.position=tower.global_position+Vector3(4,3.9,5);c.look_at(tower.global_position+Vector3.UP*1.62)
		c.force_update_transform()
		await process_frame
		plate("Eastern-watchtower-detail")
	results.checks=checks
	var ok:=not checks.values().has(false);results.pass=ok
	print("TRACK_TOWER ",JSON.stringify(results))
	if not save_dir.is_empty():
		var f:=FileAccess.open(save_dir.path_join("regression.json"),FileAccess.WRITE);f.store_string(JSON.stringify(results,"  "))
	game.sound.stop_playback()
	for i in 22:await physics_frame
	game.queue_free()
	for i in 5:await process_frame
	quit(0 if ok else 1)
