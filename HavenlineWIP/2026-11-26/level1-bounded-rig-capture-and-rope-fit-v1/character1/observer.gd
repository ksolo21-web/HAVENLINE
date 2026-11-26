extends SceneTree
## Detached test leaf; all actual movement/phase from exact stock game.
const GAME = preload("res://previews/integrated_opening.tscn")
const SAVE = preload("res://opening_save.gd")
const DRY = preload("res://previews/fixture_dry_shore_sweep.gd")
const HERO := "res://assets/characters/Character1.glb"
const HERO_SHA := "95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"
const CENTER := Vector2(450.,375.)
const GESTURE := 17
const PRE := 8
const POST := 12
const MAX_ROWS := 180
var clip_kind := ""
var motion_count := 0
var rgb := false
var writer: NativeFrameWriter
var native_format := ""
var native_path := ""
var expected_offset := Vector2.ZERO
var previous := Vector3.ZERO
var keys: Array[int] = []
var game
var pl: AnimationPlayer
var active := false
var failed := false
var t := 0
var n_draw := 0
var pin := {}
var rows: Array[Dictionary] = []
var pending := {}

class NativeFrameWriter extends RefCounted:
	const SLOT_LIMIT := 8
	const RGB_BYTES := 1280*720*3
	const RGBA_BYTES := 1280*720*4
	var m := Mutex.new()
	var wake := Semaphore.new()
	var worker := Thread.new()
	var file: FileAccess
	var pending_frames: Array[Dictionary] = []
	var reserved := 0
	var peak := 0
	var accepted := 0
	var written := 0
	var expected_bytes := 0
	var accepting := true
	var ending := false
	var reason := ""
	var digest_rows: Array[String] = []

	func start(path: String) -> bool:
		if FileAccess.file_exists(path):
			return false
		file=FileAccess.open(path, FileAccess.WRITE)
		if file==null:
			return false
		if worker.start(Callable(self,"run_worker"))!=OK:
			file.close()
			return false
		return true

	# Slots cover pending plus in-flight bytes, never just queue length.
	# This section does not perform readback, hash or I/O under the mutex.
	# Busy lock fails closed rather than waiting in the draw callback.
	func push(serial: int, bytes: PackedByteArray) -> String:
		if not m.try_lock():
			return "producer-lock-busy"
		var fail_reason := reason
		if fail_reason.is_empty() and (not accepting or ending or serial!=accepted+1 or reserved>=SLOT_LIMIT):
			fail_reason="writer-stopped-sequence-or-cap"
		if fail_reason.is_empty() and (bytes.size() not in [RGB_BYTES,RGBA_BYTES] or (expected_bytes!=0 and expected_bytes!=bytes.size())):
			fail_reason="raw-frame-size-or-format-drift"
		if fail_reason.is_empty():
			expected_bytes=bytes.size()
			accepted=serial
			reserved+=1
			peak=maxi(peak,reserved)
			# PackedByteArray is a read-only value by convention here; producer never
			# mutates it after handoff; worker uses it only for hashing and store_buffer.
			pending_frames.push_back({"serial":serial,"bytes":bytes})
		m.unlock()
		if fail_reason.is_empty():
			wake.post()
		return fail_reason

	func run_worker() -> void:
		while true:
			wake.wait()
			m.lock()
			if not accepting or (ending and pending_frames.is_empty()):
				m.unlock()
				break
			if pending_frames.is_empty():
				m.unlock()
				continue
			var rec: Dictionary=pending_frames.pop_front()
			var serial: int=rec.serial
			var bytes: PackedByteArray=rec.bytes
			var pre := written
			m.unlock()
			var result := ""
			var digest := PackedByteArray()
			if serial!=pre+1 or file.get_position()!=pre*bytes.size():
				result="output-order-or-byte-prefix"
			else:
				var hc := HashingContext.new()
				if hc.start(HashingContext.HASH_SHA256)!=OK or hc.update(bytes)!=OK:
					result="frame-hash-failed"
				else:
					digest=hc.finish()
					if digest.size()!=32:
						result="frame-hash-size"
					else:
						file.store_buffer(bytes)
						if file.get_error()!=OK or file.get_position()!=serial*bytes.size():
							result="native-raw-short-write-or-disk-error"
			# Drop both producer-owned references before releasing this slot.
			rec.clear()
			bytes=PackedByteArray()
			m.lock()
			reserved-=1
			if result.is_empty() and accepting:
				written=serial
				digest_rows.append(digest.hex_encode())
			elif not result.is_empty():
				reason=result
				accepting=false
			var stop := not accepting
			m.unlock()
			if stop:
				break
		file.flush()
		var flush_status := file.get_error()
		file.close()
		if flush_status!=OK:
			m.lock()
			if reason.is_empty():
				reason="native-raw-flush-error"
			m.unlock()

	# Not called in frame callback. Abort invalidates the whole take.
	func close_and_report(abort: bool) -> Dictionary:
		if not worker.is_started():
			return {}
		m.lock()
		ending=true
		if abort:
			accepting=false
			pending_frames.clear()
		m.unlock()
		wake.post()
		worker.wait_to_finish()
		return {"written":written,"accepted":accepted,"outstanding":reserved,"peak":peak,"reason":reason,
			"bytes_per_frame":expected_bytes,"hashes":digest_rows.duplicate()}

