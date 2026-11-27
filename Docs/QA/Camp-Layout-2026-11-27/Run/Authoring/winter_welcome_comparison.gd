extends RefCounted

var original: Skeleton3D
var target: Skeleton3D
var visual: Node3D
var correspondence: Array = []
var resting_hip_height := 0.0
var original_hip_height := 0.0
var skin_rest: Dictionary = {}
var bind_matrices: Dictionary = {}
var targets: Dictionary = {}
var low_points: Array = []
var points: PackedVector3Array
var lowest_ids: Array[int] = [-1, -1]
var anchor_ids: Array[int] = [-1, -1]
var anchors := [Vector3.ZERO, Vector3.ZERO]
var offsets := [Vector3.ZERO, Vector3.ZERO]
var previous_actor := Vector3.INF

func mount(world) -> bool:
	original = world.gait_motor.skeleton
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var file := "/workspace/shared/downloads/Havenline/winter-welcome-rig/Rig/Winter-Welcome-Articulated.glb"
	if doc.append_from_file(file, state) != OK: return false
	visual = doc.generate_scene(state)
	world.actor.add_child(visual)
	var skels := visual.find_children("*", "Skeleton3D",true,false)
	if skels.size() != 1: return false
	target = skels[0]
	var mesh: MeshInstance3D = visual.find_children("*","MeshInstance3D",true,false)[0]
	var bounds: AABB = world.actor.global_transform.affine_inverse()*mesh.global_transform*mesh.get_aabb()
	var factor:=1.75/bounds.size.y
	visual.scale*=factor
	visual.position=Vector3(-bounds.get_center().x,-bounds.position.y,-bounds.get_center().z)*factor
	for mi in world.hero_model.find_children("*","MeshInstance3D",true,false): mi.visible=false
	for mi in visual.find_children("*","MeshInstance3D",true,false): mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for name in ["Root","Pelvis","Spine","Chest","Neck","Head","Clavicle","UpperArm","Forearm","Hand","Thigh","Shin","Foot","Toe"]:
		for suffix in ([".L",".R"] if name in ["Clavicle","UpperArm","Forearm","Hand","Thigh","Shin","Foot","Toe"] else [""]):
			var src:= original.find_bone(name+suffix)
			var dst:= target.find_bone(("upper_arm" if name=="UpperArm" else name.to_lower())+suffix)
			if src>=0 and dst>=0: correspondence.append([src,dst,name+suffix])
	for side in [".L",".R"]:
		for finger in ["Thumb","Index","Middle","Ring","Little"]:
			for segment in range(1,3 if finger=="Thumb" else 4):
				var src:=original.find_bone(finger+str(segment)+side)
				var target_name:String=("pinky" if finger=="Little" else finger.to_lower())+(".%02d"%segment)+side
				var dst:=target.find_bone(target_name)
				if src>=0 and dst>=0:correspondence.append([src,dst,target_name])
	for i in target.get_bone_count(): skin_rest[i]=target.get_bone_global_rest(i)
	for q in correspondence: bind_matrices[q[0]]=original.get_bone_global_rest(q[0])
	var arr:=mesh.mesh.surface_get_arrays(0)
	var verts:PackedVector3Array=arr[Mesh.ARRAY_VERTEX]
	var bones:PackedInt32Array=arr[Mesh.ARRAY_BONES]
	var weights:PackedFloat32Array=arr[Mesh.ARRAY_WEIGHTS]
	var by_xz:Dictionary={}
	for i in verts.size():
		var pt:=verts[i]
		if pt.y>bounds.position.y+.045: continue
		var key:=Vector2i(roundi(pt.x*45),roundi(pt.z*45))
		if not by_xz.has(key) or verts[by_xz[key]].y>pt.y:by_xz[key]=i
	for i in by_xz.values():
		var influences: Array=[]
		for j in 4:
			var relative:float=weights[i*4+j]
			if relative<.00001:continue
			var bind:int=bones[i*4+j]
			var bone:=target.find_bone(mesh.skin.get_bind_name(bind))
			if bone<0:bone=mesh.skin.get_bind_bone(bind)
			if bone>=0: influences.append([bone,relative,mesh.skin.get_bind_pose(bind)*verts[i]])
		low_points.append([verts[i].x,influences])
	print("TALL_MOUNT ",JSON.stringify({"triangles":arr[Mesh.ARRAY_INDEX].size()/3,"mapped_bones":correspondence.size(),"height_m":bounds.size.y*factor,"proportion_scale":factor,"tread_samples":low_points.size(),"source_model":file}))
	return true

