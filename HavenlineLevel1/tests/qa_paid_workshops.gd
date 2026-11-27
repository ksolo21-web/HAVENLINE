extends "res://tests/field_route.gd"

const Store = preload("res://field_save.gd")
const Progress = preload("res://field_progression.gd")
const Session = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}
var events_paid := {}
var frame_index := 0
var budget := 0
var capture_dir := OS.get_environment("MACHINE_QA_VIEWS")

func check(title: String, value: bool) -> void:
 checks[title] = value
 if not value:push_error(title)

func shot(label: String) -> void:
 if capture_dir.is_empty():return
 await process_frame
 RenderingServer.force_draw(false)
 root.get_texture().get_image().save_jpg(capture_dir.path_join(label+".jpg"),.93)

func tick_once() -> void:
 await physics_frame
 frame_index += 1

func walk_into_plot(kind: String, id: String) -> void:
 var plot: Node3D = field.offer_floors[id]
 var destination := plot.global_position + Vector3.BACK*1.2
 # Stage outside this station's approach zone. Contact, payment, and the
 # following reveal are driven only through screen touch events in the real scene.
 field.actor.position = Vector3(-.20,0,-5.40) if kind=="wood" else plot.global_position + Vector3.BACK*3.2
 field.actor.velocity = Vector3.ZERO
 field.previous_dry_position = field.actor.position
 field.camera.position=field.actor.position+Vector3(7,11,11)
 for i in 7: await tick_once()
 check(kind+" priced plot visible before touch",plot.is_visible_in_tree())
 var before:Dictionary=field.inventory.paid[id].duplicate()
 var spent := false
 var sampling := OS.get_environment("MACHINE_QA_MOVIE") == "1" and kind == "meat"
 var captured := 0
 if sampling: await shot("sequence-%03d" % captured)
 for i in 180:
  if field.inventory.complete(id):break
  move_to([destination.x,destination.z],.15)
  await tick_once()
  if sampling and (not field.carry.flights.is_empty() or spent) and i%4==0:
   captured+=1
   await shot("sequence-%03d" % captured)
  if not spent and field.inventory.paid[id]!=before:
   spent=true
   await shot(kind+"-spending")
 steer(Vector2.ZERO)
 check(kind+" final receipt paid on nearby edge",field.inventory.complete(id) and not field.persist_blocked)
 var box:Rect2 = field.lakeshore._footprint(field.layout.actor_radius) if kind=="meat" else field.processors._rect(kind,field.layout.actor_radius)
 check(kind+" buyer outside final solid on purchase frame",not box.has_point(Vector2(field.actor.position.x,field.actor.position.z)))
 events_paid[kind]={"elapsed_frames":frame_index,"landed":field.inventory.paid[id].duplicate(),"actor":pt(field.actor.position)}
 for i in 25:
  await tick_once()
  if sampling and i%4 == 0:
   captured+=1
   await shot("sequence-%03d" % captured)
 await shot(kind+"-owned")
 field.set_zoom_ratio(2)
 for i in 8:await tick_once()
 await shot(kind+"-pinch")
 field.set_zoom_ratio(1)
 var start:Vector3=field.actor.position
 var aisle:Vector3=Vector3((1.35 if kind=="wood" else start.x),0.,-4.9)
 if kind=="wood":aisle.z=-5.58
 for i in 30:
  move_to([aisle.x,aisle.z],.15)
  await tick_once()
  if start.distance_to(field.actor.position)>.55:break
 steer(Vector2.ZERO)
 check(kind+" buyer can leave following construction", start.distance_to(field.actor.position)>.32 and not box.has_point(Vector2(field.actor.position.x,field.actor.position.z)))

func verify_edges(kind:String) -> void:
 var box:Rect2=field.lakeshore._footprint(0.) if kind=="meat" else field.processors._rect(kind,0.)
 var center:=box.get_center()
 for side:Vector2 in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
  var middle:=center+side*(box.size*.5)
  for d in [.51,1.10]:
   var p:=middle+side*float(d)
   var at:=Vector3(p.x,0,p.y)
   var usable:bool=field.lakeshore.at_cooker(at) if kind=="meat" else field.processors.at_station(at)==kind
   check(kind+" "+str(side)+" approach "+str(d),usable==(d<1.))

func run()->void:
 var guard=Store.Profile.new()
 if not guard.configure(OS.get_cmdline_user_args()):quit(2);return
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 camera=field.camera
 origin=root.get_visible_rect().size*Vector2(.30,.72)
 var book=field.inventory
 check("baseline save reopened",not field.persist_blocked)
 if "--machine-reopen" in OS.get_cmdline_user_args():
  check("all three individual purchases survived cold launch",field.processors.available and field.lakeshore.available and book.is_machine_owned("wood") and book.is_machine_owned("stone"))
  check("original pending wood ran after purchase only",book.settlement.hoppers.wood==0 and book.settlement.processed_wood==1)
  check("prior output stock preserved",book.settlement.processed_stone==1 and book.settlement.cooked>=1)
 else:
  check("eight expansion receipts restore without machines",book.build_order.size()==8 and not field.lakeshore.available and not field.processors.available)
  check("no collider or loading receipt before any station purchase",field.processors.guards.wood.collision_layer==0 and field.processors.guards.stone.collision_layer==0 and field.lakeshore.guard.collision_layer==0 and not field.lakeshore.at_cooker(field.lakeshore.APRON))
  for i in 110:await tick_once()
  check("v6 queue, prior work and cooked stock held intact before purchase",book.settlement.hoppers.wood==1 and is_equal_approx(book.settlement.work_seconds.wood,.42) and book.settlement.processed_wood==0 and book.settlement.cooked==1 and book.settlement.processed_stone==1)
  for kind:String in ["meat","wood","stone"]:
   var id:String=Progress.MACHINES[kind]
   var machine:Node3D=field.lakeshore.cooker if kind=="meat" else field.processors.machines[kind]
   check("future "+kind+" model absent",not machine.is_visible_in_tree())
   # Only stage the materials for the current offer, with half the further
   # receipts in the store. No purchase state or input method is mocked.
   for item:String in book.remaining(id):
    var missing:=maxi(0,book.remaining(id)[item]-book.carried[item]-book.stored[item])
    for i in missing:
     book.collect("play-"+kind+item+str(i),item)
     if i%2==0:book.deposit(item)
   field.carry.sync()
   await walk_into_plot(kind,id)
   check(kind+" model and collision earned",machine.is_visible_in_tree() and (field.lakeshore.guard.collision_layer==1 if kind=="meat" else field.processors.guards[kind].collision_layer==1))
   verify_edges(kind)
  field.actor.position=Vector3(2,0,1)
  field.actor.velocity=Vector3.ZERO
  for i in 120:await tick_once()
  check("all production receipts conserved without remote forged grants",book.settlement.processed_wood==1 and book.settlement.processed_stone==1 and book.settlement.cooked>=1)
  field._persist_world()
 check("valid paid state",not field.persist_blocked)
 print("MACHINE_QA ",JSON.stringify({"checks":checks,"visits":events_paid}))
 field.set_physics_process(false)
 field.carry.set_physics_process(false)
 await Session.drain_field_audio(self,field);field.queue_free()
 for i in 5:await process_frame
 quit(1 if false in checks.values() else 0)
