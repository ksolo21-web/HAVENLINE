extends "res://tests/qa_personal_goods.gd"
var out := OS.get_environment("HAVENLINE_WIDE_EVIDENCE")
var cash_views := {}

func photograph(label: String) -> void:
	if cash_views.has(label): return
	var rows := []
	var previous_yaw: float = field.actor.rotation.y
	var right: Vector3 = field.camera.global_basis.x
	var near := right.cross(Vector3.UP)
	var reading := (-near + right*.85).normalized()
	field.actor.rotation.y = atan2(reading.x,reading.z)
	field.camera.global_position = field.actor.global_position + field.camera_follow_offset
	for zoom in [1.,2.]:
		field.set_zoom_ratio(zoom)
		RenderingServer.force_draw(false,1./60.)
		var image := root.get_texture().get_image()
		var file := "%s-%dx.jpg" % [label,int(zoom)]
		image.save_jpg(out.path_join(file),.92)
		rows.append({"image":file,"zoom":zoom,"pack":bank.hand_goods(),"warehouse":bank.house_goods(),"counter_cash":bank.till_balance()})
	field.set_zoom_ratio(1.)
	field.actor.rotation.y = previous_yaw
	cash_views[label]=rows
	var file := FileAccess.open(out.path_join("Cash.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures":cash_views,"renderer":RenderingServer.get_video_adapter_name()},"  "))
	file.close()

func inspect_state(label: String) -> void:
	super.inspect_state(label)
	if label=="finished goods on back": photograph("Finished-pack")
	if label=="simultaneous meat and money": photograph("Money-to-pack")

func cash_on_shelf() -> int:
	var count := super.cash_on_shelf()
	if count==2 and j.house_cash==2: photograph("Warehouse-cash")
	return count
