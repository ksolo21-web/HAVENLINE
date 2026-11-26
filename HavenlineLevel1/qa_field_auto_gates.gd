extends SceneTree
## Use a sentinel-marked --l1-disposable-profile. Each crossing uses the normal
## movement motor and the field gate tick; it sends no interact key or touch.
const DT := 1./60.
var game
var failures: Array[String] = []
var assertions := 0
var crossings: Array = []

func _initialize() -> void: run.call_deferred()

func check(condition:bool,message:String) -> void:
	assertions += 1
	if not condition: failures.append(message)

func pay(id:String) -> void:
	for kind:String in game.inventory.remaining(id):
		for n in int(game.inventory.remaining(id)[kind]):
			game.inventory.collect("gate-%s-%s-%d"%[id,kind,n],kind)
			check(game.inventory.payment(id,kind,false),"fixture price "+id)
	game._finish_purchase(id)

func move_to(at:Vector3) -> void:
	game.actor.global_position=at
	game.previous_dry_position=at
	game.actor.velocity=Vector3.ZERO

func clear_gate() -> void:
	move_to(Vector3(2,0,-2))
	for j in 108: game.step_technical_gates(DT)
	await physics_frame

func cross(gate,stage:int,side:float) -> void:
	await clear_gate()
	var title: String="%s stage %d from %s"%[gate.gate_id,stage,("outside" if side>0 else "inside")]
	check(is_zero_approx(gate.angle),title+" starts latched")
	var normal:Vector3=gate.global_basis.z
	var start:Vector3=gate.global_position+normal*side*2.36
	var heading := -side*normal
	var right:Vector3=game.camera.global_basis.x
	var input:=Vector2(heading.dot(right),heading.dot(right.cross(Vector3.UP))).normalized()
	move_to(start)
	game.actor.rotation.y=atan2(heading.x,heading.z)
	var ticks:=0
	var touched_leaf:=false
	while ticks<240:
		await physics_frame
		var previous:Vector3=game.actor.global_position
		game.previous_dry_position=previous
		game.move_actor(input,DT)
		game.step_technical_gates(DT)
		for i in game.actor.get_slide_collision_count():
			if gate._leaf_bodies.has(game.actor.get_slide_collision(i).get_collider()):
				touched_leaf=true
		ticks+=1
		if gate.to_local(game.actor.global_position).z*side < -1.85: break
	check(ticks<240,title+" walks straight through")
	check(not touched_leaf,title+" maintains capsule clearance")
	check(not game.gate_button.visible,title+" has no gate button")
	check(is_equal_approx(gate.angle,PI*.5),title+" is fully open")
	check(is_equal_approx(gate.swing_direction,side),title+" opens away")
	crossings.append({"gate":gate.gate_id,"stage":stage,"from":"outside" if side>0 else "inside","physics_ticks":ticks,"leaf_contact":touched_leaf})

func safety(gate) -> void:
	await clear_gate()
	var none:Array[Vector4]=[]
	var far:=Vector3(60,0,60)
	var near:Vector3=gate.to_global(Vector3(0,0,-1.3))
	var throat:Vector3=gate.global_position
	for i in 55: gate.advance_automatic(DT,far,.31,near,none)
	check(gate.angle>1.56,"survivor independently opens gate")
	for i in 85: gate.advance_automatic(DT,throat,.31,far,none)
	check(gate.angle>1.56,"standing player keeps both leaves open")
	for i in 18: gate.advance_automatic(DT,far,.31,far,none)
	check(gate.target_open and gate.angle>1.56,"brief clearance does not trigger closing")
	var side:Vector3=gate.to_global(Vector3(.76,0,.50))
	var blockers:Array[Vector4]=[Vector4(side.x,0,side.z,.42)]
	var held:=false
	for i in 100:
		gate.advance_automatic(DT,far,.31,far,blockers)
		held = held or gate.holding_for_occupancy
	check(held and gate.angle>0.,"closing stops before a living bystander")
	for i in 110: gate.advance_automatic(DT,far,.31,far,none)
	check(is_zero_approx(gate.angle),"gate relatches after clearance")
	for i in 65: gate.advance_automatic(DT,far,.31,far,blockers)
	check(not gate.target_open and is_zero_approx(gate.angle),"hostiles never unlatch a closed camp")
	for i in 62: gate.advance_automatic(DT,near,.31,far,none)
	for i in 60: gate.advance_automatic(DT,far,.31,far,none)
	var closing_angle:float=gate.angle
	for i in 62: gate.advance_automatic(DT,gate.to_global(Vector3(0,0,1.9)),.31,far,none)
	check(closing_angle>0. and closing_angle<PI*.5 and gate.angle>1.56,"returning player reopens closing leaves")
	for i in 110: gate.advance_automatic(DT,far,.31,far,none)
	for i in 60: gate.advance_automatic(DT,gate.global_position,.31,far,none)
	check(gate.angle>1.56,"saved player at center seam is released")

func run() -> void:
	var guard:=preload("res://opening_save.gd").new()
	if not guard.configure(OS.get_cmdline_user_args()):
		printerr("A marked disposable profile is required.")
		quit(2);return
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for i in 8: await physics_frame
	game.set_physics_process(false)
	check(not game.gates[0].active and not game.gates[1].active,"unpaid gates stay inactive")
	pay("center_hearth")
	game._apply_hearth(true,false)
	for stage in [1,2,3]:
		if stage==2: pay("expansion_1")
		if stage==3:
			for id in ["storage_wood","storage_stone","storage_meat","expansion_2"]: pay(id)
		check(game.field_env.perimeter_stage==stage,"earned perimeter "+str(stage))
		for gate in game.gates:
			for side:float in [-1.,1.]: await cross(gate,stage,side)
	await safety(game.gates[0])
	print("AUTO_GATES ",JSON.stringify({"assertions":assertions,"crossings":crossings,"failures":failures,"pass":failures.is_empty()}))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
	game.queue_free()
	for i in 3: await process_frame
	quit(0 if failures.is_empty() else 1)
