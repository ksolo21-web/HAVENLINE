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
	if swing_pending!=0 or swing_ok!=(6 if phase=="write" else 0):
		print("DRAW_REJECT partial swing evidence ",swing_pending," ",swing_ok)
		quit(5)
		return
	print("L1_STOCK_POST_DRAW_OK ",phase," ",drawn.size())
	super.finish(phase)

func run() -> void:
	capture_dir=OS.get_environment("HVN_L1_STOCK_CAPTURE")
	if gate_contract().is_empty():
		print("DRAW_REJECT missing authenticated gate contract")
		quit(4)
		return
	if DisplayServer.get_name()!="X11" or capture_dir.is_empty() or not DirAccess.dir_exists_absolute(capture_dir):
		print("DRAW_REJECT display-or-owned-output")
		quit(2)
		return
	await super.run()


const R17_SHADER_PATH := "res://previews/r17_fence/assets/t03_boundary_v2.gdshader"
var checks_r17 := 0
var prior_angles := [0.0, 0.0]
var moving_frames := [0, 0]

func check_shell() -> bool:
	if game.get_script().resource_path != gate_config.script:
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
		var mount_witness := []
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
			if not col.shape is BoxShape3D or not col.shape.size.is_equal_approx(Vector3(1.18,1.35,.14)) or not leaf.mesh is BoxMesh or not leaf.mesh.size.is_equal_approx(col.shape.size) :
				return {}
			var mount := admitted_leaf(hinge,body,leaf,side)
			if mount.is_empty() or mount.visual_global_basis_matches_pivot != true:
				return {}
			mount_witness.append(mount)
			var bottom: Vector2 = game.camera.unproject_position(hinge.global_position)
			var top: Vector2 = game.camera.unproject_position(hinge.global_position+Vector3.UP*1.35)
			projected.append([bottom.x,bottom.y,top.x,top.y])
		result[expected[i]] = {"angle":gate.get("angle"),"projected_hinge_verticals_px":projected,"technical_box_leaf_placeholder":false,"mounts":mount_witness}
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
		schedule_swing()

var gate_config: Dictionary = {}
var swing_pinned := {}
var swing_pending := 0
var swing_ok := 0


func gate_contract() -> Dictionary:
	gate_config = JSON.parse_string(FileAccess.get_file_as_string("res://tests/hvn_l1_gate_config.json"))
	return gate_config

func admitted_leaf(pivot: Node3D, body: AnimatableBody3D, leaf: MeshInstance3D, side: int) -> Dictionary:
	if body.get_parent() != pivot or pivot.get_child_count() != 2 or body.get_child_count() != 2 or leaf.visible:
		return {}
	var art := pivot.get_node_or_null(String(gate_config.mesh_node)) as MeshInstance3D
	if not art or art.top_level or art.get_parent() != pivot or not art.transform.is_equal_approx(Transform3D.IDENTITY) or not art.visible:
		return {}
	if art.is_visible_in_tree() != pivot.is_visible_in_tree():
		return {}
	var source := art.mesh as ArrayMesh
	var donor_path := String(gate_config.leaves["left" if side < 0 else "right"].resource)
	if not source or source.get_surface_count() != 39 or not ResourceLoader.exists(donor_path):
		return {}
	var donor := load(donor_path) as ArrayMesh
	if donor == null or source != donor:
		return {}
	var box := source.get_aabb()
	var low := Vector3(0 if side < 0 else -1.18,0,-.07)
	var high := Vector3(1.18 if side < 0 else 0,1.35,.07)
	if not box.position.is_finite() or not box.end.is_finite():
		return {}
	for i in range(3):
		if box.position[i] < low[i] - .00001 or box.end[i] > high[i] + .00001:
			return {}
	var policy: Dictionary = gate_config.leaves["left" if side < 0 else "right"]
	var ordered_surface_stats: Array = policy.ordered_surfaces
	if ordered_surface_stats.size()!=39:
		return {}
	var signed: Array = policy.signed_aabb_m
	for i in range(3):
		if absf(box.position[i]-float(signed[0][i])) > .000001 or absf(box.end[i]-float(signed[1][i])) > .000001:
			return {}
	var by_material := {}
	var observed: Array[Dictionary] = []
	var sum_triangles := 0
	for i in range(source.get_surface_count()):
		var mat := source.surface_get_material(i)
		var exp: Dictionary = ordered_surface_stats[i]
		var primitive := int(source.surface_get_primitive_type(i))
		if not mat is StandardMaterial3D or primitive!=int(Mesh.PRIMITIVE_TRIANGLES) or mat.get("albedo_texture")!=null:
			return {}
		var is_textured := false
		for prop in mat.get_property_list():
			if int(prop.type)==TYPE_OBJECT and mat.get(prop.name) is Texture:
				is_textured=true
		var label := mat.resource_name.to_lower()
		var ni := source.surface_get_array_index_len(i)
		var nv := source.surface_get_array_len(i)
		var count := int((ni if ni > 0 else nv)/3.0)
		if is_textured or int(exp.index)!=i or label!=String(exp.material) or mat.get_class()!=String(exp["class"]) or primitive!=int(exp.primitive) or count!=int(exp.triangles) or ni!=int(exp.indices) or nv!=int(exp.vertices) or bool(exp.albedo_map):
			return {}
		observed.append({"index":i,"material":label,"class":mat.get_class(),"primitive":primitive,"triangles":count,"indices":ni,"vertices":nv,"albedo_map":false})
		by_material[label]=int(by_material.get(label,0))+count
		sum_triangles+=count
	var expected_materials: Dictionary = policy.material_triangles
	if by_material.size()!=9 or sum_triangles!=3226 or observed.size()!=39 or by_material.size() != expected_materials.size():
		return {}
	for key in expected_materials:
		if int(by_material.get(key,-1)) != int(expected_materials[key]):
			return {}
	return {"source":donor_path,"material_triangles":by_material,"surface_count":observed.size(),"ordered_surfaces":observed,
		"aabb_low":[box.position.x,box.position.y,box.position.z],
		"aabb_high":[box.end.x,box.end.y,box.end.z],"owner_pivot":String(pivot.name),
		"stock_box_hidden":true,"visual_global_basis_matches_pivot":art.global_basis.is_equal_approx(pivot.global_basis)}

