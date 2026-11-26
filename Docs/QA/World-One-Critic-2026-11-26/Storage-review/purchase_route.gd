extends "res://tests/world_house_route.gd"
## Same committed joystick route. Keep compact receipts rather than save full scene state every tick.
var last_ledger: Dictionary
var earned := {}
var prior_earned := -1
var changes: FileAccess
var state_id := 0

func snapshot() -> Dictionary:
	var ledger=field.inventory
	if prior_earned != ledger.collected.size():
		earned = ledger.EMPTY.duplicate()
		for kind in ledger.collected.values(): earned[kind]+=1
		prior_earned=ledger.collected.size()
	var now:Dictionary={"earned":earned,"carried":ledger.carried,"stored":ledger.stored,"paid":ledger.paid,"order":ledger.build_order,"tier":field.depot.house.tier}
	var point={"same_camera":camera==root.get_camera_3d() or dry}
	if last_ledger != now:
		if not changes:
			changes=FileAccess.open(out_dir.path_join("receipt-changes.jsonl"),FileAccess.WRITE)
		last_ledger=now.duplicate(true)
		state_id+=1
		changes.store_line(JSON.stringify({"tick":tick,"state_id":state_id,"ledger":last_ledger}))
		changes.flush()
	point.state_id=state_id
	return point

func _plate(id:String) -> void:
	if not plate_enabled or plate_names.has(id):return
	if id not in ["house-interior-1","house-interior-2","house-interior-3","house-tier-3"]:return
	plate_names[id]=true
	await process_frame
	RenderingServer.force_draw(false,1./24.)
	var image:=root.get_texture().get_image()
	assert(image.get_width()==1280 and image.get_height()==720 and root.scaling_3d_scale==1.)
	image.convert(Image.FORMAT_RGB8)
	image.save_jpg(out_dir.path_join(id+".jpg"),.90)
