extends "res://tests/capture_task02.gd"
# T03 disclosed QA cameras over the unchanged live scene. No hidden fence or
# alternate art state is introduced; only camera/player position and the six
# controlled climate captures differ from normal gameplay.
const Boundary=preload("res://scripts/camp_boundary.gd")
const River=preload("res://scripts/river_geometry.gd")

func gate(id:String)->Dictionary:
	for row in Boundary.gate_specs():
		if row.id==id:return row
	assert(false,"Missing gate "+id);return {}

func offset3(v:Vector2,height:float)->Vector3:
	return Vector3(v.x,height,v.y)

func tag_river_evidence(contract:Dictionary,kind:String):
	assert(kind in Boundary.RIVER_EVIDENCE_KINDS)
	records[-1]["evidence_id"]=String(contract.evidence_ids[kind])
	records[-1]["river_gate_id"]=String(contract.id)
	records[-1]["river_gate_slug"]=String(contract.slug)
	records[-1]["evidence_kind"]=kind
	records[-1]["gate_authority_id"]=String(contract.authority_id)

func river_camera_profile(slug:String,kind:String)->Dictionary:
	# Evidence cameras are T03-only disclosed QA viewpoints. The east river gate
	# has permanent cabin/tree/rock context close to the threshold, so the generic
	# tangential offsets can hide an open leaf or the route behind authored scene
	# geometry. Its profile uses the opposite shoulder and a closer camp-side
	# station; runtime gameplay camera behavior remains untouched.
	if slug=="east":
		match kind:
			"river-side-approach":return {"inward":-4.5,"tangent":-1.6,"height":4.8,"size":5.7,"profile":"east-unoccluded-v1"}
			"threshold-three-quarter":return {"inward":-3.2,"tangent":-1.6,"height":5.0,"size":5.1,"profile":"east-unoccluded-v1"}
			"camp-side-outward":return {"inward":2.8,"tangent":1.8,"height":4.4,"size":5.0,"profile":"east-unoccluded-v1"}
	match kind:
		"river-side-approach":return {"inward":-5.8,"tangent":.8,"height":4.8,"size":6.6,"profile":"standard-v1"}
		"threshold-three-quarter":return {"inward":-4.0,"tangent":2.4,"height":5.2,"size":5.7,"profile":"standard-v1"}
		"camp-side-outward":return {"inward":4.6,"tangent":-1.0,"height":4.7,"size":5.9,"profile":"standard-v1"}
	assert(false,"Unknown T03 river evidence kind "+kind)
	return {}

func apply_river_camera(contract:Dictionary,kind:String)->Dictionary:
	var profile:=river_camera_profile(String(contract.slug),kind)
	var center:Vector2=contract.center
	var offset:Vector2=Vector2(contract.inward)*float(profile["inward"])+Vector2(contract.tangent)*float(profile["tangent"])
	focus_at(center,offset3(offset,float(profile["height"])),float(profile["size"]))
	return profile

func gameplay_gate_at(contract:Dictionary):
	# Keep the shipping gameplay camera's actual position, orthographic size and
	# player placement, but disclose a QA re-aim toward the authoritative gate
	# threshold. The former generic normal_at frame looked back toward the river
	# and could omit the gate entirely, which is invalid gameplay-scale evidence.
	normal_at(Vector2(contract.outside))
	var center:Vector2=contract.center
	var target:=Vector3(center.x,Surface.height_at(center)+.65,center.y)
	game.camera.look_at(target)
	game.update_foreground_visibility(game.xyz(game.sim.position)+Vector3(0,.95,0),.1)

