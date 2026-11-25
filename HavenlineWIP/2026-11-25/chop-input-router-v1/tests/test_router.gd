extends SceneTree
const Router = preload("res://chop_input_router.gd")
const Impact = preload("res://chop_impact_bridge.gd")
const TreeScript = preload("res://resource_tree.gd")
const Open = preload("res://opening.tscn")
var opening: Node3D
var input := Router.new()
var impact := Impact.new()
var authority := RefCounted.new()
var issued: Array[RefCounted] = []
var failures := 0
var number := 0
var tree_at: Vector2
var out_at := Vector2(20,460)

func _initialize() -> void:
	call_deferred("_run")

func check(q: bool, what: String) -> void:
	number+=1
	failures+=0 if q else 1
	print(("PASS " if q else "FAIL ")+what)

func ctx() -> Dictionary:
	return {"actor":opening.actor,"tree":opening.resource_tree,"authorized":not opening.persist_blocked}

func admit(ticket: RefCounted) -> void:
	issued.append(ticket)

func frame(event: InputEvent) -> void:
	# Viewport dispatch is synchronous and still traverses normal _input.
	root.push_input(event, true)

func touch(idx: int, down: bool, where: Vector2, canceled: bool=false, device: int=0) -> void:
	var x := InputEventScreenTouch.new()
	x.index=idx
	x.position=where
	x.pressed=down
	x.canceled=canceled
	x.device=device
	frame(x)

func key(code: Key, down: bool, echo: bool=false, device: int=0) -> void:
	var x:=InputEventKey.new()
	x.physical_keycode=code
	x.pressed=down
	x.echo=echo
	x.device=device
	frame(x)

func mouse(down: bool, where: Vector2, device: int=0, button: MouseButton=MOUSE_BUTTON_LEFT) -> void:
	var x:=InputEventMouseButton.new()
	x.position=where
	x.global_position=where
	x.pressed=down
	x.device=device
	x.button_index=button
	frame(x)

func drag(i: int, at: Vector2) -> void:
	var x:=InputEventScreenDrag.new()
	x.index=i
	x.position=at
	frame(x)

func strikes() -> int:
	return opening.resource_tree.strikes

func blank() -> bool:
	return opening.resource_tree.last_sequence==0 and strikes()==0 and opening.tree_input_sequence==0 and opening.ledger.stock.wood==0

