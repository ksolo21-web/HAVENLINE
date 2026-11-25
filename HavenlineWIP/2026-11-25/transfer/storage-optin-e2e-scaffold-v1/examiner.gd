extends RefCounted
## OPT-IN SceneTree witness helper ONLY; not attached by any .tscn.
## No callback receives player input, filesystem, profile or actual game credit.
const Legacy = preload("res://opening_ledger.gd")
const WALK_SEAL := "ac4a8d52a510abd6b657872fc6f73f45d043115152ce943576c365b0d4cccd80"
const REST_SEAL := "b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6"
const ORACLE_SEAL := "392db89ab0985fa2c9464ff28807096aa4951bdad3ce22e178cd6927b45aba06"
const GOAL := Vector2(-6.125, 6.95)
const CAP := 4.4 # detached examiner pacing cap, NOT a source speed
const OUTER_SIDE := .94
const DURATION_MIN := .30
const ANGULAR_CAP := 160.
const PINE := 2
const FROZEN_REST := [Transform3D(Basis(Vector3(0.011456093581219007,0.007296203843363953,-0.9999077574103196),Vector3(0.874591869367374,-0.48481649811135924,0.006482684283585948),Vector3(-0.4847244783960686,-0.8745854609862402,-0.011935303730735718)),Vector3(-5.596517383444508,0.11266990300144689,5.796595472047229)),Transform3D(Basis(Vector3(0.01145536580342935,0.007294688045895884,-0.9999077768077527),Vector3(0.8746363991749855,-0.48473614322894054,0.006483878912129304),Vector3(-0.48464414144042306,-0.8746300126189614,-0.01193302952439823)),Vector3(-5.332379043071789,0.11283764523831509,5.796595202368235))]
const EXPECTED_TURNS := {1306:{"foot":Vector3(-4.90033340454102,0.307022362947464,8.00603199005127),"sphere":0.755859375},1353:{"foot":Vector3(-6.50744485855103,-0.0412393510341644,6.0513162612915),"sphere":0.9814453125}}
const RECEIPT := {"offer":"center-hearth","grant":"center-hearth","revision":1,"typed_debit":{"wood":3}}
enum {UNARMED, IN_FLIGHT, PARKED, FAILED}
var _state := UNARMED
var _native_game
var _native_bytes := PackedByteArray()
var _stock_view:Node3D
var _actor:Node3D
var _pose := Transform3D.IDENTITY
var _hold:Node3D
var _pieces:Array[MeshInstance3D]=[]
var _piece_ids:Array[int]=[]
var _story:Array[Dictionary]=[]
var _after:Dictionary={}
var _frame := 0
var _serial := 0

func shadow() -> Dictionary:
	return _after.duplicate(true)

func derive_plan(source:Transform3D, rest:Transform3D) -> Dictionary:
	# Pure math; not a permission to move. Actual mount is sampled at admission.
	var way := [source.origin, source.origin-OUTER_SIDE*source.basis.x.normalized(),
		Vector3(rest.origin.x,source.origin.y,rest.origin.z),rest.origin]
	var angles := source.basis.orthonormalized().get_rotation_quaternion().angle_to(rest.basis.get_rotation_quaternion())
	var ages:Array[int]=[0]
	for i in range(3):
		var distance:float=way[i].distance_to(way[i+1])
		var exact:=maxf(DURATION_MIN,1.5*distance/CAP)
		if i==1:
			exact=maxf(exact,1.5*rad_to_deg(angles)/ANGULAR_CAP)
		ages.append(ages[-1]+ceili(exact*60.))
	return {"source":source,"rest":rest,"key":way,"ages":ages}

