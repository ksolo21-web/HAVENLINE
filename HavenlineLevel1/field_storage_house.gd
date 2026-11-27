extends Node3D
## Visual and physical shell of the shared storehouse. Inventory owns physical
## contents and counts; its displays use these same shelf coordinates.
signal door_motion(opening:bool, at:Vector3)

const SHELL := preload("res://assets/storage_house/camp_storehouse.glb")
const CONNECTIONS := preload("res://assets/storage_house/connected_storehouse.glb")
const HATCH_SHADER:=preload("res://assets/storage_house/loading_hatches.gdshader")
const PLACARD_SHADER:=preload("res://assets/storage_house/loading_placard.gdshader")
const HATCH_WALLS:=["LeftWall","RightWall","BackWall","LeftArmor","RightArmor","BackArmor","RightDetail"]
const BAYS := {"wood":Vector3(-1.15,.763,.25),"stone":Vector3(-1.15,.763,-.56),"meat":Vector3(0,.772,-.92),
	"coal":Vector3(1.15,.763,.25),"slate":Vector3(-.68,.772,-.92),"metal":Vector3(.68,.772,-.92)}
# Keep balances above each bay header, clear of the stock, rims and sliding leaves.
const LABELS := {"wood":Vector3(-1.10,1.52,.66),"stone":Vector3(-1.09,1.52,-.36),"meat":Vector3(0,1.60,-.73),
	"coal":Vector3(.89,1.52,.68),"slate":Vector3(-.68,1.60,-.73),"metal":Vector3(.68,1.60,-.73)}
const ROOF := ["Roof","Gables","Signs"]
const CUTAWAY := ["Track","RightWall","Facade","DoorLeft","DoorRight","WholeRightPost"]
const TIERS := ["starter","reinforced","advanced"]
var actor: Node3D
var model: Node3D
var tier := 0
var open_amount := 0.0
var inside_view := false
var doors_open := false
var collision: StaticBody3D
var parts := {}
var shelves: Array[Label3D] = []
var last_stock := {}
var last_tier := -1
var rear_occlusion := false
var last_rear_occlusion := false
var last_roof_visible := false
var last_cutaway := false
var last_slide := -1.0
var connections_paid := false
var connection_roof: Node3D
var dock_meshes := {}
var dock_paints := {}
var hatch_material:=ShaderMaterial.new()

func _ready() -> void:
	model=SHELL.instantiate()
	add_child(model)
	for child in model.get_children(): parts[String(child.name)]=child
	var library:Node3D=CONNECTIONS.instantiate()
	connection_roof=Node3D.new()
	connection_roof.name="ConnectedSnowRoof"
	model.add_child(connection_roof)
	for mesh_part in library.get_children():
		if mesh_part.name in [&"ConnectedRoof",&"RearVent",&"SnowAndRoof"]:
			mesh_part.owner=null
			library.remove_child(mesh_part)
			connection_roof.add_child(mesh_part)
		elif mesh_part is MeshInstance3D:
			var id:=String(mesh_part.name)
			dock_meshes[id]=mesh_part.mesh
			var original:StandardMaterial3D=mesh_part.mesh.surface_get_material(0)
			var paint:=ShaderMaterial.new()
			paint.shader=PLACARD_SHADER
			paint.set_shader_parameter("original_paint",original.albedo_texture)
			dock_paints[id]=paint
	library.free()
	var paint:StandardMaterial3D=parts.BackWall.mesh.surface_get_material(0)
	hatch_material.shader=HATCH_SHADER
	hatch_material.set_shader_parameter("painted_timber",paint.albedo_texture)
	collision=StaticBody3D.new()
	collision.name="StorehouseWalls"
	add_child(collision)
	# Leave the central threshold and its apron unobstructed. Rack backs are
	# solid, protecting the aisle from clipping without sealing its doorway.
	_wall(Vector3(0,.85,-1.08),Vector3(3.05,1.70,.18))
	for side in [-1.,1.]:
		_wall(Vector3(side*1.36,.68,0),Vector3(.53,1.36,2.15))
		_wall(Vector3(side*1.18,.85,1.08),Vector3(.71,1.70,.20))
	_wall(Vector3(0,.55,-.87),Vector3(1.77,1.10,.40))
	for item in [["TIMBER",Vector3(-1.40,1.38,.524)],["STONE",Vector3(-1.39,1.38,-.486)],["SLATE",Vector3(-.68,1.38,-.756)],["FOOD",Vector3(0,1.38,-.756)],["METAL ORE",Vector3(.68,1.38,-.756)],["COAL",Vector3(1.12,1.38,.524)]]:
		var label:=Label3D.new()
		label.text=item[0]
		label.name="Bay"+String(item[0]).capitalize()
		label.position=item[1]
		label.pixel_size=.00165
		label.font_size=38
		label.outline_size=0
		label.modulate=Color("#27180f")
		label.outline_modulate=Color("#462511")
		label.billboard=BaseMaterial3D.BILLBOARD_DISABLED
		add_child(label)
		shelves.append(label)
	_apply()

