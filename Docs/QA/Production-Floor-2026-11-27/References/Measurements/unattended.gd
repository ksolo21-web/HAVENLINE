extends SceneTree
func _initialize():
    call_deferred("run")

func goods(field, conveyors, j):
    var visible_stock:=0
    for plate in conveyors.counter_rack:
        if plate.is_visible_in_tree(): visible_stock+=1
    var visible_cargo:Dictionary={}
    for lane:String in conveyors.goods:
        var unit:Node3D=conveyors.goods[lane]
        if unit.is_visible_in_tree():
            var p:=unit.global_position
            visible_cargo[lane]=[snappedf(p.x,.01),snappedf(p.y,.01),snappedf(p.z,.01)]
    return {"stored_meat":field.inventory.stored.meat,"cooker_hopper":j.hoppers.meat,"cooked":j.cooked,"prepared_shelf":j.product_store.meal,"counter_ledger":j.counter_stock,"counter_actual":visible_stock,"cargo_ledger":j.line_load.duplicate(),"cargo_in_view":visible_cargo,"paid":j.served,"worker":j.worker_supply,"held":j.held_meal,"guest_count":field.counter.queue.size()}

func run():
    var field=load('res://field_opening.tscn').instantiate()
    root.add_child(field)
    field.counter.arrival_clock=100.
    for i in 2:await physics_frame
    var line=field.settlement_loop.conveyors
    var j:Dictionary=field.inventory.settlement
    var start:Vector3=field.actor.global_position
    var mode=OS.get_environment('HL12_REVIEW_PHASE')
    var frames:=156 if mode=='outbound' else 2400
    var checkpoints:Array=[]
    var carried_and_worked:=false
    var position_error:=0.
    var appeared:Dictionary={}
    var checks:Dictionary={}
    for t in frames:
        await physics_frame
        position_error=maxf(position_error,start.distance_to(field.actor.global_position))
        carried_and_worked=carried_and_worked or (j.worker_supply!='' or j.worker_meal>0 or j.held_meal>0 or field.settlement_loop.works.active!='')
        if t%12==0 or t==frames-1:
            var obs=goods(field,line,j)
            for lane:String in obs.cargo_in_view:appeared[lane]=true
            if t%120==0 or t==frames-1:checkpoints.append({"tick":t,"observed":obs})
    var end=goods(field,line,j)
    checks["no player input or character transfer"]=position_error<.025 and not carried_and_worked and not j.rescued
    checks["no waiting buyers, staff handoffs or payments"]=field.counter.queue.is_empty() and int(j.served)==0
    if mode=="outbound":
        checks["active freight belongs to actual visible traveling cargo"]=appeared.size()>0 and end.cargo_in_view.size()>0
    else:
        checks["all six original raw meats processed after partial restart"]=end.stored_meat==0 and end.cooker_hopper==0 and end.cooked==7
        checks["two visible plates match two claimed slices of counter capacity"]=end.counter_ledger==2 and end.counter_actual==2
        checks["other five cooked meals occupy prepared shelf"]=end.prepared_shelf==5
    field._persist_world()
    checks["save committed"]=not field.persist_blocked
    print('INDEPENDENT_LINE ',JSON.stringify({"mode":mode,"checks":checks,"initial_position":str(start),"max_travel_m":position_error,"observed_cargo_types":appeared.keys(),"timeline":checkpoints,"final":end}))
    field.set_physics_process(false)
    await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,field)
    field.queue_free()
    for i in 4:await process_frame
    quit(0 if checks.values().all(func(x):return x) else 2)
