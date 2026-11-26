extends SceneTree
## Capture the imported mesh and every bone after a real Level 1 input tick.
const ANCHOR := Vector2(80,620)
var folder := OS.get_environment("HAVENLINE_GEAR_GEOMETRY")
var world
var skin: Skin
var skeleton: Skeleton3D
var binds := PackedInt32Array()
var poses: FileAccess

func _initialize():
 Engine.physics_ticks_per_second=60
 call_deferred("run")

func save_buffer(path: String, data: PackedByteArray):
 var f=FileAccess.open(folder+"/"+path,FileAccess.WRITE)
 f.store_buffer(data)
 f.close()

func capture_import():
 var part:MeshInstance3D
 for n in world.hero_model.find_children("*","MeshInstance3D",true,false):
  if n.skin:
   assert(part==null)
   part=n
 assert(part and part.mesh.get_surface_count()==1)
 skin=part.skin
 skeleton=part.get_node(part.skeleton)
 var arrays=part.mesh.surface_get_arrays(0)
 var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
 var weights:PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
 var indices:PackedInt32Array=arrays[Mesh.ARRAY_BONES]
 var faces:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
 var bones:=[]
 for i in skin.get_bind_count():
  var bone=skeleton.find_bone(skin.get_bind_name(i))
  assert(bone>=0)
  binds.append(bone);bones.append(skin.get_bind_name(i))
 save_buffer("body-v",vertices.to_byte_array())
 save_buffer("body-f",faces.to_byte_array())
 save_buffer("body-weights",weights.to_byte_array())
 save_buffer("body-bone-ids",indices.to_byte_array())
 var f=FileAccess.open(folder+"/body-info.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"bones":bones,"triangles":faces.size()/3,"vertices":vertices.size(),"weights_per_vertex":indices.size()/vertices.size()}));f.close()

func drag(power: float):
 var e=InputEventScreenDrag.new()
 e.index=4; e.position=ANCHOR+Vector2.RIGHT*power*82.
 world._input(e)

func sample(stage: int, power:float, ticks:int):
 drag(power)
 for tick in ticks:
  await physics_frame
  var local=world.actor.global_transform.affine_inverse()*skeleton.global_transform
  var mat:=PackedVector3Array()
  for i in binds.size():
   var x:Transform3D=local*skeleton.get_bone_global_pose(binds[i])*skin.get_bind_pose(i)
   mat.append(x.basis.x);mat.append(x.basis.y);mat.append(x.basis.z);mat.append(x.origin)
  poses.store_32(stage);poses.store_32(tick);poses.store_buffer(mat.to_byte_array())

func run():
 world=load("res://field_opening.tscn").instantiate();root.add_child(world)
 for i in 5:await physics_frame
 world.actor.position=Vector3(55,0,55)
 for kind:String in world.Inventory.KINDS:world.inventory.carried[kind]=5
 world.carry.sync()
 capture_import()
 poses=FileAccess.open(folder+"/body-poses",FileAccess.WRITE)
 var touch=InputEventScreenTouch.new()
 touch.index=4;touch.position=ANCHOR;touch.pressed=true
 world._input(touch)
 await sample(0,0,64)
 await sample(1,.43,96)
 await sample(2,1,96)
 await sample(3,-1,96)
 await sample(4,0,64)
 poses.close()
 world.set_physics_process(false)
 world.sound.stop_playback()
 world.queue_free()
 world=null
 skin=null
 skeleton=null
 poses=null
 for i in 16:
  OS.delay_msec(25)
  await process_frame
 quit()
