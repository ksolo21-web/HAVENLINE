extends "res://tests/qa_storage_stream.gd"
var dir:=OS.get_environment("HL_CRITIC_DIR")
var bins:={}
func place(at:Vector3):
	field.actor.global_position=at
	field.camera.global_position=at+field.camera_follow_offset
func record(name_:String, possible:Array):
	var details:Array=[]
	for f in possible:
		var u:Vector2=field.camera.unproject_position(f.mesh.global_position)/root.get_visible_rect().size
		details.append({"resource":f.kind,"to":f.to,"source":f.from,"time":f.t,"position":[f.mesh.global_position.x,f.mesh.global_position.y,f.mesh.global_position.z],"uv":[u.x,u.y]})
	bins[name_]={"pack":field.inventory.carried.duplicate(),"hoppers":field.inventory.settlement.hoppers.duplicate(),"flights":details,"zoom":field.get_zoom_ratio(),"floor_tier":field.depot.house.tier,"perimeter":field.field_env.perimeter_stage}
	RenderingServer.force_draw(false,0.)
	var img=root.get_texture().get_image()
	img.save_jpg(dir.path_join(name_+".jpg"),.95)
func observe(site:String, at:Vector3, supply_:Dictionary, target:String):
	place(at+Vector3(0,0,1.6))
	for i in 5:await physics_frame
	for k in supply_:supply(k,supply_[k])
	field.carry.sync()
	place(at)
	var seen:=false
	var peak:=0
	var mid_seen:=false
	for k in 95:
		await physics_frame
		var active=field.carry.flights.filter(func(f):return f.to==target)
		peak=maxi(peak,active.size())
		if not seen and active.size()>=mini(2,int(supply_.values()[0])) and active.any(func(f):return f.t>.34):
			seen=true
			for z in [1.,2.]:
				field.set_zoom_ratio(z)
				place(at)
				record(site+"-"+str(int(z))+"x",active)
			field.set_zoom_ratio(1.)
			place(at)
		if seen and not mid_seen and (site=="survivor" or site=="tower") and k>=22 and active.size()>=2:
			mid_seen=true
			for z in [1.,2.]:
				field.set_zoom_ratio(z)
				place(at)
				record(site+"-mid-"+str(int(z))+"x",active)
			field.set_zoom_ratio(1.)
			place(at)
		if seen and active.is_empty():
			if site=="survivor" or site=="tower":
				for z in [1.,2.]:
					field.set_zoom_ratio(z)
					place(at)
					record(site+"-paid-"+str(int(z))+"x",active)
				field.set_zoom_ratio(1.)
				place(at)
			break
	place(Vector3(2.5,0,-3.1))
	for k in 112:await physics_frame
	bins[site+"-away"]={"peak":peak,"hoppers":field.inventory.settlement.hoppers.duplicate(),"cooked":field.inventory.settlement.cooked,"processed_wood":field.inventory.settlement.processed_wood,"processed_stone":field.inventory.settlement.processed_stone,"receipt":field.inventory.build_order.duplicate(),"saw_flights":seen}
func run():
	field=Scene.instantiate();root.add_child(field);current_scene=field;camera=field.camera
	for i in 3:await physics_frame
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2"]:open_site(id)
	await observe("wood",field.processors.APRONS.wood,{"wood":3},"work:wood")
	await observe("stone",field.processors.APRONS.stone,{"stone":3},"work:stone")
	await observe("cooker",field.lakeshore.APRON,{"meat":2},"work:meat")
	var money=field.inventory.remaining("watchtower")
	await observe("tower",field.carry.receivers.watchtower.global_position,money,"watchtower")
	await observe("survivor",field.settlement_loop.works.PLOT_AT,{"wood":int(field.inventory.survivor_cost)},"work:survivor_plot")
	var out=FileAccess.open(dir.path_join("independent-native-handoffs.json"),FileAccess.WRITE);out.store_string(JSON.stringify(bins," "));out.close()
	await Session.drain_field_audio(self,field);field.queue_free()
	for i in 3:await process_frame
	quit()
