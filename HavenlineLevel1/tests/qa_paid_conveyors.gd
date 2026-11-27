extends "res://tests/field_route.gd"

const Store=preload("res://field_save.gd")
const Journal=preload("res://field_settlement.gd")
const P=preload("res://field_progression.gd")
const Session=preload("res://tests/lifecycle_test_profile.gd")
var results:Dictionary={}
var profile_path:=""
var captured:Array=[]
var outdir:=OS.get_environment("HAVENLINE_CONVEYOR_VIEWS")

func check(title:String,value:bool) -> void:
 results[title]=value
 if not value:push_error(title)

func park(at:Vector3) -> void:
 field.actor.global_position=at
 field.previous_dry_position=at
 field.actor.velocity=Vector3.ZERO

func ticks(n:int) -> void:
 for i in n:await physics_frame

func until(fn:Callable,limit:=1500) ->bool:
 for i in limit:
  if fn.call():return true
  if field.persist_blocked:return false
  await physics_frame
 return fn.call()

func buy(id:String) -> void:
 var book=field.inventory
 if id in P.LINES:
  await ticks(4)
  var dock=field.opening_hud.camp_dock
  var launcher:Vector2=dock.build.get_global_rect().get_center()
  touch(7,launcher,true)
  touch(7,launcher,false)
  await ticks(3)
  if not outdir.is_empty() and id==P.FOOD_LINE:await shot("Choose-automation")
  var choice:=Vector2.INF
  for command in dock.commands:
   if command[1]==id:choice=command[0].get_global_rect().get_center()
  check(id+" is a visible build action",choice.is_finite())
  if not choice.is_finite():return
  touch(7,choice,true)
  touch(7,choice,false)
 check(id+" physically available",book.offer_open(id) and field.offer_floors[id].visible)
 var needs:Dictionary=book.remaining(id)
 for kind:String in needs:
  for i in needs[kind]:book.collect("test-tender-"+id+kind+str(i),kind)
 field.carry.sync(true)
 var site:Node3D=field.offer_floors[id]
 if id in P.LINES:
  park(Vector3(1.15,0,.9))
  await ticks(8)
  var mark:Vector3=site.global_position
  park(mark+Vector3.BACK*2.20)
  if not outdir.is_empty() and id==P.FOOD_LINE:await shot("Chosen-purchase-plot")
  for i in 230:
   if book.complete(id):break
   move_to([mark.x,mark.z+.31],.12)
   await physics_frame
  steer(Vector2.ZERO)
  park(Vector3(1.15,0,.9))
 else:
  await walk_to_equipment_plot(id,site)
 check(id+" purchased through actual plot",book.complete(id) and not field.persist_blocked)
 await ticks(6)

func walk_to_equipment_plot(id:String,site:Node3D) -> void:
 var network=field.settlement_loop.conveyors.network
 var grid=network.aisles
 var goal:=Vector3.INF
 var nearest:=INF
 for cell:Vector2i in grid.public_cells:
  var floor_xy:Vector2=grid._at(cell)
  var point:=Vector3(floor_xy.x,0.,floor_xy.y)
  if field.Reach.plot_distance(site,point)>.4:continue
  if not network.pedestrian_clear(point,point,field.layout.actor_radius):continue
  var distance:float=field.actor.global_position.distance_to(point)
  if distance<nearest:
   nearest=distance
   goal=point
 check(id+" has a public payment edge beside the live tracks",goal.is_finite())
 if not goal.is_finite():return
 var from:Vector3=field.actor.global_position
 var received_at:=Vector3.INF
 for step in 1500:
  if field.inventory.complete(id):break
  var feet:Vector3=field.actor.global_position
  if field.Reach.plot_distance(site,feet)<=.47:
   steer(Vector2.ZERO)
   if not received_at.is_finite():received_at=feet
  else:
   var waypoint:Vector3=network.walker_waypoint(feet,goal)
   move_to([waypoint.x,waypoint.z],.038)
  await physics_frame
 steer(Vector2.ZERO)
 captured.append({"station":id,"touch_start":[from.x,from.z],"paying_floor":[received_at.x,received_at.z] if received_at.is_finite() else [],"paid":field.inventory.paid[id].duplicate(),"pack":field.inventory.carried.duplicate()})

func shot(label:String) ->void:
 if outdir.is_empty():return
 await process_frame
 RenderingServer.force_draw(false)
 root.get_texture().get_image().save_jpg(outdir.path_join(label+".jpg"),.93)

func snapshot_values() ->Dictionary:
 var book=field.inventory
 var j:Dictionary=book.settlement
 return {"stored":book.stored.duplicate(),"hoppers":j.hoppers.duplicate(),"in_transit":j.line_load.duplicate(),"product_store":j.product_store.duplicate(),"progress":j.line_progress.duplicate(),"rack":Journal.waiting_meals(j),"counter_stock":j.counter_stock,"cash":j.served,"cooked":j.cooked,"planks":j.processed_wood,"blocks":j.processed_stone}

