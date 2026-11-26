extends SceneTree
var out="/tmp/havenline-critic95-post/geom"
var w
var meta={}
func _initialize():call_deferred("run")
func dump(tag:String,root_obj:Node3D,world_xform:bool=true):
 var verts:=PackedVector3Array();var tris:=PackedInt32Array()
 var parts=root_obj.find_children("*","MeshInstance3D",true,false)
 if root_obj is MeshInstance3D:parts.push_front(root_obj)
 for m:MeshInstance3D in parts:
  if m.mesh==null:continue
  var transform= m.global_transform if world_xform else (root_obj.global_transform.affine_inverse()*m.global_transform)
  for s in m.mesh.get_surface_count():
   var a=m.mesh.surface_get_arrays(s);var start=verts.size()
   for p:Vector3 in a[Mesh.ARRAY_VERTEX]:verts.append(transform*p)
   for i:int in a[Mesh.ARRAY_INDEX]:tris.append(start+i)
 var f=FileAccess.open(out+"/"+tag+"-v",FileAccess.WRITE);f.store_buffer(verts.to_byte_array());f.close()
 f=FileAccess.open(out+"/"+tag+"-f",FileAccess.WRITE);f.store_buffer(tris.to_byte_array());f.close()
 meta[tag]=[verts.size(),tris.size()/3]
func run():
 w=load("res://field_opening.tscn").instantiate();root.add_child(w)
 for i in 5:await physics_frame
 w.set_physics_process(false);w.actor.position=Vector3.ZERO;w.actor.rotation.y=0.;w.actor.force_update_transform()
 for kind:String in w.Inventory.KINDS:
  w.inventory.carried[kind]=5
 w.carry.sync()
 dump("rack",w.carry.frame)
 for kind:String in w.Inventory.KINDS:
  var pool=w.carry.pieces["carry/"+kind]
  for i in pool.size():
   if pool[i].visible:dump(kind+str(i),pool[i])
 var kit=w.character_kit
 var poses:={}
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
 var file=FileAccess.open(out+"/transforms.json",FileAccess.WRITE);file.store_string(JSON.stringify({"meshes":meta,"samples":poses}));file.close()
 w.queue_free()
 for i in 8:await process_frame
 quit()