func _wall(center: Vector3, size_: Vector3) -> void:
	var shape:=CollisionShape3D.new()
	var box:=BoxShape3D.new()
	box.size=size_
	shape.shape=box
	shape.position=center
	collision.add_child(shape)

func configure(player:Node3D) -> void:
	actor=player

## Each external connection is bought separately. A machine-to-counter belt
## alone does not replace the unconnected architecture on the house.
func configure_connections(lanes:Array) -> void:
	var paid:=false
	for lane in lanes:
		if lane in ["wood","stone","meat","planks","blocks","stored_meal","meal_to_store"]:
			paid=true
			break
	hatch_material.set_shader_parameter("utility_receiving","planks" in lanes or "blocks" in lanes)
	hatch_material.set_shader_parameter("utility_dispatch","wood" in lanes or "stone" in lanes)
	hatch_material.set_shader_parameter("food_receiving","meal_to_store" in lanes)
	hatch_material.set_shader_parameter("food_dispatch","stored_meal" in lanes)
	hatch_material.set_shader_parameter("cold_dispatch","meat" in lanes)
	if paid==connections_paid:return
	for key in HATCH_WALLS:
		parts[key].material_override=hatch_material if paid else null
	connections_paid=paid
	last_tier=-1
	if model:_apply()

func connection_frame(prepared_food:bool,inbound:bool=false) -> MeshInstance3D:
	var id:="FoodDockFrame" if prepared_food else "UtilityDockFrame"
	var frame:=MeshInstance3D.new()
	frame.name=id
	frame.mesh=dock_meshes[id]
	frame.material_override=dock_paints[id]
	var label:=Label3D.new()
	label.name="Direction"
	label.text="IN" if inbound else "OUT"
	label.outline_size=0
	label.pixel_size=.00146
	label.font_size=64
	label.position=Vector3(0.,.584,.074)
	label.modulate=Color("#261c13")
	label.shaded=false
	label.double_sided=true
	frame.add_child(label)
	return frame

func update_state(new_tier:int, stock:Dictionary) -> void:
	tier=clampi(new_tier,0,3)
	last_stock=stock.duplicate()
	if tier==0:
		rear_occlusion=false
		inside_view=false
		doors_open=false
		open_amount=0.
	if model: _apply()

func _physics_process(delta:float) -> void:
	if tier==0 or not is_instance_valid(actor): return
	var p:=to_local(actor.global_position)
	var was_open:=doors_open
	if doors_open:
		doors_open=absf(p.x)<2.18 and p.z> -1.44 and p.z<3.99
	else:
		doors_open=absf(p.x)<1.56 and p.z> -1.10 and p.z<3.70
	if inside_view:
		inside_view=absf(p.x)<2.03 and p.z> -1.25 and p.z<3.26
	else:
		inside_view=absf(p.x)<1.39 and p.z> -1.03 and p.z<2.85
	rear_occlusion = _roof_covers_player(p)
	if doors_open!=was_open:
		door_motion.emit(doors_open,to_global(Vector3(0,1.1,1.22)))
	open_amount=move_toward(open_amount,1.0 if doors_open else 0.0,delta*2.65)
	_apply()

