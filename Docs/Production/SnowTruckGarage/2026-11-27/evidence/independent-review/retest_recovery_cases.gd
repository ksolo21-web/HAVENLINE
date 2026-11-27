extends SceneTree
const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
const Count = preload("res://exact_count.gd")
var checks := []
var failures := []
func ck(value: bool, label: String) -> void:
 checks.append({"name":label,"passed":value})
 if not value: failures.append(label)
func _initialize() -> void:
 var w := World.new()
 w.initial.accounts.warehouse.items = {"wood":"1000","steel":"1000"}
 var r := Rules.new()
 ck(r.initialize(w).ok,"initialize independent storage-funded case")
 w.quote()
 w.facts.quote.payer_id = "warehouse"
 ck(r.admit_quote("q1","q").ok,"freeze storage-funded original bill")
 w.facts = {"destruction_receipt_id":"destroy-store-1","destroyed":true}
 var death: Dictionary = r.storage_destroyed("warehouse",1,"destroy")
 ck(death.ok,"storage cargo moves to persistent estate")
 w.facts = {"replacement_receipt_id":"rebuild-store-2","new_generation":2,"working":true}
 ck(r.reopen_storage("warehouse",1,"reopen").ok,"empty rebuilt storage custody generation2")
 w.claim()
 ck(r.claim_inside_salvage("storage-estate:warehouse:1","player",1,"recover").ok,"recover original funds to available actor")
 w.buy()
 ck(not r.purchase("q1","old-payer").ok,"stale payer cannot debit rebuilt storage")
 w.facts = {"payment_authorization_id":"owner-authorized-recovery","payer_available":true}
 var rebound: Dictionary = r.rebind_quote_payer("q1","player",1,"funding-switch")
 ck(rebound.ok and r.state().quotes.q1.bill == {"wood":"100","steel":"200"},"rebind payer preserves bill and quote")
 ck(not r.rebind_quote_payer("q1","warehouse",2,"funding-switch").ok,"changed successful rebind payload rejected")
 w.buy()
 var bought: Dictionary = r.purchase("q1","buy")
 ck(bought.ok and r.state().accounts.player.items.wood == "1900" and r.state().accounts.player.items.steel == "1800","exact original bill paid once from recovered funds")
 var state_before: Dictionary = r.state()
 ck(r.purchase("q1","buy") == bought and r.state() == state_before,"repeat purchase receipt makes no mutation")
 w.quote("q-other")
 w.facts.quote.vehicle_id = "second-truck"
 ck(not r.admit_quote("q-other","second-bay-occupant").ok,"new vehicle name cannot bypass single garage occupancy")
 var save: Dictionary = JSON.parse_string(JSON.stringify(r.snapshot()))
 w.permit_restore(save)
 var restored := Rules.new()
 ck(restored.restore(save,w).ok and restored.state() == r.state(),"full recovery sequence survives actual JSON serialization")
 var before_old_death: Dictionary = restored.state()
 ck(restored.storage_destroyed("warehouse",1,"destroy") == death and restored.state() == before_old_death,"old destruction receipt cannot close new receiver")
 w.load()
 ck(restored.load_cargo("truck",1,"player",1,{"wood":"20","money":"18446744073709551617"},"new-load").ok,"post-recovery truck loads exact mixed cargo")
 w.dock()
 w.facts.receiver.generation = 2
 ck(restored.park_and_unload("truck",1,"dock-rebuilt").ok,"post-recovery truck unloads into generation2 receiver")
 ck(restored.state().accounts.warehouse.items.money == "18446744073709551617" and restored.audit().ok,"coupled rebuild rebind purchase unload conserves every resource")
 var result := {"scope":"Independent coupled recovery sequence","passed":checks.size()-failures.size(),"failed":failures.size(),"checks":checks}
 var out := FileAccess.open(get_script().resource_path.get_base_dir().path_join("retest-recovery-cases.json"),FileAccess.WRITE)
 out.store_string(JSON.stringify(result,"\t")+"\n")
 print(JSON.stringify(result))
 quit(0 if failures.is_empty() else 1)