func pose():
	# Never copy a joint center from the other skeleton. Only rotations cross
	# rest frames, preserving the selected tall model's original segment lengths.
	target.reset_bone_poses()
	var src:Dictionary={}
	var dst:Dictionary={}
	for q in correspondence:src[q[0]]=original.get_bone_global_pose(q[0])
	for q in correspondence:
		var i:int=q[0];var j:int=q[1]
		var rest:Transform3D=skin_rest[j]
		var current:Transform3D=target.get_bone_global_pose(j)
		var relative:Basis=src[i].basis*bind_matrices[i].basis.inverse()
		current.basis=relative.orthonormalized()*rest.basis
		if q[2]=="Pelvis":
			current.origin=rest.origin+(src[i].origin-bind_matrices[i].origin)
		target.set_bone_global_pose(j,current)
	for v in target.get_bone_count(): dst[v]=target.get_bone_global_pose(v)
	var min_y:=INF
	points.clear()
	lowest_ids = [-1,-1]
	for record in low_points:
		var p:=Vector3.ZERO
		for infl in record[1]:p+=(dst[infl[0]]*infl[2])*infl[1]
		var pt:=target.global_transform*p
		var side:int=0 if record[0]>0 else 1
		if lowest_ids[side]<0 or pt.y<points[lowest_ids[side]].y:lowest_ids[side]=points.size()
		points.append(pt)
		min_y=minf(min_y,pt.y)
	return min_y

func place_foot(side: int, world_shift: Vector3) -> void:
	var suffix: String = ".L" if side==0 else ".R"
	var thigh:=target.find_bone("thigh"+suffix)
	var shin:=target.find_bone("shin"+suffix)
	var foot:=target.find_bone("foot"+suffix)
	var h:=target.get_bone_global_pose(thigh)
	var k:=target.get_bone_global_pose(shin)
	var a:=target.get_bone_global_pose(foot)
	var goal:Vector3=a.origin+target.global_basis.inverse()*world_shift
	var L:float=h.origin.distance_to(k.origin)
	var S:float=k.origin.distance_to(a.origin)
	var dir:=h.origin.direction_to(goal)
	var off:=(k.origin-h.origin).slide(dir).normalized()
	var dist:=clampf(h.origin.distance_to(goal),absf(L-S)+.0005,L+S-.0005)
	var proj:float=(L*L-S*S+dist*dist)/(2.*dist)
	var pivot:Vector3=h.origin+dir*proj+off*sqrt(maxf(0,L*L-proj*proj))
	var endpoint:Vector3=h.origin+dir*dist
	h.basis=Basis(Quaternion(h.origin.direction_to(k.origin),h.origin.direction_to(pivot)))*h.basis
	k.basis=Basis(Quaternion(k.origin.direction_to(a.origin),pivot.direction_to(endpoint)))*k.basis
	k.origin=pivot
	a.origin=endpoint
	target.set_bone_global_pose(thigh,h)
	target.set_bone_global_pose(shin,k)
	target.set_bone_global_pose(foot,a)

func match_floor(world):
	var current:float=pose()
	var from_ground:Vector2=world.gait_motor._heights()
	var up:float=clampf(minf(from_ground.x,from_ground.y)-current,-.25,.25) if is_finite(current) else 0.
	visual.global_position.y+=up
	var actor:Vector3=world.actor.global_position
	if actor.distance_to(previous_actor)>1.2:
		anchor_ids=[-1,-1]
		offsets=[Vector3.ZERO,Vector3.ZERO]
	previous_actor=actor
	for side in 2:
		var entered:float=from_ground[side]-actor.y
		if entered>.017:
			anchor_ids[side]=-1
			offsets[side]=Vector3(offsets[side]).move_toward(Vector3.ZERO,.020)
		else:
			var low:int=lowest_ids[side]
			if low<0:continue
			var id:int=anchor_ids[side]
			# Continue the anchor through true loading, roll to the next part
			# of the tread as the heel lifts, then release during swing.
			if id<0 or points[id].y-points[low].y>.014:
				id=low
				anchor_ids[side]=id
				anchors[side]=points[id]+Vector3(offsets[side])
			var shift:Vector3=Vector3(anchors[side])-points[id]
			offsets[side]=Vector3(shift.x,0,shift.z).limit_length(.112)
		place_foot(side,offsets[side])