# From the north work aisle the closed snow roof can sit between the player
# and the gameplay camera. Lift the same authored roof used by the front
# cutaway, without opening the doors or displaying warehouse UI at the saw.
func _roof_covers_player(p:Vector3) -> bool:
	if p.z >= -1.15 or p.z < -5.5 or absf(p.x)>4.5: return false
	var camera := get_viewport().get_camera_3d()
	if not camera: return false
	var torso := p + Vector3.UP*.86
	var toward_camera := to_local(camera.global_position)-torso
	if camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		toward_camera = global_basis.inverse()*camera.global_basis.z
	var roof := (parts.Roof as MeshInstance3D).get_aabb().grow(.16 if rear_occlusion else .04)
	return roof.intersects_segment(torso,torso+toward_camera.normalized()*8.) != null

func _apply() -> void:
	visible=tier>0
	collision.collision_layer=1 if tier>0 else 0
	var roof_visible := tier>0 and not inside_view and not rear_occlusion
	if last_tier != tier or last_roof_visible != roof_visible:
		connection_roof.visible=roof_visible and connections_paid
		var original_roof:=roof_visible and not connections_paid
		for key in ROOF: parts[key].visible=original_roof
		parts.GableArmor.visible=original_roof and tier==3
		parts.RoofStuds.visible=original_roof and tier==3
		last_roof_visible=roof_visible
	if last_rear_occlusion != rear_occlusion:
		# Keep the blue lower wall and its steel facing together, like the
		# lowered walls of the author’s front cutaway.
		for key in ["BackWall","BackArmor"]:
			parts[key].scale.y = .39 if rear_occlusion else 1.
		last_rear_occlusion = rear_occlusion
	if last_tier!=tier or last_cutaway!=inside_view:
		for key in CUTAWAY: parts[key].visible=not inside_view
		parts.StarterRope.visible=tier==1
		parts.RightPostRope.visible=tier==1 and not inside_view
		parts.RightPostBand.visible=tier>=2 and not inside_view
		parts.Footing.visible=tier>=2
		for key in ["LeftArmor","BackArmor","AdvancedShelves"]:
			parts[key].visible=tier==3
		for key in ["RightArmor","FacadeArmor","DoorLeftArmor","DoorRightArmor"]:
			parts[key].visible=tier==3 and not inside_view
		parts.RightDetail.visible=not inside_view
		for key in ["CutawayPanels","CutawayTrack","CutDoorLeft","CutDoorRight","CutRightPost"]:
			parts[key].visible=inside_view
		parts.Headers.visible=inside_view
		parts.InteriorArmor.visible=inside_view and tier==3
		for label in shelves:label.visible=inside_view
		last_tier=tier
		last_cutaway=inside_view
	if not is_equal_approx(open_amount,last_slide):
		var slide:=smoothstep(0.,1.,open_amount)*.795
		for key in ["DoorLeft","DoorLeftArmor"]:parts[key].position.x=-slide
		for key in ["DoorRight","DoorRightArmor"]:parts[key].position.x=slide
		parts.CutDoorLeft.position.x=-slide*.57
		parts.CutDoorRight.position.x=slide*.57
		last_slide=open_amount

# Reachable floor between the original side counters, rear bench and
# doorway piers. The player must enter through the open front threshold.
func on_walkable_aisle(at:Vector3,radius:float)->bool:
	if tier==0:return false
	var p:=to_local(at)
	if absf(p.y)>.55 or p.z<-.67+radius-.008 or p.z>1.50:return false
	var side_limit:=1.095-radius
	if p.z>.98-radius:side_limit=.825-radius
	return absf(p.x)<=side_limit+.008

func is_interior_visible() -> bool:
	return tier>0 and inside_view

func bay_position(kind:String) ->Vector3:
	return to_global(BAYS.get(kind,Vector3.ZERO))

func bay_label_position(kind:String) ->Vector3:
	return to_global(LABELS.get(kind,Vector3.ZERO))
