extends SceneTree
var field
var camera: Camera3D
var origin := Vector2.ZERO
var touch_held := false
var last_input := Vector2.ZERO
func _initialize()->void:
 call_deferred("run")

func touch(id:int,pos:Vector2,pressed:bool)->void:
 var e:=InputEventScreenTouch.new()
 e.index=id
 e.position=pos
 e.pressed=pressed
 root.push_input(e,true)

func steer(direction:Vector2)->void:
 if direction.is_zero_approx():
  if touch_held:
   touch(0,origin,false)
   touch_held=false
   last_input=Vector2.ZERO
  return
 if not touch_held:
  touch(0,origin,true)
  touch_held=true
 if last_input.distance_to(direction)<.006: return
 var e:=InputEventScreenDrag.new()
 e.index=0
 e.position=origin+direction*82.
 e.relative=(direction-last_input)*82.
 e.screen_relative=e.relative
 root.push_input(e,true)
 last_input=direction

func pt(x:Vector3)->Array:return [x.x,x.y,x.z]

func move_to(p:Array,tol:float)->bool:
 var pos:Vector3=field.actor.global_position
 var delta:=Vector3(float(p[0])-pos.x,0.,float(p[1])-pos.z)
 if delta.length()<=tol:
  steer(Vector2.ZERO);return true
 var right:=camera.global_basis.x
 var near:=right.cross(Vector3.UP)
 var d:=Vector2(delta.dot(right),delta.dot(near)).normalized()
 steer(d*clampf(delta.length()*1.25,.3,.98))
 return false


var result:={}
func check_one(z:float)->Dictionary:
 field.set_zoom_ratio(z)
 field.carry.advance(0.)
 var counts:Dictionary=field.carry.presented.duplicate()
 var ymax:=-INF
 var yscreen:=INF
 for kind:String in field.inventory.KINDS:
  var key:="carry/"+kind
  if not field.carry.pieces.has(key):continue
  for unit:Node3D in field.carry.pieces[key]:
   if not unit.visible: continue
   for mesh:MeshInstance3D in unit.find_children("*","MeshInstance3D",true,false):
    if not mesh.mesh: continue
    for i in 8:
     var point:=mesh.to_global(mesh.get_aabb().get_endpoint(i))
     ymax=maxf(ymax,point.y-field.actor.global_position.y)
     yscreen=minf(yscreen,camera.unproject_position(point).y/root.get_visible_rect().size.y)
 return {"visible":counts,"highest_m_above_feet":ymax,"top_fraction":yscreen}

func run()->void:
 field=load("res://field_opening.tscn").instantiate();root.add_child(field);current_scene=field;camera=field.camera
 origin=Vector2(root.size.x*.28,root.size.y*.7)
 for i in 6:await physics_frame
 result.revision=OS.get_environment("PACK_BUILD")
 result.before=field.inventory.carried.duplicate()
 result.atrest=[check_one(1.),check_one(2.)]
 field.set_zoom_ratio(1.)
 var steps:Array=[]
 var from:Vector3=field.actor.global_position
 for i in 43:
  steer(Vector2(.82,.12) if i<32 else Vector2.ZERO)
  await physics_frame
  var bootR:Transform3D=field.gait_motor._boot_world(1)
  var bootL:Transform3D=field.gait_motor._boot_world(0)
  steps.append([i,pt(field.actor.global_position),pt(bootL.origin),pt(bootR.origin)])
 result.steps=steps
 result.traveled_m=from.distance_to(field.actor.global_position)
 result.after=field.inventory.carried.duplicate()
 var f=FileAccess.open(OS.get_environment("PACK_OUT"),FileAccess.WRITE)
 f.store_string(JSON.stringify(result));f.close()
 await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
 field.queue_free();await process_frame;quit()