func fail(code: String, detail: Dictionary) -> void:
	if failed:
		return
	failed=true
	active=false
	print("C1_NORMAL_REJECT ", JSON.stringify({"reason":code,"detail":detail,"tick":t,"frame":Engine.get_physics_frames()}))
	call_deferred("finish_failed")

func finish_failed() -> void:
	if writer!=null:
		writer.close_and_report(true)
	quit(5)

func _initialize() -> void:
	call_deferred("run")

func tx(w: Transform3D) -> Array:
	return [vec(w.origin), vec(w.basis.x), vec(w.basis.y), vec(w.basis.z)]

func vec(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

func vv(v: Vector2) -> Array:
	return [v.x,v.y]

func ev(down: bool, offset: Vector2 = Vector2.ZERO) -> void:
	if down and offset!=Vector2.ZERO:
		var drag := InputEventScreenDrag.new()
		drag.index=GESTURE
		drag.device=1
		drag.position=CENTER+offset
		game._input(drag)
	else:
		var touch := InputEventScreenTouch.new()
		touch.index=GESTURE
		touch.device=1
		touch.pressed=down
		touch.position=CENTER
		game._input(touch)

func protected() -> Dictionary:
	var tree = game.resource_tree
	var groups := []
	for g in game.gates:
		groups.append({"open":g.target_open,"angle":g.angle,"visible":g.is_visible_in_tree()})
	var visible := {}
	for k in game.wood_visuals:
		visible[k]=game.wood_visuals[k].is_visible_in_tree()
	return {"wood":game.ledger.stock.wood,"sources":game.ledger.collected.duplicate(true),
		"snapshot":game.ledger.snapshot(),"receipt":game.ledger.receipt.duplicate(true),
		"trees":[tree.phase,tree.strikes,tree.blocked,game.tree_input_sequence],"gates":groups,
		"camp":game.camp_built.is_visible_in_tree(),"loose_wood":visible,
		"save":[game.persist_requested,game.persist_blocked],
		"world":tx(game.global_transform),"scene":game.scene_file_path}

func cam_check(camera: Camera3D) -> bool:
	return camera==root.get_camera_3d() and camera.projection==Camera3D.PROJECTION_ORTHOGONAL and is_equal_approx(camera.size,13.) and root.size==Vector2i(1280,720) and camera.global_basis.z.normalized().dot(Vector3(7,11,11).normalized())>.999999


var skin_mesh: MeshInstance3D
var skin_skeleton: Skeleton3D
var skin_spine: int
var slots: Array[int] = []
var static_buffers := {}
var sparse_buffers := {}
var shape_rows: Array[Dictionary] = []
var bind_notes: Array[Dictionary] = []
var palette_rows: Array[Dictionary] = []

func f32(a: PackedVector3Array) -> PackedByteArray:
	var f := PackedFloat32Array()
	f.resize(3*a.size())
	for i in a.size():
		f[3*i]=a[i].x
		f[3*i+1]=a[i].y
		f[3*i+2]=a[i].z
	return f.to_byte_array()

func prepare_skin() -> bool:
	var src: Node3D
	for child in game.actor.get_children():
		if child is Node3D and child.scene_file_path==HERO:
			if src!=null:
				fail("palette-duplicate-import",{})
				return false
			src=child as Node3D
	if src==null or not src.is_ancestor_of(pl):
		fail("palette-exact-import-owner",{})
		return false
	var all := src.find_children("*","MeshInstance3D",true,false)
	if all.size()!=1:
		fail("palette-import-mesh-census",{"found":all.size()})
		return false
	skin_mesh=all[0] as MeshInstance3D
	skin_skeleton=skin_mesh.get_node_or_null(skin_mesh.skeleton) as Skeleton3D
	var m := skin_mesh.mesh as ArrayMesh
	var s := skin_mesh.skin
	if skin_skeleton==null or not src.is_ancestor_of(skin_skeleton) or not skin_mesh.is_visible_in_tree() or not m or not s or s.get_bind_count()!=66 or skin_skeleton.get_bone_count()!=66 or m.get_blend_shape_count()!=0:
		fail("palette-native-skin-scope",{})
		return false
	skin_spine=skin_skeleton.find_bone("Spine02")
	if skin_spine<0:
		fail("palette-spine-identity",{})
		return false
	for i in 66:
		var name := String(s.get_bind_name(i))
		var bone: int=skin_skeleton.find_bone(name) if not name.is_empty() else s.get_bind_bone(i)
		var b := s.get_bind_pose(i)
		if bone<0 or bone>=66 or bone in slots or not b.is_finite():
			fail("palette-native-slot-mapping",{"slot":i,"bone":bone,"name":name})
			return false
		slots.append(bone)
		bind_notes.append({"slot":i,"bone":bone,"name":String(skin_skeleton.get_bone_name(bone)),"bind":tx(b),"rest":tx(skin_skeleton.get_bone_global_rest(bone))})
	var total_faces := 0
	for i in m.get_surface_count():
		var a := m.surface_get_arrays(i)
		var orig: PackedVector3Array=a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array=a[Mesh.ARRAY_INDEX]
		var w: PackedFloat32Array=a[Mesh.ARRAY_WEIGHTS]
		var j: PackedInt32Array=a[Mesh.ARRAY_BONES]
		if m.surface_get_primitive_type(i)!=Mesh.PRIMITIVE_TRIANGLES or orig.is_empty() or idx.is_empty() or idx.size()%3!=0 or w.size()!=4*orig.size() or j.size()!=4*orig.size():
			fail("palette-static-stream-domain",{"surface":i})
			return false
		total_faces+=int(idx.size()/3)
		var pfx := "s"+str(i)+"-"
		static_buffers[pfx+"source.f32"]=f32(orig)
		static_buffers[pfx+"indices.i32"]=idx.to_byte_array()
		static_buffers[pfx+"weights.f32"]=w.to_byte_array()
		static_buffers[pfx+"joints.i32"]=j.to_byte_array()
		shape_rows.append({"rows":orig.size(),"indices":idx.size(),"prefix":pfx})
	if total_faces!=96001:
		fail("palette-face-census",{"faces":total_faces})
		return false
	return true

func sample_skin(c: Dictionary) -> bool:
	var pal: Array = []
	var s := skin_mesh.skin
	var before := Engine.get_physics_frames()
	var before_process := Engine.get_process_frames()
	if not skin_mesh.is_visible_in_tree() or before!=int(c.physics) or before_process!=int(c.process) or c.clip!="l1_hero_preview/"+clip_kind:
		fail("palette-sample-not-identical-draw",{"common":c,"physics":before,"process":before_process})
		return false
	for i in 66:
		var p := skin_skeleton.get_bone_global_pose(slots[i])
		var prod := p*s.get_bind_pose(i)
		if not p.is_finite() or not prod.is_finite():
			fail("palette-joint-nonfinite",{"slot":i})
			return false
		pal.append([tx(p),tx(prod)])
	var sp := skin_skeleton.get_bone_global_pose(skin_spine)
	if t in keys:
		var baked := skin_mesh.bake_mesh_from_current_skeleton_pose()
		if not baked or baked.get_surface_count()!=shape_rows.size():
			fail("palette-sparse-native-bake",{"surfaces":shape_rows.size()})
			return false
		for i in shape_rows.size():
			var ba := baked.surface_get_arrays(i)
			var idx: PackedInt32Array=ba[Mesh.ARRAY_INDEX]
			var positions: PackedVector3Array=ba[Mesh.ARRAY_VERTEX]
			var pfx: String=shape_rows[i].prefix
			if baked.surface_get_primitive_type(i)!=Mesh.PRIMITIVE_TRIANGLES or positions.size()!=shape_rows[i].rows or idx.to_byte_array()!=static_buffers[pfx+"indices.i32"]:
				fail("palette-bake-index-or-row-mismatch",{"surface":i})
				return false
			# Keep packed native positions in memory without converting/writing on step.
			sparse_buffers[str(t)+"-"+pfx+"baked.f32"]=positions
	if Engine.get_physics_frames()!=before or Engine.get_process_frames()!=before_process or pl.current_animation_position!=float(c.phase):
		fail("palette-callback-advanced",{})
		return false
	palette_rows.append({"tick":t,"physics":before,"process":before_process,"draw":n_draw,"phase":c.phase,"clip":c.clip,
		"pose_and_product_by_slot":pal,"mesh":tx(skin_mesh.global_transform),"skeleton":tx(skin_skeleton.global_transform),
		"spine_local":tx(sp),"spine_world":tx(skin_skeleton.global_transform*sp)})
	return true

func finish_skin() -> bool:
	if palette_rows.size()!=3 or palette_rows.front().tick!=keys.front() or palette_rows.back().tick!=keys.back():
		fail("palette-window-count",{"rows":palette_rows.size()})
		return false
	var m := skin_mesh.mesh as ArrayMesh
	for i in shape_rows.size():
		var a := m.surface_get_arrays(i)
		var pfx: String=shape_rows[i].prefix
		if f32(a[Mesh.ARRAY_VERTEX])!=static_buffers[pfx+"source.f32"] or a[Mesh.ARRAY_BONES].to_byte_array()!=static_buffers[pfx+"joints.i32"] or a[Mesh.ARRAY_WEIGHTS].to_byte_array()!=static_buffers[pfx+"weights.f32"] or a[Mesh.ARRAY_INDEX].to_byte_array()!=static_buffers[pfx+"indices.i32"]:
			fail("palette-immutable-stream-after-route",{"surface":i})
			return false
	var out := OS.get_environment("HVN_C1_NORMAL_OUT")
	if out.is_empty() or not DirAccess.dir_exists_absolute(out):
		fail("palette-owned-output-missing",{})
		return false
	var meta := {}
	for key in static_buffers.keys()+sparse_buffers.keys():
		var payload: PackedByteArray=static_buffers[key] if static_buffers.has(key) else f32(sparse_buffers[key])
		var fn := out.path_join(key)
		var obj: FileAccess = FileAccess.open(fn,FileAccess.WRITE) if not FileAccess.file_exists(fn) else null
		if obj==null:
			fail("palette-owned-output-write",{"key":key})
			return false
		obj.store_buffer(payload)
		obj.close()
		if FileAccess.get_file_as_bytes(fn)!=payload:
			fail("palette-owned-output-readback",{"key":key})
			return false
		meta[key]={"sha256":FileAccess.get_sha256(fn),"bytes":payload.size()}
	var json_path := out.path_join("palette.json")
	var json_file: FileAccess = FileAccess.open(json_path,FileAccess.WRITE) if not FileAccess.file_exists(json_path) else null
	if json_file==null:
		fail("palette-owned-metadata-write",{})
		return false
	json_file.store_string(JSON.stringify({"bindings":bind_notes,"surfaces":shape_rows,"streams":meta,"rows":palette_rows,"gpu_vertex_readback":false}))
	json_file.close()
	return true

func draw() -> void:
	if not active or failed:
		return
	var phys := Engine.get_physics_frames()
	var proc := Engine.get_process_frames()
	if pending.is_empty() or phys!=int(pending.frame) or t!=int(pending.tick) or n_draw+1!=t or rows.size()>=MAX_ROWS:
		fail("draw-gap-duplicate-not-same-tick-or-cap",{"queued":pending,"draw_physics":phys,"t":t})
		return
	var a: CharacterBody3D = game.actor
	var camera: Camera3D = game.camera
	var p := a.position
	var held := t>PRE and t<=PRE+motion_count
	var f := Vector2(p.x-previous.x,p.z-previous.z)
	var pose := String(pl.current_animation)
	var phase := pl.current_animation_position
	var step_expected := ((4.0 if clip_kind=="run" else 1.5)/60.0) if held else 0.0
	if not game.bound or protected()!=pin or not cam_check(camera) or not a.is_on_floor() or not p.is_finite() or absf(p.z-11.8)>.025 or not DRY.dry_footprint(Vector2(p.x,p.z),.31,game.bank_side):
		fail("stock-state-camera-grounding-or-dry-corridor",{"p":vec(p),"stock_camera":cam_check(camera)})
		return
	if held:
		if game.touch_id!=GESTURE or game.touch_origin!=CENTER or (game.touch_now-CENTER-expected_offset).length()>.0001 or absf(f.x-step_expected)>.002 or absf(f.y)>.0005 or absf(wrapf(a.rotation.y-PI*.5,-PI,PI))>.002 or pose!="l1_hero_preview/"+clip_kind:
			fail("walk-run-ordinary-input-pose-speed-yaw",{"phase":phase,"clip":pose,"move":vv(f),"held":held})
			return
	elif game.touch_id!=-1 or f.length()>.0005 or pose!="l1_hero_preview/idle":
		fail("stock-idle-before-after",{"pose":pose,"move":vv(f),"pressed":game.touch_id})
		return
	if not pl.is_playing() or not is_finite(phase):
		fail("clip-phase-invalid",{"clip":pose})
		return
	n_draw+=1
	var row := {"tick":t,"draw":n_draw,"physics":phys,"process":proc,"clip":pose,"phase":phase,
		"length":pl.current_animation_length,"held":held,"position":vec(p),"velocity":vec(a.velocity),
		"actor":tx(a.global_transform),"camera":tx(camera.global_transform),"floor":true,"delta_xz":vv(f),
		"input":[game.touch_id,vv(game.touch_origin),vv(game.touch_now)]}
	if t in keys and not sample_skin(row):
		return
	if rgb:
		var pic := root.get_texture().get_image()
		if pic==null or pic.is_empty() or pic.get_size()!=Vector2i(1280,720) or pic.has_mipmaps():
			fail("uncropped-same-draw-native-buffer-invalid",{})
			return
		var fmt := "rgb8" if pic.get_format()==Image.FORMAT_RGB8 else ("rgba8" if pic.get_format()==Image.FORMAT_RGBA8 else "")
		if fmt.is_empty() or (not native_format.is_empty() and native_format!=fmt):
			fail("unexpected-or-changing-native-color-format",{"format":pic.get_format()})
			return
		native_format=fmt
		var payload := pic.get_data()
		pic=null
		var status := writer.push(n_draw,payload)
		if not status.is_empty():
			fail("bounded-writer-refused-same-draw",{"writer":status})
			return
	if Engine.get_physics_frames()!=phys or Engine.get_process_frames()!=proc or pl.current_animation_position!=phase or root.get_camera_3d()!=camera or tx(camera.global_transform)!=row.camera:
		fail("observer-drifted-after-capture",{})
		return
	rows.append(row)
	pending={}

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size()!=2 or args[0] not in ["--c1-walk","--c1-run"] or args[1] not in ["--trace-only","--native-rgb"] or SAVE.new().requested(args) or DisplayServer.get_name()!="X11" or Engine.physics_ticks_per_second!=60:
		fail("entry-not-exact-native-no-save-60hz",{"args":args})
		return
	clip_kind=args[0].trim_prefix("--c1-")
	rgb=args[1]=="--native-rgb"
	motion_count=98 if clip_kind=="run" else 154
	keys.assign([PRE+12,PRE+49,PRE+85] if clip_kind=="run" else [PRE+12,PRE+82,PRE+152])
	game=GAME.instantiate()
	root.add_child(game)
	if not game.bound or game.scene_file_path!="res://previews/integrated_opening.tscn" or game.global_transform!=Transform3D.IDENTITY:
		fail("scene-not-stock-and-unshifted-root",{})
		return
	pl=game.hero_locomotion.player
	var key := StringName("l1_hero_preview/"+clip_kind)
	var nominal := 1.25 if clip_kind=="run" else 2.3333332538604736
	if not is_instance_valid(pl) or FileAccess.get_sha256(HERO)!=HERO_SHA or not pl.has_animation(key) or absf(pl.get_animation(key).length-nominal)>.0005 or pl.get_animation(key).loop_mode!=Animation.LOOP_LINEAR or not prepare_skin():
		fail("asset-import-clip-identity",{})
		return
	for frame in range(10):
		await physics_frame
	pin=protected()
	var start: Vector3=game.actor.position
	var camera: Camera3D=game.camera
	if absf(start.x+3.25)>.001 or absf(start.z-11.8)>.001 or not game.actor.is_on_floor() or pin.wood!=0 or not pin.sources.is_empty() or not pin.receipt.is_empty() or pin.camp or pin.save!=[false,false] or pin.trees[1]!=0 or not cam_check(camera):
		fail("unfresh-spawn-baseline",{"at":vec(start),"protected":pin})
		return
	var x: Vector3=Vector3.RIGHT.rotated(Vector3.UP,-atan2(7.,11.))
	expected_offset=Vector2(x.x,x.z)*(82.0 if clip_kind=="run" else 30.75)
	if rgb:
		var out := OS.get_environment("HVN_C1_NORMAL_OUT")
		if out.is_empty() or not DirAccess.dir_exists_absolute(out):
			fail("owned-rgb-target-unavailable",{})
			return
		native_path=out.path_join("native.rgb")
		writer=NativeFrameWriter.new()
		if not writer.start(native_path):
			fail("bounded-writer-open-or-start",{})
			return
	active=true
	RenderingServer.frame_post_draw.connect(draw)
	while t<PRE+motion_count+POST and not failed:
		if not pending.is_empty():
			fail("prior-native-frame-missing",{"queued":pending})
			return
		previous=game.actor.position
		t+=1
		if t==PRE+1:
			ev(true)
			ev(true,expected_offset)
		elif t==PRE+motion_count+1:
			ev(false)
		pending={"frame":Engine.get_physics_frames(),"tick":t}
		await physics_frame
	active=false
	RenderingServer.frame_post_draw.disconnect(draw)
	if failed:
		return
	if n_draw!=t or not pending.is_empty() or game.touch_id!=-1 or protected()!=pin or not cam_check(camera):
		fail("end-state-or-frame-count",{})
		return
	var writer_result := {}
	if rgb:
		writer_result=writer.close_and_report(false)
		if writer_result.is_empty() or writer_result.accepted!=rows.size() or writer_result.written!=rows.size() or writer_result.outstanding!=0 or not writer_result.reason.is_empty() or writer_result.hashes.size()!=rows.size() or writer_result.peak<1 or writer_result.peak>NativeFrameWriter.SLOT_LIMIT:
			fail("bounded-writer-final-order-count-flush-or-backpressure",writer_result)
			return
	if not finish_skin():
		return
	print("C1_NORMAL_RECEIPT ",JSON.stringify({"asset":HERO_SHA,"kind":clip_kind,"rgb":rgb,"pre":PRE,"post":POST,
		"motion_rows":motion_count,"keys":keys,"rows":rows,"start":vec(start),"end":vec(game.actor.position),"protected":pin,
		"rgb_sha256":FileAccess.get_sha256(native_path) if rgb else "","native_format":native_format,"writer":writer_result,"image":[1280,720],"stock_ordinary_touch_only":true}))
	quit(0)