func _run() -> void:
	opening=Open.instantiate()
	root.add_child(opening)
	opening.set_physics_process(false)
	opening.set_process_input(true)
	await process_frame
	opening.actor.position=Vector3(-1.17,0,6)
	opening.actor.rotation_degrees.y=-90.0
	opening.step_tree(0.)
	tree_at=opening.tree_button.get_global_rect().get_center()
	check(opening.touches_tree_button(tree_at) and not opening.touches_tree_button(out_at),"exact tree and outside controls distinct")
	check(impact.configure(authority,opening,ctx) and input.configure(impact,authority,admit),"fixture capability on actual opening node")
	opening.detached_test_chop_input=input
	check(not opening.persist_requested and blank(),"fresh unsaved profile")
	touch(1,true,out_at)
	drag(1,out_at+Vector2(30,0))
	check(opening.touch_id==1 and opening.touch_now==out_at+Vector2(30,0),"movement acquired on original route")
	touch(4,true,tree_at)
	check(issued.size()==1 and input._touch_owner==4 and opening.touch_id==1 and blank(),"independent chop press, no strike or stock")
	touch(5,false,tree_at)
	touch(4,false,tree_at,false,InputEvent.DEVICE_ID_EMULATION)
	drag(4,out_at)
	check(input._touch_owner==4 and opening.touch_id==1 and opening.touch_now==out_at+Vector2(30,0),"wrong or mirrored up and chop drag leave movement plus chop unchanged")
	touch(4,false,out_at)
	check(input._touch_owner==-1 and opening.touch_id==1 and blank(),"lift initiating finger outside tree before movement lift")
	touch(1,false,tree_at)
	check(opening.touch_id==-1 and blank(),"independent movement release on tree control")
	if issued.is_empty():
		quit(2)
		return
	check(impact.finish_or_cancel(authority,issued[0]) and blank(),"ordinary release did not cancel ticket")
	touch(2,true,out_at)
	touch(3,true,tree_at)
	check(issued.size()==2 and opening.touch_id==2 and input._touch_owner==3,"second ordering establishes both independently")
	touch(2,false,out_at)
	check(opening.touch_id==-1 and input._touch_owner==3,"movement lift first leaves chop captured")
	touch(3,false,out_at,true)
	check(input._touch_owner==-1 and not impact.marker_reached(authority,issued[1]) and blank(),"real canceled initiating touch outside discards pending marker")
	touch(6,true,tree_at)
	touch(5,false,out_at,true)
	check(input._touch_owner==6 and issued.size()==3,"unrelated cancellation does not revoke admitted touch")
	touch(6,false,out_at)
	check(not impact.marker_reached(RefCounted.new(),issued[2]) and blank(),"wrong marker capability does not touch original ledger")
	check(impact.marker_reached(authority,issued[2]) and strikes()==1 and opening.resource_tree.last_sequence==1 and opening.tree_input_sequence==0 and opening.ledger.stock.wood==0,"one true route-to-fixture marker strikes exact tree only")
	check(not impact.marker_reached(authority,issued[2]) and strikes()==1 and impact.finish_or_cancel(authority,issued[2]),"copied or replayed marker never adds notch")
	key(KEY_F,true,true)
	key(KEY_F,true,false,InputEvent.DEVICE_ID_EMULATION)
	check(issued.size()==3,"F echo and tagged mirror press ignored")
	key(KEY_F,true)
	check(issued.size()==4 and input._key_held and strikes()==1,"physical F admitted but no early strike")
	key(KEY_G,false)
	key(KEY_F,false,true)
	key(KEY_F,false,false,InputEvent.DEVICE_ID_EMULATION)
	check(input._key_held,"unrelated/echo/mirror key ups do not release F")
	key(KEY_F,false)
	check(not input._key_held and impact.finish_or_cancel(authority,issued[3]),"genuine F release leaves pending until lifecycle")
	mouse(true,tree_at,InputEvent.DEVICE_ID_EMULATION)
	check(issued.size()==4,"mirror primary press ignored on tree")
	mouse(true,tree_at)
	check(issued.size()==5 and input._mouse_held,"genuine primary press admitted")
	mouse(false,out_at,InputEvent.DEVICE_ID_EMULATION)
	mouse(false,out_at,0,MOUSE_BUTTON_RIGHT)
	check(input._mouse_held,"mirror and unrelated mouse up do not release")
	mouse(false,out_at)
	check(not input._mouse_held and impact.finish_or_cancel(authority,issued[4]),"real primary release outside clears captured channel")
	# Busy refused touch is still physically captured; its release cannot
	# revoke a different admitted owner.
	key(KEY_F,true)
	touch(7,true,tree_at)
	check(issued.size()==6 and input._touch_owner==7,"busy touch does not add another request")
	touch(7,false,out_at,true)
	check(input._touch_owner==-1 and impact.finish_or_cancel(authority,issued[5]),"busy touch cancel never revokes F's ticket")
	key(KEY_F,false)
	# Original priority and no movement acquisition at gate. Configure
	# current real gate mechanism, not a mocked handler.
	var gate: Node3D=opening.gates[0]
	gate.set_earned(true)
	opening.actor.position=gate.position+Vector3(.4,0,0)
	opening.nearest_gate=gate
	opening.gate_button.show()
	var gate_at: Vector2=opening.gate_button.get_global_rect().get_center()
	check(opening.touches_gate_button(gate_at) and not opening.touches_tree_button(gate_at),"actual gate control distinct")
	var was: bool=gate.target_open
	mouse(true,gate_at,InputEvent.DEVICE_ID_EMULATION)
	check(gate.target_open==was,"original gate ignores tagged pointer mirror")
	mouse(true,gate_at)
	mouse(false,out_at)
	check(gate.target_open!=was and issued.size()==6 and opening.touch_id==-1,"actual gate mouse press routed before any chop")
	touch(8,true,gate_at)
	touch(8,false,out_at)
	check(opening.touch_id==-1 and input._touch_owner==-1 and issued.size()==6,"gate touch does not claim chop or move")
	check(strikes()==1 and opening.resource_tree.last_sequence==1 and opening.ledger.stock.wood==0,"all releases and gate inputs leave one fixture strike and no stock")
	print("ROUTER %d/%d" % [number-failures,number])
	opening.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
