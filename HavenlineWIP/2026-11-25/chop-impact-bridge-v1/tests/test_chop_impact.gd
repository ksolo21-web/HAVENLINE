extends SceneTree
const Bridge = preload("res://chop_impact_bridge.gd")
const TreeScript = preload("res://resource_tree.gd")
const Ledger = preload("res://opening_ledger.gd")
var number := 0
var failures := 0
var owner: Node3D
var player: Node3D
var target: TreeScript
var current_actor: Node3D
var current_tree: TreeScript
var authority := RefCounted.new()
var wrong := RefCounted.new()
var bridge := Bridge.new()
var ledger := Ledger.new()
var context_allowed := true

func _initialize() -> void:
	call_deferred("_run")

func check(v: bool, label: String) -> void:
	number += 1
	failures += 0 if v else 1
	print(("PASS " if v else "FAIL ")+label)

func context() -> Dictionary:
	return {"actor":current_actor,"tree":current_tree,"authorized":context_allowed}

func advance_cooldown() -> void:
	for i in range(24):
		target.advance(1.0/60.0,player.global_position,.31)

func next_f() -> RefCounted:
	bridge.release(&"key_f")
	return bridge.press(&"key_f")

func valid_hit() -> void:
	var req := next_f()
	check(req != null,"fresh deliberate F press requests a swing")
	check(bridge.marker_reached(authority,req),"one simulated authorized marker reaches tree")
	check(bridge.finish_or_cancel(authority,req),"exact lifecycle closes completed marker")

func fall_replay(expect_first: bool) -> void:
	check(target.phase=="falling" and target.strikes==3,"three accepted impacts required to enter falling")
	for i in range(45):
		target.advance(1.0/60.0,player.global_position,.31)
	check(target.blocked and is_zero_approx(target.falling_clock) and target.phase=="falling" and ledger.stock.wood==int(not expect_first),"unchanged occupied sweep holds motion/credit")
	player.position.x = -.57
	for i in range(59):
		target.advance(1.0/60.0,player.global_position,.31)
	check(target.phase=="ready_to_credit" and target.settle_clock>=TreeScript.SETTLE_SECONDS,"existing unoccupied fall plus dwell before credit")
	if target.starter_credit_seen:
		check(not expect_first,"repeat fall retains original credit state")
	else:
		check(expect_first and ledger.collect_wood(TreeScript.TREE_ID),"fixture publishes original ledger credit once")
	target.mark_credited()
	check(target.phase=="credited" and ledger.stock.wood==1 and not ledger.collect_wood(TreeScript.TREE_ID),"existing ledger rejects replay")
	for i in range(299):
		target.advance(1.0/60.0,player.global_position,.31)
	check(target.phase=="credited","5-second regrowth remains inactive through tick 299")
	target.advance(1.0/60.0,player.global_position,.31)
	check(target.phase=="rooted" and target.strikes==0 and target.starter_credit_seen and ledger.stock.wood==1,"original regrowth at 300 without new stock")
	player.position.x = -1.17

