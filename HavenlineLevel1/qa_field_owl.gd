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
	var launches := 0
	var max_claw_error := 0.0
	var max_surface_error := 0.0
	func _event(id: String, _at: Vector3) -> void:
		if id=="owl_dive": launches+=1
	var owl := Owl.new()
	var deaths := 0
	var tick := 0
	func is_inside_camp(p: Vector3) -> bool:
		return absf(p.x) <= 4. and absf(p.z) <= 4.
	func outside(p: Vector3, margin: float) -> bool:
		return absf(p.x) > 4.+margin or absf(p.z) > 4.+margin
	func owl_contact(wolf: Node3D, at: Vector3) -> bool:
		if not owl.permits_contact(wolf,at): return false
		max_claw_error=maxf(max_claw_error,at.distance_to(owl.claw_tip(owl.planted_claw)))
		# Check distance to the drawable triangle itself. A vertical ray through
		# overlapping coat layers can select another surface above the contact.
		var skin: MeshInstance3D=wolf.contact_mesh()
		var point:=skin.to_local(at)
		var faces: PackedVector3Array=wolf.hit_surface.get_faces()
		var distance:=INF
		for i in range(0,faces.size(),3):
			var a: Vector3=faces[i]
			var b: Vector3=faces[i+1]
			var c: Vector3=faces[i+2]
			var normal: Vector3=(b-a).cross(c-a).normalized()
			if normal.length_squared()<.5: continue
			var on_plane:=point-normal*(point-a).dot(normal)
			var bary:=Geometry3D.get_triangle_barycentric_coords(on_plane,a,b,c)
			if bary.x>=-.00001 and bary.y>=-.00001 and bary.z>=-.00001:
				distance=minf(distance,at.distance_to(skin.to_global(on_plane)))
		max_surface_error=maxf(max_surface_error,distance)
		if not wolf.receive_hit(1,at): return false
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
var grasp := 0.
var reach := 0.
var asymmetric_bank := 0.
var brake_pitch := 1000.
var strike_ticks := 0
var planting_error := 0.
var max_joint_step := 0.0
func sensors_match_imported_art() -> bool:
	var owl=host.owl
	var mesh: ArrayMesh = owl.plumage.mesh
	var arrays:=mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var shapes := mesh.surface_get_blend_shape_arrays(0)
	if owl.claw_binds.size()!=6 or shapes.size()!=3: return false
	for i in 6:
		var index := vertices.find(owl.claw_binds[i])
		if index<0: return false
		for joint in 4:
			var offset:=4*index+joint
			if arrays[Mesh.ARRAY_WEIGHTS][offset]>.001 and arrays[Mesh.ARRAY_BONES][offset]!=0: return false
		for k in 3:
			var rendered: Vector3 = shapes[k][Mesh.ARRAY_VERTEX][index]
			var expected: Vector3 = vertices[index]+[owl.claw_tucks,owl.claw_reaches,owl.claw_grips][k][i]
			if rendered.distance_to(expected)>.00002: return false
	return true
func has_wing_influences() -> bool:
	var mesh: ArrayMesh = host.owl.plumage.mesh
	var arrays := mesh.surface_get_arrays(0)
	var joints: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	var counts := {}
	for i in joints.size():
		if weights[i]>.35: counts[joints[i]]=int(counts.get(joints[i],0))+1
	for bone in host.owl.shoulders+host.owl.elbows+host.owl.wrists:
		if int(counts.get(bone,0))<16: return false
	return true

func _initialize() -> void:
	call_deferred("run")
