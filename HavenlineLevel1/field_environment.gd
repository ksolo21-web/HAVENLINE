extends Node3D

const CENTERS := {"wood":Vector2(-3.2,-2.1), "stone":Vector2(-3.2,.65), "meat":Vector2(2.8,-2.1)}
const BUY := Vector2(0,2.4)
const UPGRADE := Vector2(2.65,1.7)
const FILL := preload("res://assets/field_camp/payment_fill.gdshader")
const DONOR := "res://assets/field_camp/"
const PLATE := preload("res://assets/field_camp/wood_storage_empty.glb")
const PANEL := preload("res://assets/field_camp/opening_fence_panel.obj")
const DOOR := preload("res://assets/field_camp/opening_gate_leaf.obj")
const POST := preload("res://assets/field_camp/gate_post.obj")
const HEARTH := preload("res://assets/field_camp/furnace.glb")
const SNOW := preload("res://assets/field_camp/field_snow.gdshader")
const TIMBER := preload("res://assets/field_camp/t03_boundary_v2.gdshader")
const GRAIN := preload("res://assets/field_camp/opening_wood_grain.png")
const STOCK_PAINT := {"stone":preload("res://assets/field_camp/stone_storage.png"), "meat":preload("res://assets/field_camp/meat_storage.png")}
var world
var buy_anchor := Node3D.new()
var upgrade_anchor := Node3D.new()
var upgrade_label: Label3D
var upgrade_pending := true
var payment_ink := {}
const STOCKED_PAINT := preload("res://assets/field_camp/stocked_plot_paint.png")
var stock_anchors := {}
var stock_surfaces := {}
var empty_stock_paint := {}
var count_labels := {}
var payment_label: Label3D
var camp_state := -1
var palette := {}
var canopy_materials := {}
var seasonal_pines: Array[Node3D] = []
# Trees on the future storage ground merge with the permanent north/west woodline.
const SEASONAL_POCKETS := [
	Vector2(-4.8,-3.7), Vector2(-3.0,-3.55), Vector2(-1.25,-3.68), Vector2(.65,-3.55), Vector2(2.55,-3.68),
	Vector2(-4.75,-1.94), Vector2(-3.18,-1.77), Vector2(-1.36,-2.11), Vector2(.40,-2.04), Vector2(2.05,-2.14),
	Vector2(-4.5,-.19), Vector2(-2.9,-.27), Vector2(-1.1,-.53), Vector2(.80,-.73),
	Vector2(-4.29,1.49), Vector2(-2.55,1.19),
]
# Five west-grove pines border the quarry work area. Their roots previously
# landed on the stone or in front of its pick contact from the fixed camera.
const QUARRY_EDGE := [
	Vector2(-10.97,.76), Vector2(-9.45,6.79), Vector2(-10.55,-.68),
	Vector2(-12.93,1.01), Vector2(-10.08,1.91)
]
var snow := ShaderMaterial.new()
var reveal_tween: Tween
const StockLayout = preload("res://field_stock_layout.gd")

func receiver_position(kind: String) -> Vector2:
	return UPGRADE if kind == "upgrade" else CENTERS.get(kind, BUY)

func landing_position(kind: String, index: int) -> Vector3:
	var base: Node3D = stock_anchors[kind]
	return base.to_global(StockLayout.position(kind,index))

func install(host: Node3D) -> void:
	world = host
	name = "SettledFieldEnvironment"
	if get_parent() == null: world.add_child(self)
	var snow_mesh: MeshInstance3D = world.get_node("SnowGround_NoPaintedPaths").find_children("*","MeshInstance3D", false, false)[0]
	# The inherited private collider remains 40m across. Extend its visual
	# surface beyond the corners of either camera orientation without adding travel.
	var snow_box := snow_mesh.mesh as BoxMesh
	if snow_box: snow_box.size = Vector3(120.,snow_box.size.y,120.)
	snow.shader = SNOW
	snow_mesh.material_override = snow
	world.camp_built.get_node("CampOnlySurface").hide()
	for child in world.camp_built.get_children():
		if "technical-marker" in str(child.name): child.hide()
	install_walls()
	install_hearth()
	install_woods.call_deferred()
	for kind: String in CENTERS:
		install_plot(kind)
	install_payment(buy_anchor,false)
	install_payment(upgrade_anchor,true)
	set_built(not world.ledger.receipt.is_empty(),false)

