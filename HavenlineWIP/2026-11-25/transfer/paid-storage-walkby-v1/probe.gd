extends "res://tests/paid_two_visual_probe.gd"
const REST := [Transform3D(Basis(Vector3(0.011456093581219007,0.007296203843363953,-0.9999077574103196),Vector3(0.874591869367374,-0.48481649811135924,0.006482684283585948),Vector3(-0.4847244783960686,-0.8745854609862402,-0.011935303730735718)),Vector3(-5.596517383444508,0.11266990300144689,5.796595472047229)),Transform3D(Basis(Vector3(0.01145536580342935,0.007294688045895884,-0.9999077768077527),Vector3(0.8746363991749855,-0.48473614322894054,0.006483878912129304),Vector3(-0.48464414144042306,-0.8746300126189614,-0.01193302952439823)),Vector3(-5.332379043071789,0.11283764523831509,5.796595202368235))]
# Read-only observation; don't instantiate either predicted receiver or log.
var phase := ""
var previous: Array[Transform3D] = []
var obs_ticks := 0
var min_cast_fraction := 1.
var obstructed := 0
var horizontal_body_contact := 0
var readouts := 0
var gate_drift := 0
var gate_angles: Array[float] = []
const CROWN_RADIUS := .235427
var transparent_test := SphereShape3D.new()

func tf(t:Transform3D) -> Array:
	return [pt(t.origin),pt(t.basis.x),pt(t.basis.y),pt(t.basis.z)]

func projected_position(world:Vector3) -> Vector2:
	# Use the actual orthographic camera's frustum. This is geometry only.
	return game.camera.unproject_position(world)

func fits(a:Rect2, b:Rect2, viewport:Rect2) -> bool:
	return a.has_area() and b.has_area() and viewport.encloses(a) and viewport.encloses(b)

func hull_gap(a:PackedVector2Array,b:PackedVector2Array) -> float:
	var best:=-INF
	for h in [a,b]:
		for k in range(h.size()-1):
			var edge:Vector2=h[k+1]-h[k]
			if edge.length_squared()<1e-12:
				continue
			var axis:=Vector2(-edge.y,edge.x).normalized()
			var amin:=INF
			var bmin:=INF
			var amax:=-INF
			var bmax:=-INF
			for f in a:
				amin=minf(amin,f.dot(axis))
				amax=maxf(amax,f.dot(axis))
			for f in b:
				bmin=minf(bmin,f.dot(axis))
				bmax=maxf(bmax,f.dot(axis))
			best=maxf(best,maxf(bmin-amax,amin-bmax))
	return best

func shape_query(at:Vector3) -> PhysicsShapeQueryParameters3D:
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = transparent_test
	q.transform = Transform3D(Basis.IDENTITY,at)
	q.exclude = [game.actor.get_rid()]
	q.collision_mask = 1
	return q