func step(count: int) -> void:
	for i in count:
		host.tick+=1
		if is_instance_valid(moving_target):
			moving_target.position.z=2.5+.42*sin(float(host.tick)/44.)
		var rotations: Array[Quaternion] = []
		for joint in host.owl.shoulders+host.owl.elbows+host.owl.wrists: rotations.append(host.owl.skeleton.get_bone_pose_rotation(joint))
		host.owl.advance(1./60.)
		var index := 0
		for joint in host.owl.shoulders+host.owl.elbows+host.owl.wrists:
			max_joint_step=maxf(max_joint_step,rotations[index].angle_to(host.owl.skeleton.get_bone_pose_rotation(joint)))
			index+=1
		states[host.owl.state]=true
		var owl=host.owl
		if owl.state=="bank":
			asymmetric_bank=maxf(asymmetric_bank,absf(owl.skeleton.get_bone_pose_rotation(owl.shoulders[0]).get_euler().z+owl.skeleton.get_bone_pose_rotation(owl.shoulders[1]).get_euler().z))
		if owl.state=="dive": reach=maxf(reach,owl.talon_weights.y)
		if owl.state=="strike":
			strike_ticks+=1
			grasp=maxf(grasp,owl.talon_weights.z)
			brake_pitch=minf(brake_pitch,owl.art.rotation.x)
			planting_error=maxf(planting_error,owl.claw_tip(owl.planted_claw).distance_to(owl.planted_at))
		if host.owl.plumage.find_blend_shape_by_name("FlightTalons") == 0:
			var tuck: float = host.owl.plumage.get_blend_shape_value(0)
			if host.owl.state in ["bank","follow"]: flying_tuck=maxf(flying_tuck,tuck)
			if host.owl.state=="dive": striking_tuck=minf(striking_tuck,tuck)
		if host.owl.state in ["follow","bank"]:
			var roll: float=host.owl.skeleton.get_bone_pose_rotation(host.owl.shoulders[1]).get_euler().z
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
	checks["both owned Meshy poses are present and only the folded Pathfinder is drawn on the post"]=host.owl.folded.name=="FrostwingPathfinder" and host.owl.plumage.name=="SkyboundSentinel" and host.owl.folded.visible and not host.owl.plumage.visible
	checks["six wing bones deform original Sentinel feather vertices"]=has_wing_influences()

	checks["remote callback blocked outside contact"]=not host.owl_contact(wolf,wolf.position)
	host.actor.position=Vector3(7.2,0,2.5)
	moving_target=wolf
	step(35)
	checks["telegraphed takeoff before first damage"]=states.has("takeoff") and host.strikes.is_empty()
	step(640)
	checks["six sensors match the actual imported claw vertices in all three poses"]=sensors_match_imported_art()
	checks["asymmetric banking visibly rolls both wing pairs"]=asymmetric_bank>.22
	checks["both talons reach before first damage and rake during a planted brake"]=reach>.99 and grasp>.95 and brake_pitch<-.10 and strike_ticks>=27
	checks["first rendered claw touches wolf triangle at hit and stays planted"]=host.max_claw_error<.0005 and host.max_surface_error<.0005 and planting_error<.0005
	checks["six feather joints fold and flare without a one-frame angular snap"]=max_joint_step<=.226
	checks["each of three attack telegraphs fired once"]=states.has("windup") and host.launches==3
	checks["one defeat and exactly three physical contacts on moving wolf"]=host.strikes.size()==3 and host.deaths==1 and wolf.hp==0
	var spacing:=true
	for i in range(1,host.strikes.size()):
		spacing=spacing and host.strikes[i][0]-host.strikes[i-1][0]>=int(60*Owl.RELOAD)
	checks["contact recovery and cooldown enforced"]=spacing and states.has("recover") and states.has("dive") and states.has("bank")
	checks["flight talons retract and extend before impact"]=host.owl.plumage.get_blend_shape_count()==3 and flying_tuck>.9 and striking_tuck<.01
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
	print("OWL_QA "+JSON.stringify({"checks":checks,"strikes":host.strikes,"states":states.keys(),"wing_range_rad":[wing_min,wing_max],"max_hit_error_m":host.max_claw_error,"max_mesh_error_m":host.max_surface_error,"max_plant_error_m":planting_error,"max_joint_step_rad_at_60hz":max_joint_step,"grasp":grasp,"reach":reach,"braking_pitch":brake_pitch}))
	host.free()
	quit(int(false in checks.values()))
