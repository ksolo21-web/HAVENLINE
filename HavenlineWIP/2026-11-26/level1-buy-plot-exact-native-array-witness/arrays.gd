extends RefCounted
const Pose = preload("res://tests/c1_plate_snapshot.gd")
const EXPECTED := [["Character1/Armature/Skeleton3D/tripo_node_4eb29cfe-0224-4bae-964c-c3bd963ca259",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Lower log | knot side",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Lower log | knot side",1],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Lower log | far side",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Lower log | far side",1],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Crown log",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Crown log",1],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/One flax lashing | continuous perimeter",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Hitch | left tail",0],["TechnicalPublishedWoodStockView/TechnicalWoodBundleRepresentative/Hitch | right tail",0]]

static func digest(x: PackedByteArray) -> String:
	var ctx := HashingContext.new()
	if ctx.start(HashingContext.HASH_SHA256)!=OK or ctx.update(x)!=OK:
		return ""
	return ctx.finish().hex_encode()

static func collect(actor: Node3D, camera: Camera3D, pose: Dictionary, folder: String, phase: String) -> Dictionary:
	if Pose.tf(actor.global_transform)!=pose.actor or Pose.tf(camera.global_transform)!=pose.camera or Engine.get_physics_frames()!=pose.physics:
		return {}
	var records := []
	for m in pose.surfaces:
		var mesh := actor.get_node_or_null(NodePath(m.relative)) as MeshInstance3D
		if mesh==null or not mesh.is_visible_in_tree() or Pose.tf(mesh.global_transform)!=m.world:
			return {}
		for s in m.surfaces:
			var a := mesh.mesh.surface_get_arrays(s.surface)
			var mat := mesh.get_active_material(s.surface) as BaseMaterial3D
			if mat==null or mat.cull_mode!=s.cull or mat.transparency!=BaseMaterial3D.TRANSPARENCY_DISABLED:
				return {}
			var pos: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var ids: PackedInt32Array = a[Mesh.ARRAY_INDEX]
			var bones: PackedInt32Array = PackedInt32Array() if a[Mesh.ARRAY_BONES]==null else a[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array = PackedFloat32Array() if a[Mesh.ARRAY_WEIGHTS]==null else a[Mesh.ARRAY_WEIGHTS]
			if pos.size()!=s.vertices or ids.size()!=s.indices or weights.size()!=s.weights or bones.size()!=weights.size():
				return {}
			var chunks: Array[PackedByteArray] = [pos.to_byte_array(),ids.to_byte_array(),bones.to_byte_array(),weights.to_byte_array()]
			if records.size()>=EXPECTED.size() or [m.relative,s.surface]!=EXPECTED[records.size()]:
				return {}
			var counts := [12*pos.size(),4*ids.size(),4*bones.size(),4*weights.size()]
			var meta := []
			for i in chunks.size():
				if chunks[i].size()!=counts[i]:
					return {}
				var fn := "%s.part%02d.%s.bin" % [phase,records.size(),["p","i","j","w"][i]]
				if FileAccess.file_exists(folder.path_join(fn)):
					return {}
				var stream_sha := "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" if chunks[i].is_empty() else digest(chunks[i])
				if stream_sha.length()!=64:
					return {}
				var file := FileAccess.open(folder.path_join(fn),FileAccess.WRITE)
				if file==null:
					return {}
				file.store_buffer(chunks[i])
				file.close()
				meta.append({"file":fn,"bytes":counts[i],"sha256":stream_sha})
			records.append({"relative":m.relative,"surface":s.surface,"decl":s,"mesh_world":m.world,"visible":true,"arrays":meta})
	var labels := []
	for item in actor.find_children("*","Label3D",true,false):
		var label := item as Label3D
		if label.is_visible_in_tree():
			var box := label.get_aabb()
			var f: Array = []
			for i in range(8):
				var xy := camera.unproject_position(label.to_global(box.get_endpoint(i)))
				f.append([xy.x,xy.y])
			labels.append({"relative":String(actor.get_path_to(label)),"text":label.text,"pixel_bounds_corners":f,"world":Pose.tf(label.global_transform)})
	if records.size()!=EXPECTED.size() or Engine.get_physics_frames()!=pose.physics or Pose.tf(actor.global_transform)!=pose.actor or Pose.tf(camera.global_transform)!=pose.camera:
		return {}
	return {"tick":pose.tick,"physics":pose.physics,"frame_pose_digest":digest(JSON.stringify(pose).to_utf8_buffer()),"parts":records,"labels":labels}
