extends "res://tests/field_route.gd"

const Scene = preload("res://field_opening.tscn")
const Session = preload("res://tests/lifecycle_test_profile.gd")
var checks := {}
var measurements := {}
var receipt_id := 0

func verify(id:String, correct:bool) -> void:
 checks[id] = correct
 if not correct: push_error(id)

func supply(kind:String, quantity:int) -> void:
 for i in quantity:
  receipt_id += 1
  field.inventory.collect("stream-fixture-%d" % receipt_id, kind)

func open_site(id:String) -> void:
 var needs:Dictionary = field.inventory.remaining(id)
 for kind:String in needs:
  supply(kind, needs[kind])
  for i in int(needs[kind]): field.inventory.payment(id,kind,false)
 field._finish_purchase(id)
 field._apply_hearth(true,false)
 field.reveal_countdown = -1.

func walk_to(target:Vector3) -> bool:
 for frame in 200:
  if move_to([target.x,target.z],.18): return true
  await physics_frame
 steer(Vector2.ZERO)
 return false

func route() -> void:
 for id in ["center_hearth","expansion_1","storage_wood"]: open_site(id)
 field.actor.position = field.depot.APRON + Vector3(0,0,2.05)
 for row in [["wood",10],["meat",20],["stone",4]]: supply(row[0],row[1])
 field.carry.sync()
 field._persist_world()
 var before = field.inventory.paid.duplicate(true)
 camera = field.camera
 var reached = await walk_to(field.depot.SITE + Vector3(.03,0,.43))
 for i in 80: await physics_frame
 verify("Touch joystick enters the actual starter building", reached and field.depot.house.open_amount>.99 and field.depot.house.is_interior_visible())
 verify("Starter center and interior unload only FOOD and TIMBER",field.depot.visit=="load" and field.inventory.stored.meat==20 and field.inventory.stored.wood==10 and field.inventory.carried.stone==4 and field.inventory.paid==before)
 verify("FOOD shelf shows authored meat and balance",field.depot.labels.meat.text=="200" and field.depot.bins.meat.is_visible_in_tree() and field.carry.pieces["storage/meat"].any(func(piece):return piece.is_visible_in_tree()))
 measurements["touch_entrance"]={"ending":str(field.actor.position),"visit":field.depot.visit,"stored":field.inventory.stored.duplicate(),"carried":field.inventory.carried.duplicate(),"house_tier":field.depot.house.tier}
 field._persist_world()

func cold() -> void:
 var ledger=field.inventory
 verify("Cold reload keeps starter tier and typed receipts",field.depot.house.tier==1 and ledger.carried.stone==4 and ledger.stored.wood==10 and ledger.stored.meat==20 and ledger.carried.meat==0)
 for i in 80: await physics_frame
 verify("Remaining at the depot cannot duplicate a receipt",ledger.stored.meat==20 and ledger.stored.wood==10 and ledger.carried.stone==4 and field.depot.offer=="storage_stone")

 var apron:Vector3=field.depot.APRON
 verify("Can walk to the center of the apron from inside", await walk_to(apron+Vector3(0,0,-.12)))
 var held:Dictionary=ledger.carried.duplicate()
 verify("Door center stays on the unloaded house",field.depot.visit=="load" and held.stone==4)
 var plot:Vector3=field.depot.UPGRADE_AT
 var reached_plot:=await walk_to(plot)
 for i in 60: await physics_frame
 verify("The separate upgrade plot is reachable from the loading door",reached_plot and field.depot.on_upgrade_side(field.actor.position) and not field.depot.at_apron(field.actor.position) and ledger.paid.storage_stone.wood>0 and ledger.paid.storage_stone.stone>0)
 measurements["side_approach"]={"approach":str(field.actor.position),"remaining":ledger.remaining("storage_stone"),"stock":ledger.stored.duplicate()}

