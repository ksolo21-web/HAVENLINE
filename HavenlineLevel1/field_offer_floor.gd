extends Node3D

const Progress = preload("res://field_progression.gd")
const HUD = preload("res://field_hud.gd")
var title: Label3D
var icon: Sprite3D
var price: Node3D
var floor_art
var ink: ShaderMaterial

func install(environment, id: String, at: Vector3) -> void:
	floor_art = environment
	name = "Offer_" + id
	position = at + Vector3.UP * .009
	scale = Vector3(.86,1,.86)
	for part in environment.buy_anchor.get_children():
		if part is MeshInstance3D and part.name in [&"Gray",&"Brackets"]:
			var mesh := part.duplicate() as MeshInstance3D
			add_child(mesh)
			if part.name == &"Gray":
				ink = mesh.material_override.duplicate()
				mesh.material_override = ink
				ink.set_shader_parameter("paid",0.)
	title = environment.flat_label(self,Vector3(0,.008,-.19),.0061)
	title.text = Progress.TITLES[id]
	title.modulate = Color.WHITE
	price = environment.cost_row(self,Progress.offers({})[id].keys(),.47)
	if id.begins_with("storage_"):
		icon = Sprite3D.new()
		icon.texture = HUD.MATERIAL_ICONS[id.trim_prefix("storage_")]
		icon.axis = Vector3.AXIS_Y
		icon.pixel_size = .006
		icon.position = Vector3(0,.009,-.62)
		icon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(icon)
	hide()

func set_due(ledger, id: String, active: bool) -> void:
	visible = active
	if not active: return
	var due: Dictionary = ledger.remaining(id)
	floor_art.show_costs(price,due)
	var total := 0
	var left := 0
	for kind in due:
		total += int(ledger.costs[id][kind])
		left += int(due[kind])
	if ink: ink.set_shader_parameter("paid",1.-float(left)/maxi(total,1))

func set_depot(ledger, id: String, owns_bays: bool) -> void:
	# Once the building exists its GLB supplies the dark, gold-edged loading
	# apron. The single shared receiver stays active behind the contextual HUD.
	for part in get_children():
		part.visible = not owns_bays
	if owns_bays: return
	set_due(ledger,id,true)
	title.text = Progress.TITLES[id]
	icon.texture = HUD.MATERIAL_ICONS[id.trim_prefix("storage_")]
