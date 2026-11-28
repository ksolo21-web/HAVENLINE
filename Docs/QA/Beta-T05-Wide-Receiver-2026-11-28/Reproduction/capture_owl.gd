extends "res://tests/qa_owl_gate_patrol.gd"

var evidence := OS.get_environment("HAVENLINE_PATCH_EVIDENCE")
var rendered: Array = []
var hit_view := false
var perch_view := false
var scope_frames := 0

func picture(file: String) -> void:
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	var image := root.get_texture().get_image()
	image.save_jpg(evidence.path_join(file),.87)
	var owl = field.owl
	rendered.append({"file":file,"tick":frames_at,"state":owl.state,"zoom":field.get_zoom_ratio(),
		"size":[image.get_width(),image.get_height()],"feet":pt(owl.global_position),
		"player_feet":pt(field.actor.global_position),"camera":pt(camera.global_position),
		"art_scale":pt(owl.art.scale),"hits":field.inventory.settlement.owl_hits,
		"wolf_hp":wolf.hp if is_instance_valid(wolf) else -1})

func record() -> void:
	var state: String = field.owl.state
	if not perch_view:
		perch_view = true
		await picture("Perch-1x.jpg")
	if frames_at < 165 and frames_at%4 == 0:
		await picture("Sequence-%03d.jpg"%scope_frames)
		scope_frames += 1
	if state=="strike" and not hit_view:
		hit_view = true
		await picture("Talons-1x.jpg")
		field.set_zoom_ratio(2.0)
		field.follow_camera(1.0/60.0)
		await picture("Talons-2x.jpg")
		field.set_zoom_ratio(1.0)
	await super.record()
	var out := FileAccess.open(evidence.path_join("Frames.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify({"captures":rendered,"renderer":RenderingServer.get_video_adapter_name(),
		"render_scale":root.scaling_3d_scale,"scenario":"Paid owl, ordinary east gate joystick approach, hostile wolf"}, "  "))
	out.close()