func lock_save() ->void:
 var dir:=DirAccess.open(profile_path)
 check("acquire competing lock",dir.make_dir(Store.LOCK)==OK)
 var f:=FileAccess.open(profile_path.path_join(Store.LOCK).path_join("owner-"+str(OS.get_process_id())),FileAccess.WRITE)
 f.close()

func unlock_save() ->void:
 var dir:=DirAccess.open(profile_path)
 dir.remove(Store.LOCK+"/owner-"+str(OS.get_process_id()))
 dir.remove(Store.LOCK)

func run()->void:
 var profile=Store.Profile.new()
 if not profile.configure(OS.get_cmdline_user_args()):quit(2);return
 profile_path=profile.directory if "directory" in profile else ""
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--l1-disposable-profile="):profile_path=arg.trim_prefix("--l1-disposable-profile=")
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 camera=field.camera
 origin=root.get_visible_rect().size*Vector2(.30,.72)
 var book=field.inventory
 var loop=field.settlement_loop
 var belts=loop.conveyors
 var j:Dictionary=book.settlement
 var phase:="initial"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--conveyor="):phase=arg.trim_prefix("--conveyor=")
 park(Vector3(1.15,0,.9))
 check("opened valid isolated save",not field.persist_blocked)
 if phase=="growth":
  check("genuine new kitchen has no free saw or drill",book.is_machine_owned("meat") and not book.is_machine_owned("wood") and not book.is_machine_owned("stone"))
  await buy(P.SUPPLY_LINE)
  check("unowned outbuildings remain disconnected",await until(func():return j.cooked>=2) and j.line_load.wood==0 and j.line_load.stone==0 and book.stored.wood==3 and book.stored.stone==3)
  await buy(P.MACHINES.wood)
  check("new saw connects without rebuying supply",await until(func():return j.processed_wood>=1) and book.build_order.count(P.SUPPLY_LINE)==1 and j.processed_stone==0)
  await buy(P.MACHINES.stone)
  check("next quarry connects to the existing supply purchase",await until(func():return j.processed_stone>=1) and book.build_order.count(P.SUPPLY_LINE)==1)
  captured.append(snapshot_values())
 elif phase=="relocate":
  await buy(P.SUPPLY_LINE)
  check("raw supply alone cannot sell a meal",j.served==0 and not book.complete(P.FOOD_LINE))
  check("moving actual timber exists",await until(func():return j.line_load.wood==1 and j.line_progress.wood>.10))
  var before:float=j.line_progress.wood
  var center:Vector2=field.camp_layout.center(P.MACHINES.wood)
  var dest:=Vector2.INF
  for offset in [Vector2(1.,0),Vector2(0,1.5),Vector2(2.25,1.5),Vector2(1.5,3.),Vector2(3.,5.),Vector2(7.,10.)]:
   if field.camp_layout.reason(P.MACHINES.wood,center+offset).is_empty():
    dest=center+offset
    break
  check("moved the paid saw mid-dispatch",dest.is_finite() and field.camp_layout.relocate(P.MACHINES.wood,dest))
  belts.refresh_paths()
  var port:Vector3=field.processors.input_position("wood")
  var moved_route:PackedVector3Array=belts.paths.wood
  check("remaining distance targets the new real hopper",not moved_route.is_empty() and moved_route[-1].distance_to(port)<.001 and absf(j.line_progress.wood-before)<.0001)
  for lane:String in ["wood","stone","meat"]:
   var path:PackedVector3Array=belts.paths[lane]
   var within:=not path.is_empty()
   for point:Vector3 in path:within=within and field.camp_layout.bounds().has_point(Vector2(point.x,point.z))
   check(lane+" route remains inside the paid walls",within)
  # Allow physical travel across the expanded court and back after relocation.
  var delivered:bool=await until(func():return j.product_store.planks==3 and j.product_store.blocks==3 and j.cooked==4,5400)
  check("all six outputs return to typed stock after moving without a duplicate",delivered and j.processed_wood==3 and j.processed_stone==3 and j.served==0)
  captured.append({"old_saw":[center.x,center.y],"new_saw":[dest.x,dest.y],"active_fraction":before,"state":snapshot_values()})
 elif phase=="film":
  var first_food:=-1
  var first_cash:=-1
  var runs:=[]
  park(Vector3(.52,0.,-4.20))
  for i in 542:
   if i==247:field.set_zoom_ratio(1.7)
   if i==248:park(Vector3(2.6,0.,-5.55))
   if i==21:await shot("Normal-gameplay-moving-stock")
   if i==188:await shot("Normal-gameplay-production")
   if field.counter.belt_serving and first_food<0:
    first_food=i
   if field.counter.belt_serving and is_instance_valid(field.counter.cash) and field.counter.cash.visible and first_cash<0:
    first_cash=i
   if i>=265 and field.counter.belt_serving and is_instance_valid(field.counter.cash) and field.counter.cash.visible and not results.has("pinch cash"):
    await shot("Pinch-customer-payment")
    results["pinch cash"]=true
   if i>=265 and j.line_load.meal==1 and j.line_progress.meal>.28 and not results.has("pinch delivery"):
    await shot("Pinch-moving-meal")
    results["pinch delivery"]=true
   if i%12==0:runs.append({"tick":i,"operation":snapshot_values()})
   await physics_frame
  captured.append({"observed_belt_service_tick":first_food,"visible_cash_tick":first_cash,"samples":runs})
  check("real serving and cash rendered",first_food>=0 and first_cash>=0 and j.served>=2)
 elif phase=="initial":
  check("real v7 unlocked buildings and no gifted lines",book.build_order.size()==11 and not book.complete(P.FOOD_LINE) and not book.complete(P.SUPPLY_LINE))
  await ticks(100)
  check("unpaid belts never move stock",j.hoppers=={"wood":0,"stone":0,"meat":0} and j.served==0 and j.cooked==1 and book.stored.wood==3)
  await buy(P.FOOD_LINE)
  check("food line does not activate raw line",not book.complete(P.SUPPLY_LINE) and j.hoppers.wood==0 and book.stored.meat==6)
  check("base food purchase installs serial storage and request links",not belts.line_live("meal") and belts.line_live("meal_to_store") and belts.line_live("stored_meal"))
  check("real roast reaches paying non-player customer",await until(func():return j.served==1,2500))
  check("food sale is a real paid counter exchange",field.events.any(func(e):return e.event=="meal_served") and j.held_meal==0 and j.worker_meal==0)
  await buy(P.SUPPLY_LINE)
  check("both purchases install all eight typed routes",await until(func():return belts.blocked_lane.is_empty() and belts.lengths.size()==8 and belts.lengths.values().all(func(n):return n>0),200))
  check("side docks dispatch without swinging the pedestrian doors",await until(func():return j.line_load.stone==1 and j.line_progress.stone>.04,900) and not field.depot.house.doors_open)
  captured.append(snapshot_values())
  await shot("storehouse-supplies-moving")
  await ticks(4)
  field._checkpoint_lifecycle()
  check("normalized partial paths persisted",j.line_progress.stone>0. and j.line_load.stone==1)
 elif phase=="interrupt":
  check("cold start restores moving load",j.line_load.stone==1 and j.line_progress.stone>0.)
  field.set_physics_process(false)
  var previous:=FileAccess.get_file_as_bytes(profile_path.path_join(Store.PRIMARY))
  lock_save()
  j.line_progress.stone=1.
  loop.conveyors.refresh_paths()
  check("rejected landing pauses safely",not belts._arrive("stone") and field.persist_blocked)
  check("previous durable bytes stay intact",FileAccess.get_file_as_bytes(profile_path.path_join(Store.PRIMARY))==previous)
  unlock_save()
 elif phase=="finish":
  check("failed landing can be retried from saved input",j.line_load.stone==1 and j.line_progress.stone>0. and j.hoppers.stone>=0)
  check("wood, stone and meals finish offscreen and earn cash",await until(func():return j.served==7 and j.product_store.planks==3 and j.product_store.blocks==3,8000))
  check("entire path conserved all goods",book.stored.wood==0 and book.stored.stone==0 and book.stored.meat==0 and j.cooked==7 and Journal.waiting_meals(j)==0 and j.counter_stock==0)
  check("one purchased input meal per completed order",field.events.any(func(e):return e.event=="conveyor_delivery") and j.served==7)
  captured.append(snapshot_values())
  await shot("paid-orders-and-production")
  await ticks(160)
  check("idle empty lines cannot pay twice",j.served==7 and j.line_load==Journal.LINE_EMPTY)
  field._checkpoint_lifecycle()
 else:
  check("earned cash and both purchases survive restart",j.served==7 and book.complete(P.FOOD_LINE) and book.complete(P.SUPPLY_LINE) and not field.persist_blocked)
  await ticks(70)
  check("idle storehouse cannot create extra product",j.served==7 and j.cooked==7 and j.product_store.planks==3 and j.product_store.blocks==3)
 print("CONVEYOR_QA ",JSON.stringify({"phase":phase,"checks":results,"receipts":captured}))
 field.set_physics_process(false)
 await Session.drain_field_audio(self,field)
 field.queue_free()
 await process_frame
 quit(1 if false in results.values() else 0)