func drive(dest:String, at:Vector3, measure:Callable, expected:int) -> void:
 var first := -1
 var last := -1
 var peak := 0
 var launch := -1
 var launches:Dictionary={}
 var initial:int=measure.call()
 field.actor.position=at
 for frame in 150:
  field._step_receivers()
  field.settlement_loop.works.advance(1./60.)
  if not field.carry.flights.is_empty() and launch<0: launch=frame
  peak=maxi(peak,field.carry.flights.size())
  for packet in field.carry.flights: launches[packet.mesh.get_instance_id()]=true
  field.carry.advance(1./60.)
  if measure.call()>initial and first<0: first=frame+1
  if measure.call()==expected:
   last=frame+1
   break
 var elapsed:float=(last-launch)/60.
 measurements[dest]={"launch":launch,"first":first,"end":last,"max_simultaneous":peak,"launched_packets":launches.size(),"seconds":elapsed}
 verify(dest+" commits the exact target",last>0 and launch>=0 and peak>1)
 if dest.begins_with("hopper"):
  verify(dest+" streams a short overlapping load",elapsed<=.26 and elapsed>=.19)
 elif dest=="52 mixed":
  verify("Large typed load follows the locked end time", elapsed>=.835 and elapsed<=.91)
  verify("Every bundle in the gameplay-sized stack has an individual flight",launches.size()==52)
 else:
  verify(dest+" finishes in the measured plot window",elapsed<=.68 and elapsed>=.28)

func transactions() -> void:
 field.set_physics_process(false)
 field.carry.set_physics_process(false)
 var inv=field.inventory
 for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill"]: open_site(id)
 for pair in [["wood",17],["stone",17],["meat",18]]: supply(pair[0],pair[1])
 field.carry.sync()
 field.actor.position=Vector3(0,0,4)
 field._step_receivers()
 drive("52 mixed",field.depot.APRON,func():return inv.stored.meat+inv.stored.wood+inv.stored.stone,52)
 verify("Simultaneous large stream preserves each resource",inv.stored.wood==17 and inv.stored.stone==17 and inv.stored.meat==18 and inv.carried.wood+inv.carried.stone+inv.carried.meat==0)
 for kind:String in ["wood","stone","meat"]:
  supply(kind,3)
  field.carry.sync()
  var at:Vector3=field.lakeshore.APRON if kind=="meat" else field.processors.APRONS[kind]
  verify("Site cannot invent a "+kind+" receipt", not field.settlement_loop.works.receive(kind,kind,1))
  drive("hopper-"+kind,at,func():return inv.settlement.hoppers[kind],3)
  verify(kind+" fills its own hopper without consuming stored stock",inv.carried[kind]==0 and inv.stored[kind]==(18 if kind=="meat" else 17))
 supply("wood",8)
 field.carry.sync()
 drive("survivor",field.settlement_loop.works.PLOT_AT,func():return inv.settlement.survivor_wood,inv.survivor_cost)
 verify("Survivor payment persisted exactly once",inv.settlement.survivor_paid and inv.carried.wood==0)
 var due:Dictionary=inv.remaining("watchtower")
 drive("plot",field.carry.receivers.watchtower.global_position,func():return inv.paid.watchtower.wood+inv.paid.watchtower.stone,due.wood+due.stone)
 verify("Purchase consumed the right shelf totals",inv.stored.wood==17-due.wood and inv.stored.stone==17-due.stone and inv.build_order.count("watchtower")==1)
 field._persist_world()
 # An old high balance must finish without creating an object per receipt.
 supply("slate",205)
 supply("metal",68)
 field.carry.sync()
 field.actor.position=Vector3.ZERO
 field._step_receivers()
 field.actor.position=field.depot.APRON
 var counts:Dictionary={}
 for i in 70:
  field._step_receivers()
  for packet in field.carry.flights: counts[packet.mesh.get_instance_id()]=true
  field.carry.advance(1./60.)
 verify("Large legacy load conserves each type within the visual budget",inv.stored.slate==205 and inv.stored.metal==68 and inv.carried.slate==0 and inv.carried.metal==0 and counts.size()<=field.carry.MAX_BATCH_PIECES)
 measurements["273 legacy bundles"]={"visual_packets":counts.size(),"stored_slate":inv.stored.slate,"stored_metal":inv.stored.metal}