func donor_mesh(source: Mesh) -> MeshInstance3D:
	var vis := MeshInstance3D.new()
	vis.mesh = source
	for i in source.get_surface_count():
		var code := String(source.surface_get_name(i)).to_lower()
		var imported := source.surface_get_material(i)
		if imported and not imported.resource_name.is_empty(): code = imported.resource_name.to_lower()
		if not palette.has(code):
			var ink := ShaderMaterial.new()
			ink.shader = TIMBER
			var colors := {"timber_dark":"795b41","snow":"e8f2f6","blue":"455966","rope":"cfb894","timber":"ffffff"}
			ink.set_shader_parameter("base_color",Color(colors.get(code,"85614a")))
			ink.set_shader_parameter("detail_strength",.012)
			if code in ["timber","timber_dark"]:
				ink.set_shader_parameter("ground_bounce",.35)
			if code == "timber":
				ink.set_shader_parameter("use_reference_grain",true)
				ink.set_shader_parameter("reference_grain",GRAIN)
			palette[code] = ink
		vis.set_surface_override_material(i,palette[code])
	return vis

func install_walls() -> void:
	for i in world.layout.walls_xz.size():
		var row: Array = world.layout.walls_xz[i]
		var body: StaticBody3D = world.camp_colliders[i]
		body.get_child(0).hide()
		var along_x := float(row[2]) > float(row[3])
		var run := maxf(row[2], row[3])
		var n := maxi(1, roundi(run / 2.6))
		for j in n:
			var vis := donor_mesh(PANEL)
			body.add_child(vis)
			var along := run*((j+.5)/n-.5)
			vis.position = Vector3(along if along_x else 0.,-.49,0. if along_x else along)
			vis.rotation.y = 0. if along_x else PI*.5
			vis.scale = Vector3((run/n+.018)/2.94,.92,1.62)
	for gate in world.gates:
		for i in 2:
			var leaf: AnimatableBody3D = gate._leaf_bodies[i]
			for child in leaf.get_children():
				if child is MeshInstance3D: child.hide()
			var vis := donor_mesh(DOOR)
			leaf.add_child(vis)
			vis.position.y = -.5
			vis.scale = Vector3(gate.LEAF_LENGTH/2.9,.93,1.15)
			var post := donor_mesh(POST)
			gate.add_child(post)
			var sign_x := -1 if i==0 else 1
			post.position = Vector3(sign_x*(gate.HALF_SPAN+.15),-.045,0)
			post.scale = Vector3(.96,.9,.96)

func install_hearth() -> void:
	var base: Node3D = world.camp_built.get_node("CenteredHearth_StudioTrialOnly")
	for child in base.get_children():
		if not child is StaticBody3D: child.hide()
	var shell: Node3D = world.model(HEARTH,base,2.25)
	shell.name = "RecoveredStoneFurnace"
	var fire := OmniLight3D.new()
	fire.name = "CoalGlow"
	fire.light_color = Color("ffa457")
	fire.light_energy = .62
	fire.omni_range = 3.15
	fire.position = Vector3(0,.60,.8)
	base.add_child(fire)
	for m: MeshInstance3D in shell.find_children("*","MeshInstance3D",true,false):
		m.layers = 2
	fire.light_cull_mask = 1
	for body in base.get_children():
		if body is StaticBody3D:
			var shape: CollisionShape3D = body.get_child(0)
			var cylinder := shape.shape as CylinderShape3D
			cylinder.radius = 1.14

func canopy_ink(material: Material) -> Material:
	if not material is StandardMaterial3D or material.resource_name.to_lower() not in ["crown","lip"]:
		return material
	if not canopy_materials.has(material):
		var shaded := material.duplicate() as StandardMaterial3D
		shaded.emission_enabled = true
		shaded.emission = Color("637aa5")
		shaded.emission_energy_multiplier = .40
		# Uniform local skylight also reaches atlas-dark blue branch undersides.
		shaded.emission_texture = null
		shaded.emission_operator = BaseMaterial3D.EMISSION_OP_ADD
		canopy_materials[material] = shaded
	return canopy_materials[material]

