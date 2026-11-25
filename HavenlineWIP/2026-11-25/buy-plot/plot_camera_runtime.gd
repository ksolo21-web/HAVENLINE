extends "res://tests/test_integrated_opening.gd"
const AUTH = preload("res://previews/construction_plot_ground.gd")
const CANONICAL = preload("res://opening.tscn")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.size = Vector2i(1280,720)
	await process_frame
	game = GAME.instantiate()
	game.position = Vector3(2.0,1.1,-3.0)
	root.add_child(game)
	await tick(10)
	var pad = game.purchase_pad_view
	check(game.bound and pad.binding_ready, "exact offered anchor and translated preview")
	var marker := pad.scene_view.get_node_or_null("ReferenceConstructionPlot") as MeshInstance3D
	check(marker != null and marker.is_visible_in_tree(), "one reference construction surface visible at spawn")
	if marker == null:
		quit(1)
		return
	var action := pad.scene_view.get_node("Action") as Label3D
	var cost := pad.scene_view.get_node("Cost") as Label3D
	check(not action.is_visible_in_tree() and not cost.is_visible_in_tree() and pad.scene_view.find_children("*","CanvasItem",true,false).is_empty(),"offer has no floating text, billboard, tether or clickable control")
	var visible_meshes := 0
	for mesh: MeshInstance3D in pad.find_children("*","MeshInstance3D",true,false):
		if mesh.is_visible_in_tree():
			visible_meshes += 1
	check(visible_meshes == 1, "archived V5 hidden in preview; production marker only")
	check(AUTH.build(game.pad_anchor, 4) == null, "unknown price cannot show or authorize stale art")
	check(pad.global_position.is_equal_approx(game.to_global(game.pad_anchor)) and pad.find_children("*","CollisionObject3D",true,false).is_empty(), "same logical anchor without a collision or pedestal")
	check(game.opening_hud.prompt.text.count("3 wood") == 1 and game.opening_hud.get_child_count() == 5,"one affordability cue in the existing objective, no additional widget")
	var arrays := marker.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
	var clearance_error := 0.0
	var uv_error := 0.0
	for i in range(0,verts.size(),3):
		var triangle: Array[Vector3] = [verts[i],verts[i+1],verts[i+2],(verts[i]+verts[i+1]+verts[i+2])/3.0,(verts[i]+verts[i+1])/2.0]
		for vertex in triangle:
			var point: Vector3 = game.to_local(marker.to_global(vertex))
			var sample := Terrain.sample(Vector2(point.x,point.z))
			clearance_error = maxf(clearance_error, absf(point.y - float(sample.height) - AUTH.FLUSH_GAP))
		var expected := (Vector2(verts[i].x,verts[i].z)+Vector2.ONE*AUTH.FIELD*.5)/AUTH.FIELD
		uv_error = maxf(uv_error,expected.distance_to(uvs[i]))
	check(clearance_error < .00001 and uv_error < .00001 and verts.size() > 30 and verts.size() < 1600 and is_equal_approx(AUTH.FIELD,1.40),"aligned indexed terrain faces, flush to 9 mm without misplaced art")
	var image: Image = marker.material_override.albedo_texture.get_image()
	check(image.get_pixel(0,0).a < .01 and image.get_pixel(16,45).r > .9 and image.get_pixel(5,120).a > .9 and image.get_pixel(130,111).a > .9,"texture has rounded edge, bracket and continuous neutral face")
	check(marker.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF,"no extrusion or falsely suspended shadow")
	print("terrain clearance max err=",clearance_error,"; UV err=",uv_error,"; triangles=",verts.size()/3)
	for dims in [Vector2i(1280,720),Vector2i(844,390),Vector2i(640,360),Vector2i(390,844)]:
		root.size = dims
		await process_frame
		await process_frame
		var card := _screen_rect(marker,[Vector2(3,3),Vector2(253,3),Vector2(3,253),Vector2(253,253)])
		var digit := _screen_rect(marker,[Vector2(148,169),Vector2(199,169),Vector2(148,232),Vector2(199,232)])
		var approx_cap := _screen_rect(marker,[Vector2(171,169),Vector2(171,232)]).size.y
		var final := root.get_final_transform()
		var objective: Rect2 = final * game.opening_hud.plate.get_global_rect()
		var label := game.opening_hud.prompt as Label
		var font := label.get_theme_font("font")
		var logical_font := label.get_theme_font_size("font_size")
		var ts := TextServerManager.get_primary_interface()
		var rid := font.get_rids()[0]
		var glyph := ts.font_get_glyph_index(rid,logical_font,"H".unicode_at(0),0)
		ts.font_render_glyph(rid,Vector2i(logical_font,0),glyph)
		var physical_cap := float(ts.font_get_glyph_size(rid,Vector2i(logical_font,0),glyph).y)*final.get_scale().y
		check(Rect2(Vector2.ZERO,Vector2(dims)).encloses(card) and digit.size.y > 2.0 and not objective.intersects(card) and physical_cap >= 12.0,"ground offer inside output and legible objective does not overlap it at "+str(dims))
		print("objective physical glyph cap ",dims," ",physical_cap," HUD=",objective)
		print("projection ",dims," face=",card.size," glyph bounds=",digit.size," cap centerline px=",approx_cap)
	root.size = Vector2i(1280,720)
	await process_frame
	var outside: Vector3 = game.pad_anchor + Vector3(-.58,0,.58)
	check(await travel(outside), "real movement reaches visible near-diagonal plot but outside payable circle")
	check(not game._within_logical_reach(game.pad_anchor,.72) and marker.is_visible_in_tree(),"oversized graphic is not purchase authorization")
	for source_id in ["wood-a","wood-b","wood-c"]:
		check(game._collect_wood_source(source_id),"seed exact fixture source "+source_id)
	await tick(4)
	check(game.ledger.stock.wood == 3 and game.ledger.receipt.is_empty() and not game.camp_built.visible and marker.is_visible_in_tree(),"fully funded outside .72 does not debit or grant")
	check(not game.fund_opening_receiver("wrong receiver","wood"),"noncanonical receiver denied")
	check(await travel(game.pad_anchor),"normal movement reaches preserved payable center")
	await tick(4)
	check(game.ledger.stock.wood == 0 and not game.ledger.receipt.is_empty() and game.camp_built.visible and not marker.is_visible_in_tree(),"single real proximity receipt hides every plot pixel")
	check(not game.opening_hud.prompt.text.contains("3 wood") and not game.opening_hud.plot_cost_accessible,"paid receipt removes truthful affordability cue")
	var paid := var_to_bytes(game.ledger.snapshot())
	await tick(15)
	check(paid == var_to_bytes(game.ledger.snapshot()),"staying on paid site never re-debits")
	var canonical = CANONICAL.instantiate()
	root.add_child(canonical)
	canonical.set_physics_process(false)
	check(canonical.purchase_pad_view.binding_ready and canonical.purchase_pad_view.scene_view.get_node_or_null("ReferenceConstructionPlot") == null and canonical.purchase_pad_view.scene_view.get_node("Action").is_visible_in_tree(),"default launch still uses original studio view")
	print("reference plot checks=",checks," failures=",failures)
	quit(1 if failures else 0)

func _screen_rect(marker: MeshInstance3D, pixels: Array) -> Rect2:
	var rect := Rect2()
	var first := true
	for px: Vector2 in pixels:
		var local: Vector2 = (px/256.0-Vector2.ONE*.5)*AUTH.FIELD
		var terrain_xz := Vector2(game.pad_anchor.x,game.pad_anchor.z)+local
		var h: float = Terrain.sample(terrain_xz).height
		var global := marker.to_global(Vector3(local.x,h-game.pad_anchor.y+AUTH.FLUSH_GAP,local.y))
		var pixel: Vector2 = root.get_final_transform()*game.camera.unproject_position(global)
		rect = Rect2(pixel,Vector2.ZERO) if first else rect.expand(pixel)
		first = false
	return rect