func leave_upgrade() -> void:
 field.set_physics_process(false)
 field.carry.set_physics_process(false)
 for id in ["center_hearth","expansion_1","storage_wood"]: open_site(id)
 var inv=field.inventory
 var due=inv.remaining("storage_stone")
 for kind in due: supply(kind,due[kind])
 field.carry.sync()
 field.actor.position=Vector3.ZERO
 field._step_receivers()
 var edge:Vector3=field.depot.UPGRADE_AT
 field.actor.position=edge
 field.actor.velocity=Vector3.RIGHT*6.
 for i in 30:
  field._step_receivers()
  field.carry.advance(1./60.)
 verify("Traversing the marked side while moving cannot buy",field.carry.flights.is_empty() and inv.remaining("storage_stone")==due and field.depot.upgrade_mark.is_visible_in_tree())
 field.actor.velocity=Vector3.ZERO
 for i in 70:
  field._step_receivers()
  field.carry.advance(1./60.)
  if field.carry.flights.size()>=2: break
 var incoming:Dictionary={}
 for flight in field.carry.flights:
  incoming[flight.kind]=incoming.get(flight.kind,0)+flight.units
 field.actor.position=Vector3.ZERO
 for i in 80:
  field._step_receivers()
  field.carry.advance(1./60.)
 var exact:bool=not incoming.is_empty() and not inv.complete("storage_stone")
 for kind in due: exact=exact and inv.paid.storage_stone[kind]==incoming.get(kind,0)
 verify("Leaving a deliberately started upgrade lands only released packets",exact)
 var partial:Dictionary=inv.paid.storage_stone.duplicate()
 field.actor.position=edge
 for i in 120:
  field._step_receivers()
  field.carry.advance(1./60.)
 verify("Reentry pays the remaining balance exactly once",inv.complete("storage_stone") and inv.build_order.count("storage_stone")==1 and inv.carried.wood==0 and inv.carried.stone==0)
 measurements["interrupted_upgrade"]={"launched":incoming,"partial_paid":partial,"paid":inv.paid.storage_stone.duplicate(),"next":field.depot.offer}

func machine_approaches() -> void:
 for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill"]: open_site(id)
 for kind:String in ["wood","meat","stone"]:
  var at:Vector3 = field.lakeshore.APRON if kind=="meat" else field.processors.APRONS[kind]
  # Start on the actual work aisle. All subsequent positions come from the
  # shipping joystick, actor collisions and run acceleration.
  field.actor.position=at+(Vector3(1.70,0,.15) if kind=="wood" else Vector3(0,0,1.75))
  supply(kind,3)
  field.carry.sync()
  for i in 110:
   if field.settlement_loop.works._site()==kind: break
   move_to([at.x,at.z],.05)
   await physics_frame
  steer(Vector2.ZERO)
  for i in 24: await physics_frame
  verify("Touch approach and release stays on "+kind+" machine",field.settlement_loop.works._site()==kind and field.inventory.settlement.hoppers[kind]==3 and field.inventory.carried[kind]==0)
  measurements[kind+"_touch"]={"resting":str(field.actor.position),"target":str(at),"stored_in_hopper":field.inventory.settlement.hoppers[kind]}

func run() -> void:
 field=Scene.instantiate()
 root.add_child(field)
 camera=field.camera
 await physics_frame
 if "--stream-route" in OS.get_cmdline_user_args(): await route()
 elif "--stream-cold" in OS.get_cmdline_user_args(): await cold()
 elif "--stream-aprons" in OS.get_cmdline_user_args(): await machine_approaches()
 elif "--stream-depart" in OS.get_cmdline_user_args(): leave_upgrade()
 else: transactions()
 field.set_physics_process(false)
 field.carry.set_physics_process(false)
 await Session.drain_field_audio(self,field)
 field.queue_free()
 for i in 4: await process_frame
 print("TRANSFER_VERDICT ",JSON.stringify({"checks":checks,"measures":measurements}))
 quit(1 if checks.values().has(false) else 0)
