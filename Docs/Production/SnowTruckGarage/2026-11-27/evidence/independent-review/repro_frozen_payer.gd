extends SceneTree
const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
func _initialize() -> void:
 var w := World.new()
 w.initial.accounts.warehouse.items = {"wood":"1000","steel":"1000"}
 var r := Rules.new()
 var result := {}
 result.initialize = r.initialize(w)
 w.quote()
 w.facts.quote.payer_id = "warehouse"
 result.quote = r.admit_quote("q1","q")
 w.facts = {"destruction_receipt_id":"destroy-store-1","destroyed":true}
 result.destroy = r.storage_destroyed("warehouse",1,"destroy")
 w.facts = {"replacement_receipt_id":"rebuild-store-2","new_generation":2,"working":true}
 result.reopen = r.reopen_storage("warehouse",1,"reopen")
 w.claim()
 result.recover_funds = r.claim_inside_salvage("storage-estate:warehouse:1","player",1,"recover")
 w.buy()
 result.old_quote_buy = r.purchase("q1","buy-after-rebuild")
 w.quote("q2")
 result.new_quote = r.admit_quote("q2","q2")
 result.current_quote = r.state().quotes.q1
 result.has_funding_rebind = r.has_method("rebind_quote_payer")
 var out := FileAccess.open(get_script().resource_path.get_base_dir().path_join("repro-frozen-payer.json"),FileAccess.WRITE)
 out.store_string(JSON.stringify(result,"\t")+"\n")
 print(JSON.stringify(result))
 quit(0)
