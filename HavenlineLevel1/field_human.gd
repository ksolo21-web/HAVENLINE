extends Node3D
## The forester wears the survivor rig; customer models use their own turnarounds.
const PORTRAITS := {
	"survivor_male_01": preload("res://assets/settlement_people/survivor_male_01.glb"),
	"customer_female_01": preload("res://assets/settlement_people/customer_female_01.glb"),
	"customer_male_01": preload("res://assets/settlement_people/customer_male_01.glb")
}
const CHOP_SECONDS := 1.55
const ApprovedTools := preload("res://weapon_orbit.gd")
const WorkSwing := preload("res://forester_work_swing.gd")
const ToolContacts := preload("res://orbit_head_contacts.gd")
var skeleton: Skeleton3D
var mining_tool: Node3D
var tool: Node3D
var bundle: Node3D
var bones := {}
var mode := ""
var pose_progress := 0.0
var body_model: Node3D
var identity := ""
var forester_gait: RefCounted
var work_strike_point := Vector3.INF
var tool_pose: Callable

func configure(id: String) -> void:
	if not PORTRAITS.has(id) or skeleton: return
	identity = id
	var model: Node3D = PORTRAITS[id].instantiate()
	add_child(model)
	body_model = model
	skeleton = model.find_children("*","Skeleton3D",true,false)[0]
	var surface: MeshInstance3D = model.find_children("*","MeshInstance3D",true,false)[0]
	for index in surface.mesh.get_surface_count():
		var original: BaseMaterial3D = surface.mesh.surface_get_material(index)
		if original.resource_name == "Turnaround head":
			var head := ShaderMaterial.new()
			head.shader = preload("res://assets/settlement_people/head_view.gdshader")
			head.set_shader_parameter("studio",original.albedo_texture)
			var calibration := PackedVector4Array()
			for row in JSON.parse_string(FileAccess.get_file_as_string("res://assets/settlement_people/"+id+".projection.json")):
				calibration.append(Vector4(row[0],row[1],row[2],row[3]))
			head.set_shader_parameter("projection",calibration)
			surface.set_surface_override_material(index,head)
		else:
			var wardrobe := original.duplicate() as BaseMaterial3D
			wardrobe.vertex_color_use_as_albedo = false
			surface.set_surface_override_material(index,wardrobe)
	for i in skeleton.get_bone_count():
		bones[String(skeleton.get_bone_name(i))] = i
	if id == "survivor_male_01":
		forester_gait=preload("res://forester_gait.gd").new()
		forester_gait.bind(skeleton)
		forester_gait.tread.bind(surface,skeleton)
		tool = ApprovedTools.AXE.instantiate()
		add_child(tool)
		tool.hide()
		mining_tool = ApprovedTools.PICK.instantiate()
		add_child(mining_tool)
		mining_tool.hide()
		bundle = preload("res://field_art.gd").make("wood",.46)
		add_child(bundle)
		bundle.position = Vector3(0,.58,.235)
		bundle.hide()
	pose("idle",0)

func travel_pose(phase: float, pace: float, loaded: bool) -> void:
	if not forester_gait: return
	pose("travel",phase)
	var u := phase*TAU
	# The wrist trails the upper arm as the elbow passes the ribcage.
	var stride := cos(u)
	var run := smoothstep(.85,5.8,pace)
	var power := smoothstep(0.,.8,pace)
	var forward := (lerpf(.05,.16,run) + (.075 if loaded else 0.)) * power
	_bend("Pelvis",forward*.4,-.105*stride*power,.017*sin(u)*power)
	_bend("Chest",forward,.15*stride*power,-.025*sin(u)*power)
	_bend("Head",-forward*.57,-.055*stride*power)
	for side in ["L","R"]:
		var sign_x := 1. if side == "L" else -1.
		var sweep := stride*sign_x
		var arm_swing := lerpf(.32,.72,run)*(.78 if loaded else 1.)
		_bend("UpperArm."+side,arm_swing*sweep*power,-.035*sign_x,-.06*sign_x)
		var elbow := cos(u-.27)*sign_x
		_bend("Forearm."+side,-.21-run*.50+.16*elbow*power)
	forester_gait.update(phase,pace > .035,pace)

func _bend(bone: String, x: float, y: float = 0, z: float = 0) -> void:
	skeleton.set_bone_pose_rotation(bones[bone],Quaternion.from_euler(Vector3(x,y,z)))

