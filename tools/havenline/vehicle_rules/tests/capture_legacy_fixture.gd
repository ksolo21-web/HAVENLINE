extends SceneTree
const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
func _initialize() -> void:
	var w := World.new()
	w.initial.resources.append("fuel")
	w.initial.accounts.player.items["fuel"] = "200"
	var r := Rules.new()
	assert(r.initialize(w).ok)
	w.quote()
	assert(r.admit_quote("q1","legacy-quote").ok)
	w.buy()
	assert(r.purchase("q1","legacy-purchase").ok)
	w.load()
	assert(r.load_cargo("truck",1,"player",1,{"fuel":"5","wood":"10"},"legacy-load").ok)
	var f := FileAccess.open("res://evidence/fuel-v2/legacy-v1-snapshot.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(r.snapshot(),"\t") + "\n")
	print("Legacy snapshot captured")
	quit()
