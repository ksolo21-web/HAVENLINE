extends "res://tests/test_integrated_opening.gd"

func pt(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

func output_surface(parts: Array[Node], directory: String, tag: String) -> bool:
	var rows := []
	for child in parts:
		var mesh := child as MeshInstance3D
		if not mesh.is_visible_in_tree():
			continue
		if mesh.mesh == null or mesh.mesh.get_blend_shape_count() != 0 or mesh.skin == null:
			return false
		var skel := mesh.get_node_or_null(mesh.skeleton) as Skeleton3D
		if skel == null or mesh.skin.get_bind_count() != 66:
			return false
		var matrices: Array[Transform3D] = []
		for j in range(mesh.skin.get_bind_count()):
			var k := skel.find_bone(String(mesh.skin.get_bind_name(j))) if mesh.skin.get_bind_name(j) != &"" else mesh.skin.get_bind_bone(j)
			if k < 0:
				return false
			matrices.append(skel.get_bone_global_pose(k) * mesh.skin.get_bind_pose(j))
		for i in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(i) != Mesh.PRIMITIVE_TRIANGLES:
				return false
			var row: Array = mesh.mesh.surface_get_arrays(i)
			var v: PackedVector3Array = row[Mesh.ARRAY_VERTEX]
			var b: PackedInt32Array = row[Mesh.ARRAY_BONES]
			var w: PackedFloat32Array = row[Mesh.ARRAY_WEIGHTS]
			var ix: PackedInt32Array = row[Mesh.ARRAY_INDEX]
			var width := b.size() / float(v.size())
			if width not in [4.,8.] or w.size()!=b.size() or ix.is_empty():
				return false
			var fitted := []
			for a in range(v.size()):
				var pr := Vector3.ZERO
				var sum := 0.
				for j in range(int(width)):
					var h := a*int(width)+j
					if w[h] == 0.:
						continue
					pr += (matrices[b[h]] * v[a])*w[h]
					sum += w[h]
				if absf(sum-1.)>.0002:
					return false
				fitted.append(pt(mesh.to_global(pr)))
			rows.append({"positions":fitted,"triangles":Array(ix)})
	var f := FileAccess.open(directory.path_join(tag+".json"),FileAccess.WRITE)
	if rows.is_empty() or f == null:
		return false
	f.store_string(JSON.stringify(rows))
	return true

func collect() -> bool:
	if not await travel(game.wood_anchors["wood-b"]) or not await travel(game.wood_anchors["wood-c"]):
		return false
	if not await travel(game.point([-.35,6.])) or not await travel(game.point([-.85,6.])):
		return false
	if game.ledger.stock.wood != 2 or not game.resource_tree.can_address(game.actor.global_position,game.tree_facing()):
		return false
	for i in range(3):
		press(KEY_F)
		await tick(21)
	if not await travel(game.point([0.,6.])):
		return false
	await tick(58)
	return game.ledger.stock.wood == 3 and game.resource_tree.phase == "credited"

func exact_paid_cut(start: int) -> bool:
	if not await travel(game.point([-.35,6.])) or not await travel(game.point([-.85,6.])):
		return false
	if not game.resource_tree.can_address(game.actor.global_position, game.tree_facing()) or game.ledger.stock.wood!=start:
		return false
	for i in range(3):
		press(KEY_F)
		await tick(21)
	if game.resource_tree.phase != "falling" or game.ledger.stock.wood!=start:
		return false
	if not await travel(game.point([0.,6.])):
		return false
	for i in range(65):
		if game.resource_tree.phase=="credited":
			break
		await tick(1)
	return game.resource_tree.phase=="credited" and game.ledger.stock.wood==start+1 and game.ledger.pine_occurrences==start+1

var stable_ids:Array[int] = []
var watch_motion := false
var got_motion := false

func count_mount(wanted: int) -> bool:
	var carry:Node3D=game.wood_stock_view
	var n:=0
	for crown in carry.paid_crowns:
		if crown.is_visible_in_tree():
			n+=1
		if crown.get_parent()!=carry or crown.scale!=Vector3.ONE or crown.basis!=Basis.IDENTITY:
			return false
	return n==wanted and carry.presented_units==game.ledger.stock.wood and carry.counter.is_visible_in_tree()==(game.ledger.stock.wood>0)

func quick_clearance(label:String) -> bool:
	var carry:Node3D=game.wood_stock_view
	var anim:AnimationPlayer=game.hero_locomotion.player
	var visual:Node3D
	for child in game.actor.get_children():
		if child.is_ancestor_of(anim):
			visual=child
	if visual==null or not game.actor.is_on_floor():
		return false
	var maxz := -INF
	var min_y:=INF
	var max_y:=-INF
	var max_x:=-INF
	var min_x:=INF
	var actor_min_z:=INF
	var bodies:=0
	for m in visual.find_children("*","MeshInstance3D",true,false):
		if not m.is_visible_in_tree():
			continue
		var skel:=m.get_node_or_null(m.skeleton) as Skeleton3D
		if skel==null or m.skin==null or m.skin.get_bind_count()!=66:
			return false
		var skin_mats:Array[Transform3D]=[]
		for j in range(m.skin.get_bind_count()):
			var b:=skel.find_bone(String(m.skin.get_bind_name(j))) if m.skin.get_bind_name(j)!=&"" else int(m.skin.get_bind_bone(j))
			if b<0:
				return false
			skin_mats.append(skel.get_bone_global_pose(b)*m.skin.get_bind_pose(j))
		var local:Transform3D=carry.global_transform.affine_inverse()*m.global_transform
		for si in range(m.mesh.get_surface_count()):
			var arr:Array=m.mesh.surface_get_arrays(si)
			var vv:PackedVector3Array=arr[Mesh.ARRAY_VERTEX]
			var wb:PackedFloat32Array=arr[Mesh.ARRAY_WEIGHTS]
			var ix:PackedInt32Array=arr[Mesh.ARRAY_BONES]
			if wb.is_empty() or wb.size()!=ix.size() or wb.size()%vv.size()!=0:
				return false
			var n:=int(wb.size()/float(vv.size()))
			if n not in [4,8]:
				return false
			for k in range(vv.size()):
				var p:=Vector3.ZERO
				var sum:=0.
				for j in range(n):
					var idx:=k*n+j
					if wb[idx]!=0.:
						p+=(skin_mats[ix[idx]]*vv[k])*wb[idx]
						sum+=wb[idx]
				if absf(sum-1.)>0.0002:
					return false
				var q:=local*p
				actor_min_z=minf(actor_min_z,q.z);maxz=maxf(maxz,q.z)
				min_y=minf(min_y,q.y);max_y=maxf(max_y,q.y)
				min_x=minf(min_x,q.x);max_x=maxf(max_x,q.x)
		bodies+=1
	if bodies!=1 or not count_mount(2):
		return false
	var boxes:Array[AABB]=[]
	for c in carry.paid_crowns:
		var bounds:AABB=c.transform*c.get_aabb()
		if not carry.fitted_bounds.encloses(bounds) or c.get_active_material(0)==null or c.get_active_material(1)==null:
			return false
		boxes.append(bounds)
	var actor_gap:=actor_min_z-maxf(boxes[0].end.z,boxes[1].end.z)
	var pair_gap:=boxes[1].position.z-boxes[0].end.z
	var ids:Array[int]=[]
	var marks:= []
	var shp:CollisionShape3D
	for n in game.actor.get_children():
		if n is CollisionShape3D and n.shape is CapsuleShape3D and not n.disabled:
			if shp!=null:
				return false
			shp=n
	if shp==null or carry.get_parent()!=game.actor:
		return false
	var capsule:CapsuleShape3D=shp.shape
	var t:Transform3D=carry.global_transform.affine_inverse()*shp.global_transform
	if not t.basis.is_conformal() or absf(t.basis.x.length()-1.0)>0.0001:
		return false
	var cap_zmin:float=t.origin.z-absf(t.basis.y.z)*maxf(0.0,capsule.height/2.0-capsule.radius)-capsule.radius
	var cap_gap:=cap_zmin-maxf(boxes[0].end.z,boxes[1].end.z)
	for c in carry.paid_crowns:
		if c.get_parent()!=carry or not c.scale.is_equal_approx(Vector3.ONE):
			return false
		ids.append(c.get_instance_id())
		marks.append({"name":c.name,"local":pt(c.position),"world":pt(c.global_position),"surface0":c.get_active_material(0).resource_name,"surface1":c.get_active_material(1).resource_name})
	print("CROWN_SAMPLE ",JSON.stringify({"label":label,"actor_back_separating_plane_gap_m":actor_gap,"pair_plan_z_separation_m":pair_gap,"stock_on_real_actor":marks,"tick":tick_count,"anim":anim.current_animation,"anim_t":anim.current_animation_position,"actor_yaw":game.actor.rotation.y,"actor_world":pt(game.actor.global_position),"mesh_count":bodies,"capsule_back_plane_gap_m":cap_gap,"actor_speed":game.actor.velocity.length()}))
	return ids==stable_ids and actor_gap>0.001 and pair_gap>=.001

var sampled_run := 0
var thresholds := [.12,.25,.40,.55]
var stock_snapshot :PackedByteArray

func tick(n:int) -> void:
	if not watch_motion:
		await super.tick(n)
		return
	for i in range(n):
		await super.tick(1)
		var anim:AnimationPlayer=game.hero_locomotion.player
		if sampled_run < thresholds.size() and game.actor.velocity.length()>0.65 and game.actor.is_on_floor() and String(anim.current_animation).get_file().to_lower()=="run" and anim.current_animation_position>=thresholds[sampled_run]:
			check(anim.current_animation_position < thresholds[sampled_run]+0.06, "ordinary advancing run threshold reached")
			check(quick_clearance("ordinary_run_phase_%d" % sampled_run), "grounded run native skin separated and same pieces")
			check(var_to_bytes(game.ledger.snapshot())==stock_snapshot,"inventory and receipt unchanged in motion")
			sampled_run+=1

func run() -> void:
	game=GAME.instantiate()
	root.add_child(game)
	if not game.bound or game.persist_requested:
		quit(2)
		return
	await tick(25)
	check(count_mount(0) and not game.wood_stock_view.payload.is_visible_in_tree(),"initial zero has no wood visual")
	check(await collect() and count_mount(0) and game.wood_stock_view.payload.is_visible_in_tree(),"prepay original all three remain baseline bundle, no candidate handover")
	check(await travel(game.point([0.,3.30])) and await travel(game.pad_anchor) and game.ledger.has_exact_paid_hearth() and game.ledger.stock.wood==0,"real receipt exact three wood")
	check(count_mount(0) and not game.wood_stock_view.payload.is_visible_in_tree(),"paid zero no wood visual")
	check(await travel(game.point([0.,2.])), "return to original inner checkpoint")
	press(KEY_E)
	await tick(70)
	check(await travel(game.point([0.,6.])), "normal exit through opened South gate")
	for k in range(2):
		for x in range(320):
			if game.resource_tree.phase=="rooted":
				break
			await tick(1)
		check(await exact_paid_cut(k), "one genuine new paid wood")
		check(count_mount(k+1) and not game.wood_stock_view.payload.is_visible_in_tree(), "typed paid publication uses exact one/two distinct candidate visuals")
		var ids:Array[int]=[]
		for c in game.wood_stock_view.paid_crowns:
			ids.append(c.get_instance_id())
		if k==0:
			stable_ids=ids
			check(ids.size()==2 and ids[0]!=ids[1],"two known stable visual IDs allocated once, second hidden")
		else:
			check(ids==stable_ids,"still same two IDs after second legitimate cut")
		if failures:
			quit(1)
			return
	var before:=var_to_bytes(game.ledger.snapshot())
	check(await travel(game.point([0.,6.])) and await travel(game.point([0.,2.])), "exact ordinary return through South")
	await tick(12)
	check(quick_clearance("paid_south_inner_still"),"same exact postpaid idle body and carry")
	stock_snapshot=before
	watch_motion=true
	check(await travel(game.point([0.,6.])), "ordinary long south leg through open gate")
	watch_motion=false
	check(sampled_run==thresholds.size(), "all four genuine run phases occurred")
	await tick(12)
	check(quick_clearance("paid_late_turn_settled"),"same stable wood IDs after movement, zero conservative crossing")
	game.sync_progress_visuals()
	check(quick_clearance("same_state_republication"),"idempotent visual republish does not detach or recreate")
	check(var_to_bytes(game.ledger.snapshot())==before,"real wood and hearth receipt remain untouched after movement/pose checks")
	print("PROBE_COUNT ",checks," failures ",failures," grounded ",grounded)
	quit(1 if failures else 0)
