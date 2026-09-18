extends SceneTree
const Model = preload("res://scripts/world_transform.gd")
const Simulation = preload("res://scripts/simulation.gd")
var failures: Array[String] = []
var checks: Array[Dictionary] = []
func check(name: String, passed: bool) -> void:
 checks.append({"name":name,"passed":passed})
 if not passed: failures.append(name)
func fresh_model():
 var m = Model.new()
 check("catalog configured",m.configure_from_file())
 check("target registered",m.register_target("save-target","seed"))
 return m
func json_copy(value): return JSON.parse_string(JSON.stringify(value))
func same(a,b): return json_copy(a)==json_copy(b)
func _initialize(): call_deferred("run")
func run():
 var args=OS.get_cmdline_user_args()
 var case_id=String(args[0]) if args.size()==1 else ""
 var sim=Simulation.new()
 sim.stored={"wood":20,"stone":12,"metal":4,"fuel":2}
 sim.inventory={"wood":3,"stone":2,"metal":1,"fuel":0}
 sim.update_level()
 var model=fresh_model()
 var baseline=sim.snapshot()
 for invalid_level in [0,5,-1,1.5,"2",null,INF,NAN]:
  var invalid_save=json_copy(baseline);invalid_save.level=invalid_level
  check("invalid earned level rejects atomically: "+str(invalid_level),not sim.restore(invalid_save) and same(sim.snapshot(),baseline))
 var initial=model.export_component_state()
 var invalid_position=json_copy(baseline);invalid_position.position=[INF,0]
 check("invalid saved position rejects without mutating valid world",not sim.restore(invalid_position) and same(sim.snapshot(),baseline))
 match case_id:
  "fresh_save":
   var s=Simulation.new()
   var m=Model.new();m.configure_from_file()
   check("fresh simulation restores",s.restore(json_copy(baseline)))
   check("fresh component restores",m.import_component_state(json_copy(initial)))
   check("fresh complete payload conserved",same(s.snapshot(),baseline) and same(m.export_component_state(),initial))
  "previous_version_save", "migration":
   var legacy=json_copy(baseline)
   legacy.erase("world_transform_debit_receipts")
   var s=Simulation.new()
   check("pre-T10 schema1 snapshot restores",s.restore(legacy))
   check("absent ledger initializes empty",s.world_transform_debit_receipts.is_empty())
   var restored=s.snapshot();restored.erase("world_transform_debit_receipts")
   check("legacy inventory identity jobs progression conserved",same(restored,legacy))
   var m=fresh_model()
   check("new component starts at unadvanced revision",m.export_component_state().targets["save-target"].revision==0)
   if case_id=="migration":
    var next=Simulation.new()
    check("migrated save reloads",next.restore(json_copy(s.snapshot())))
    check("migration is idempotent",same(next.snapshot(),s.snapshot()))
  "existing_current_save", "interrupted_save", "reload", "rollback_recovery":
   var intent=model.commit_transform("save-transaction","framework_anchor_seed_to_foundation","save-target",sim.stored)
   var pending=json_copy(model.export_component_state())
   var receipt=sim.commit_world_transform_debit(intent)
   check("authority debits exactly once",receipt.get("authority_applied",false) and sim.stored.wood==12 and sim.stored.stone==8)
   var paid=json_copy(sim.snapshot())
   if case_id in ["existing_current_save","reload"]:
    check("component accepts paid receipt",model.accept_authoritative_receipt(receipt).passed)
   var persisted=json_copy(model.export_component_state())
   var s=Simulation.new();var m=Model.new();m.configure_from_file()
   check("paid authority snapshot restores",s.restore(paid))
   check("matching component snapshot restores",m.import_component_state(persisted))
   if case_id=="rollback_recovery":
    check("stale pending component can recover against current authority",m.import_component_state(pending))
   var before=s.snapshot()
   var replay=s.commit_world_transform_debit(intent)
   check("authority retry replays without debit",replay.get("simulation_replayed",false) and same(s.snapshot(),before))
   var accepted=m.accept_authoritative_receipt(replay)
   check("recovered world advances once",accepted.passed and m.export_component_state().targets["save-target"].revision==1)
   check("duplicate acceptance cannot grant progress",m.accept_authoritative_receipt(replay).get("replayed",false) and m.export_component_state().targets["save-target"].revision==1)
   var invariant_before=baseline.duplicate(true);invariant_before.erase("stored");invariant_before.erase("world_transform_debit_receipts")
   var invariant_after=s.snapshot();invariant_after.erase("stored");invariant_after.erase("world_transform_debit_receipts")
   check("carried inventory identity jobs progression conserved",same(invariant_after,invariant_before))
   var malformed=m.export_component_state();malformed.receipts.clear()
   var model_before=m.export_component_state()
   check("tampered advanced component rejects atomically",not m.import_component_state(malformed) and same(m.export_component_state(),model_before))
  _: failures.append("unknown save case")
 print(JSON.stringify({"task_id":"T10","case":case_id,"passed":failures.is_empty(),"failures":failures,"checks":checks,"simulation_schema":1,"component_schema":Model.COMPONENT_SCHEMA_VERSION,"scope":"T10 transaction component with authoritative simulation ledger; global save versioning and full-history anti-rollback remain T14; no entitlements or premium grants in T10"}))
 quit(0 if failures.is_empty() else 1)
