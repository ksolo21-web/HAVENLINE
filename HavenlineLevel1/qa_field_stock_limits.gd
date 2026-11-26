extends SceneTree

const Carry = preload("res://field_carry.gd")
const Ledger = preload("res://field_inventory.gd")
const Layout = preload("res://field_stock_layout.gd")
const Art = preload("res://field_art.gd")
const CAP := {"wood":1, "stone":2, "meat":7,"coal":2,"slate":2,"metal":2}
const COUNT := 120
var failures: Array[String] = []
var arrived := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok and label not in failures:
		failures.append(label)
		push_error(label)

func check_display(carry: Carry, kind: String, count: int) -> void:
	var pool: Array = carry.pieces["storage/"+kind]
	var visible := 0
	for n in pool.size():
		if pool[n].visible:
			visible += 1
			check(pool[n].global_position.is_equal_approx(carry._floor_position(kind,n)),kind+" physical slot")
	check(visible == mini(count,CAP[kind]) and pool.size() <= CAP[kind],kind+" representative pool")

func run() -> void:
	var ledger := Ledger.new()
	var cost := {}
	for kind: String in Ledger.KINDS: cost[kind]=COUNT
	ledger.configure({"bulk":cost})
	var carry := Carry.new()
	var actor := Node3D.new()
	root.add_child(actor)
	root.add_child(carry)
	carry.setup(ledger,actor,Art.make)
	carry.set_physics_process(false)
	carry.define_receiver("bulk",actor)
	carry.unit_landed.connect(func(_kind,_where): arrived+=1)
	for kind: String in Ledger.KINDS:
		var anchor := Node3D.new()
		root.add_child(anchor)
		anchor.position = Vector3(CAP[kind],0,5)
		carry.define_storage(kind,anchor)
		for n in COUNT:
			check(ledger.collect("%s-%d" % [kind,n],kind),kind+" unique payment unit")
			check(carry.deposit_storage(kind),kind+" dispatch")
			var f: Dictionary = carry.flights[0]
			check(carry.flights.size()==1 and ledger.stored[kind]==n,kind+" single owned flight")
			carry.advance(.35)
			var i := mini(n,CAP[kind]-1)
			var target: Node3D = carry.pieces["storage/"+kind][i]
			check(f.mesh.global_position.is_equal_approx(target.global_position) and f.mesh.scale.is_equal_approx(target.scale) and absf(angle_difference(f.mesh.rotation.y,target.rotation.y))<.0001,kind+" incoming meets displayed packet")
			check(ledger.stored[kind]==n+1 and ledger.carried[kind]==0,kind+" exact deposit")
			check_display(carry,kind,n+1)
		for step in COUNT:
			var count := COUNT-step
			var i := mini(count-1,CAP[kind]-1)
			var source: Node3D = carry.pieces["storage/"+kind][i]
			check(carry.contribute("bulk"),kind+" dispatch stored payment")
			var f: Dictionary = carry.flights[0]
			check(carry.flights.size()==1 and f.from=="storage" and f.mesh.global_position.is_equal_approx(source.global_position) and f.mesh.scale.is_equal_approx(source.scale) and absf(angle_difference(f.mesh.rotation.y,source.rotation.y))<.0001,kind+" debit leaves visible source")
			carry.advance(.35)
			check(ledger.stored[kind]==count-1 and ledger.paid.bulk[kind]==step+1,kind+" exact withdrawal")
			check_display(carry,kind,count-1)
		var pool: Array = carry.pieces["storage/"+kind].duplicate()
		# Synthetic worst-case balances stress presentation separately from receipts.
		for amount in [1000000,1,999999,0]:
			ledger.stored[kind]=amount
			carry.sync()
			check_display(carry,kind,amount)
			check(carry.pieces["storage/"+kind] == pool,kind+" stable million-unit pool")
		await process_frame
	check(arrived==COUNT*2*Ledger.KINDS.size() and ledger.complete("bulk"),"one physical arrival per deposited or paid unit")
	print(JSON.stringify({"arrivals":arrived,"full_visual_instances":CAP,"max_balance_tested":1000000,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