func tint_canopy(node:Node3D) -> void:
	var parts: Array[MeshInstance3D] = []
	world.meshes(node,parts)
	for part in parts:
		for i in part.mesh.get_surface_count():
			var material := part.get_active_material(i)
			var shaded := canopy_ink(material)
			if material != shaded: part.set_surface_override_material(i,shaded)

func install_woods() -> void:
	var parent := Node3D.new()
	parent.name = "PeripheralSnowForest"
	world.add_child(parent)
	# Place trees in irregular groves, leaving the active approach and both gate corridors open.
	var positions := [Vector2(-13,3),Vector2(-15,1),Vector2(-12,-1.4),Vector2(-11.7,-5.4),Vector2(-9.7,-7.2),
		Vector2(-7.5,-9.5),Vector2(-5.7,-10.4),Vector2(-2.4,-10.8),Vector2(.4,-12.3),Vector2(3.1,-10.6),
		Vector2(6.2,-11.1),Vector2(9.2,-10.2),Vector2(11.4,-8.6),Vector2(14.8,-7.8),
		Vector2(-15,5.5),Vector2(-17,8.2),Vector2(-14.4,11.2),Vector2(-12,14),Vector2(-15,14.2),
		Vector2(-7.0,2.65),Vector2(-8.4,4.8),Vector2(-7.0,7.45),Vector2(-9.4,8.5),
		Vector2(-10.4,4.7),Vector2(-9.9,11.1),Vector2(-7.5,12.5),Vector2(-6.2,14.6),
		Vector2(7.8,-6.0),Vector2(9.55,-4.9),Vector2(11.6,-4.0),Vector2(13.4,-3.5),
		Vector2(9.8,3.95),Vector2(11.6,5.45),Vector2(12.45,7.85),Vector2(14.5,8.2),
		Vector2(10.9,10.1),Vector2(13.15,10.3),Vector2(14.1,12.25),Vector2(16.1,11.4)]
	# Two interlocking tree lines meet around the northwest corner. Three
	# staggered rows frame the portrait horizon and the paid rear wall.
	for row in 3:
		for column in 13:
			var x := -13.4 + column * 1.58 + (row % 2) * .73
			var z := -5.3 - row * 1.32 + sin(column*1.41+row)*.27
			positions.append(Vector2(x,z))
		for column in 8:
			var x := -6.15 - row*1.32 + sin(column*1.7+row)*.22
			var z := -4.25 + column*1.58 + (row % 2)*.67
			positions.append(Vector2(x,z))
	for column in 8:
		# Beyond the active woods and wolves, fill the near corners on tall screens.
		positions.append(Vector2(2.5+column*1.45,21.2+sin(column)*.45))
		positions.append(Vector2(14.8+sin(column*1.42)*.5,10.2+column*1.5))
	# Smaller companion crowns break up evenly spaced silhouettes. The actual
	# harvest and enemy anchors are set by the world before this deferred pass.
	tint_canopy(world.get_node("ExteriorExactT01Visuals"))
	if camp_state == 0 and world.has_method("_add_pine"):
		for i in SEASONAL_POCKETS.size():
			var stem: Node3D = world._add_pine(SEASONAL_POCKETS[i])
			stem.scale = Vector3.ONE*(1.05 + .20*fposmod(i*.618,1))
			stem.rotation.y = i*2.39996
			seasonal_pines.append(stem)
	var blocked: Array[Vector2] = []
	if "trees" in world:
		for tree: Node3D in world.trees:
			tint_canopy(tree)
			blocked.append(Vector2(tree.position.x,tree.position.z))
	if "enemies" in world:
		for enemy: Node3D in world.enemies:
			blocked.append(Vector2(enemy.position.x,enemy.position.z))
	var transforms := [[],[],[]]
	var occupied: Array[Vector2] = []
	var initial := positions.size()
	var quarry_tree := 0
	for i in 32:
		var offset := Vector2(1.35,0).rotated(2.39996*i)
		var candidate: Vector2 = positions[i]+offset
		if absf(candidate.x)>7.5 or candidate.y < -7.: positions.append(candidate)
	for i in positions.size():
		var at: Vector2 = positions[i]
		if blocked.any(func(p:Vector2): return p.distance_squared_to(at) < 3.2) or occupied.any(func(p:Vector2): return p.distance_squared_to(at) < 1.25):
			continue
		occupied.append(at)
		# Keep the accepted grove count and mesh variants. The clearing applies
		# to this occupied quarry, leaving the broader woodline intact.
		if at.distance_squared_to(Vector2(-6,3)) < 2.4*2.4 and quarry_tree < QUARRY_EDGE.size():
			at = QUARRY_EDGE[quarry_tree]
			quarry_tree += 1
		var scale_factor := (.72+.19*fposmod(i*.618,1)) if i<initial else (.48+.19*fposmod(i*.414,1))
		var basis := Basis(Vector3.UP,i*2.39996).scaled(Vector3.ONE*scale_factor)
		transforms[i%3].append(Transform3D(basis,Vector3(at.x,0,at.y)))
	for variant in 3:
		var tree: Node3D = world.CONIFERS[variant].instantiate()
		var parts: Array[MeshInstance3D] = []
		world.meshes(tree,parts)
		for part in parts:
			var multi := MultiMesh.new()
			multi.transform_format = MultiMesh.TRANSFORM_3D
			var lit_mesh := part.mesh.duplicate() as Mesh
			for i in lit_mesh.get_surface_count(): lit_mesh.surface_set_material(i,canopy_ink(part.get_active_material(i)))
			multi.mesh = lit_mesh
			multi.instance_count = transforms[variant].size()
			for i in multi.instance_count: multi.set_instance_transform(i,transforms[variant][i]*part.transform)
			var grove := MultiMeshInstance3D.new()
			grove.multimesh = multi
			grove.set_meta("tree_variant",variant)
			grove.set_meta("tree_placements",transforms[variant])
			parent.add_child(grove)
		tree.free()

