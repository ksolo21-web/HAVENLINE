extends SceneTree
var out := OS.get_environment("HAVENLINE_GEAR_GEOMETRY")
var w
var meta={}
var nodeparts=[]
var origins={}
func _initialize():call_deferred("run")
func dump(tag:String,root_obj:Node3D,world_xform:bool=true):
 var verts:=PackedVector3Array();var tris:=PackedInt32Array()
 var parts=root_obj.find_children("*","MeshInstance3D",true,false)
 if root_obj is MeshInstance3D:parts.push_front(root_obj)
 if tag=="rack":nodeparts=[]
 for m:MeshInstance3D in parts:
  if m.mesh==null or (world_xform and not m.is_visible_in_tree()):continue
  var transform= m.global_transform if world_xform else (root_obj.global_transform.affine_inverse()*m.global_transform)
  for s in m.mesh.get_surface_count():
   var a=m.mesh.surface_get_arrays(s);var start=verts.size()
   if tag=="rack":
    nodeparts.append({"name":str(m.name),"first_face":tris.size()/3,"count":a[Mesh.ARRAY_INDEX].size()/3,"local_to_world":var_to_str(transform)})
   for p:Vector3 in a[Mesh.ARRAY_VERTEX]:verts.append(transform*p)
   for i:int in a[Mesh.ARRAY_INDEX]:tris.append(start+i)
 var f=FileAccess.open(out+"/"+tag+"-v",FileAccess.WRITE);f.store_buffer(verts.to_byte_array());f.close()
 f=FileAccess.open(out+"/"+tag+"-f",FileAccess.WRITE);f.store_buffer(tris.to_byte_array());f.close()
 meta[tag]=[verts.size(),tris.size()/3]
 origins[tag]=[root_obj.global_position.x,root_obj.global_position.y,root_obj.global_position.z]
 f=FileAccess.open(out+"/root-origins.json",FileAccess.WRITE);f.store_string(JSON.stringify(origins));f.close()
 if tag=="rack":
  f=FileAccess.open(out+"/rack-classes.json",FileAccess.WRITE);f.store_string(JSON.stringify(nodeparts));f.close()
func dump_supports():
 dump("rack",w.carry.frame)
 if "dividers" in w.carry:
  for family in w.carry.dividers:
   var divider=w.carry.dividers[family]
   if divider.is_visible_in_tree():dump("divider-"+family,divider)
func run():
 w=load("res://field_opening.tscn").instantiate();root.add_child(w)
 for i in 5:await physics_frame
 w.set_physics_process(false);w.actor.position=Vector3.ZERO;w.actor.rotation.y=0.;w.actor.force_update_transform()
 w.camera.position=Vector3(7,11,11)
 w.camera.look_at(Vector3.ZERO)
 w.camera.size=13.0
 w.camera.force_update_transform()
 for kind:String in w.Inventory.KINDS:
  w.inventory.carried[kind]=5
 w.carry.sync()
 w.carry.rack.force_update_transform()
 dump_supports()
 for kind:String in w.Inventory.KINDS:
  var pool=w.carry.pieces["carry/"+kind]
  for i in pool.size():
   if pool[i].visible:dump(kind+str(i),pool[i])
 var kit=w.character_kit
 var poses:={}
 var direction:Vector3=kit.CAMERA_NEAR
 var orbit_geometry={"near_direction_xz":[direction.x,direction.z],"side_radius":kit.RADIUS_SIDE,"depth_radius":kit.RADIUS_DEPTH,"upgraded_radius_multiplier":kit.UPGRADED_RADIUS}
 for kind in ["axe","pickaxe"]:
  for count in [1,3]:
   kit.set_upgraded(count==3);kit.reach_scale=kit.UPGRADED_RADIUS if count==3 else 1.;kit.begin(kind);kit.height=kit.desired_height()
   var rows:=[]
   for step in 108:
    kit.elapsed=minf(step/120.,kit.PERIOD);kit.pose()
    var node:Node3D=kit.slots[0][kind]
    if step==0 and count==1:dump(kind,node,false)
    var x=node.global_transform;var b=x.basis
    rows.append([kit.elapsed,b.x.x,b.y.x,b.z.x,x.origin.x,b.x.y,b.y.y,b.z.y,x.origin.y,b.x.z,b.y.z,b.z.z,x.origin.z])
   poses[kind+str(count)]=rows
 var file=FileAccess.open(out+"/transforms.json",FileAccess.WRITE);file.store_string(JSON.stringify({"meshes":meta,"samples":poses,"origins":origins,"orbit_geometry":orbit_geometry}));file.close()
 var mixed=out
 out=mixed+"/full-72"
 DirAccess.make_dir_recursive_absolute(out)
 for family:String in w.Inventory.KINDS:w.inventory.carried[family]=12
 w.carry.sync()
 var count_visible:=0
 dump_supports()
 for family:String in w.Inventory.KINDS:
  var items=w.carry.pieces["carry/"+family]
  for i in items.size():
   if items[i].is_visible_in_tree():
    dump(family+str(i),items[i])
    count_visible+=1
 if count_visible!=72:
  printerr("Only %d of the 72 full-load units were captured."%count_visible)
  quit(1)
  return
 print("Captured all 72 mounted meshes at the normal gameplay camera.")
 for family:String in w.Inventory.KINDS:
  for k:String in w.Inventory.KINDS:w.inventory.carried[k]=1 if k==family else 0
  w.carry.sync()
  out=mixed+"/single-"+family
  DirAccess.make_dir_recursive_absolute(out)
  meta={}
  dump_supports()
  dump(family+"0",w.carry.pieces["carry/"+family][0])
 for n in [2,3,5,20]:
  for k:String in w.Inventory.KINDS:w.inventory.carried[k]=n if k=="wood" else 0
  w.carry.sync()
  out=mixed+"/timber-"+str(n)
  DirAccess.make_dir_recursive_absolute(out)
  meta={}
  dump_supports()
  for i in w.carry.pieces["carry/wood"].size():
   if w.carry.pieces["carry/wood"][i].is_visible_in_tree():dump("wood"+str(i),w.carry.pieces["carry/wood"][i])
 w.set_physics_process(false)
 w.sound.stop_playback()
 w.queue_free()
 w=null
 for i in 16:
  OS.delay_msec(25)
  await process_frame
 quit()
