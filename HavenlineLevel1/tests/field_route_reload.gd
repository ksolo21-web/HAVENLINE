extends SceneTree
func _initialize():
 call_deferred("run")

func run():
 var scene=load("res://field_opening.tscn").instantiate()
 root.add_child(scene)
 for n in 4:await physics_frame
 var state:Dictionary=scene.inventory.snapshot()
 var receipt={"stored":state.stored,"carried":state.carried,"receipts":state.paid,"collected":state.collected,"camp_active":scene.camp_active,"visible_camp":scene.camp_built.is_visible_in_tree(),"active_gates":scene.gates.all(func(g):return g.active),"tool_count":scene.character_kit.count,"persist_requested":scene.persist_requested,"persist_blocked":scene.persist_blocked}
 var expected=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("FIELD_QA_OUTPUT").path_join("route-result.json")))
 var ok:bool=scene.persist_requested and not scene.persist_blocked and scene.camp_active and scene.camp_built.visible and scene.character_kit.count==3 and scene.inventory.complete("center_hearth") and scene.inventory.complete("orbit_upgrade") and state.stored.keys().all(func(kind):return int(state.stored[kind])==int(expected.stocks_after_upgrade.get(kind,0))) and state.carried.values().all(func(n):return n==0)
 receipt["pass"]=ok
 var f=FileAccess.open(OS.get_environment("FIELD_QA_OUTPUT").path_join("fresh-process-reload.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify(receipt,"  "));f.close()
 scene.queue_free()
 for n in 12:
  OS.delay_msec(20)
  await process_frame
 quit(0 if ok else 3)