func flat_label(parent:Node3D, at:Vector3, px:float) -> Label3D:
	var label := Label3D.new()
	label.position = at
	label.rotation.x = -PI/2
	label.font_size = 48
	label.pixel_size = px
	label.outline_size = 9
	label.modulate = Color("fff5db")
	label.outline_modulate = Color("332824")
	label.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(label)
	return label

func install_plot(kind: String) -> void:
	var center: Vector2 = CENTERS[kind]
	var anchor := Node3D.new()
	anchor.name = kind.capitalize()+"StoragePlot"
	anchor.position = Vector3(center.x,.005,center.y)
	world.camp_built.add_child(anchor)
	stock_anchors[kind] = anchor
	var deck := PLATE.instantiate() as Node3D
	anchor.add_child(deck)
	var meshes: Array[MeshInstance3D] = []
	world.meshes(deck,meshes)
	stock_surfaces[kind] = []
	for geometry in meshes:
		for i in geometry.mesh.get_surface_count():
			var mat := geometry.get_active_material(i) as StandardMaterial3D
			if mat and mat.albedo_texture:
				var local := mat.duplicate() as StandardMaterial3D
				var type_paint: Texture2D = STOCK_PAINT.get(kind,mat.albedo_texture)
				local.albedo_texture = type_paint
				local.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				geometry.set_surface_override_material(i,local)
				stock_surfaces[kind].append([geometry,i])
				empty_stock_paint[kind] = type_paint
	var label := flat_label(anchor,Vector3(0,.005,.79),.0068)
	label.text = "0"
	count_labels[kind] = label

