extends "res://tests/world_house_route.gd"

var samples:={}
var pending:=false

func observe_clip(row:Dictionary) -> void:
 var count:int=field.inventory.carried.wood
 var id:=""
 if count in [3,12,37,42] and (count>=37 or field.carry.flights.is_empty()):id="cargo-%d"%count
 if row.label=="Laden gate crossing" and absf(field.actor.position.z-4.)<.65 and count>=35:id="cargo-at-gate"
 if id.is_empty() or samples.has(id) or pending:return
 samples[id]=true
 capture_rack(id)

func capture_rack(id:String) -> void:
 pending=true
 if plate_enabled:
  await process_frame
  RenderingServer.force_draw(false,1./24.)
 var camera:Camera3D=root.get_camera_3d()
 var minimum:=Vector2(INF,INF)
 var maximum:=Vector2(-INF,-INF)
 var top:=-INF
 var visible_counts:={}
 for kind in ["wood","stone","meat"]:
  var units:=0
  for model in field.carry.pieces.get("carry/"+kind,[]):
   if not model.is_visible_in_tree():continue
   units+=1
   var meshes=model.find_children("*","MeshInstance3D",true,false)
   if model is MeshInstance3D:meshes.push_back(model)
   for part in meshes:
    if not part.is_visible_in_tree():continue
    var bounds:AABB=part.get_aabb()
    for i in 8:
     var corner:Vector3=part.to_global(bounds.get_endpoint(i))
     var projected:=camera.unproject_position(corner)
     minimum=minimum.min(projected)
     maximum=maximum.max(projected)
     top=maxf(top,corner.y)
  visible_counts[kind]=units
 var captured=field.inventory.carried.duplicate()
 if id.begins_with("cargo-") and id!="cargo-at-gate" and int(id.trim_prefix("cargo-"))!=int(captured.wood):
  samples.erase(id);pending=false;return
 var record={"id":id,"tick":tick,"carried":captured,"flights":field.carry.flights.size(),"stage":phases[index].label,"visible_mesh_units":visible_counts,"top_above_feet_m":top-field.actor.position.y,"screen_bounds_xyxy":[minimum.x,minimum.y,maximum.x,maximum.y],"viewport":[root.size.x,root.size.y],"native_scale":root.scaling_3d_scale,"camera":str(camera.get_path()),"feet":pt(field.actor.position),"zoom":field.get_zoom_ratio()}
 if plate_enabled:
  var image:Image=root.get_texture().get_image()
  assert(image.get_size()==root.size and root.scaling_3d_scale==1.0)
  image.convert(Image.FORMAT_RGB8)
  image.save_png(out_dir.path_join(id+".png"))
 event("cargo_readback",record)
 pending=false