func _sample(p:Dictionary,n:int) -> Transform3D:
	var src:Transform3D=p.source
	var dst:Transform3D=p.rest
	if n<=0:
		return src
	if n>=p.ages[3]:
		return dst
	var k:=0
	while k<2 and n>=p.ages[k+1]:
		k+=1
	var u:=float(n-int(p.ages[k]))/float(int(p.ages[k+1])-int(p.ages[k]))
	var e:=u*u*(3.-2.*u)
	var storage:Basis=src.basis
	if k==1:
		# Retain exact native matrix at start; interpolate only its tiny numerical
		# residual during the turn. No mesh scale operation.
		var rot:=src.basis.orthonormalized()
		var residue:=rot.inverse()*src.basis
		storage=rot.slerp(dst.basis,e)*Basis(residue.x.lerp(Vector3.RIGHT,e),
			residue.y.lerp(Vector3.UP,e),residue.z.lerp(Vector3.BACK,e))
	elif k==2:
		storage=dst.basis
	var point:Vector3=p.key[k]
	return Transform3D(storage,point.lerp(p.key[k+1],e))

func _fail() -> bool:
	# Caller ends the entire disposable scene on this same tick. Do not continue
	# showing a stale combined world or retry after any transition attempt.
	_state=FAILED
	return false

func examine_and_commit(game, request_wood:String, expected_ids:Array[int],
		exact_rest:Array[Transform3D], verifier:Callable, mark:String) -> bool:
	# Only an opt-in owning SceneTree test can call this. No runtime dispatch.
	if _state!=UNARMED or _serial!=0 or not is_instance_valid(game) or mark!="EXAMINER_ONLY_WEST_V1":
		return false
	if request_wood!="wood" or expected_ids.size()!=2 or expected_ids[0]==expected_ids[1] or exact_rest.size()!=2:
		return false
	for i in range(2):
		if exact_rest[i]!=FROZEN_REST[i]:
			return false
	if game.persist_requested or game.persist_blocked or not game.bound or not game.actor.is_on_floor() or game.actor.velocity.length()>.005:
		return false
	var p:Vector3=game.actor.global_position
	if Vector2(p.x,p.z).distance_to(GOAL)>.035:
		return false
	var live:Dictionary=game.ledger.snapshot().duplicate(true)
	var strict:=Legacy.new()
	if not strict.restore(live) or not strict.has_exact_paid_hearth() or live.receipt!=RECEIPT:
		return false
	if live.get("version")!=2 or live.get("pine_occurrences")!=PINE or live.stock!={"wood":PINE}:
		return false
	var view:Node3D=game.wood_stock_view
	if view.get("paid_crowns")==null or view.paid_crowns.size()!=2 or view.presented_units!=PINE or view.payload.visible:
		return false
	var local_nodes:Array[MeshInstance3D]=[]
	var plans:Array[Dictionary]=[]
	for i in range(2):
		var child:MeshInstance3D=view.paid_crowns[i]
		if not is_instance_valid(child) or child.get_parent()!=view or child.get_instance_id()!=expected_ids[i] or not child.is_visible_in_tree() or child.mesh==null:
			return false
		if child.mesh.get_surface_count()!=2 or child.basis!=Basis.IDENTITY:
			return false
		if child.get_active_material(0)==null or child.get_active_material(1)==null or child.get_active_material(0).resource_name!="Bark | painted ridges" or child.get_active_material(1).resource_name!="End grain | amber":
			return false
		local_nodes.append(child)
		plans.append(derive_plan(child.global_transform,exact_rest[i]))
	# NO default/synthetic validator. SceneTree runner must install its own bound
	# native evidence collector. It gets actual transforms and derived motion,
	# never caller-supplied success booleans or changed site/poses.
	if not verifier.is_valid():
		return false
	var before:=var_to_bytes(live)
	var confirmed:Variant=verifier.call(game,plans,expected_ids,game.actor.global_transform)
	if not confirmed is Dictionary or not _validate_confirmation(confirmed, plans,expected_ids):
		return false
	if before!=var_to_bytes(game.ledger.snapshot()) or game.actor.velocity.length()>.005:
		return _fail()
	for i in range(2):
		if local_nodes[i].get_parent()!=view or local_nodes[i].global_transform!=plans[i].source or not local_nodes[i].is_visible_in_tree():
			return _fail()
	# Stage native logical receipt in detached memory, without editing v2 game.
	var new:= {"version":3,"collected":live.collected.duplicate(),"receipt":live.receipt.duplicate(true),
		"harvest_through":PINE,"deposit_through":1,"carried":{"wood":0},"stored":{"wood":2}}
	if new.carried.wood+new.stored.wood+3!=new.collected.size()+new.harvest_through:
		return _fail()
	_native_game=game
	_native_bytes=before
	_stock_view=view
	_actor=game.actor
	_pose=game.actor.global_transform
	_hold=Node3D.new()
	_hold.name="OptInExaminerStorageCustodyOnly"
	game.add_child(_hold)
	_pieces=local_nodes
	_piece_ids=expected_ids.duplicate()
	_story=plans
	# Move EXACT original view objects (identity), no clones or ghost pile.
	# Count view is fixture-owned only after one memory publication. No awaits.
	for i in range(2):
		_pieces[i].reparent(_hold,true)
		_pieces[i].global_transform=_story[i].source
		if _pieces[i].get_instance_id()!=_piece_ids[i] or _pieces[i].get_parent()!=_hold:
			return _fail()
	view.counter.hide()
	_after=new
	_serial=1
	_state=IN_FLIGHT
	return true

