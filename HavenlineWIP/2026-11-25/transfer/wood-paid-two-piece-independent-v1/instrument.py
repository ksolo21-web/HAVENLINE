from pathlib import Path
p=Path('project/tests/paid_two_visual_probe.gd')
s=p.read_text().replace('\t\tskel.force_update_all_bone_transforms()\n','')
s=s.replace('var marks:= []','''var marks:= []
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
	var cap_gap:=cap_zmin-maxf(boxes[0].end.z,boxes[1].end.z)''')
s=s.replace('\t\tids.append(c.get_instance_id())\n\t\tmarks.append', '\t\tif c.get_parent()!=carry or not c.scale.is_equal_approx(Vector3.ONE):\n\t\t\treturn false\n\t\tids.append(c.get_instance_id())\n\t\tmarks.append',1)
s=s.replace('"mesh_count":bodies','"mesh_count":bodies,"capsule_back_plane_gap_m":cap_gap,"actor_speed":game.actor.velocity.length()')
s=s.replace('func tick(n:int) -> void:', 'var sampled_run := 0\nvar thresholds := [.12,.25,.40,.55]\nvar stock_snapshot :PackedByteArray\n\nfunc tick(n:int) -> void:')
a=s.index('\t\tif not got_motion')
b=s.index('\nfunc run()',a)
s=s[:a]+'''		var anim:AnimationPlayer=game.hero_locomotion.player
		if sampled_run < thresholds.size() and game.actor.velocity.length()>0.65 and game.actor.is_on_floor() and String(anim.current_animation).get_file().to_lower()=="run" and anim.current_animation_position>=thresholds[sampled_run]:
			check(anim.current_animation_position < thresholds[sampled_run]+0.06, "ordinary advancing run threshold reached")
			check(quick_clearance("ordinary_run_phase_%d" % sampled_run), "grounded run native skin separated and same pieces")
			check(var_to_bytes(game.ledger.snapshot())==stock_snapshot,"inventory and receipt unchanged in motion")
			sampled_run+=1
'''+s[b:]
s=s.replace('watch_motion=true\n\tcheck(await travel(game.point([-.40,1.72]),14), "old exact ordinary turn/near stance")','stock_snapshot=before\n\twatch_motion=true\n\tcheck(await travel(game.point([0.,6.])), "ordinary long south leg through open gate")')
s=s.replace('check(got_motion, "a real moving sample occurred")','check(sampled_run==thresholds.size(), "all four genuine run phases occurred")')
p.write_text(s)