func _run() -> void:
	owner = Node3D.new()
	root.add_child(owner)
	player = Node3D.new()
	owner.add_child(player)
	player.position = Vector3(-1.17,0,6)
	player.rotation_degrees.y = -90.0
	current_actor = player
	target = TreeScript.new()
	owner.add_child(target)
	target.position = Vector3(-2,0,6)
	var donor_root := Node3D.new()
	var donor_scene := PackedScene.new()
	donor_scene.pack(donor_root)
	donor_root.free()
	target.build(donor_scene,true)
	current_tree = target
	check(bridge.press(&"key_f")==null and target.strikes==0,"default unconfigured bridge is inert")
	check(bridge.configure(authority,owner,context),"explicit detached test capability installed")
	check(not bridge.configure(wrong,owner,context),"cannot replace configured authority")
	check(bridge.press(&"key_f",true)==null and bridge.press(&"mouse_primary",false,true)==null and bridge.press(&"unknown")==null,"echo/emulation/wrong input ignored")
	var request := bridge.press(&"key_f")
	check(request!=null and target.strikes==0 and target.last_sequence==0,"request alone makes no notch or sequence")
	check(bridge.press(&"key_f")==null and bridge.press(&"mouse_primary")==null,"held/cross-channel while pending cannot queue")
	check(not bridge.marker_reached(wrong,request) and not bridge.marker_reached(authority,RefCounted.new()) and target.strikes==0,"untrusted/wrong ticket cannot mark or consume")
	check(bridge.marker_reached(authority,request) and target.strikes==1,"first exact simulated authorized marker")
	check(not bridge.marker_reached(authority,request) and target.strikes==1,"same marker only consumed once")
	check(bridge.press(&"touch_tree")==null,"impact is not playback end; another channel cannot overlap")
	check(bridge.finish_or_cancel(authority,request),"exact playback closure")
	check(bridge.press(&"key_f")==null and bridge.press(&"mouse_primary")==null and bridge.press(&"touch_tree")==null,"held/blocked raw channels cannot autorepeat when idle")
	bridge.release(&"key_f",true)
	check(bridge.press(&"key_f")==null,"emulated release cannot reset physical latch")
	bridge.release(&"mouse_primary")
	bridge.release(&"touch_tree")
	request = next_f()
	check(request!=null and not bridge.marker_reached(authority,request) and target.strikes==1,"exact underlying cooldown denies a new real marker")
	bridge.finish_or_cancel(authority,request)
	advance_cooldown()
	request = next_f()
	player.rotation_degrees.y = 90.0
	check(not bridge.marker_reached(authority,request) and target.strikes==1,"facing rechecked at impact")
	player.rotation_degrees.y = -90.0
	check(not bridge.marker_reached(authority,request),"denied marker cannot replay after facing restored")
	bridge.finish_or_cancel(authority,request)
	request = next_f()
	player.position.x = 1.0
	check(not bridge.marker_reached(authority,request) and target.strikes==1,"reach rechecked at impact")
	bridge.finish_or_cancel(authority,request)
	player.position.x = -1.17
	request = next_f()
	context_allowed=false
	check(not bridge.marker_reached(authority,request) and target.strikes==1,"persistence/gameplay authorization rechecked at impact")
	bridge.finish_or_cancel(authority,request)
	context_allowed=true
	request = next_f()
	var replacement_actor := Node3D.new()
	owner.add_child(replacement_actor)
	replacement_actor.transform=player.transform
	current_actor=replacement_actor
	check(not bridge.marker_reached(authority,request) and target.strikes==1,"identical transform cannot substitute another actor")
	bridge.finish_or_cancel(authority,request)
	current_actor=player
	request = next_f()
	var replacement_tree := TreeScript.new()
	owner.add_child(replacement_tree)
	replacement_tree.position=target.position
	replacement_tree.build(donor_scene,true)
	current_tree=replacement_tree
	check(not bridge.marker_reached(authority,request) and target.strikes==1 and replacement_tree.strikes==0,"same wood ID cannot substitute another tree instance")
	bridge.finish_or_cancel(authority,request)
	current_tree=target
	request = next_f()
	check(bridge.finish_or_cancel(authority,request),"playback cancellation does not strike")
	var after_cancel := next_f()
	check(after_cancel!=null and not bridge.marker_reached(authority,request),"late previous exact marker cannot hit or consume new ticket")
	check(bridge.marker_reached(authority,after_cancel) and target.strikes==2,"only new matching ticket strikes")
	bridge.finish_or_cancel(authority,after_cancel)
	advance_cooldown()
	valid_hit()
	fall_replay(true)
	for i in range(3):
		valid_hit()
		advance_cooldown()
	fall_replay(false)
	request = next_f()
	check(request!=null and bridge.disarm(authority) and not bridge.marker_reached(authority,request),"teardown invalidates pending without any delayed credit")
	print("CHOP IMPACT ",number," checks ",failures," failures")
	quit(0 if failures==0 else 1)