func _validate_confirmation(q:Dictionary,plans:Array[Dictionary],ids:Array[int]) -> bool:
	# Runner-specific closure still needs implementation and independent review.
	# Must cover whole native walk and exact planned fixture volume; a prior
	# 25/26 is NEVER a valid confirmation. No foreign route/placement proof.
	for k in ["walk_manifest","rest_manifest","oracle","native_ids","plans","continuous_plan_checked","original_walk_exact","anomalies_verified_elsewhere","fixed_leaf_transforms","visual_floor_finite_support","geometry_negatives","actual_settled_whole_actor"]:
		if not q.has(k):
			return false
	if not (q.walk_manifest==WALK_SEAL and q.rest_manifest==REST_SEAL and q.oracle==ORACLE_SEAL and q.native_ids==ids and q.plans==plans and q.continuous_plan_checked==true and q.original_walk_exact==true and q.fixed_leaf_transforms==true and q.visual_floor_finite_support==true and q.geometry_negatives==true and q.actual_settled_whole_actor==true):
		return false
	var disputed:Variant=q.anomalies_verified_elsewhere
	if not disputed is Dictionary or disputed.size()!=2:
		return false
	for k in EXPECTED_TURNS:
		var actual:Variant=disputed.get(k)
		if not actual is Dictionary or not actual.get("foot") is Vector3 or not actual.get("sphere") is float or not actual.get("swept_oriented_clearance_m") is float or not actual.get("observed_obstacle_ids") is Array:
			return false
		if actual.foot.distance_to(EXPECTED_TURNS[k].foot)>.001 or absf(actual.sphere-EXPECTED_TURNS[k].sphere)>.001 or actual.observed_obstacle_ids.is_empty() or not is_finite(actual.swept_oriented_clearance_m) or actual.swept_oriented_clearance_m<=.0001:
			return false
	return true

func frame_at_next_fixture_tick() -> bool:
	if _state!=IN_FLIGHT or not is_instance_valid(_hold):
		return false
	if _native_bytes!=var_to_bytes(_native_game.ledger.snapshot()) or not _actor.is_on_floor() or _actor.velocity.length()>.005 or _actor.global_transform.origin.distance_to(_pose.origin)>.003 or not _actor.global_transform.basis.is_equal_approx(_pose.basis):
		return _fail()
	if _hold.get_child_count()!=2 or _stock_view.counter.is_visible_in_tree() or _stock_view.payload.is_visible_in_tree():
		return _fail()
	for i in range(2):
		if _pieces[i].get_parent()!=_hold or _pieces[i].get_instance_id()!=_piece_ids[i] or not _pieces[i].is_visible_in_tree():
			return _fail()
	_frame+=1
	var t0:int=_story[0].ages[3]+6
	for i in range(2):
		_pieces[i].global_transform=_sample(_story[i],_frame-(0 if i==0 else t0))
	if _frame>=t0+int(_story[1].ages[3]):
		_state=PARKED
	return true
