extends "res://tests/field_route.gd"
## A separate meat contract survives the same filesystem restart as a paid
## survivor. The archived pre-roost slot contains a rescued, working forester.
const Session=preload("res://tests/lifecycle_test_profile.gd")
const Save=preload("res://field_save.gd")
const Crew=preload("res://field_crew.gd")
const SELF="res://tests/qa_owl_contract.gd"
var checks:Dictionary={}

func check(label:String, ok:bool)->void:
 checks[label]=ok
 if not ok:push_error(label)

func archived_cash(state:Dictionary)->Dictionary:
 return {"collected":state.collected.size(),"stored":state.stored,"carried":state.carried,"worker_meal":state.settlement.worker_meal,"served":state.settlement.served,"owl_hits":state.settlement.owl_hits}

func run()->void:
 var args:=OS.get_cmdline_user_args()
 var phase:=args[-1] if not args.is_empty() else ""
 if phase not in ["partial","reopen","owned","legacy"]:
  var path=Session.make_directory()
  var code=0
  for step in ["partial","reopen","owned"]:
   if code==0:code=Session.child(SELF,path,step)
  Session.remove_owned(path)
  path=Session.make_directory()
  if code==0:
   code=DirAccess.copy_absolute(ProjectSettings.globalize_path("res://tests/fixtures/legacy_rescued_worker.json"),path.path_join(Save.PRIMARY))
   if code==0:code=Session.child(SELF,path,"legacy")
  Session.remove_owned(path)
  quit(code);return
 if not Save.Profile.new().configure(args):quit(2);return
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 camera=field.camera
 origin=Vector2(root.size.x*.20,root.size.y*.72)
 # Inspect the load synchronously, before any previously reserved meal is served.
 var inv=field.inventory
 var j:Dictionary=inv.settlement
 var works=field.settlement_loop.works
 for wolf in field.enemies.duplicate():field.encounters._remove(wolf)
 field.encounters.remaining=400.
 check("save_ready",field.field_ready and not field.persist_blocked)
 match phase:
  "partial":
   for i in inv.costs.center_hearth.wood:
    inv.collect("contract-hearth-%s"%i,"wood");inv.payment("center_hearth","wood",false)
   field._finish_purchase("center_hearth");field._apply_hearth(true,false)
   for i in 3:inv.collect("contract-meat-%s"%i,"meat")
   field.carry.sync(true)
   field.actor.position=field.gates[0].position-Vector3(0,0,1.5)
   for point in [field.gates[0].position+Vector3(0,0,2.3),Crew.ROOST_AT]:
    for i in 330:
     if move_to([point.x,point.z],.32):break
     await physics_frame
   steer(Vector2.ZERO)
   for i in 65:await physics_frame
   check("walked_through_south_gate_to_separate_roost",field.actor.position.distance_to(Crew.ROOST_AT)<.6 and not field.field_env.is_inside_camp(field.actor.position))
   check("partial_tender_left_no_unearned_owl",j.owl_meat==3 and not Crew.owns_owl(j) and works.owl_plot.visible and not field.owl.visible and not j.survivor_paid)
  "reopen":
   check("three_paid_receipts_reopen",j.owl_meat==3 and Crew.owl_due(j)==3 and not j.survivor_paid)
   for i in 3:inv.collect("contract-extra-%s"%i,"meat")
   field.carry.sync(true)
   field.actor.position=Crew.ROOST_AT
   for i in 100:await physics_frame
   check("only_three_more_meat_spent",inv.carried.meat==0 and j.owl_meat==6)
   check("paid_owl_independent_of_rescue",Crew.owns_owl(j) and field.owl.visible and not j.survivor_paid and works.plot.visible and not works.owl_plot.visible)
  "owned":
   field.owl.advance(.01)
   check("owl_ownership_survives_relaunch",Crew.owns_owl(j) and field.owl.visible and not j.owl_legacy and j.owl_meat==6 and not j.survivor_paid)
  "legacy":
   var original=JSON.parse_string(JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/legacy_rescued_worker.json")).payload)
   field.owl.advance(.01)
   check("genuine_version9_paid_bundle_grandfathered",original.version==9 and original.settlement.survivor_paid and j.owl_legacy and Crew.owns_owl(j) and j.owl_meat==0 and not works.owl_plot.visible and field.owl.visible)
   check("legacy_earnings_unchanged",archived_cash(original)==archived_cash(JSON.parse_string(JSON.stringify(inv.snapshot()))))
 field._persist_world()
 check("all_transactions_persist",not field.persist_blocked)
 var out:=OS.get_environment("WORKER_PROOF")
 if not out.is_empty():
  var f:=FileAccess.open(out.path_join("Owl-contract-"+phase+".json"),FileAccess.WRITE)
  f.store_string(JSON.stringify({"checks":checks,"paid_meat":j.owl_meat,"legacy":j.owl_legacy,"survivor":j.survivor_paid,"feet":str(field.actor.position),"cost_display":field.Progress.units(Crew.OWL_MEAT)}," "));f.close()
 print("OWL_CONTRACT ",phase," ",JSON.stringify(checks))
 await Session.drain_field_audio(self,field);field.queue_free()
 for i in 3:await process_frame
 quit(int(false in checks.values()))
