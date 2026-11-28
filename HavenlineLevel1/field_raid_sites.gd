extends RefCounted

const OfferFloor = preload("res://field_offer_floor.gd")
const Notice = preload("res://field_raid_notice.gd")
const FENCE_IDS := [
	"fence-south-west", "fence-south-east", "fence-east-north", "fence-east-south", "fence-north", "fence-west"
]
const BUILDINGS := {"furnace": "center_hearth", "cooker": "camp_cooker", "saw": "saw_bench", "drill": "quarry_drill", "tower": "watchtower"}
const EAST_BREACH_ROWS := [2, 3]
const TITLES := {
	"gate-south": "South gate", "gate-east": "East gate", "furnace": "Furnace",
	"fence-south-west": "Southwest fence", "fence-south-east": "Southeast fence",
	"fence-east-north": "Northeast fence", "fence-east-south": "Southeast fence",
	"fence-north": "North fence", "fence-west": "West fence",
	"cooker": "Cooker", "saw": "Saw", "drill": "Drill", "tower": "Tower"
}
class FencePort extends Node3D:
	var gate_id := ""
	var active := true
	var breached := false
	var HALF_SPAN := 1.30

var world
var director
var notice: Control
var repair_pad: Node3D
var repair_target := ""
var markers := {}
var ports := {}
var shown_message := ""
var message_left := 0.
var raid_label := ""

func setup(host: Node3D, state: RefCounted) -> void:
	world = host
	director = state

func gate(id: String) -> Node3D:
	for g: Node3D in world.gates:
		if g.gate_id == id:
			return g
	var index := FENCE_IDS.find(id)
	if index in EAST_BREACH_ROWS and world.field_env.perimeter_stage > 0:
		if not ports.has(id):
			var port := FencePort.new()
			port.gate_id = id
			port.name = "RaidFace_" + id
			world.field_env.add_child(port)
			port.rotation.y = PI * .5
			ports[id] = port
		var face: FencePort = ports[id]
		var row: Array = world.layout.walls_xz[index]
		face.position = Vector3(row[0], 0., row[1])
		face.HALF_SPAN = float(row[3]) * .5
		face.breached = director.is_down(id)
		return face
	return null

func outside_normal(g: Node3D) -> Vector3:
	var forward := g.global_basis.z.normalized()
	var test := g.global_position + forward
	return -forward if world.field_env.is_inside_camp(test) else forward

func title(id: String) -> String:
	return String(TITLES.get(id, id))

func building(id: String) -> Node3D:
	if id in BUILDINGS and world.camp_layout and world.camp_layout.owned(BUILDINGS[id]):
		return world.camp_layout.building(BUILDINGS[id])
	return null

func site_position(id: String) -> Vector3:
	var door := gate(id)
	if door:
		return door.global_position
	var index := FENCE_IDS.find(id)
	if index >= 0:
		var row: Array = world.layout.walls_xz[index]
		return Vector3(row[0], 0., row[1])
	var object := building(id)
	return object.global_position if is_instance_valid(object) else Vector3.INF

func repair_position(id: String) -> Vector3:
	var point := site_position(id)
	if not point.is_finite():
		return point
	var door := gate(id)
	if door:
		var offset := .88 if id.begins_with("gate-") else 0.
		return point - outside_normal(door) * 2.15 + door.global_basis.x.normalized() * offset
	if id.begins_with("fence-"):
		var court: Vector4 = world.field_env.COURTS[world.field_env.perimeter_stage - 1]
		var center := Vector3((court.x + court.z) * .5, 0., (court.y + court.w) * .5)
		return point.move_toward(center, 1.9)
	return point + Vector3(0., 0., 2.40)

func _nearby_damaged_site() -> String:
	if not world.camp_active or not world.field_env.is_inside_camp(world.actor.global_position):
		return ""
	var radius_squared := 3.15 * 3.15
	var chosen := ""
	for id: String in director.condition:
		var at := repair_position(id)
		if not at.is_finite():
			continue
		var distance: float = world.actor.global_position.distance_squared_to(at)
		if distance < radius_squared:
			chosen = id
			radius_squared = distance
	return chosen

func _nearby_repair_valid(id: String, bill: Dictionary) -> bool:
	return _can_repair(id,bill,world.actor.global_position,world.inventory.carried)

func _can_repair(id: String, bill: Dictionary, at: Vector3, stock: Dictionary) -> bool:
	if id.is_empty() or bill.is_empty() or world.persist_blocked or world.reset_time > 0.:
		return false
	if not world.field_env.is_inside_camp(at):
		return false
	if id.begins_with("fence-") and director.is_down(id) and _breach_occupied(FENCE_IDS.find(id)):
		return false
	return at.distance_squared_to(repair_position(id)) <= 1.95 * 1.95 and bill.keys().all(
			func(kind: String): return int(stock.get(kind, 0)) >= int(bill[kind]))

func _breach_occupied(index: int) -> bool:
	var row: Array = world.layout.walls_xz[index]
	var half := Vector2(float(row[2]), float(row[3])) * .5 + Vector2.ONE * .55
	var box := Rect2(Vector2(row[0], row[1]) - half, half * 2.)
	var occupants: Array = [world.actor] + world.enemies
	if is_instance_valid(world.survivor):
		occupants.append(world.survivor.actor)
	for actor: Node3D in occupants:
		if is_instance_valid(actor) and box.has_point(Vector2(actor.global_position.x, actor.global_position.z)):
			return true
	return false

