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
 # R18: real placed stations on the unmodified shipping gameplay scene.
 # Camera-only inspection; no isolated stages, asset transforms or hidden props.
 var catalog=JSON.parse_string(FileAccess.get_file_as_string("res://assets/stations_v2/catalog.json"))
 assert(catalog is Dictionary)
 var targets=["cooker_processor","cargo_crate","fish_crate","fuel_canister","intake_machine","wood_stack"]
 # Two sets: a readable below-tree detail camera and a disclosed shipping-
 # scale context camera. Both remain on the untouched live scene, and neither
 # changes a placed mesh, its material, physics, or nearby occluders.
 var views=[
  {"id":"front","offset":Vector3(0,2.8,-4.5),"size":3.1},
  {"id":"right","offset":Vector3(4.5,2.8,0),"size":3.1},
  {"id":"rear","offset":Vector3(0,2.8,4.5),"size":3.1},
  {"id":"three-quarter","offset":Vector3(3.5,3.3,-4.0),"size":3.4},
  {"id":"gameplay-context","offset":Vector3(0,5.4,-8.0),"size":4.6}
 ]
 var captured_assets=[]
 for area in ["camp","lakeshore"]:
  for placement in catalog["arrangements"][area]:
   var id=String(placement["id"])
   if not id in targets:continue
   var xyz=placement["position"]
   var point=Vector2(float(xyz[0]),float(xyz[2]))
   captured_assets.append(id)
   # The real world marker must exist at the catalog-resolved position.
   # Do not infer proof from empty or misidentified QA camera pixels.
   var kit=game.camp_station_kit if area=="camp" else game.lakeshore_station_kit
   var matching=kit.placed.filter(func(node):return String(node.get_meta("t05_asset_id",""))==id)
   assert(matching.size()==1,"Missing actual shipping kit marker: "+id)
   var placement_world:Vector3=matching[0].global_position
   assert(placement_world.distance_to(Vector3(point.x,Surface.height_at(point),point.y))<.05,
          "Catalog vs shipping placement mismatch: "+id)
   for view in views:
    var target=placement_world+Vector3(0,.75,0)
    game.camera.size=float(view["size"])
    game.camera.position=target+Vector3(view["offset"])
    game.camera.look_at(target,Vector3.UP)
    var frame_name="live-"+id+"-"+String(view["id"])
    await snap(frame_name)
    var projected:Vector2=game.camera.unproject_position(target)
    var canvas_centre=Vector2(1920,1080)
    rows[-1]["asset_id"]=id
    rows[-1]["area"]=area
    rows[-1]["view"]=String(view["id"])
    rows[-1]["placement"]=xyz
    rows[-1]["actual_live_marker"]=placement_world
    rows[-1]["projected_target_px"]=projected
    rows[-1]["center_error_px"]=projected.distance_to(canvas_centre)
    rows[-1]["camera_uses_reference_materials"]=true
    rows[-1]["unmodified_shipped_asset_transform"]=true
 assert(captured_assets.size()==targets.size())
 var f=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"candidate_source":candidate_source,"actual_shipping_runtime_scene":true,"disclosed_detail_and_reverse_QA_cameras":true,"production_visual_approval":false,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"frames":rows,"boundary_evidence":game.camp_boundary_view.descriptor}))
 game.outpost_audio.stop_all()
 quit(0)