func capture_gallery():
	focus_at(Vector2(0,2.1),Vector3(0,36,.01),29.0);await snap("perimeter-topdown")
	focus_at(Vector2(0,2.0),Vector3(21,30,27),25.0);await snap("perimeter-oblique")
	focus_at(Vector2(0,2.0),Vector3(0,31,.01),22.0);await snap("camp-lanes-overhead")
	focus_at(Vector2(0,2.0),Vector3(16,20,19),17.0);await snap("camp-lanes-oblique")
	var north:Dictionary=gate("north-main")
	focus_at(north.center,Vector3(0,7,9),7.3);await snap("north-gate-front")
	focus_at(north.center,Vector3(0,7,-9),7.3);await snap("north-gate-rear")
	var west:Dictionary=gate("west-work");focus_at(west.center,Vector3(-7.5,6.2,4.8),6.3);await snap("west-work-gate")
	var east:Dictionary=gate("east-work");focus_at(east.center,Vector3(7.5,6.2,4.8),6.3);await snap("east-work-gate")

	# Formal T03 river-gate evidence contract. Each gate gets four independent
	# views, all derived from the same gate geometry that drives leaves/routes.
	for contract in Boundary.river_gate_contracts():
		var slug:=String(contract.slug)
		var profile:=apply_river_camera(contract,"river-side-approach")
		await snap("river-gate-"+slug+"-approach");tag_river_evidence(contract,"river-side-approach");records[-1]["qa_view_profile"]=profile["profile"]
		profile=apply_river_camera(contract,"threshold-three-quarter")
		await snap("river-gate-"+slug);tag_river_evidence(contract,"threshold-three-quarter");records[-1]["qa_view_profile"]=profile["profile"]
		profile=apply_river_camera(contract,"camp-side-outward")
		await snap("river-gate-"+slug+"-camp-side");tag_river_evidence(contract,"camp-side-outward");records[-1]["qa_view_profile"]=profile["profile"]
		gameplay_gate_at(contract)
		await snap("gameplay-river-gate-"+slug);tag_river_evidence(contract,"gameplay-scale")
		records[-1]["gameplay_camera_position_and_scale_preserved"]=true
		records[-1]["qa_camera_reaimed_to_authoritative_threshold"]=true
		records[-1]["qa_view_profile"]="shipping-gameplay-position-reaim-v1"

	for row in [[-8.0,"west"],[1.5,"centre"],[9.0,"east"]]:
		var p:=Boundary.south_point(float(row[0]));focus_at(p,Vector3(0,7,9),7.4);await snap("south-fence-"+String(row[1]))
	for row in [[Vector2(0,7.2),"central-spine-north"],[Vector2(0,2.4),"central-spine-centre"]]:
		normal_at(row[0]);await snap(String(row[1]))
	focus_at(Boundary.bank_lane_point(1.5),Vector3(0,11,9),9.0);await snap("central-spine-river")
	for row in [[Vector2(-9.4,2.4),"cross-lane-west"],[Vector2(0,2.25),"cross-lane-centre"],[Vector2(9.4,2.4),"cross-lane-east"]]:
		normal_at(row[0]);await snap(String(row[1]))
	for row in [[Boundary.SHELTER_WEST,"shelter-branch-west"],[Boundary.SHELTER_EAST,"shelter-branch-east"]]:
		normal_at(row[0]);await snap(String(row[1]))
	for row in [[-9.0,"west"],[1.5,"centre"],[10.0,"east"]]:
		normal_at(Boundary.bank_lane_point(float(row[0])));await snap("bank-lane-"+String(row[1]))
	var panel:Dictionary=Boundary.panel_specs()[5]
	focus_at(panel.mid,Vector3(0,4.0,4.6),4.1);await snap("fence-panel-detail")
	focus_at(north.a,Vector3(-1.8,3.5,4.6),3.7);await snap("gate-post-detail")
	focus_at(north.center,Vector3(0,4.2,4.8),4.2);await snap("open-gate-leaves-detail")
	normal_at(Vector2(0,7.0));await snap("gameplay-north-gate")
	normal_at(Vector2(-10.4,2.4));await snap("gameplay-west-gate")
	normal_at(Vector2(10.4,2.4));await snap("gameplay-east-gate")
	focus_at(Vector2(1.0,-1.5),Vector3(0,31,.01),22.5);await snap("reserved-crossings-overhead")
	# Same camera and held unrelated animation poses for condition comparison only.
	focus_at(Vector2(0,2.0),Vector3(16,20,19),17.0)
	var held:=0
	for animation in game.world.find_children("*","AnimationPlayer",true,false):animation.pause();held+=1
	for setting in [["day",0.0],["dusk",400.0],["night",930.0],["dawn",990.0],["blizzard-night",630.0],["day-return",0.0]]:
		game.sim.climate.seconds=float(setting[1]);game.outpost_view.sync(game.sim,.1,false);await snap("boundary-condition-"+String(setting[0]));records[-1]["held_unrelated_animation_players"]=held

func capture_native():
	focus_at(Vector2(0,2.1),Vector3(0,36,.01),29.0);await snap("native-perimeter")
	focus_at(Vector2(0,2.0),Vector3(21,30,27),25.0);await snap("native-camp-oblique")
	var north:Dictionary=gate("north-main");focus_at(north.center,Vector3(0,7,9),7.3);await snap("native-north-gate")
	var west:Dictionary=gate("west-work");focus_at(west.center,Vector3(-7.5,6.2,4.8),6.3);await snap("native-side-gate-west")
	var east:Dictionary=gate("east-work");focus_at(east.center,Vector3(7.5,6.2,4.8),6.3);await snap("native-side-gate-east")
	for contract in Boundary.river_gate_contracts():
		var profile:=apply_river_camera(contract,"threshold-three-quarter")
		await snap("native-river-gate-"+String(contract.slug));records[-1]["qa_view_profile"]=profile["profile"]
	focus_at(Boundary.south_point(1.5),Vector3(0,7,9),7.4);await snap("native-south-fence")
	focus_at(Vector2(0,2.0),Vector3(0,31,.01),22.0);await snap("native-lane-network")
	var panel:Dictionary=Boundary.panel_specs()[5];focus_at(panel.mid,Vector3(0,4.0,4.6),4.1);await snap("native-fence-detail")

func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=not native;game.capture_directory=output;game.capture_frames=100
	game.size=Vector2(3840,2160) if native else Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	if native:await capture_native()
	else:await capture_gallery()
	var report={"task":"T03-boundary-v2","renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"captures":records,"forest":game.reference_forest_evidence,"river":game.outpost_view.evidence(game.sim),"boundary":game.camp_boundary_view.descriptor,"disclosed_qa_cameras":true,"conditions_hold_unrelated_animations_only":true,"native_frames_are_not_physical_fps_evidence":true,"task_approved":false}
	var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
