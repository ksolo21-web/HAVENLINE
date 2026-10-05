extends SceneTree
const Main=preload("res://scripts/main.gd")
const Boundary=preload("res://scripts/camp_boundary.gd")
const Surface=preload("res://scripts/outpost_surface.gd")
var game
var output="user://material-review"
var candidate_source=""
var rows=[]
func _initialize():
 for a in OS.get_cmdline_user_args():
  if a.begins_with("--out="):output=a.trim_prefix("--out=")
 candidate_source=OS.get_environment("GITHUB_SHA")
 assert(candidate_source.length()==40,"Frozen material review requires exact GITHUB_SHA")
 call_deferred("run")
func focus(point:Vector2,offset:Vector3,size:float):
 var target=Vector3(point.x,Surface.height_at(point)+.7,point.y)
 game.camera.size=size
 game.camera.position=target+offset
 game.camera.look_at(target,Vector3.UP)
func snap(name):
 await process_frame
 await process_frame
 await RenderingServer.frame_post_draw
 var img=game.scene_view.get_texture().get_image()
 assert(img.get_width()==3840 and img.get_height()==2160,"Diagnostic must be native4K")
 img.save_png(output.path_join(name+".png"))
 rows.append({"name":name,"resolution":[img.get_width(),img.get_height()],"camera_position":game.camera.position,"camera_size":game.camera.size})
 print("MATERIAL_REVIEW_FRAME ",name)
func run():
 DirAccess.make_dir_recursive_absolute(output)
 game=Main.new();game.qa_mode=true;game.render_review=false;game.capture_frames=1000;game.capture_directory=output;game.size=Vector2(3840,2160)
 root.add_child(game);game.set_process(false);game.set_physics_process(false)
 game._process(.016)
 await snap("whole-camp")
 var panel:Dictionary=Boundary.panel_specs()[5]
 focus(panel.mid,Vector3(0,4.0,4.6),4.1)
 await snap("fence-detail")
 var gate:Dictionary=Boundary.gate_specs()[0]
 focus(gate.center,Vector3(0,4.2,4.8),4.2)
 await snap("gate-detail")
 focus(gate.center,Vector3(0,4.2,-4.8),4.2)
 await snap("gate-rear")
 focus(panel.mid,Vector3(0,4.0,-4.6),4.1)
 await snap("fence-rear")
 for setting in [["night",930.0],["blizzard",630.0]]:
  game.sim.climate.seconds=float(setting[1]);game.outpost_view.sync(game.sim,.1,false)
  focus(gate.center,Vector3(0,4.2,4.8),4.2)
  await snap("gate-"+String(setting[0]))
 game.sim.climate.seconds=0.0;game.outpost_view.sync(game.sim,.1,false)
 focus(Vector2(0,2.0),Vector3(16,20,19),17.0)
 await snap("whole-camp-oblique")
 var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"candidate_source":candidate_source,"actual_shipping_runtime_scene":true,"disclosed_detail_and_reverse_QA_cameras":true,"production_visual_approval":false,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"frames":rows,"boundary_evidence":game.camp_boundary_view.descriptor}))
 game.outpost_audio.stop_all()
 quit(0)
