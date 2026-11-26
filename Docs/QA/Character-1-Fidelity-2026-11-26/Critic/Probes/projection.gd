extends SceneTree
var w
var meshes={}
var data={}

func _initialize(): call_deferred("verify")
func proj(p:Vector3,axis:Vector3)->float:return p.dot(axis)
func bounds(meshes_to_check:Array):
 var mi:=Vector2(INF,INF)
 var ma:=-mi
 for m:MeshInstance3D in meshes_to_check:
  if not m.is_visible_in_tree() or not m.mesh:continue
  var mesh=m.mesh
  if not meshes.has(mesh):
   var vs:=PackedVector3Array()
   for s in mesh.get_surface_count():
    var arr=mesh.surface_get_arrays(s)
    vs.append_array(arr[Mesh.ARRAY_VERTEX])
   meshes[mesh]=vs
  var mat:=m.global_transform
  var cam=w.camera
  var orig:Vector2=cam.unproject_position(mat.origin)
  var ax:Vector2=cam.unproject_position(mat.origin+mat.basis.x)-orig
  var ay:Vector2=cam.unproject_position(mat.origin+mat.basis.y)-orig
  var az:Vector2=cam.unproject_position(mat.origin+mat.basis.z)-orig
  var fx=Vector3(ax.x,ay.x,az.x);var fy=Vector3(ax.y,ay.y,az.y)
  var vs:PackedVector3Array=meshes[mesh]
  for v:Vector3 in vs:
   var q=orig+Vector2(v.dot(fx),v.dot(fy)); mi=mi.min(q);ma=ma.max(q)
 return [] if mi.x == INF else [snappedf(mi.x,.01),snappedf(mi.y,.01),snappedf(ma.x,.01),snappedf(ma.y,.01)]
func verify():
 w=load("res://field_opening.tscn").instantiate();root.add_child(w)
 for i in 4:await physics_frame
 for z in [1.,2.]:
  w.actor.position=Vector3(55,0,55);w.actor.velocity=Vector3.ZERO;w.camera.position=w.actor.position+Vector3(7,11,11);w.set_zoom_ratio(z)
  for i in 10:await physics_frame
  for load_type in ["timber","six"]:
   for kind in w.Inventory.KINDS:w.inventory.carried[kind]=24 if load_type=="timber" and kind=="wood" else (5 if load_type=="six" else 0)
   w.carry.sync()
   for i in 2:await physics_frame
   for deg in [0,45,90,135,180,225,270,315]:
    if z==2. and deg not in [0,135,180,270]:continue
    w.actor.rotation.y=atan2(7.,11.)+deg_to_rad(deg)
    var all:Array=w.carry.rack.find_children("*","MeshInstance3D",true,false)
    var pieces={}
    for kind in w.Inventory.KINDS:
     var group=[]
     for unit in w.carry.pieces.get(w.carry.HAND+"/"+kind,[]):
      if unit is MeshInstance3D:group.append(unit)
      group.append_array(unit.find_children("*","MeshInstance3D",true,false))
     pieces[kind]=bounds(group)
    data["%s-%d-%03d"%[load_type,z,deg]]={"feet":str(w.camera.unproject_position(w.actor.global_position)),"viewport":str(root.size),"virtual":str(root.get_visible_rect().size),"camera_size":w.camera.size,"all_rack_and_packets":bounds(all),"families":pieces}
 var f=FileAccess.open(OS.get_environment("CHAR_REVIEW_OUTPUT")+"/projection.json",FileAccess.WRITE);f.store_string(JSON.stringify(data));f.close()
 w.queue_free()
 for i in 12:await process_frame
 quit()
