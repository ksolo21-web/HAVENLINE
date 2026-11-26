extends SceneTree

var w
var rows := []
var folder := OS.get_environment("CHAR_REVIEW_OUTPUT")
const ANCHOR := Vector2(96, 300)

func _initialize():
 call_deferred("run")

func shot(path: String, full := false):
 RenderingServer.force_draw(false)
 var im := root.get_texture().get_image()
 if full:
  im.save_jpg(folder+"/"+path+".jpg", .96)
 var center: Vector2=w.camera.unproject_position(w.actor.global_position)
 var rect := Rect2i(int(center.x)-170, maxi(0,int(center.y)-560),340,mini(600,int(center.y)+34))
 var cropped:=im.get_region(rect)
 cropped.save_png(folder+"/"+path+".png")
 return [rect.position.x,rect.position.y,rect.size.x,rect.size.y]

func sample(id: String, layers: bool):
 var rect=shot(id,true)
 if layers:
  w.carry.rack.hide()
  shot(id+"-body")
  w.hero_model.hide()
  shot(id+"-ground")
  w.carry.rack.show()
  shot(id+"-cargo")
  w.hero_model.show()
 var p:Vector3 = w.actor.global_position
 var q:Vector2=w.camera.unproject_position(p)
 rows.append({"plate":id,"camera":str(w.camera.global_transform),"viewport":str(root.size),"projected_feet":[q.x,q.y],"region":rect,"zoom":w.trial_camera.zoom_ratio,"yaw":w.actor.rotation.y,"load":w.inventory.carried.duplicate(),"speed":w.actor.velocity.length(),"gait":w.character_kit.locomotion.current,"position":[p.x,p.y,p.z]})

func load_pack(load_type:String):
 for kind in w.Inventory.KINDS:
  var n=0
  if load_type=="six": n=5
  if load_type=="timber" and kind=="wood":n=24
  w.inventory.carried[kind]=n
 w.carry.sync()

func input_touch(touch: bool, drag:=Vector2.ZERO):
 if drag==Vector2.ZERO:
  var e:=InputEventScreenTouch.new();e.index=1;e.position=ANCHOR;e.pressed=touch;w._input(e)
 else:
  var e:=InputEventScreenDrag.new();e.index=1;e.position=ANCHOR+drag*82;w._input(e)

func run():
 w=load("res://field_opening.tscn").instantiate();root.add_child(w)
 for i in 4: await physics_frame
 for zoom in [1.,2.]:
  w.actor.position=Vector3(55,0,55)
  w.actor.velocity=Vector3.ZERO
  w.camera.position=w.actor.position+Vector3(7,11,11)
  w.set_zoom_ratio(zoom)
  for i in 10: await physics_frame
  # Aim at the actual gameplay viewing direction, keeping the normal camera transform.
  var just_idle := OS.get_environment("CHAR_REVIEW_EMPTY") == "1"
  var loads := ["empty"] if just_idle else ["empty","timber","six"]
  for load_type in loads:
   load_pack(load_type)
   for i in 2: await physics_frame
   for deg in [0,45,90,135,180,225,270,315]:
    if zoom==2. and deg not in [0,135,180,270]:continue
    w.actor.rotation.y=atan2(7.,11.)+deg_to_rad(deg)
    sample("%s-%d-%03d"%[load_type,zoom,deg],true)
  if just_idle: continue
  load_pack("six")
  input_touch(true)
  var facing:=Vector2(.79,.59)
  for m in [["walk",facing*.43,60],["run",facing*.95,60],["turn",-facing*.95,54]]:
   input_touch(true,m[1])
   for i in int(m[2]):
    await physics_frame
    if i in [5,20,36,51]:
     sample("%s-%d-%03d"%[m[0],zoom,i],false)
  input_touch(false)
  for i in 20: await physics_frame
  sample("stop-%d"%zoom,false)
 var f=FileAccess.open(folder+"/observations.json", FileAccess.WRITE)
 f.store_string(JSON.stringify(rows));f.close()
 w.queue_free()
 for i in 12: await process_frame
 quit(0)
