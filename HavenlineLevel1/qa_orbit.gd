extends SceneTree
const Opening = preload("res://orbit_opening.tscn")
var output := OS.get_environment("HAVENLINE_SWIRL_CAPTURE")
class HostileProbe extends Node3D:
	var hp := 4
	var turns := []
	func can_receive_swirl() -> bool:
		return hp > 0
	func take_swirl_hit(turn: int) -> bool:
		if turns.has(turn) or hp <= 0:
			return false
		turns.append(turn)
		hp -= 1
		return true
var scene
var rows := []
var frame := 0
func _initialize() -> void: call_deferred("run")
func run() -> void:
	if output.is_empty():
		quit(3)
		return
	DirAccess.make_dir_recursive_absolute(output)
	scene = Opening.instantiate()
	root.add_child(scene)
	await process_frame
	if scene.persist_requested or not scene.surfaces.has(scene.resource_tree):
		printerr("Missing trunk or profile isolation ",scene.surfaces)
		quit(10)
		return
	var side := Vector3(1,0,-1).normalized()
	var results := {}
	for label in ["tree", "rock", "combat"]:
		var body: Node3D
		var alt: HostileProbe
		if label == "combat":
			body = probe(Vector3(1.,0.,-6.))
			body.name="HostileA"
			alt = probe(Vector3(.04,0,-7.05))
			alt.name="HostileB"
		else:
			body = scene.resource_tree if label == "tree" else scene.resource_rock
		var range_m := 3.09 if label == "combat" else 2.50
		scene.character_kit.rest()
		scene.actor.global_position = body.global_position + side * range_m
		if label=="combat":
			scene.character_kit.set_upgraded(true)
			alt.global_position=scene.actor.global_position-side.rotated(Vector3.UP,PI*.75)*range_m
		scene.actor.rotation.y = atan2(-side.x,-side.z) + PI*.67
		scene.camera.global_position=scene.actor.global_position + Vector3(7,11,11)
		var from: int = scene.contacts.size()
		for tick in 208:
			await process_frame
			if DisplayServer.get_name()!="headless":
				await RenderingServer.frame_post_draw
			var kit = scene.character_kit
			rows.append({"frame":frame,"case":label,"tool":kit.equipped,"turn":kit.turn_id,"time":kit.elapsed,"tip":str(kit.current_tip),"contacts":scene.contacts.size()-from})
			if label != "combat" and DisplayServer.get_name()!="headless":
				root.get_texture().get_image().save_jpg(output+"/" +"%04d.jpg"%frame, .94)
			frame+=1
		results[label] = scene.contacts.slice(from)
		if label=="combat":
			results["hostile_hp"]=[body.hp,alt.hp]
		scene.actor.global_position = Vector3(3,0,-9)
		await process_frame
		await process_frame
		if not scene.character_kit.active:
			quit(11)
			return
	var out := FileAccess.open(output+"/" +"results.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"hits":results,"frames":rows}, "  "))
	out.close()
	print("SWIRL ",results)
	var ok: bool = results.tree.size()==3 and results.rock.size()==3 and scene.resource_rock.phase=="mined" and results.hostile_hp[0]<4 and results.hostile_hp[1]<4
	quit(0 if ok else 12)

func probe(at: Vector3) -> HostileProbe:
	var body := HostileProbe.new()
	scene.add_child(body)
	body.global_position=at
	body.add_to_group("swirl_hostiles")
	var part := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(.30,1.5,.30)
	part.mesh=box
	part.hide()
	body.add_child(part)
	part.position.y=.75
	scene.register_hostile(body,part)
	return body
