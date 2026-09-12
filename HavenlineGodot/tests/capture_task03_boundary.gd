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

func capture_gallery():
	focus_at(Vector2(0,2.1),Vector3(0,36,.01),29.0);await snap("perimeter-topdown")
	focus_at(Vector2(0,2.0),Vector3(21,30,27),25.0);await snap("perimeter-oblique")
	focus_at(Vector2(0,2.0),Vector3(0,31,.01),22.0);await snap("camp-lanes-overhead")
	focus_at(Vector2(0,2.0),Vector3(16,20,19),17.0);await snap("camp-lanes-oblique")
	var north:Dictionary=gate("north-main")
	focus_at(north.center,Vector3(0,7,9),7.3);await snap("north-gate-front")
	focus_at(north.center,Vector3(0,7,-9),7.3);await snap("north-gate-rear")
	# Slightly oblique side-gate views expose the open leaves, grounded hinge
	# posts and packed lane in one frame instead of flattening the gate head-on.
	var west:Dictionary=gate("west-work");focus_at(west.center,Vector3(-7.5,6.2,4.8),6.3);await snap("west-work-gate")
	var east:Dictionary=gate("east-work");focus_at(east.center,Vector3(7.5,6.2,4.8),6.3);await snap("east-work-gate")
	for row in [["river--9.0","west",Vector3(3.6,5.4,6.2)],["river-1.5","centre",Vector3(2.8,5.4,6.2)],["river-10.0","east",Vector3(-3.6,5.4,6.2)]]:
		var g:Dictionary=gate(row[0]);focus_at(g.center,row[2],5.7);await snap("river-gate-"+String(row[1]))
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
	normal_at(Boundary.bank_lane_point(1.5));await snap("gameplay-river-gate-centre")
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
	for id_name in [["river--9.0","west",Vector3(3.6,5.4,6.2)],["river-1.5","centre",Vector3(2.8,5.4,6.2)],["river-10.0","east",Vector3(-3.6,5.4,6.2)]]:
		var g:Dictionary=gate(id_name[0]);focus_at(g.center,id_name[2],5.7);await snap("native-river-gate-"+String(id_name[1]))
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
