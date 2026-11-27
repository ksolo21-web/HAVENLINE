extends "res://tests/qa_paid_conveyors.gd"

const L=preload("res://field_logistics.gd")
var samples:Array=[]

func projected_rack(j:Dictionary)->Dictionary:
 return {"planks":L.rack(j,"wood"),"blocks":L.rack(j,"stone"),"meal":L.rack(j,"meat")}

func report()->Dictionary:
 var state:=snapshot_values()
 state.output_rack=projected_rack(field.inventory.settlement)
 state.remaining_orders=field.settlement_loop.conveyors.unclaimed_orders()
 return state

func mark(tick:int,label:String)->void:
 samples.append({"tick":tick,"event":label,"state":report()})

func test_pressure()->void:
 var book=field.inventory
 var b=field.settlement_loop.conveyors
 var j:Dictionary=book.settlement
 field.set_physics_process(false)
 b.refresh_paths()
 # The seed fixture has all paid machines and no outstanding jobs.
 # Forty-eight processed lots already occupy their legal typed bin. Four
 # more left by earlier production are visible on the actual machine outfeed.
 for source:String in ["wood","stone"]:
  for i in L.SPACE[L.PRODUCT[source]]+L.WORK_RACK+2:
   assert(book.collect("pressure-%s-%s"%[source,i],source))
   book.carried[source]-=1
  j["processed_"+source]+=L.SPACE[L.PRODUCT[source]]+L.WORK_RACK
  j.product_store[L.PRODUCT[source]]=L.SPACE[L.PRODUCT[source]]
  j.hoppers[source]=2
  var existing:=L.rack(j,source)
  check(source+" stored location and outlet remain separate",existing>=4 and j.product_store[L.PRODUCT[source]]==48)
  check(source+" backed up outfeed prevents a new work cycle",not field.settlement_loop._running(source))
  check(source+" full typed store holds the original product at source",not b._launch(L.PRODUCT[source]) and j.line_load[L.PRODUCT[source]]==0 and L.rack(j,source)==existing)
 for i in L.SPACE.meal+Journal.ROAST_RACK_CAPACITY+2:
  assert(book.collect("backpressure-food-%s"%i,"meat"))
  book.carried.meat-=1
 j.product_store.meal=L.SPACE.meal
 j.cooked+=L.SPACE.meal+Journal.ROAST_RACK_CAPACITY
 j.hoppers.meat=2
 check("full prepared inventory holds compatible cooker output",not b._launch("meal_to_store") and not field.settlement_loop._running("meat"))
 var before:Dictionary=book.snapshot()
 check("full house and outlets stay a valid conserved checkpoint",book.restore(JSON.parse_string(JSON.stringify(before))))
 j=book.settlement
 check("no order leaves prepared goods at their source",field.counter.queue.is_empty() and not b._launch("stored_meal") and not b._launch("meal"))
 field.counter._walk_queue(.2)
 if field.counter.queue.is_empty():field.counter._walk_queue(2.)
 check("first real arriving shopper can draw from a full prepared bay",b.unclaimed_orders()>0 and b._launch("stored_meal"))
 check("two sources cannot own the same fresh/stored merge",not b._launch("meal") and j.line_load.stored_meal==1)
 j.line_progress.stored_meal=1.
 check("reserved portion lands at the real guarded buffer",b._arrive("stored_meal") and j.counter_stock==1)
 check("freed prepared capacity accepts exactly one surplus",b._launch("meal_to_store") and not b._launch("meal_to_store"))
 check("work restarts after a cooked rack slot is freed",field.settlement_loop._running("meat"))
 # A second genuine order reaches the clerk before the first roast has
 # cleared the shared outlet. It must wait for roast-sized clearance.
 for tick in 360:
  field.counter._walk_queue(1./60.)
  if b.unclaimed_orders()>0:break
 check("second fresh order waits behind surplus leaving the same cooker throat",b.unclaimed_orders()>0 and not b._launch("meal") and j.line_load.meal_to_store==1)
 j.line_progress.meal_to_store=(b.COOKER_HEADWAY+.1)/b.lengths.meal_to_store
 check("cleared cooker can release the next roast to a different branch",b._launch("meal") and j.line_load.meal_to_store==1 and j.line_load.meal==1)
 var forged:Dictionary=book.snapshot().duplicate(true)
 forged.settlement.line_load.meal=1
 forged.settlement.line_load.stored_meal=1
 check("forged overlapping food sources rejected",not book.restore(forged))
 forged=book.snapshot().duplicate(true)
 forged.settlement.product_store.blocks+=1
 check("forged warehouse capacity rejected",not book.restore(forged))
 mark(0,"backpressure and selective demand")