func schedule_swing() -> void:
	if not game.camp_built.is_visible_in_tree():
		return
	for k in range(2):
		var gate := game.gates[k] as Node3D
		var angle := float(gate.get("angle"))
		if not gate.get("target_open"):
			continue
		for bin in [22.5,45.0,67.5]:
			var label := String(gate.get("gate_id"))+"-"+str(int(bin*10.0))
			if label not in swing_pinned and rad_to_deg(angle) >= bin:
				swing_pinned[label] = true
				swing_pending += 1
				RenderingServer.frame_post_draw.connect(
					_capture_swing.bind(k,bin,angle,label,Engine.get_physics_frames(),tick_count),CONNECT_ONE_SHOT)

func _capture_swing(k: int, bin: float, queued_angle: float, label: String, queued_frame: int, queued_tick: int) -> void:
	swing_pending -= 1
	var gate := game.gates[k] as Node3D
	var drawn_angle := float(gate.get("angle"))
	var camera := game.camera as Camera3D
	var root_at := Vector3(7,11,11).normalized()
	var issue := Engine.get_physics_frames()-queued_frame
	if issue < 0 or issue > 1 or drawn_angle + .000001 < queued_angle or rad_to_deg(drawn_angle) >= bin+4.4 or not gate.get("target_open") or gate_and_light(label).is_empty():
		draw_failures += 1
		print("DRAW_REJECT clearance-swing-state ",label)
		return
	if root.get_camera_3d()!=camera or camera.projection!=Camera3D.PROJECTION_ORTHOGONAL or not is_equal_approx(camera.size,13.0) or camera.global_basis.z.normalized().dot(root_at)<.999999:
		draw_failures += 1
		print("DRAW_REJECT clearance-camera ",label)
		return
	var image := root.get_texture().get_image()
	if not image or image.is_empty() or image.get_size()!=Vector2i(1280,720):
		draw_failures += 1
		print("DRAW_REJECT clearance-readback ",label)
		return
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(image.get_data())
	var pixel := hash.finish().hex_encode()
	var path := capture_dir.path_join("swing-"+label+".png")
	if FileAccess.file_exists(path) or image.save_png(path)!=OK:
		draw_failures += 1
		print("DRAW_REJECT clearance-file ",label)
		return
	swing_ok += 1
	print("CLEARANCE_SWING_FRAME ", JSON.stringify({"label":label,"gate":gate.get("gate_id"),"target_deg":bin,
		"queue_deg":rad_to_deg(queued_angle),"draw_deg":rad_to_deg(drawn_angle),"queue_tick":queued_tick,
		"physics_delta":issue,"native_buffer_sha256":pixel,"width":1280,"height":720}))