func probe_geometry() -> bool:
	var carry:Node3D=game.wood_stock_view
	var anim:AnimationPlayer=game.hero_locomotion.player
	if not count_mount(2) or not game.actor.is_on_floor():
		return false
	var visual:Node3D
	for child in game.actor.get_children():
		if child.is_ancestor_of(anim):
			visual=child
	if visual==null:
		return false
	var body := Rect2()
	var first := true
	var minz:=INF
	for m in visual.find_children("*","MeshInstance3D",true,false):
		if not m.is_visible_in_tree():
			continue
		var skel:=m.get_node_or_null(m.skeleton) as Skeleton3D
		if skel==null or m.skin==null or m.skin.get_bind_count()!=66:
			return false
		skel.force_update_all_bone_transforms()
		var mat:Array[Transform3D]=[]
		for j in range(m.skin.get_bind_count()):
			var b:=skel.find_bone(String(m.skin.get_bind_name(j))) if m.skin.get_bind_name(j)!=&"" else int(m.skin.get_bind_bone(j))
			if b<0:
				return false
			mat.append(skel.get_bone_global_pose(b)*m.skin.get_bind_pose(j))
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
						p+=(mat[ix[idx]]*vv[k])*wb[idx]
						sum+=wb[idx]
				if absf(sum-1.)>0.0002:
					return false
				var world:Vector3=m.to_global(p)
				var screen:=projected_position(world)
				if not screen.is_finite():
					return false
				body=Rect2(screen,Vector2.ZERO) if first else body.expand(screen)
				first=false
				minz=minf(minz,carry.to_local(world).z)
	if first:
		return false
	var target_screens:Array[Rect2]=[]
	var carry_rects:Array[Rect2]=[]
	var target_hulls:Array[PackedVector2Array]=[]
	var scene_rays := [0,0]
	var seen := [0,0]
	var ds:PhysicsDirectSpaceState3D=game.actor.get_world_3d().direct_space_state
	for i in range(2):
		var held:MeshInstance3D=carry.paid_crowns[i]
		var target:Transform3D=REST[i]
		var fit_target := Rect2()
		var fit_carry := Rect2()
		var points:=PackedVector2Array()
		var f := true
		for j in range(held.mesh.get_surface_count()):
			var a:Array=held.mesh.surface_get_arrays(j)
			var vv:PackedVector3Array=a[Mesh.ARRAY_VERTEX]
			for p in vv:
				var parked:=target*p
				var u:=projected_position(parked)
				var h:=projected_position(held.global_transform*p)
				points.append(u)
				fit_target=Rect2(u,Vector2.ZERO) if f else fit_target.expand(u)
				fit_carry=Rect2(h,Vector2.ZERO) if f else fit_carry.expand(h)
				f=false
				# Sample every vertex in layer-1 collider visibility alone.
				# Ray ends just before the proven visible +12mm level.
				var from:Vector3=game.camera.project_ray_origin(u)
				var toward:Vector3=from.lerp(parked,.9999)
				var rq:=PhysicsRayQueryParameters3D.create(from,toward,1,[game.actor.get_rid()])
				if not ds.intersect_ray(rq).is_empty():
					scene_rays[i]+=1
				seen[i]+=1
		target_screens.append(fit_target)
		target_hulls.append(Geometry2D.convex_hull(points))
		carry_rects.append(fit_carry)
	var viewport:Rect2=game.camera.get_viewport().get_visible_rect()
	var clear:=false
	var pair_screen_gap:=hull_gap(target_hulls[0],target_hulls[1])
	if fits(target_screens[0],target_screens[1],viewport) and pair_screen_gap>.001:
		clear=true
		for i in range(2):
			for block in [body,carry_rects[0],carry_rects[1]]:
				clear=clear and not target_screens[i].intersects(block,true)
			clear=clear and scene_rays[i]==0
	var a0:AABB=carry.paid_crowns[0].transform*carry.paid_crowns[0].get_aabb()
	var a1:AABB=carry.paid_crowns[1].transform*carry.paid_crowns[1].get_aabb()
	var g:=minz-maxf(a0.end.z,a1.end.z)
	var identities:Array[int]=[]
	for c in carry.paid_crowns:
		identities.append(c.get_instance_id())
	print("WALK_GEOM ",JSON.stringify({"tick":tick_count,"phase":phase,"world":pt(game.actor.global_position),"motion":pt(game.actor.velocity),"animation":anim.current_animation,"anim_t":anim.current_animation_position,"both_conservative_open":clear,"actor_local_back_gap_m":g,"crown_target_pair_projection_gap_native_units":pair_screen_gap,"scene_rays_blocked":scene_rays,"scene_rays_total":seen,"skin_rect":rect(body),"carry_rects":[rect(carry_rects[0]),rect(carry_rects[1])],"target_rects":[rect(target_screens[0]),rect(target_screens[1])],"viewport":rect(viewport),"camera":tf(game.camera.global_transform)}))
	readouts+=1
	return g>.001 and identities==stable_ids

func rect(r:Rect2) -> Array:
	return [r.position.x,r.position.y,r.end.x,r.end.y]

