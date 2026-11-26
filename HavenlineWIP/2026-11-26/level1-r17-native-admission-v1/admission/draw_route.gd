extends "res://tests/hvn_l1_combined_route.gd"
## Frame-read observation only: never changes frame/view/terrain/animation/game state.
const WRITER := ["fresh-spawn","paid-first-frame","south-bidirectional","east-bidirectional","writer-v2"]
const COLD := ["cold-v2-no-replay"]
var capture_dir := ""
var armed := 0
var draw_failures := 0
var drawn: Array[String] = []

func snapshot_state() -> Dictionary:
	var a = game.actor.position
	var camera = game.camera
	var offset: Vector3 = camera.position - a
	return {"tick":tick_count,"physics_frames":Engine.get_physics_frames(),
		"stock":int(game.ledger.stock.wood),"renewals":int(game.ledger.pine_occurrences),
		"paid":game.ledger.receipt==RECEIPT,"camp_visible":game.camp_built.is_visible_in_tree(),
		"pad_hidden":live_pad_hidden(),"hearth_center_paid":camp_ok(not game.ledger.receipt.is_empty()),
		"south_open":game.gates[0].target_open,"east_open":game.gates[1].target_open,
		"offset":[offset.x,offset.y,offset.z],"actor":[a.x,a.y,a.z]}

func checkpoint(phase: String) -> void:
	super.checkpoint(phase)
	if phase not in WRITER and phase not in COLD:
		return
	if armed != 0 or phase in drawn:
		draw_failures += 1
		print("DRAW_REJECT duplicate-or-overlapping-checkpoint ",phase)
		return
	armed += 1
	RenderingServer.frame_post_draw.connect(_draw.bind(phase,snapshot_state()), CONNECT_ONE_SHOT)

func _draw(phase: String, queued: Dictionary) -> void:
	armed -= 1
	var current := snapshot_state()
	var evidence := gate_and_light(phase)
	if evidence.is_empty():
		draw_failures += 1
		print("DRAW_REJECT R17-mesh-material-paid-state-gate-or-daylight-custody ",phase)
		return
	print("R17_NATIVE_DRAW_EVIDENCE ", JSON.stringify(evidence))
	checks_r17 += 1
	var camera := game.camera as Camera3D
	var image := root.get_texture().get_image()
	if root.size != Vector2i(1280,720) or image == null or image.is_empty() or image.get_size() != Vector2i(1280,720):
		draw_failures += 1
		print("DRAW_REJECT frame-size-or-readback ",phase)
		return
	var view_direction := Vector3(7.0,11.0,11.0).normalized()
	if root.get_camera_3d() != camera or camera.projection != Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(camera.size,13.0) or camera.global_basis.z.normalized().dot(view_direction)<.999999:
		draw_failures += 1
		print("DRAW_REJECT camera-custody ",phase)
		return
	for key in ["stock","renewals","paid","camp_visible","pad_hidden","hearth_center_paid","south_open","east_open"]:
		if queued[key] != current[key]:
			draw_failures += 1
			print("DRAW_REJECT checkpoint-drift ",phase," ",key)
			return
	if int(current.physics_frames)-int(queued.physics_frames) < 0 or int(current.physics_frames)-int(queued.physics_frames) > 1:
		draw_failures += 1
		print("DRAW_REJECT draw-outside-one-physics-step ",phase)
		return
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(image.get_data())
	var pixel_digest := hash.finish().hex_encode()
	var name := capture_dir.path_join(phase+".png")
	if FileAccess.file_exists(name) or image.save_png(name)!=OK:
		draw_failures+=1
		print("DRAW_REJECT destination ",phase)
		return
	drawn.append(phase)
	print("L1_POST_DRAW ",JSON.stringify({"phase":phase,"queued":queued,"draw":current,"viewport_px":[root.size.x,root.size.y],"image_px":[image.get_width(),image.get_height()],"camera_ortho":camera.size,"display":DisplayServer.get_name(),"pixel_sha256":pixel_digest}))

func finish(phase: String) -> void:
	# The final authoritative checkpoint normally quits immediately. Only this
	# observer waits one normal draw for its final capture; gameplay stays live.
	if armed>0:
		await RenderingServer.frame_post_draw
		if armed>0:
			await process_frame
	var expected: Array = WRITER if phase=="write" else COLD
	if drawn!=expected or armed!=0 or draw_failures!=0 or checks_r17!=expected.size():
		print("DRAW_REJECT incomplete-or-invalid-order ",phase," ",drawn)
		quit(3)
		return
	print("R17_MOTION_TICKS ", JSON.stringify(moving_frames))
	print("L1_STOCK_POST_DRAW_OK ",phase," ",drawn.size())
	super.finish(phase)

func run() -> void:
	capture_dir=OS.get_environment("HVN_L1_STOCK_CAPTURE")
	if DisplayServer.get_name()!="X11" or capture_dir.is_empty() or not DirAccess.dir_exists_absolute(capture_dir):
		print("DRAW_REJECT display-or-owned-output")
		quit(2)
		return
	await super.run()

const R17_PATH := "res://previews/r17_fence/r17_fence_view.gd"
const R17_SHADER_PATH := "res://previews/r17_fence/assets/t03_boundary_v2.gdshader"
var checks_r17 := 0
var prior_angles := [0.0, 0.0]
var moving_frames := [0, 0]

