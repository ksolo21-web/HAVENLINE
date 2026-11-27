extends "res://tests/qa_storage_stream.gd"

const BUILD_ORDER = ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","watchtower","orbit_upgrade","camp_cooker","saw_bench","quarry_drill"]
var visits := []

func point_for(id: String) -> Vector3:
 return field.carry.receivers[id].global_position

func touch_plot(point: Vector3, tolerance := .42) -> bool:
 for tick in 360:
  var flat:Vector3 = (field.actor.position-point).slide(Vector3.UP)
  if flat.length() <= tolerance:
   steer(Vector2.ZERO)
   for settle in 12: await physics_frame
   if (field.actor.position-point).slide(Vector3.UP).length() <= tolerance+.24: return true
  move_to([point.x,point.z],.08)
  await physics_frame
 steer(Vector2.ZERO)
 return false

func purchase(id: String, should_finish := true) -> void:
 var inv=field.inventory
 var before:Dictionary=inv.paid[id].duplicate()
 var target := point_for(id)
 if id in field.Progress.MACHINES.values(): target.z += 1.42
 var reached:=await touch_plot(target)
 for i in 100: await physics_frame
 var pos:Vector3=field.actor.global_position
 visits.append({"id":id,"funded":inv.paid[id].duplicate(),"position":[pos.x,pos.z],"before":before,"next":field.next_project,"prompt":field.opening_hud.prompt.text})
 verify("Touch reaches "+id,reached)
 if should_finish:
  verify(id+" completed exactly once",inv.complete(id) and inv.build_order.count(id)==1)
 else:
  verify(id+" partial receipt lands without a free unlock",not inv.complete(id) and inv.paid[id]!=before)

func verify_marker(id:String) -> void:
 var inv=field.inventory
 var floor=field.carry.receivers[id]
 var price:Dictionary=inv.remaining(id)
 verify(id+" visibly offers the actual target",floor.is_visible_in_tree() and floor.get_node("Brackets").is_visible_in_tree() and floor.get_node("Gray").is_visible_in_tree())
 if id == "center_hearth": return
 verify(id+" has a centered painted building or equipment glyph", floor.icon!=null and floor.icon.is_visible_in_tree())
 verify(id+" offers the correct recipe",floor.title.text==field.Progress.TITLES[id] and price.keys().all(func(kind):return str(field.Progress.units(price[kind]))==floor.price.get_node(NodePath(kind)).text))
 if id in ["storage_stone","storage_meat"]:
  verify(id+" is separate from the actual loading door",floor.global_position.distance_to(field.depot.APRON)>1.8 and not field.depot.on_upgrade_side(field.depot.APRON))

func fresh_partial() -> void:
 var inv=field.inventory
 verify("New profile offers only the hearth",field.next_project=="center_hearth" and not field.depot.apron.visible and not field.depot.upgrade_mark.visible)
 for match_ in [["wood",47],["stone",8],["meat",3]]: supply(match_[0],match_[1])
 field.carry.sync()
 for id in BUILD_ORDER.slice(0,3):
  verify_marker(id)
  await purchase(id)
 verify_marker("storage_stone")
 verify("Starter has one priced upgrade and a separate place to stock",field.depot.house.tier==1 and field.depot.apron.get_node("Gray").visible==false and field.depot.upgrade_mark.visible)
 # Deposit through the real doorway then pay with both stored timber and
 # carried stone. Timber in the storehouse remains tender for this plot.
 await touch_plot(field.depot.SITE+Vector3(0,0,.48),.22)
 for i in 64: await physics_frame
 verify("House loading leaves its upgrade balances available", inv.stored.wood==5 and inv.stored.meat==3 and inv.carried.stone==2 and inv.paid.storage_stone=={"wood":0,"stone":0})
 await touch_plot(field.depot.APRON+Vector3(0,0,-.16),.20)
 await purchase("storage_stone",false)
 verify("Partial payment correctly combines stored timber with carried stone",inv.paid.storage_stone=={"wood":5,"stone":2} and inv.stored.wood==0 and inv.carried.stone==0 and inv.stored.meat==3)
 verify_marker("storage_stone")
 field._persist_world()

func finish_build() -> void:
 var inv=field.inventory
 verify("Restored partial is the next visible plot",field.next_project=="storage_stone" and field.depot.offer=="storage_stone" and inv.paid.storage_stone=={"wood":5,"stone":2})
 verify_marker("storage_stone")
 for row in [["wood",73],["stone",56],["meat",6]]: supply(row[0],row[1])
 # Accounts created by the previous process intentionally have overlapping
 # fixture sequence IDs; use distinct per-process ID ranges before supplying.
 field.carry.sync()
 for i in 44: await physics_frame
 verify("Cold resume on a plot cannot spend until a new visit",inv.paid.storage_stone=={"wood":5,"stone":2})
 await touch_plot(field.depot.UPGRADE_AT+Vector3(0,0,2.55))
 await purchase("storage_stone")
 verify_marker("storage_meat")
 verify("Standing on reinforced plot cannot cascade into advanced tier",inv.paid.storage_meat=={"wood":0,"meat":0})
 await touch_plot(field.depot.UPGRADE_AT+Vector3(0,0,2.55))
 await purchase("storage_meat")
 verify("Completed advanced house retires its upgrade floor",not field.depot.upgrade_mark.is_visible_in_tree() and inv.stored.meat>=0)
 await touch_plot(Vector3(-1.86,0,-1.18))
 for id in BUILD_ORDER.slice(5):
  if id == "camp_cooker":
   await touch_plot(Vector3(4.6,0,-4.6))
   await touch_plot(Vector3(.65,0,-5.45))
  elif id == "quarry_drill":
   await touch_plot(Vector3(-2.2,0,-5.05))
   await touch_plot(Vector3(4.5,0,-5.1))
  verify_marker(id)
  await purchase(id)
 verify("All eleven offers retire with no duplicate purchases",inv.build_order==BUILD_ORDER and field.next_project.is_empty() and field.offer_floors.values().all(func(node):return not node.is_visible_in_tree()))
 verify("Late game directs an unpaid player to the remaining survivor objective",field.opening_hud.prompt.text.contains("80 wood") and field.settlement_loop.works.plot.is_visible_in_tree())
 field._persist_world()

func final_cold() -> void:
 var inv=field.inventory
 verify("Completed world reopens with the same eleven receipts",inv.build_order==BUILD_ORDER and field.next_project.is_empty() and field.depot.house.tier==3)
 verify("Late restored profile keeps real unfinished objectives visible",not field.depot.upgrade_mark.visible and field.settlement_loop.works.plot.is_visible_in_tree() and field.opening_hud.prompt.text.contains("80 wood"))
 verify("No new plot until a genuine recipe exists",not field.ready_to_enter_level_2() if field.has_method("ready_to_enter_level_2") else not field.settlement_loop.ready())

func run() -> void:
 field=Scene.instantiate()
 root.add_child(field)
 current_scene=field
 camera=field.camera
 await physics_frame
 if "--plot6-start" in OS.get_cmdline_user_args(): await fresh_partial()
 elif "--plot6-resume" in OS.get_cmdline_user_args():
  receipt_id=1000
  await finish_build()
 elif "--plot6-end" in OS.get_cmdline_user_args(): final_cold()
 else: verify("Explicit route phase",false)
 field.set_physics_process(false)
 field.carry.set_physics_process(false)
 await Session.drain_field_audio(self,field)
 field.queue_free()
 for i in 4: await process_frame
 print("PLOT_ROUTE ",JSON.stringify({"checks":checks,"visits":visits}))
 quit(1 if checks.values().has(false) else 0)