func _attach_notice() -> void:
	notice = Notice.new()
	world.opening_hud.add_child(notice)
	notice.repair.pressed.connect(_repair_pressed)

func flash_status(text: String) -> void:
	shown_message = text
	message_left = 3.8

func _set_repair_pad(id: String, bill: Dictionary) -> void:
	if id != repair_target:
		if is_instance_valid(repair_pad):
			repair_pad.queue_free()
			repair_pad = null
		repair_target = id
		if not id.is_empty():
			repair_pad = OfferFloor.new()
			world.field_env.add_child(repair_pad)
			repair_pad.install_custom(world.field_env, "repair_" + id, repair_position(id), title(id), bill.keys())
			repair_pad.show()
	if is_instance_valid(repair_pad):
		world.field_env.show_costs(repair_pad.price, bill)

func update_notice(delta: float) -> void:
	message_left = maxf(0., message_left - delta)
	var id := _nearby_damaged_site()
	if director.phase == "quiet" and id.is_empty() and message_left == 0. and not is_instance_valid(notice):
		return
	if not is_instance_valid(notice):
		_attach_notice()
	var text := shown_message if message_left > 0. else ""
	if director.phase == "warning":
		var seconds := maxi(0, ceili(director.seconds_left))
		text = "Raid · %s in %d:%02d" % [title(director.entrance), seconds / 60, seconds % 60]
	elif director.phase == "attack":
		var gate_id: String = director.entrance
		text = "Raid · %s breached" % title(gate_id) if director.is_down(gate_id) else "Raid · %s %d HP" % [title(gate_id), director.hp(gate_id)]
	raid_label = text
	var bill: Dictionary = director.repair_bill(id)
	_set_repair_pad(id, bill)
	var verb := "Rebuild " if director.is_down(id) and id in BUILDINGS else "Repair "
	var quote := verb + title(id) if not id.is_empty() else ""
	notice.display(text, quote, _nearby_repair_valid(id, bill))

func _repair_pressed() -> void:
	repair(repair_target)

func repair(id: String) -> bool:
	var bill: Dictionary = director.repair_bill(id)
	if not _nearby_repair_valid(id, bill):
		return false
	if not _commit_repair(id,bill,world.inventory.carried): return false
	world.present_character_contact(&"repair", repair_position(id))
	return true

func worker_repair(id: String) -> bool:
	if director.phase == "attack" or not world.survivor.can_defend(): return false
	var bill: Dictionary = director.repair_bill(id)
	var stock: Dictionary = world.inventory.settlement.worker_load
	if not _can_repair(id,bill,world.survivor.actor.global_position,stock): return false
	return _commit_repair(id,bill,stock)

func _commit_repair(id: String, bill: Dictionary, stock: Dictionary) -> bool:
	var checkpoint: Dictionary = director.snapshot()
	for kind: String in bill:
		stock[kind] -= int(bill[kind])
	director.finish_repair(id)
	apply_condition()
	world._checkpoint_lifecycle()
	if world.persist_blocked:
		director.restore(checkpoint)
		apply_condition()
		return false
	world._event("raid_site_repaired", site_position(id), "build")
	flash_status(title(id) + " ready")
	return true

func _marker(id: String) -> Label3D:
	if markers.has(id):
		return markers[id]
	var label := Label3D.new()
	label.name = "Condition_" + id
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.pixel_size = .004
	label.font_size = 30
	label.outline_size = 6
	label.modulate = Color("#ffdb98")
	label.no_depth_test = false
	world.add_child(label)
	markers[id] = label
	return label

func apply_condition() -> void:
	if not world.camp_active:
		return
	for g: Node3D in world.gates:
		g.set_breached(director.is_down(g.gate_id))
	_apply_east_fence()
	if world.field_env.hearth_shell:
		var down: bool = director.is_down("furnace")
		world.field_env.hearth_shell.visible = not down
		world.field_env.hearth_fire.set_fired(not down)
		world.field_env.hearth_footprint.get_parent().set_deferred("collision_layer", 0 if down else 1)
	if world.lakeshore:
		world.lakeshore.refresh_ownership(false)
	if world.processors:
		world.processors.refresh_ownership(false)
	for id: String in director.condition:
		var point := site_position(id)
		if not point.is_finite():
			continue
		var tag := _marker(id)
		tag.global_position = point + Vector3.UP * (2.2 if id in BUILDINGS else 1.8)
		tag.text = title(id) + (" · Broken" if director.is_down(id) else " · %d HP" % director.hp(id))
		tag.show()
	for id: String in markers.keys():
		if not director.condition.has(id):
			markers[id].queue_free()
			markers.erase(id)

func _apply_east_fence() -> void:
	var palisades: MultiMeshInstance3D = world.field_env.palisades
	if not is_instance_valid(palisades):
		return
	var mesh := palisades.multimesh
	for index: int in EAST_BREACH_ROWS:
		var broken: bool = director.is_down(FENCE_IDS[index])
		var row: Array = world.layout.walls_xz[index]
		var collider = world.camp_colliders[index]
		if collider.collision_layer != (0 if broken else 1):
			collider.collision_layer = 0 if broken else 1
			world.field_env.wall_revision += 1
		var y := -16. if broken else 0.
		for i in mesh.instance_count:
			var panel := mesh.get_instance_transform(i)
			if absf(panel.origin.x - float(row[0])) > .04 or absf(panel.origin.z - float(row[1])) > float(row[3]) * .5 + .03:
				continue
			if not is_equal_approx(panel.origin.y, y):
				panel.origin.y = y
				mesh.set_instance_transform(i, panel)
