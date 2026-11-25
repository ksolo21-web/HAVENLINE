extends RefCounted
## Only for a reviewed opt-in disposable SceneTree fixture.
const BASE := "11c14a1c41971067c7dc97db69375f720a408f68"
const CARRY := "2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5"
const WALK := "ac4a8d52a510abd6b657872fc6f73f45d043115152ce943576c365b0d4cccd80"
const ADAPTER := "a3e65c87e6dfc3f51a8a4c34a9a246e5d583e583c3204c80266f504b4e040099"
const FIRST := 1277
const NEAR := 1333
const FINISH := 1423
const FIELDS := ["tick","gesture_sha256","actor_capsule","actor_pose","velocity","grounded","animation","clip_time","carry_points","carry_signatures","scene_obstacle_geometry","two_crown_native_account","camera","view","skin_sha256"]

var prior:Dictionary={}
var chain:=""
var tick:=FIRST
var nonce:=""
var ids:Array[int]=[]
var latest:Dictionary={}
var failed:=false
var ticket:RefCounted
var trace:Array[Dictionary]=[]
var completed:=false

static func hex64(s:Variant) -> bool:
	if not s is String or s.length()!=64:
		return false
	for ch in s:
		if not ch in "0123456789abcdef":
			return false
	return true

static func canon(s:Dictionary) -> String:
	return JSON.stringify(s,"",true,true)

static func chain_step(previous:String,s:Dictionary) -> String:
	return (previous+"\n"+canon(s)).sha256_text()

static func valid_row(r:Dictionary,n:int) -> bool:
	if r.size()!=FIELDS.size() or r.get("tick")!=n or r.get("grounded")!=true:
		return false
	for k in FIELDS:
		if not r.has(k):
			return false
	return hex64(r.gesture_sha256) and hex64(r.skin_sha256)

func deny() -> bool:
	failed=true
	ticket=null
	return false

func start_b(a:Dictionary,actual_a_sha:String,independently_allowed_a_sha:String,own_nonce:String,own_runtime:String) -> bool:
	# Artifact bytes/digest must be computed by the sealed local owning runner,
	# not parsed from untrusted JSON. Fresh nonce is not a gameplay credential.
	if failed or nonce!="" or actual_a_sha!=independently_allowed_a_sha or not hex64(actual_a_sha):
		return deny()
	if a.get("baseline")!=BASE or a.get("carry")!=CARRY or a.get("walk_baseline")!=WALK or a.get("turn_adapter")!=ADAPTER:
		return deny()
	if a.get("mode")!="FULL_NO_ACTION" or a.get("state_end_tick")!=FINISH or a.get("stable_near_tick")!=NEAR or a.get("notice_ticks")!=[1306,1353]:
		return deny()
	if not hex64(a.get("turn_receipt_sha")) or not hex64(a.get("equivalence_profile_sha")) or not hex64(a.get("prefix_commit")) or not hex64(a.get("nonce")) or not hex64(a.get("runtime")):
		return deny()
	if not hex64(own_nonce) or not hex64(own_runtime) or own_nonce==a.nonce or own_runtime==a.runtime:
		return deny()
	if a.get("actual_receiver_claims")!=0 or a.get("other_sweeps_clear")!=true or a.get("ledger_unchanged")!=true or not a.get("prefix_rows") is Array or not a.get("turns") is Dictionary:
		return deny()
	if a.turns.size()!=2 or not a.turns.has(1306) or not a.turns.has(1353) or a.prefix_rows.size()!=NEAR-FIRST+1:
		return deny()
	var prefix:String=a.equivalence_profile_sha
	for i in range(a.prefix_rows.size()):
		var r:Variant=a.prefix_rows[i]
		if not r is Dictionary or not valid_row(r,FIRST+i):
			return deny()
		prefix=chain_step(prefix,r)
	if prefix!=a.prefix_commit:
		return deny()
	prior=a.duplicate(true)
	chain=a.equivalence_profile_sha
	nonce=own_nonce
	return true

func observe_b_native_frame(r:Dictionary,new_ids:Array[int]) -> bool:
	# Callback owner samples actual native B. Feeding the archived A rows
	# instead violates the contract, even if hashes match.
	if failed or nonce=="" or tick>NEAR or not valid_row(r,tick):
		return deny()
	if new_ids.size()!=2 or new_ids[0]<=0 or new_ids[1]<=0 or new_ids[0]==new_ids[1]:
		return deny()
	if ids.is_empty():
		ids=new_ids.duplicate()
	if new_ids!=ids or canon(r)!=canon(prior.prefix_rows[tick-FIRST]):
		return deny()
	chain=chain_step(chain,r)
	latest=r.duplicate(true)
	tick+=1
	return true

func admit_b_plan(prove_live:Callable,plans:Array[Dictionary],live_ids:Array[int]) -> Dictionary:
	if failed or completed or ticket!=null or tick!=NEAR+1 or chain!=prior.get("prefix_commit") or live_ids!=ids or not prove_live.is_valid():
		deny()
		return {}
	var q:Variant=prove_live.call(plans,live_ids,latest)
	if not q is Dictionary or q.get("own_nonce")!=nonce or q.get("own_tick")!=NEAR or q.get("current_ids")!=ids or q.get("current_exact_plan")!=plans:
		deny()
		return {}
	if q.get("whole_sweep")!=true or q.get("visible_finite_end")!=true or q.get("native_inputs_and_ambient_exact")!=true or q.get("actor_carry_camera_controls")!=true:
		deny()
		return {}
	ticket=RefCounted.new()
	return {"private_b_ticket":ticket,"prior_route_approved_turns":prior.turns,"live_b_plan_proof":q}

func observe_b_action(native_row:Dictionary,in_own_tick:RefCounted,live_witness:Callable) -> bool:
	if failed or completed or ticket==null or in_own_tick!=ticket or not live_witness.is_valid():
		return deny()
	if native_row.get("physics_tick")!=NEAR+trace.size() or native_row.get("subject_ids")!=ids or native_row.get("claims")!=1:
		return deny()
	# Actual provider checks scene/physics/input, no added controls lock.
	if live_witness.call(latest,ids,native_row)!=true:
		return deny()
	trace.append(native_row.duplicate(true))
	return true

func close_b_once(in_own_tick:RefCounted,settled_receipt:Callable) -> Dictionary:
	if failed or completed or ticket==null or in_own_tick!=ticket or trace.size()<3 or not settled_receipt.is_valid():
		return {}
	if settled_receipt.call(trace,ids,latest)!=true:
		deny()
		return {}
	completed=true
	ticket=null
	# Reserve/publish a stopwatch result only AFTER the completed exact scene
	# receipt and visibility check clears; any failed trial has no timing.
	return {"status":"EXAMINER_WITNESS_ONLY","first_observation":trace[0].physics_tick,
		"qualified_settled_observation":trace[-1].physics_tick,
		"observed_nominal_ticks":trace[-1].physics_tick-trace[0].physics_tick,
		"trace_receipt_sha256":JSON.stringify(trace,"",true,true).sha256_text()}
