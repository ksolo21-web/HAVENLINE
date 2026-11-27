extends SceneTree
var world
func _initialize()->void:call_deferred("run")
func run()->void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for tick in 5:await physics_frame
	var ok:bool=world.field_ready and not world.persist_blocked
	var initial:int=world.player_character()
	var boot_id:=OS.get_environment("MOTION_PREF_BOOT")
	ok=ok and initial==(4 if boot_id=="2" else 1)
	world.inventory.collect("identity-proof-pack","wood")
	world.carry.sync(true)
	world.player_hp=world.MAX_HP-3
	var persistent_actor: int=world.actor.get_instance_id()
	var rows: Array=[]
	for role in ([2,3,1,4] if boot_id=="1" else [4,2,3,1]):
		var initial_ledger:Dictionary=world.inventory.snapshot().duplicate(true)
		var initial_hp:int=world.player_hp
		var chosen:bool=world.set_player_character(role)
		var state_kept:bool=initial_ledger==world.inventory.snapshot() and initial_hp==world.player_hp
		await physics_frame
		var wardrobe=world.player_wardrobe
		var rig:Skeleton3D=wardrobe.source if role==1 else wardrobe.target
		if not rig:
			print("Absent rig for C",role);ok=false;break
		var sole:PackedVector3Array=wardrobe.boot_contacts()
		var valid:bool=state_kept and chosen and rig.get_bone_count()==64 and rig.find_bone("Shin.L")>0 and rig.find_bone("Shin.R")>0 and rig.find_bone("Head")>=0 and sole.size()==2 and persistent_actor==world.actor.get_instance_id()
		rows.append({"role":role,"valid":valid,"health_and_ledger_preserved":state_kept,"bones":rig.get_bone_count(),"stance":[sole[0].y,sole[1].y] if sole.size()==2 else [],"scene":str(rig.get_path()),"original_visible":wardrobe.originals[0].is_visible_in_tree(),"feet":wardrobe.tread.soles.size()})
		ok=ok and valid
	print(JSON.stringify({"boot":boot_id,"initial_role":initial,"role_switches":rows,"ok":ok}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for tick in 4:await process_frame
	quit(0 if ok else 3)