func check_shell() -> bool:
	if game.get_script().resource_path != R17_PATH:
		return false
	var shell := game.camp_built.get_node_or_null("R17FenceViewOnly") as Node3D
	if not shell or shell.get_child_count() != 2 or shell.is_visible_in_tree() != game.camp_built.is_visible_in_tree():
		return false
	var totals := [7680,704]
	var names := ["R17WallPanels","R17ThresholdPosts"]
	for n in range(2):
		var batch := shell.get_node_or_null(names[n]) as MultiMeshInstance3D
		if not batch or batch.is_visible_in_tree() != shell.is_visible_in_tree() or batch.multimesh.instance_count != [12,4][n]:
			return false
		var mesh := batch.multimesh.mesh as ArrayMesh
		if not mesh or mesh.get_surface_count() != [2,3][n]:
			return false
		var tris := 0
		for i in range(mesh.get_surface_count()):
			var mat := mesh.surface_get_material(i) as ShaderMaterial
			if not mat or mat.shader.resource_path != R17_SHADER_PATH or mesh.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
				return false
			var ni := mesh.surface_get_array_index_len(i)
			var nv := mesh.surface_get_array_len(i)
			tris += int((ni if ni > 0 else nv) / 3.0)
		if tris * batch.multimesh.instance_count != totals[n]:
			return false
	for i in range(6):
		var body := game.camp_colliders[i] as StaticBody3D
		var row: Array = game.layout.walls_xz[i]
		var box := body.get_child(1) as CollisionShape3D
		var vis := body.get_child(0) as MeshInstance3D
		if not box or not vis or vis.visible or not box.shape is BoxShape3D or not box.shape.size.is_equal_approx(Vector3(float(row[2]),.95,float(row[3]))) or not body.position.is_equal_approx(game.point([row[0],row[1]],.475)):
			return false
	var hidden_markers := 0
	for child in game.camp_built.get_children():
		if child is Node3D and not child is CollisionObject3D and child.get_child_count() == 1:
			var marker := child.get_child(0) as MeshInstance3D
			if marker and marker.mesh is BoxMesh and marker.mesh.size.is_equal_approx(Vector3(.20,1.44,.20)):
				if marker.visible:
					return false
				hidden_markers += 1
	return hidden_markers == 4

func gate_and_light(phase: String) -> Dictionary:
	if not check_shell():
		return {}
	var light: DirectionalLight3D = null
	for child in game.get_children():
		if child is DirectionalLight3D:
			if light != null:
				return {}
			light = child as DirectionalLight3D
	if not light or not light.rotation_degrees.is_equal_approx(Vector3(-48,-28,0)) or not light.shadow_enabled:
		return {}
	var result := {}
	for i in range(2):
		var gate := game.gates[i] as Node3D
		var expected := ["gate-south","gate-east"]
		var originals: Array = game.layout.gates
		if gate.get_script().resource_path != "res://technical_gate.gd" or gate.get("gate_id") != expected[i] or not gate.position.is_equal_approx(game.point(originals[i].center_xz)):
			return {}
		if not gate.rotation_degrees.is_equal_approx(Vector3(0,90 * i,0)):
			return {}
		var projected := []
		for side in [-1,1]:
			var hinge := gate.get_node("HingeLeft" if side < 0 else "HingeRight") as Node3D
			var axis := gate.basis.x
			var at := gate.position + axis * (float(side) * 1.20)
			var ground_y := float(game.point([at.x+3.25, at.z-5.80]).y)
			if not is_equal_approx(hinge.position.x,1.2 * side) or not is_equal_approx(hinge.global_position.y,ground_y) or not is_equal_approx(hinge.rotation.y, -side * float(gate.get("angle"))):
				return {}
			var body := hinge.get_child(0) as AnimatableBody3D
			var col := body.get_child(0) as CollisionShape3D
			var leaf := body.get_child(1) as MeshInstance3D
			if body.collision_layer != (1 if gate.get("active") else 0) or body.collision_mask != 0 or body.sync_to_physics or not is_equal_approx(body.position.x,-side*.59):
				return {}
			if not col.shape is BoxShape3D or not col.shape.size.is_equal_approx(Vector3(1.18,1.35,.14)) or not leaf.mesh is BoxMesh or not leaf.mesh.size.is_equal_approx(col.shape.size) or not leaf.visible:
				return {}
			var bottom: Vector2 = game.camera.unproject_position(hinge.global_position)
			var top: Vector2 = game.camera.unproject_position(hinge.global_position+Vector3.UP*1.35)
			projected.append([bottom.x,bottom.y,top.x,top.y])
		result[expected[i]] = {"angle":gate.get("angle"),"projected_hinge_verticals_px":projected,"technical_box_leaf_placeholder":true}
	return {"phase":phase,"stock_daylight_degrees":[-48,-28,0],"stock_shadow_enabled":true,"gates":result,"panels":12,"posts":4,"tris":8384}

func tick(n: int) -> void:
	for i in range(n):
		await super.tick(1)
		for g in range(2):
			var angle := float(game.gates[g].angle)
			var delta := absf(angle - float(prior_angles[g]))
			if delta > .000001:
				moving_frames[g] += 1
			if angle < 0 or angle > PI*.5+.00001 or delta > 2.3/60.0+.0001:
				draw_failures += 1
			prior_angles[g] = angle