func find_break()->Vector2:
 var layout=field.camp_layout
 var floor:Rect2=layout.bounds()
 var home:Vector2=layout.center("storage_wood")
 for x in range(0,3):
  var left:=snappedf(floor.position.x+1.97+x*.25,.25)
  for z in range(1,ceilf(floor.size.y)*2):
   var at:=Vector2(left,snappedf(floor.position.y+z*.5,.25))
   if not layout.reason("storage_wood",at).is_empty():continue
   var stub:=at+Vector2(-2.10,-.67)
   if not floor.grow(-.245).has_point(stub) and not at.is_equal_approx(home):return at
 return Vector2.INF

func live_break()->void:
 var b=field.settlement_loop.conveyors
 var j:Dictionary=field.inventory.settlement
 var home:Vector2=field.camp_layout.center("storage_wood")
 var bad:=find_break()
 check("found legal relocation obstructing a utility rail",bad.is_finite())
 if not bad.is_finite():return
 check("input is genuinely travelling before its port is disconnected",await until(func():return j.line_load.wood>0 and j.line_progress.wood>.02 or j.line_load.stone>0 and j.line_progress.stone>.02))
 var raw:="wood" if j.line_load.wood>0 else "stone"
 var previous:float=j.line_progress[raw]
 var shelf:int=field.inventory.stored[raw]
 check("normally placed storehouse can disconnect a paid line",field.camp_layout.relocate("storage_wood",bad))
 b.refresh_paths()
 check("disconnected lane is visible to HUD and unavailable for dispatch",not b.blocked_lane.is_empty() and b.paths[raw].is_empty())
 await ticks(120)
 check("stranded load pauses without spending again",j.line_load[raw]==1 and is_equal_approx(j.line_progress[raw],previous) and field.inventory.stored[raw]==shelf)
 mark(120,"cut route")
 field._checkpoint_lifecycle()
 var receipt:=FileAccess.open(profile_path.path_join("route-hold-qa.json"),FileAccess.WRITE)
 receipt.store_string(JSON.stringify({"raw":raw,"fraction":previous,"shelf":shelf,"home":[home.x,home.y]}))
 receipt.close()

func reconnect_after_restart()->void:
 var b=field.settlement_loop.conveyors
 var j:Dictionary=field.inventory.settlement
 var saved:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(profile_path.path_join("route-hold-qa.json")))
 var raw:String=saved.raw
 var home:=Vector2(saved.home[0],saved.home[1])
 b.refresh_paths()
 check("physical disconnection survives restart",b.paths[raw].is_empty() and not b.blocked_lane.is_empty())
 await ticks(90)
 check("closed app and fresh launch did not debit again or bank movement",j.line_load[raw]==1 and is_equal_approx(j.line_progress[raw],saved.fraction) and field.inventory.stored[raw]==int(saved.shelf))
 check("relocated house can be restored",field.camp_layout.relocate("storage_wood",home))
 b.refresh_paths()
 check("original rail reconnects without resetting ownership",b.paths[raw].size()>1 and j.line_load[raw]==1)
 check("paused bundle reaches its proper paid machine",await until(func():return j["processed_"+raw]>0,1600))
 mark(0,"reconnected")

