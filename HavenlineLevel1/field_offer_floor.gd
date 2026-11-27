extends Node3D

const Progress = preload("res://field_progression.gd")
const HUD = preload("res://field_hud.gd")
var title: Label3D
var icon: Sprite3D
var price: Node3D
var shown_id := ""
var floor_art
var ink: ShaderMaterial
var corners: StandardMaterial3D

func install(environment, id: String, at: Vector3) -> void:
	install_custom(environment,id,at,Progress.TITLES[id],Progress.offers({})[id].keys())
	_install_glyph(id)

func install_custom(environment, id:String, at:Vector3, caption:String, kinds:Array) -> void:
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
			else:
				corners = mesh.material_override.duplicate()
				mesh.material_override = corners
				corners.albedo_color = Color("f8fbff")
	title = environment.flat_label(self,Vector3(0,.008,-.19),.0061)
	title.text = caption
	title.modulate = Color.WHITE
	price = environment.cost_row(self,kinds,.47)
	hide()

func _install_glyph(id: String) -> void:
	icon = Sprite3D.new()
	icon.texture = preload("res://assets/field_camp/orbit_upgrade.svg") if id == Progress.AXES else preload("res://assets/field_camp/hearth_mark.svg")
	icon.axis = Vector3.AXIS_Y
	icon.pixel_size = .0038 if id == Progress.AXES else .0044
	icon.position = Vector3(0,.012,-.19)
	icon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(icon)
	title.position.z = -.70
	price.position.z = .58
	shown_id = id

func change_project(id: String, ledger) -> void:
	if id == shown_id: return
	shown_id = id
	title.text = Progress.TITLES[id]
	remove_child(price)
	price.queue_free()
	price = floor_art.cost_row(self,ledger.costs[id].keys(),.58)

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
	set_fill(1.-float(left)/maxi(total,1))

func set_fill(fraction: float) -> void:
	ink.set_shader_parameter("paid",fraction)
	corners.albedo_color = Color("5be72e") if fraction > 0. else Color("f8fbff")

func set_depot(ledger, id: String, owns_bays: bool) -> void:
	# The completed house supplies the loading mat in its own authored model.
	for part in get_children(): part.visible = not owns_bays
	if not owns_bays and not id.is_empty():
		change_project(id,ledger)
		set_due(ledger,id,true)
