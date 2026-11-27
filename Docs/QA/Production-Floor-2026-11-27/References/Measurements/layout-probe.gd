extends SceneTree

func _initialize():
    call_deferred("run")

func xyz(v: Vector3) -> Array:
    return [v.x, v.y, v.z]

func rect(r: Rect2) -> Array:
    return [r.position.x, r.position.y, r.size.x, r.size.y]

func run():
    var game = load("res://field_opening.tscn").instantiate()
    root.add_child(game)
    game.set_physics_process(false)
    for i in 4:
        await process_frame
    var line = game.settlement_loop.conveyors
    line.refresh_paths()
    var net = line.network
    var info = {"build_order":game.inventory.build_order, "bounds":rect(game.camp_layout.bounds()), "gates":{}, "footprints":{}, "routes":{}, "player_radius":game.layout.actor_radius, "render_state":[]}
    for gate in game.gates: info.gates[gate.name] = xyz(gate.global_position)
    for id in game.camp_layout.NAMES:
        if game.camp_layout.owned(id):
            info.footprints[id] = rect(game.camp_layout.footprint(id,game.camp_layout.center(id)))
    info["aprons"] = {"store":xyz(game.depot.apron.global_position), "counter":xyz(game.counter.service_point.global_position), "cooker_in":xyz(game.lakeshore.apron_position()), "cooker_out":xyz(game.lakeshore.output_apron_position()), "saw":xyz(game.processors.apron_position("wood")), "drill":xyz(game.processors.apron_position("stone"))}
    for lane in net.routes:
        info.routes[lane] = []
        for point in net.routes[lane]: info.routes[lane].append(xyz(point))
    var b: Rect2=game.camp_layout.bounds()
    var step:=.075
    var window := {"saw":[],"drill":[],"cooker_in":[],"counter":[],"store":[]}
    var z:=b.position.y+step*.5
    while z<b.end.y:
        var x:=b.position.x+step*.5
        var spans:Dictionary={}
        while x<b.end.x:
            var feet:=Vector3(x,0,z)
            var station:String=game.processors.at_station(feet)
            var accept:Dictionary={"saw":station=="wood","drill":station=="stone","store":game.depot.at_loading_area(feet),"counter":game.counter.at_service(feet),"cooker_in":game.lakeshore.at_cooker(feet)}
            for k:String in accept:
                if accept[k]:
                    if spans.has(k): spans[k][1]=x
                    else: spans[k]=[x,x]
                elif spans.has(k):
                    window[k].append([z,spans[k][0],spans[k][1]])
                    spans.erase(k)
            x+=step
        for k:String in spans:
            window[k].append([z,spans[k][0],spans[k][1]])
        z+=step
    info["activation_rows"]=window
    var f = FileAccess.open(OS.get_environment('HL12_REF_LAYOUT'), FileAccess.WRITE)
    f.store_string(JSON.stringify(info))
    f.close()
    print("REFERENCE_LAYOUT ", info.routes.keys())
    await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,game)
    game.queue_free()
    for i in 4: await process_frame
    quit(0)