func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--l1-disposable-profile="):profile_path=arg.trim_prefix("--l1-disposable-profile=")
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 camera=field.camera
 park(Vector3(1.15,0,.9))
 var b=field.settlement_loop.conveyors
 var j:Dictionary=field.inventory.settlement
 check("source save opens",not field.persist_blocked)
 var mode:="graph"
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--connection="):mode=arg.trim_prefix("--connection=")
 if mode=="pressure":await test_pressure()
 elif mode=="relocate":await live_break()
 elif mode=="reconnect":await reconnect_after_restart()
 elif mode=="legacy":
  check("v8 partly delivered direct roast preserved under serial installation",j.line_load.stored_meal==1 and is_equal_approx(j.line_progress.stored_meal,.42) and j.line_load.meal==0 and j.product_store.meal==0)
  check("only the paid serial path is installed",b.line_live("stored_meal") and not b.line_live("meal") and not b.line_live("meat"))
  check("migrated roast reaches staffed counter and pays exactly once",await until(func():return j.served==1,1700))
  await ticks(160)
  check("idle outbound legacy reservation cannot repeat",j.served==1 and j.cooked==1 and j.counter_stock==0 and j.line_load==L.TRANSIT)
  mark(0,"settled legacy food delivery")
 else:
  b.refresh_paths()
  check("all eight docked typed routes exist",L.LANES.all(func(lane):return not b.paths[lane].is_empty()))
  check("no cash, fuel, furnace, raw-ore or decorative stations receive generic outputs",b.paths.keys().all(func(k):return k in L.LANES) and b.paths.size()==8)
  var initial_cooked:int=j.cooked
  var initial_paid:int=j.served
  var initial_shown:Dictionary=j.line_load.duplicate()
  check("genuine v8 airborne inventory remains owned",initial_shown.wood==1 and initial_shown.stone==1 and initial_shown.meat==1)
  mark(0,"resumed three v8 dispatches")
  var previous:Dictionary=j.line_load.duplicate()
  var track_alignments:Array[float]=[]
  for i in 5600:
   var next:Dictionary=j.line_load.duplicate()
   if b.goods.planks.visible:
    var t:float=j.line_progress.planks
    var a:Vector3=b._sample("planks",maxf(0,t-.001))
    var z:Vector3=b._sample("planks",minf(1,t+.001))
    var tangent:=z-a
    var local:Vector3=field.depot.house.to_local(a)
    if tangent.length()>.001 and absf(tangent.normalized().y)<.35 and not field.depot.FOOTPRINT.has_point(Vector2(local.x,local.z)):
     var alignment:=absf(tangent.normalized().dot(b.goods.planks.global_basis.x.normalized()))
     track_alignments.append(alignment)
   if next!=previous:
    mark(i,"ownership changes")
    previous=next
   if int(j.served)==7 and j.product_store.planks==3 and j.product_store.blocks==3:break
   await physics_frame
  check("long planks stay aligned on the exterior rollers",track_alignments.size()>8 and track_alignments.min()>.88)
  check("finished timber and dressed stone arrive into different storage bays",j.product_store.planks==3 and j.product_store.blocks==3 and L.rack(j,"wood")==0 and L.rack(j,"stone")==0)
  check("cooker, fresh/stored dispatch and staff preserve one roast per sale",j.cooked-initial_cooked==6 and j.served-initial_paid==6 and j.cooked==j.served and L.rack(j,"meat")==0 and j.product_store.meal==0)
  check("no duplicate work remains in transit",j.line_load==L.TRANSIT)
  check("committed final receipts round trip",field.inventory.restore(JSON.parse_string(JSON.stringify(field.inventory.snapshot()))))
 print("CONNECTED_QA ",JSON.stringify({"mode":mode,"checks":results,"transitions":samples}))
 field.set_physics_process(false)
 await Session.drain_field_audio(self,field)
 field.queue_free()
 await process_frame
 quit(1 if false in results.values() else 0)
