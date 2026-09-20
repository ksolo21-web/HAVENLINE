extends SceneTree
const View = preload("res://scripts/world_transform_view.gd")
const DEVICES = [Vector2i(2400,1080),Vector2i(2400,1080),Vector2i(2560,1600),Vector2i(2732,2048),Vector2i(2520,1080),Vector2i(2208,1768)]
const ANGLES = ["front","side","three-quarter","overhead","gameplay","detail"]
var rows: Array = []
var errors: Array = []
func _initialize():
    call_deferred("run")
func run():
    var view = View.new()
    root.add_child(view)
    view.configure("copy-preflight")
    var camera = Camera3D.new()
    root.add_child(camera)
    camera.current = true
    await process_frame
    var branches: Array = []
    for state in ["ready","preview","committing"]:
        branches.append({"id":state,"state":state,"errors":[],"shortfalls":{},"next":{}})
    for resource_case in [false,true]:
        for prerequisite_case in [false,true]:
            if not resource_case and not prerequisite_case: continue
            var reasons: Array = []
            if resource_case: reasons.append("insufficient_resources")
            if prerequisite_case: reasons.append("missing_prerequisite:harvesting_online")
            var shortfalls = {"wood":1,"stone":2} if resource_case else {}
            branches.append({"id":"blocked-%s-%s" % [resource_case,prerequisite_case],"state":"blocked","errors":reasons,"shortfalls":shortfalls,"next":{}})
    branches.append({"id":"complete-no-next","state":"complete","errors":[],"shortfalls":{},"next":{}})
    branches.append({"id":"complete-ready","state":"complete","errors":[],"shortfalls":{},"next":{"target_state":"reinforced","passed":true,"errors":[],"shortfalls":{}}})
    for resource_case in [false,true]:
        for prerequisite_case in [false,true]:
            if not resource_case and not prerequisite_case: continue
            var reasons: Array = []
            if resource_case: reasons.append("insufficient_resources")
            if prerequisite_case: reasons.append("missing_prerequisite:harvesting_online")
            branches.append({"id":"complete-%s-%s" % [resource_case,prerequisite_case],"state":"complete","errors":[],"shortfalls":{},"next":{"target_state":"reinforced","passed":false,"errors":reasons,"shortfalls":{"wood":12,"stone":8,"metal":2} if resource_case else {}}})
    var replay: Dictionary=branches[-1].duplicate(true)
    replay.id="replay"
    branches.append(replay)
    for state in ["ready","blocked","committing","complete"]:
        var after: Dictionary=branches[-1].duplicate(true)
        after.id="accepted-max-revision-"+state
        after.state=state
        after.revision=3
        after.accepted_scale=Vector3(1.0,1.35,1.0)
        if state=="blocked":
            after.errors=["insufficient_resources","missing_prerequisite:harvesting_online"]
            after.shortfalls={"wood":1,"stone":2,"metal":3,"fuel":4}
        branches.append(after)
    for branch in branches:
        view.target_state="foundation"
        view.target_revision=int(branch.get("revision",1))
        view._accepted_scale=branch.get("accepted_scale",Vector3(0.65,0.12,0.65))
        view.displayed_costs={"wood":8,"stone":4}
        view.lifecycle=branch.state
        view.block_reasons.assign(branch.errors)
        view.blocked_shortfalls=branch.shortfalls
        view.next_preview=branch.next
        view._apply_visuals()
        view.set_process(false)
        var text: String=view.feedback_text()
        if text.contains("online") or text.contains("Harvest Wood") or text.contains("Gather Stone"): errors.append({"branch":branch.id,"error":"invented prerequisite instruction"})
        if branch.state=="complete":
            if not text.contains("Spent:") or not text.contains("Foundation complete"): errors.append({"branch":branch.id,"error":"missing accepted debit identity"})
        elif text.contains("Spent:") or text.contains("Paid:"): errors.append({"branch":branch.id,"error":"premature debit claim"})
        if branch.state=="blocked" and branch.shortfalls.is_empty() and text.contains("deliver for"): errors.append({"branch":branch.id,"error":"invented delivery"})
        for device_index in DEVICES.size():
            root.size=DEVICES[device_index]
            root.content_scale_size=DEVICES[device_index]
            await process_frame
            for scale in [0.85,1.0,1.35]:
                view.configure_readability(scale)
                for angle in ANGLES:
                    configure_camera(camera,angle)
                    if branch.state=="committing":
                        view._pulse_time=0.0
                        view._process(0.25 / View.PULSE_HZ)
                    var report: Dictionary=view.projected_readability(camera)
                    var row={"branch":branch.id,"device_index":device_index,"scale":scale,"angle":angle,"text":text,"passed":report.passed,"projection":report}
                    rows.append(row)
                    if not report.passed: errors.append(row)
    var transition_cases: Array=[]
    view.set_locked()
    view.set_ready()
    view.set_process(false)
    configure_camera(camera,"gameplay")
    var revision_before: int=view.target_revision
    var costs_before: Dictionary=view.displayed_costs.duplicate(true)
    var nodes_before: int=view._visual_root.get_child_count()
    for next_scale in [0.85,1.35,1.0]:
        view.configure_readability(next_scale)
        var immediate: Dictionary=view.projected_readability(camera)
        var nominal: float=view._beacon.pixel_size * absf(camera.unproject_position(view._beacon.global_position + camera.global_transform.basis.y).y-camera.unproject_position(view._beacon.global_position).y)
        var expected: float=next_scale * float(immediate.label_scale)
        var passed: bool=immediate.passed and absf(nominal-expected)<0.001 and view.target_revision==revision_before and view.displayed_costs==costs_before and view._visual_root.get_child_count()==nodes_before and not view.is_processing()
        transition_cases.append({"scale":next_scale,"actual_font_unit_pixels":nominal,"expected_font_unit_pixels":expected,"passed":passed})
        if not passed:errors.append(transition_cases[-1])
    var extra_cases: Array=[]
    view.target_state="W".repeat(192)
    view.lifecycle="blocked"
    view.block_reasons.assign(["missing_prerequisite:unknown_gate","another_observable_error"])
    view.blocked_shortfalls={"wood":9223372036854775806,"stone":9223372036854775806,"metal":9223372036854775806,"fuel":9223372036854775806}
    view.displayed_costs=view.blocked_shortfalls.duplicate(true)
    view._apply_visuals()
    view.set_process(false)
    var extreme_text: String=view.feedback_text()
    if not extreme_text.contains("9223372036854775806") or not extreme_text.contains("Requires unknown gate") or not extreme_text.contains("Another observable error"):
        errors.append({"error":"extreme input dropped a resource or reason"})
    for size in DEVICES:
        root.size=size
        root.content_scale_size=size
        await process_frame
        for scale in [0.85,1.0,1.35]:
            view.configure_readability(scale)
            for angle in ANGLES:
                configure_camera(camera,angle)
                var first: Dictionary=view.projected_readability(camera)
                var second: Dictionary=view.projected_readability(camera)
                var passed: bool=not first.passed and not second.passed and first.label_rect==second.label_rect and first.layout_lane==second.layout_lane
                extra_cases.append({"kind":"impossible_extended_catalog","size":[size.x,size.y],"scale":scale,"angle":angle,"passed":passed})
                if not passed:errors.append(extra_cases[-1])
    view.target_state="foundation"
    view.lifecycle="ready"
    view.block_reasons.clear()
    view.blocked_shortfalls.clear()
    view.displayed_costs={"wood":8,"stone":4}
    view._apply_visuals()
    view.set_process(false)
    configure_camera(camera,"gameplay")
    camera.far=2.0
    var far_case: Dictionary=view.projected_readability(camera)
    extra_cases.append({"kind":"far_plane_crossing","passed":not far_case.passed and not far_case.projection_valid})
    camera.far=4000.0
    camera.position=view._beacon.global_position
    var near_case: Dictionary=view.projected_readability(camera)
    extra_cases.append({"kind":"near_plane_crossing","passed":not near_case.passed and not near_case.projection_valid})
    configure_camera(camera,"gameplay")
    view.scale=Vector3(2.0,1.0,1.0)
    var nonuniform: Dictionary=view.projected_readability(camera)
    extra_cases.append({"kind":"unsupported_nonuniform_parent","passed":not nonuniform.passed and not nonuniform.projection_valid})
    view.scale=Vector3.ONE
    for extra in extra_cases:
        if not extra.passed:errors.append(extra)
    var output="/tmp/t10-feedback-layout.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--out="): output=arg.trim_prefix("--out=")
    var f=FileAccess.open(output,FileAccess.WRITE)
    f.store_string(JSON.stringify({"branch_count":branches.size(),"case_count":rows.size(),"rows":rows,"extra_cases":extra_cases,"transition_cases":transition_cases,"errors":errors,"passed":errors.is_empty(),"rendered_proof":false,"task_approved":false}))
    f.close()
    print(JSON.stringify({"branches":branches.size(),"cases":rows.size(),"failures":errors.size(),"passed":errors.is_empty()}))
    quit(0 if errors.is_empty() else 1)
func configure_camera(camera: Camera3D,angle: String):
    camera.fov=44.0
    var target=Vector3(0.0,0.9,0.0)
    var up=Vector3.UP
    match angle:
        "front": camera.position=Vector3(0,3.5,7.5)
        "side": camera.position=Vector3(7.5,3.5,0)
        "three-quarter": camera.position=Vector3(5.6,3.8,6.2)
        "overhead":
            camera.position=Vector3(0,9,0.05)
            camera.fov=40
            target=Vector3(0,0.8,0)
            up=Vector3.FORWARD
        "gameplay":
            camera.position=Vector3(5.2,7,8.7)
            camera.fov=48
            target=Vector3(0,0.75,0)
        "detail":
            camera.position=Vector3(3.5,2.9,5.2)
            camera.fov=40
            target=Vector3(0,1.15,0)
    camera.look_at(target,up)