func pose(action: String, phase: float) -> void:
	if not skeleton: return
	pose_progress = phase
	if action != mode:
		skeleton.reset_bone_poses()
		mode = action
		if tool: tool.visible = mode == "chop"
		if mining_tool: mining_tool.visible = mode == "mine"
		if bundle: bundle.visible = mode == "carry"
	var angle := fposmod(phase,1.0)*TAU
	if mode in ["chop","mine"]:
		if not forester_gait: return
		var target := to_local(work_strike_point) if work_strike_point.is_finite() else Vector3(0,.96,.64)
		var held := mining_tool if mode == "mine" else tool
		WorkSwing.drive(self,held,phase,mode=="mine",target)
		if tool_pose.is_valid(): tool_pose.call(held, mode == "mine", phase)
		return
	if mode == "receive":
		var reach := sin(clampf(phase,0.,1.)*PI)
		skeleton.position = Vector3.ZERO
		_bend("Chest",.095*reach)
		_bend("Head",.165*reach)
		for side in ["L","R"]:
			var sign_x := 1. if side == "L" else -1.
			_bend("UpperArm."+side,-.92*reach,.09*sign_x*reach,-.14*sign_x*reach)
			_bend("Forearm."+side,-.18-.63*reach,-.24*sign_x*reach,.11*sign_x*reach)
		return
	if mode == "travel": return
	var moving := mode in ["walk","carry"]
	var stride := sin(angle) if moving else 0.
	var sway := cos(angle) if moving else 0.
	var lift := .018*(1.-cos(angle*2.)) if moving else .006*sin(angle)
	skeleton.position = Vector3(.013*sway,lift,0)
	_bend("Pelvis",.012,-.095*stride,.025*sway)
	_bend("Chest",.025+.013*cos(angle),.16*stride,-.035*sway)
	_bend("Head",-.02,-.055*stride,.018*sway)
	for side in ["L","R"]:
		var sign_x := 1. if side == "L" else -1.
		var step := stride*sign_x
		var recovery := maxf(0.,cos(angle)*sign_x)
		_bend("Thigh."+side,-.56*step-.11*recovery,.012*sign_x,0)
		_bend("Shin."+side,.10+.74*recovery if moving else .025)
		_bend("Foot."+side,.34*step-.35*recovery if moving else -.022)
		if mode == "carry":
			_bend("UpperArm."+side,-.68,.06*sign_x,-.22*sign_x)
			_bend("Forearm."+side,-.79,-.60*sign_x,.24*sign_x)
		else:
			_bend("UpperArm."+side,.34*step,-.03*sign_x,-.015*sign_x)
			_bend("Forearm."+side,-.13-.17*maxf(-step,0.))

	if forester_gait:
		forester_gait.update(phase,moving)
		if mode == "carry":
			_hold_bundle()

# Keep the two gloved palms on opposite lower log ends as the torso rises
# and falls. Grip positions are in the character's space, like the bundle.
func _hold_bundle() -> void:
	for side in ["L","R"]:
		var sign_x := 1.0 if side=="L" else -1.0
		var arm: int = bones["UpperArm."+side]
		var forearm: int = bones["Forearm."+side]
		var hand: int = bones["Palm."+side]
		var shoulder := skeleton.get_bone_global_pose(arm).origin
		var upper := skeleton.get_bone_rest(forearm).origin
		var lower := skeleton.get_bone_rest(hand).origin
		var palm := Vector3(sign_x*.206,.650,.231)-skeleton.position
		var reach := palm-shoulder
		var distance := clampf(reach.length(),.001,upper.length()+lower.length()-.001)
		var axis := reach.normalized()
		var along := (upper.length_squared()-lower.length_squared()+distance*distance)/(2.*distance)
		var bend := Vector3(sign_x*.65,-.65,-.55).slide(axis).normalized()
		var elbow := shoulder+axis*along+bend*sqrt(maxf(0.,upper.length_squared()-along*along))
		var arm_basis := Basis(Quaternion(upper.normalized(),(elbow-shoulder).normalized()))
		var fore_basis := Basis(Quaternion(lower.normalized(),(palm-elbow).normalized()))
		skeleton.set_bone_global_pose(arm,Transform3D(arm_basis,shoulder))
		skeleton.set_bone_global_pose(forearm,Transform3D(fore_basis,elbow))
		skeleton.set_bone_global_pose(hand,Transform3D(fore_basis,palm))

func blade_points() -> PackedVector3Array:
	var result := PackedVector3Array()
	if mode=="mine" and mining_tool:
		for vertex: Vector3 in ToolContacts.PICKAXE: result.append(mining_tool.global_transform*vertex)
	elif mode=="chop" and tool:
		for vertex: Vector3 in ToolContacts.AXE: result.append(tool.global_transform*vertex)
	return result