func install_payment(anchor:Node3D, upgrade:bool) -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DONOR+"build_inlay.json"))
	anchor.name = "OrbitUpgradeFloor" if upgrade else "ConstructionPaymentFloor"
	add_child(anchor)
	var at := UPGRADE if upgrade else BUY
	anchor.position = Vector3(at.x,.008,at.y)
	if upgrade: anchor.scale = Vector3(.84,1.,.84)
	for role in (["gray","brackets"] if upgrade else ["gray","brackets","castle"]):
		var brush := SurfaceTool.new()
		brush.begin(Mesh.PRIMITIVE_TRIANGLES)
		var layer := 0. if role=="gray" else .002
		for p in data.vertices[role]:
			brush.set_normal(Vector3.UP)
			brush.add_vertex(Vector3(float(p[0])*2.64,layer,-float(p[2])*2.18))
		var ink := StandardMaterial3D.new()
		ink.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ink.cull_mode = BaseMaterial3D.CULL_DISABLED
		ink.albedo_color = Color({"gray":"51bd37","brackets":"78df59","castle":"fff3d5"}[role])
		var mark := MeshInstance3D.new()
		mark.name = role.capitalize()
		mark.mesh = brush.commit()
		if role=="gray":
			var fill := ShaderMaterial.new()
			fill.shader = FILL
			fill.set_shader_parameter("grounded",Color("69727a") if not upgrade else Color("5d5147"))
			fill.set_shader_parameter("funded",Color("3bc615"))
			payment_ink["upgrade" if upgrade else "buy"] = fill
			mark.material_override = fill
		else:
			ink.albedo_color = Color("e9e4cb") if upgrade else ink.albedo_color
			mark.material_override = ink
		mark.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		anchor.add_child(mark)
	if upgrade:
		var icon := Sprite3D.new()
		icon.texture = preload("res://assets/field_camp/orbit_upgrade.svg")
		icon.axis = Vector3.AXIS_Y
		icon.pixel_size = .005
		icon.position = Vector3(0,.006,-.24)
		icon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		anchor.add_child(icon)
		upgrade_label = flat_label(anchor,Vector3(0,.007,.53),.0068)
		upgrade_label.text = "Stone  2    Meat  1"
	else:
		payment_label = flat_label(anchor,Vector3(0,.007,.57),.0068)
		payment_label.text = "Wood  3"

func set_payment(remaining: Dictionary) -> void:
	var caption := PackedStringArray()
	for kind in ["wood","stone","meat"]:
		if remaining.has(kind):
			caption.append("%s  %d" % [kind.capitalize(),remaining[kind]])
	payment_label.text = "    ".join(caption)

func set_payment_progress(fraction:float, receiver: String = "buy") -> void:
	if payment_ink.has(receiver): payment_ink[receiver].set_shader_parameter("paid",clampf(fraction,0,1))

func set_upgrade_payment(remaining: Dictionary) -> void:
	var stone := int(remaining.get("stone",0))
	var meat := int(remaining.get("meat",0))
	upgrade_pending = stone + meat > 0
	upgrade_label.text = "Stone  %d    Meat  %d" % [stone,meat]
	upgrade_anchor.visible = camp_state == 1 and upgrade_pending

func sync_stock(counts: Dictionary) -> void:
	for kind in count_labels:
		var count := int(counts.get(kind,0))
		count_labels[kind].text = str(count)
		var paint: Texture2D = STOCKED_PAINT if count > 0 else empty_stock_paint[kind]
		# Ultra replaces textured materials when the scene node enters the tree.
		# Resolve the material currently bound to the visible surface on each change.
		for surface: Array in stock_surfaces[kind]:
			var geometry: MeshInstance3D = surface[0]
			var ink := geometry.get_active_material(surface[1]) as StandardMaterial3D
			if ink.albedo_texture != paint:
				ink.albedo_texture = paint

func set_built(built: bool, animate := true) -> void:
	if camp_state == int(built): return
	camp_state = int(built)
	if built:
		for tree in seasonal_pines:
			world.retire_tree(tree,animate)
		seasonal_pines.clear()
	world.purchase_pad_view.hide()
	buy_anchor.visible = not built
	upgrade_anchor.visible = built and upgrade_pending
	if reveal_tween: reveal_tween.kill()
	if built and animate:
		reveal_tween = create_tween().set_parallel(true)
		reveal_tween.tween_method(func(t:float): snow.set_shader_parameter("reveal",t),0.,1.,.3)
		for plot in stock_anchors.values():
			plot.scale = Vector3(.88,1.,.88)
			reveal_tween.tween_property(plot,"scale",Vector3.ONE,.3).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	else:
		snow.set_shader_parameter("reveal",1. if built else 0.)
