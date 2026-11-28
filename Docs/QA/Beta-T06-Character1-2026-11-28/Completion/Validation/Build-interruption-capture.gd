extends SceneTree
const Motion = preload("res://field_character_motion.gd")
const PEAKS := {"chop":[.6038,.8113],"mine":[.5841,.7257],"dismantle":[.60,.4571,.625],"deposit":[.3537,.2439],"build":[.6809,.5638,.710],"repair":[.7717,.7935,.7117],"rescue":[.5156,.62],"service":[.3678,.4368],"attack_contact":[.2553,.6702,.2303]}
const Session = preload("res://tests/lifecycle_test_profile.gd")
var output := OS.get_environment("HAVENLINE_T06_SURFACE")
var mode := OS.get_environment("HAVENLINE_T06_SURFACE_WEIGHT")
var world: Node3D
var mesh: MeshInstance3D
var rig: Skeleton3D
var file: FileAccess

func _initialize() -> void:
	Engine.physics_ticks_per_second = 120
	run.call_deferred()

func emit_vector(v: Vector3) -> void:
	file.store_float(v.x)
	file.store_float(v.y)
	file.store_float(v.z)

func emit_matrix(t: Transform3D) -> void:
	emit_vector(t.basis.x)
	emit_vector(t.basis.y)
	emit_vector(t.basis.z)
	emit_vector(t.origin)

func capture() -> void:
	var local: Transform3D = world.actor.global_transform.affine_inverse() * rig.global_transform
	for i in mesh.skin.get_bind_count():
		var bone := mesh.skin.get_bind_bone(i)
		if bone<0:bone=rig.find_bone(mesh.skin.get_bind_name(i))
		emit_matrix(local * rig.get_bone_global_pose(bone) * mesh.skin.get_bind_pose(i))

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await physics_frame
	world.actor.global_position = Vector3(30.,0.,26.)
	world.actor.rotation.y = 0.
	for i in 16: await physics_frame
	world.set_physics_process(false)
	var motion = world.character_motion
	motion.cancel()
	rig = motion.rig
	mesh = world.hero_model.find_children("*","MeshInstance3D",true,false)[0]
	var mesh_meta := []
	for surface in mesh.mesh.get_surface_count():
		var arrays: Array = mesh.mesh.surface_get_arrays(surface)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
		var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		file = FileAccess.open(output.path_join("surface-%d.bin"%surface),FileAccess.WRITE)
		for v in positions: emit_vector(v)
		for b in bones: file.store_32(b)
		for w in weights: file.store_float(w)
		for i in indices: file.store_32(i)
		file.close()
		mesh_meta.append({"vertices":positions.size(),"assignments":bones.size(),"indices":indices.size()})
	var joints := []
	for i in mesh.skin.get_bind_count():
		var b := mesh.skin.get_bind_bone(i)
		joints.append(String(mesh.skin.get_bind_name(i)) if b<0 else String(rig.get_bone_name(b)))
	file = FileAccess.open(output.path_join("pose.bin"),FileAccess.WRITE)
	capture()
	var idx := 1
	var clips := []
	for key: StringName in [&"build"]:
		var spec: Array = Motion.CLIPS[key]
		var track := [0.0,.18,.21,.237879,.25787,.27787,.28787,.297872340425532,.30787,.31787,.33787,.35787,.396,.45,1.0]
		for peak: float in PEAKS[String(key)]:
			for delta: float in [-.06,-.025,0.,.025,.06]: track.append(clampf(peak+delta,0.,1.))
		for beat in [1,2,3]:track.append(float(spec[beat]))
		track.sort()
		var start := idx
		for phase in track:
			var weight := float(Motion.LIVE_GAINS[key]) if mode == "live" else 1.
			var dt: float = maxf(0., phase - .297872340425532) * .52
			var prior := {"action":&"build","phase":.297872340425532,"weight":weight,"elapsed":dt,"target":Vector3.INF}
			motion.pose(Motion.select(0.,0.,0.,&"deposit",dt/.68,Motion.LEAD), float(Motion.LIVE_GAINS[&"deposit"]), Vector3.INF, prior)
			capture()
			motion.clear_pose()
			idx+=1
		clips.append({"name":String(key),"first":start,"samples":track,"seconds":spec[0],"contact":spec[2]})
	file.close()
	var metadata := FileAccess.open(output.path_join("Pose.json"),FileAccess.WRITE)
	metadata.store_string(JSON.stringify({"sha256":FileAccess.get_sha256("res://assets/characters/Character1Fresh.glb"),"surfaces":mesh_meta,"binds":joints,"poses":idx,"clips":clips}," "))
	metadata.close()
	await Session.drain_field_audio(self,world)
	world.queue_free()
	await process_frame
	quit()
