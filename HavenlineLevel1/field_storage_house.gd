extends Node3D
## Visual and physical shell of the shared storehouse. Inventory owns physical
## contents and counts; its three displays use these same shelf coordinates.
signal door_motion(opening:bool, at:Vector3)

const SHELL := preload("res://assets/storage_house/camp_storehouse.glb")
const BAYS := {"wood":Vector3(-1.15,.763,.25),"stone":Vector3(-1.15,.763,-.56),"meat":Vector3(0,.772,-.92)}
const LABELS := {"wood":Vector3(-.83,.65,.15),"stone":Vector3(-.83,.65,-.64),"meat":Vector3(0,.68,-.625)}
const CUTAWAY := ["Roof","Gables","Signs","Track","RightWall","Facade"]
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
var last_cutaway := false
var last_slide := -1.0

func _ready() -> void:
	model=SHELL.instantiate()
	add_child(model)
	for child in model.get_children(): parts[String(child.name)]=child
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
	for item in [["TIMBER",Vector3(-1.40,1.38,.524)],["MATERIALS",Vector3(-1.39,1.38,-.486)],["HIDES",Vector3(-.68,1.38,-.756)],["FOOD",Vector3(0,1.38,-.756)],["CARGO",Vector3(.68,1.38,-.756)],["FUEL",Vector3(1.12,1.38,.524)]]:
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

func update_state(new_tier:int, stock:Dictionary) -> void:
	tier=clampi(new_tier,0,3)
	last_stock=stock.duplicate()
	if tier==0:
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
	if doors_open!=was_open:
		door_motion.emit(doors_open,to_global(Vector3(0,1.1,1.22)))
	open_amount=move_toward(open_amount,1.0 if doors_open else 0.0,delta*2.65)
	_apply()

func _apply() -> void:
	visible=tier>0
	collision.collision_layer=1 if tier>0 else 0
	if last_tier!=tier or last_cutaway!=inside_view:
		for key in CUTAWAY: parts[key].visible=not inside_view
		parts.StarterRope.visible=tier==1
		parts.Footing.visible=tier>=2
		for key in ["LeftArmor","BackArmor","DoorLeftArmor","DoorRightArmor","AdvancedShelves"]:
			parts[key].visible=tier==3
		for key in ["GableArmor","RoofStuds","RightArmor","FacadeArmor"]:
			parts[key].visible=tier==3 and not inside_view
		parts.RightDetail.visible=not inside_view
		parts.CutawayPanels.visible=inside_view
		parts.Headers.visible=inside_view
		parts.InteriorArmor.visible=inside_view and tier==3
		for label in shelves:label.visible=inside_view
		last_tier=tier
		last_cutaway=inside_view
	if not is_equal_approx(open_amount,last_slide):
		var slide:=smoothstep(0.,1.,open_amount)*.795
		for key in ["DoorLeft","DoorLeftArmor"]:parts[key].position.x=-slide
		for key in ["DoorRight","DoorRightArmor"]:parts[key].position.x=slide
		last_slide=open_amount

func is_interior_visible() -> bool:
	return tier>0 and inside_view

func bay_position(kind:String) ->Vector3:
	return to_global(BAYS.get(kind,Vector3.ZERO))

func bay_label_position(kind:String) ->Vector3:
	return to_global(LABELS.get(kind,Vector3.ZERO))