func tick(n:int) -> void:
	if phase=="":
		await super.tick(n)
		return
	for i in range(n):
		await super.tick(1)
		obs_ticks+=1
		var carrying:Node3D=game.wood_stock_view
		var curr:Array[Transform3D]=[]
		var nearest:=1.
		var unsafe:=0
		var grounded_now:bool=game.actor.is_on_floor()
		for j in range(2):
			if absf(game.gates[j].angle-gate_angles[j])>1e-6:
				gate_drift+=1
		var ds:PhysicsDirectSpaceState3D=game.actor.get_world_3d().direct_space_state
		for j in range(game.actor.get_slide_collision_count()):
			var hit:KinematicCollision3D=game.actor.get_slide_collision(j)
			if hit.get_normal().y<.5:
				horizontal_body_contact+=1
		for j in range(2):
			var cur:Transform3D=carrying.paid_crowns[j].global_transform
			curr.append(cur)
			# Sphere encloses all possible rigid orientations and any plausible
			# interpolation from endpoint mount offsets. Intermediate offsets
			# bound: r * (1-cos(theta/2)); do not conflate with engine CCD.
			var rad:= CROWN_RADIUS
			if not previous.is_empty():
				var old:Transform3D=previous[j]
				var yaw_delta := old.basis.orthonormalized().get_rotation_quaternion().angle_to(cur.basis.orthonormalized().get_rotation_quaternion())
				var leaf_r:float=carrying.paid_crowns[j].position.length()
				rad += leaf_r * (1.-cos(.5*yaw_delta))+.00002
			transparent_test.radius=rad
			var q:=shape_query(cur.origin)
			if not ds.intersect_shape(q,8).is_empty():
				unsafe+=1
			if not previous.is_empty():
				q=shape_query(previous[j].origin)
				if not ds.intersect_shape(q,8).is_empty():
					unsafe+=1
				q.motion=cur.origin-previous[j].origin
				if q.motion.length_squared()>1e-10:
					var cast:=ds.cast_motion(q)
					if cast.size()!=2:
						unsafe+=1
					else:
						nearest=minf(nearest,cast[0])
		previous=curr
		min_cast_fraction=minf(min_cast_fraction,nearest)
		if not grounded_now or unsafe>0 or nearest<.99998:
			obstructed+=1
			print("WALK_OBSTRUCTION ",JSON.stringify({"tick":tick_count,"phase":phase,"unsafe":unsafe,"fraction":nearest,"grounded":grounded_now,"world":pt(game.actor.global_position)}))
		if obs_ticks%6==1:
			if not probe_geometry():
				check(false,"native geometry sample validity")

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

	check(not game.camp_built.has_node("StorageReceiver") and game.ledger.stock.wood==2,"display-only trial has no storage receiver or new stock")
	var opening_south:Vector3=game.actor.global_position
	var south_gate=game.gates[0]
	var east_gate=game.gates[1]
	check(south_gate.target_open and not east_gate.target_open,"existing South open and East closed")
	gate_angles=[float(south_gate.angle),float(east_gate.angle)]
	phase="south_inbound"
	check(probe_geometry(),"baseline settled paired source/camera")
	check(await travel(game.point([-1.60,2.25])),"ordinary westward clearance leg")
	phase="near_edge_approach"
	check(await travel(game.point([-2.875,1.15])),"ordinary approach into diagnostic near-side window")
	check(probe_geometry(),"native arrived near edge camera sample")
	phase="along_west_departure"
	check(await travel(game.point([-3.30,.20])),"ordinary departure along west flank")
	check(probe_geometry(),"native west flank camera sample")
	phase="return_south"
	check(await travel(game.point([-1.60,2.25])) and await travel(game.point([0.,2.])),"ordinary safe corridor departure back to existing South waypoint")
	check(probe_geometry(),"non-spawned target view after route")
	phase=""
	check(game.actor.global_position.distance_to(opening_south)<.075,"landed back at original South point")
	check(obstructed==0 and horizontal_body_contact==0 and obs_ticks>30 and readouts>8 and gate_drift==0,"grounding, body slide normals and continuously swept conservative carry terrain/walls/leaves guards")
	check(var_to_bytes(game.ledger.snapshot())==before and count_mount(2) and south_gate.target_open and not east_gate.target_open,"unchanged native paid ledger/two carried pieces/gates; no delivery")
	print("WALK_SUM ",JSON.stringify({"checks":checks,"failures":failures,"ticks":obs_ticks,"camera_geometric_samples":readouts,"min_carry_cast_fraction":min_cast_fraction,"obstructed_ticks":obstructed,"body_horizontal_contacts":horizontal_body_contact,"gate_angle_drift_frames":gate_drift,"gate_angles":gate_angles}))
	quit(1 if failures else 0)
