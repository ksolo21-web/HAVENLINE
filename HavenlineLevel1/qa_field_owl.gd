extends SceneTree
## Uses the real expedition owl and real wolf triangle mesh with a moving target.
const Owl := preload("res://field_owl.gd")
const Wolf := preload("res://field_enemy.gd")

class Gate extends Node3D:
	const HALF_SPAN := 1.20

class Host extends Node3D:
	var actor := Node3D.new()
	var field_env = self
	var encounters = self
	var gate := Gate.new()
	var gates := [gate]
	var enemies := []
	var player_hp := 4
	var field_ready := true
	var inventory := {"settlement":{"survivor_paid":false}}
	var strikes := []
	var owl := Owl.new()
	var deaths := 0
	var tick := 0
	func is_inside_camp(p: Vector3) -> bool:
		return absf(p.x) <= 4. and absf(p.z) <= 4.
	func outside(p: Vector3, margin: float) -> bool:
		return absf(p.x) > 4.+margin or absf(p.z) > 4.+margin
	func owl_contact(wolf: Node3D, at: Vector3) -> bool:
		if not owl.permits_contact(wolf,at) or not wolf.receive_hit(1,at): return false
		strikes.append([tick,at.x,at.y,at.z,wolf.hp])
		return true
	func install() -> void:
		add_child(actor)
		add_child(gate)
		gate.position=Vector3(0,0,4)
		add_child(owl)
		owl.setup(self)

var checks := {}
var host := Host.new()
var states := {}
var wing_min := 999.
var wing_max := -999.
var flying_tuck := 0.
var striking_tuck := 1.
var moving_target: Node3D
func _initialize() -> void:
	call_deferred("run")
func step(count: int) -> void:
	for i in count:
		host.tick+=1
		if is_instance_valid(moving_target):
			moving_target.position.z=2.5+.42*sin(float(host.tick)/44.)
		host.owl.advance(1./60.)
		states[host.owl.state]=true
		if host.owl.plumage.get_blend_shape_count() == 1:
			var tuck: float = host.owl.plumage.get_blend_shape_value(0)
			if host.owl.state in ["bank","follow"]: flying_tuck=maxf(flying_tuck,tuck)
			if host.owl.state=="dive": striking_tuck=minf(striking_tuck,tuck)
		if host.owl.state in ["follow","bank"]:
			var roll: float=host.owl.shoulders[1].rotation.z
			wing_min=minf(wing_min,roll)
			wing_max=maxf(wing_max,roll)
func run() -> void:
	root.add_child(host)
	host.install()
	var wolf := Wolf.new()
	host.add_child(wolf)
	wolf.position=Vector3(9.1,0,2.5)
	wolf.configure(host.actor)
	wolf.defeated.connect(func(_at):host.deaths+=1)
	host.enemies=[wolf]
	step(90)
	checks["unpaid owl hidden and harmless"]=not host.owl.visible and host.strikes.is_empty()
	host.owl.setup(host)
	checks["setup is idempotent"]=host.owl.get_child_count()==1 and host.owl.shoulders.size()==2
	host.inventory.settlement.survivor_paid=true
	step(25)
	checks["paid purchase perches once on south gate"]=host.owl.visible and host.owl.state=="perched" and host.owl.global_position.distance_to(Vector3(-1.35,1.718,4))<.005
	checks["both wrists and primaries are independent mesh assemblies"]=host.owl.wrists[0]!=host.owl.wrists[1] and host.owl.wrists[0].get_child(0) is MeshInstance3D and host.owl.wrists[1].get_child(0) is MeshInstance3D
	checks["remote callback blocked outside contact"]=not host.owl_contact(wolf,wolf.position)
	host.actor.position=Vector3(7.2,0,2.5)
	moving_target=wolf
	step(35)
	checks["telegraphed takeoff before first damage"]=states.has("takeoff") and host.strikes.is_empty()
	step(640)
	checks["one defeat and exactly three physical contacts on moving wolf"]=host.strikes.size()==3 and host.deaths==1 and wolf.hp==0
	var spacing:=true
	for i in range(1,host.strikes.size()):
		spacing=spacing and host.strikes[i][0]-host.strikes[i-1][0]>=int(60*Owl.RELOAD)
	checks["contact recovery and cooldown enforced"]=spacing and states.has("recover") and states.has("dive") and states.has("bank")
	checks["flight talons retract and extend before impact"]=host.owl.plumage.get_blend_shape_count()==1 and flying_tuck>.9 and striking_tuck<.01
	checks["wing flap changes through the flight cycle"]=wing_max-wing_min>.82
	checks["spent contact authorization cleared"]=not host.owl.permits_contact(wolf,host.owl.contact_point)
	var boss:=Wolf.new()
	boss.is_boss=true
	host.add_child(boss)
	boss.position=Vector3(9.6,0,2.2)
	boss.configure(host.actor)
	host.enemies=[boss]
	for i in range(350):
		step(1)
		if host.owl.state=="dive":break
	host.actor.position=Vector3.ZERO
	step(180)
	checks["recall immediately cancels boss dive into safe camp"]=host.owl.state=="perched" and boss.hp==boss.max_hp()
	host.actor.position=Vector3(8,0,2)
	step(300)
	checks["live boss uses standard damage and health feedback"]=boss.hp>0 and boss.hp<boss.max_hp()
	host.actor.position=Vector3.ZERO
	step(160)
	checks["returns to the same physical post"]=host.owl.global_position.distance_to(Vector3(-1.35,1.718,4))<.005
	print("OWL_QA "+JSON.stringify({"checks":checks,"strikes":host.strikes,"states":states.keys(),"wing_range_rad":[wing_min,wing_max]}))
	host.free()
	quit(int(false in checks.values()))
