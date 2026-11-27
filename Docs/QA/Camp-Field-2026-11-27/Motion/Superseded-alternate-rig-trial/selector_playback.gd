extends SceneTree
var field
func _initialize()->void:call_deferred("sample")
func sample()->void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 4:await physics_frame
	if not field.field_ready or field.persist_blocked:quit(2);return
	var run_id:=OS.get_environment("MOTION_RUN")
	var initial:int=field.player_character()
	var invalid:bool=field.set_player_character(15)
	var rows:=[]
	var ok:=not invalid and initial==(1 if run_id=="1" else 3)
	var actor_id:int=field.actor.get_instance_id()
	for role in ([2,4,1,3] if run_id=="1" else [3,1]):
		var chosen:bool=field.set_player_character(role)
		await physics_frame
		var ward=field.player_wardrobe
		var contacts:PackedVector3Array=ward.boot_contacts()
		var checks:bool=chosen and field.player_character()==role and actor_id==field.actor.get_instance_id() and ward.originals[0].is_visible_in_tree()==(role==1) and (role==1 or (ward.target.get_bone_count()==52 and ward.visual.is_visible_in_tree())) and contacts.size()==2
		ok=ok and checks
		rows.append({"role":role,"original_skin_visible":ward.originals[0].is_visible_in_tree(),"world_actor_preserved":field.actor.get_instance_id()==actor_id,"bones":ward.source.get_bone_count() if role==1 else ward.target.get_bone_count(),"two_physical_boot_contacts":contacts.size()==2,"passed":checks})
	var o=FileAccess.open(OS.get_environment("MOTION_OUT")+"/selector-"+run_id+".json",FileAccess.WRITE)
	o.store_string(JSON.stringify({"boot":run_id,"initial_role":initial,"invalid_id_rejected":not invalid,"choices":rows,"passed":ok},"  "));o.close()
	field.sound.stop_playback();field.queue_free()
	for i in 3:await process_frame
	quit(0 if ok else 8)
