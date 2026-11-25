extends SceneTree
const Kit = preload("res://character_kit.gd")
const Hero = preload("res://assets/characters/Character1.glb")
const PHASES := [0.07, 0.15, 0.23, 0.31, 0.39, 0.47, 0.55, 0.63, 0.71, 0.79, 0.87, 0.95]
var samples := 0
var failures: Array[String] = []

func vec(v: Vector3) -> Array:
	return [v.x, v.y, v.z]

func frame(x: Transform3D) -> Dictionary:
	return {"origin":vec(x.origin),"x":vec(x.basis.x),"y":vec(x.basis.y),"z":vec(x.basis.z)}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var host := Node3D.new()
	root.add_child(host)
	host.position = Vector3(1.7, -0.2, 2.4)
	host.rotation.y = 0.63
	var hero := Hero.instantiate() as Node3D
	host.add_child(hero)
	# Derive the same source height normalization used by opening.model().
	var bounds := AABB()
	var started := false
	var meshes := hero.find_children("*","MeshInstance3D",true,false)
	for node in meshes:
		var visual := node as MeshInstance3D
		var box := (host.global_transform.affine_inverse() * visual.global_transform) * visual.get_aabb()
		bounds = bounds.merge(box) if started else box
		started = true
	var layout: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://layout.json"))
	var fac := float(layout.actor_height) / maxf(0.01,bounds.size.y)
	hero.scale *= fac
	hero.position = Vector3(-bounds.get_center().x,-bounds.position.y,-bounds.get_center().z) * fac
	var kit = Kit.new()
	if not started or not kit.install(host,hero,null):
		push_error("Exact imported kit failed admission")
		quit(2)
		return
	var rig: Skeleton3D = kit._skeleton
	var player: AnimationPlayer = kit._player
	var manifest: Dictionary = kit._sockets
	var bone_names: Array[String]=[]
	for b in range(rig.get_bone_count()):
		bone_names.append(rig.get_bone_name(b))
	var bindings: Array = []
	for node in meshes:
		var v := node as MeshInstance3D
		if v.skin == null:
			continue
		var slot_poses: Array = []
		for k in range(v.skin.get_bind_count()):
			slot_poses.append({"bind_bone":v.skin.get_bind_bone(k),"bind_name":String(v.skin.get_bind_name(k)),"pose":frame(v.skin.get_bind_pose(k))})
		bindings.append({"scene_path":String(hero.get_path_to(v)),"skeleton_path":String(v.skeleton),"skin_binds":slot_poses})
	print("GRIP_HEADER ",JSON.stringify({"bone_order":bone_names,"hero_mesh_bindings":bindings,"hero_factor":fac,"phase_thresholds":PHASES,"subject":"exact PR108 + offset-only character_kit","stage":"target-only after natural clip callback, before and after explicit kit placement","pending":"no skin/contact, integration order or renders"}))
	for action in ["carry","chop","mine"]:
		kit.begin_action(action)
		var clip := player.current_animation
		if clip.is_empty():
			failures.append(action + " clip missing")
			continue
		var duration := player.get_animation(clip).length
		var phase_cursor := 0
		var limit := Time.get_ticks_msec() + 3500
		while phase_cursor < PHASES.size() and Time.get_ticks_msec() < limit:
			await process_frame
			var position := player.current_animation_position
			var step_ratio := position / duration
			if step_ratio < PHASES[phase_cursor]:
				continue
			if phase_cursor + 1 < PHASES.size() and step_ratio >= PHASES[phase_cursor + 1]:
				failures.append(action + " skipped phase bucket run at normal cadence")
				break
			var p_l: Node3D = kit._palm_l.get_node("LocalOffset")
			var p_r: Node3D = kit._palm_r.get_node("LocalOffset")
			var sheath: Node3D = kit._sheath.get_node("LocalOffset")
			var tool_id := "pickaxe" if action == "mine" else "axe"
			var tool: Node3D = kit._pick if action == "mine" else kit._axe
			kit.equipped = tool_id
			kit._place(false)
			var all_poses: Array = []
			for b in range(rig.get_bone_count()):
				all_poses.append(frame(rig.get_bone_global_pose(b)))
			var hero_visuals: Array = []
			for node in meshes:
				var v:=node as MeshInstance3D
				hero_visuals.append({"name":String(v.name),"scene_path":String(hero.get_path_to(v)),"world":frame(v.global_transform),"mesh_surfaces":v.mesh.get_surface_count(),"skin_bind_count":v.skin.get_bind_count() if v.skin != null else 0})
			var tool_visuals: Array = []
			var tool_nodes:=tool.find_children("*","MeshInstance3D",true,false)
			if tool is MeshInstance3D:
				tool_nodes.push_front(tool)
			for node in tool_nodes:
				var v:=node as MeshInstance3D
				tool_visuals.append({"name":String(v.name),"world":frame(v.global_transform),"mesh_surfaces":v.mesh.get_surface_count()})
			var y_band: Array = manifest.pick_grip_y if action == "mine" else manifest.axe_grip_y
			var swapped := p_l.global_position.y <= p_r.global_position.y
			var sample := {"action":action,"clip":String(clip),"position_s":position,"duration_s":duration,"threshold":PHASES[phase_cursor],"ratio":step_ratio,
				"anatomical_L":frame(p_l.global_transform),"anatomical_R":frame(p_r.global_transform),"sheath":frame(sheath.global_transform),
				"attachment_L":frame(kit._palm_l.global_transform),"attachment_R":frame(kit._palm_r.global_transform),
				"observed_low_label":"L" if swapped else "R","observed_high_label":"R" if swapped else "L","identity_sentinel": {"A":"L_Hand","B":"R_Hand"},
				"band_local_y":y_band,"low_band_world":vec(tool.global_transform*Vector3(0,float(y_band[0]),0)),
				"high_band_world":vec(tool.global_transform*Vector3(0,float(y_band[1]),0)),"tool":tool_id,"tool_world":frame(tool.global_transform),"tool_visuals":tool_visuals,
				"rig_world":frame(rig.global_transform),"rig_bone_poses":all_poses,"hero_visuals":hero_visuals}
			if tool_visuals.is_empty() or not tool.visible:
				failures.append(action + " visual root missing or hidden")
			print("GRIP_SAMPLE ",JSON.stringify(sample))
			samples += 1
			phase_cursor += 1
		if phase_cursor != PHASES.size():
			failures.append(action + " sampled " + str(phase_cursor) + "/" + str(PHASES.size()))
	print("GRIP_VERDICT ", JSON.stringify({"samples":samples,"full_target":PHASES.size()*3,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
