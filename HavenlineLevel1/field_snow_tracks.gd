extends Node3D
## Real foot landings when the character has the Havenline rig. Unrigged agents
## use the same bounded renderer with distance-driven alternating contacts.
## Add the living survivor or worker scene root to this group in its scene or
## before add_child(). Its Havenline foot bones are used when available.
const SURVIVOR_GROUP := &"snow_track_survivors"
const LIFE := 17.0
const CELL := 12.0
const PER_CELL := 96
const MAX_MARKS := 720
const NAMES := {"human": ["Foot.L","Foot.R"], "wolf": ["FrontLPaw","RearRPaw","FrontRPaw","RearLPaw"]}
var clock := 0.0
var living := {}
var chunks := {}
var total := 0
var mask: Callable
var material := ShaderMaterial.new()
var plane := PlaneMesh.new()
var next_trim := 0.0

func _init() -> void:
	process_physics_priority = 90
	material.shader = preload("res://assets/field_world/snow_print.gdshader")
	material.set_shader_parameter("track_mask",preload("res://assets/field_world/snow_prints.png"))
	plane.size = Vector2.ONE
	plane.material = material

func _ready() -> void:
	get_tree().node_added.connect(_discover_survivor)
	for survivor in get_tree().get_nodes_in_group(SURVIVOR_GROUP):
		_discover_survivor(survivor)

func _exit_tree() -> void:
	if get_tree().node_added.is_connected(_discover_survivor):
		get_tree().node_added.disconnect(_discover_survivor)

func _discover_survivor(node: Node) -> void:
	if node is Node3D and node.is_in_group(SURVIVOR_GROUP) and get_parent().is_ancestor_of(node):
		register_actor(node, "human")

func configure(snow_query: Callable) -> void:
	mask = snow_query

func register_actor(actor: Node3D, species: String = "human", size: float = 1.0, sole_sample := Callable()) -> void:
	if not is_instance_valid(actor) or not NAMES.has(species): return
	if living.has(actor): return
	if not actor.is_inside_tree() or not actor.is_node_ready():
		var deferred_registration:=register_actor.bind(actor,species,size,sole_sample)
		if not actor.ready.is_connected(deferred_registration):
			actor.ready.connect(deferred_registration,CONNECT_ONE_SHOT)
		return
	var feet: Array = []
	var rigs := actor.find_children("*","Skeleton3D",true,false)
	var skeleton: Skeleton3D
	for rig: Skeleton3D in rigs:
		if rig.find_bone(NAMES[species][0])>=0:
			skeleton=rig
			break
	if skeleton:
		for name_: String in NAMES[species]:
			var id := skeleton.find_bone(name_)
			if id < 0:
				feet.clear()
				break
			var rest := skeleton.to_global(skeleton.get_bone_global_rest(id).origin)
			feet.append({"bone":id,"height":rest.y-actor.global_position.y,"lifted":false,"last":Vector3.INF})
	living[actor]={"species":species,"size":maxf(.1,size),"skeleton":skeleton,"feet":feet,"sole_sample":sole_sample,"previous":actor.global_position,"distance":0.0,"step":0,"moving_until":0.0}
	var cleanup:=unregister_actor.bind(actor)
	if not actor.tree_exiting.is_connected(cleanup):
		actor.tree_exiting.connect(cleanup,CONNECT_ONE_SHOT)

func unregister_actor(actor: Node3D) -> void:
	living.erase(actor)

func reset_actor(actor: Node3D) -> void:
	if not living.has(actor): return
	var data: Dictionary=living[actor]
	data.previous=actor.global_position
	data.distance=0.0
	data.step=0
	data.moving_until=0.0
	for foot in data.feet:
		foot.lifted=false
		foot.last=Vector3.INF

func _physics_process(delta: float) -> void:
	clock += delta
	for actor: Node3D in living.keys():
		var data: Dictionary=living[actor]
		var previous: Vector3=data.previous
		var now := actor.global_position
		var travel := (now-previous).slide(Vector3.UP)
		var distance := travel.length()
		data.previous=now
		if not actor.is_visible_in_tree() or ("hp" in actor and actor.hp<=0) or distance>maxf(2.5,12.0*delta*data.size):
			reset_actor(actor)
			continue
		if distance>.025*delta: data.moving_until=clock+.16
		if not data.feet.is_empty():
			_sample_feet(actor,data)
		elif distance>.025*delta:
			_sample_stride(actor,data,previous,travel,distance)
	if clock>=next_trim:
		next_trim=clock+.22
		_trim(false)

func _sample_feet(actor: Node3D,data: Dictionary) -> void:
	var skel: Skeleton3D=data.skeleton
	var size:float=data.size
	var wolf:bool=data.species=="wolf"
	var forward:=actor.global_basis.z.slide(Vector3.UP).normalized()
	var contacts := PackedVector3Array()
	if data.sole_sample.is_valid() and clock <= data.moving_until:
		contacts = data.sole_sample.call()
	for i in data.feet.size():
		var foot: Dictionary=data.feet[i]
		var p:=skel.to_global(skel.get_bone_global_pose(foot.bone).origin)
		var lift:float=p.y-actor.global_position.y-foot.height
		var threshold := .025 * size
		if contacts.size() == data.feet.size():
			p = contacts[i]
			lift = p.y - actor.global_position.y
			threshold = .005 * size
		if lift>.052*size:
			foot.lifted=true
		elif foot.lifted and lift < threshold:
			foot.lifted=false
			if contacts.is_empty():
				p+=forward*(.08 if not wolf else .045)*size
			p.y=actor.global_position.y
			if clock<=data.moving_until and (not (foot.last as Vector3).is_finite() or p.distance_to(foot.last)>.07*size):
				_emit_mark(p,atan2(forward.x,forward.z),wolf,i in ([2,1] if wolf else [1]),size)
				foot.last=p

func _sample_stride(actor:Node3D,data:Dictionary,start:Vector3,travel:Vector3,distance:float) -> void:
	var wolf:bool=data.species=="wolf"
	var size:float=data.size
	var span:float=(.245 if wolf else .56)*size
	var remaining:=distance
	var forward:=travel/distance
	var right:=Vector3(forward.z,0,-forward.x)
	while data.distance+remaining>=span:
		var advance:float=span-data.distance
		remaining-=advance
		var center:=start+forward*(distance-remaining)
		var foot:int=data.step%(4 if wolf else 2)
		var left:=foot in [0,3] if wolf else foot==0
		center+=right*(-1 if left else 1)*(.19 if wolf else .11)*size
		if wolf: center+=forward*(.36 if foot in [0,2] else -.36)*size
		_emit_mark(center,atan2(forward.x,forward.z),wolf,not left,size)
		data.step+=1
		data.distance=0.0
	data.distance+=remaining

func _emit_mark(position_:Vector3,heading:float,wolf:bool,right:bool,size:float) -> void:
	var extent:=Vector2(.245,.29) if wolf else Vector2(.225,.365)
	extent*=size
	# Avoid bleeding limbs over the edge of a thawed floor or an ice boundary.
	if not _snow(position_,extent,heading): return
	var key:=Vector2i(floori(position_.x/CELL),floori(position_.z/CELL))
	if total>=MAX_MARKS: _drop_oldest()
	if not chunks.has(key):
		var multi:=MultiMesh.new()
		multi.transform_format=MultiMesh.TRANSFORM_3D
		multi.use_custom_data=true
		multi.mesh=plane
		multi.instance_count=PER_CELL
		multi.visible_instance_count=0
		var node:=MultiMeshInstance3D.new()
		node.name="SnowImpressions"
		node.multimesh=multi
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(node)
		node.global_position=Vector3(key.x*CELL,0,key.y*CELL)
		chunks[key]={"node":node,"marks":[]}
	var chunk:Dictionary=chunks[key]
	var marks:Array=chunk.marks
	if marks.size()>=PER_CELL:
		marks.pop_front()
		total-=1
		_refresh(chunk)
	var stamp={"p":position_,"yaw":heading,"extent":extent,"wolf":wolf,"right":right,"time":clock}
	marks.append(stamp)
	total+=1
	_write(chunk,stamp,marks.size()-1)
	chunk.node.multimesh.visible_instance_count=marks.size()

func _snow(p:Vector3,extent:Vector2,heading:float) -> bool:
	if not mask.is_valid() or not bool(mask.call(p)): return false
	for dir:Vector2 in [Vector2(-1,-1),Vector2(1,-1),Vector2(1,1),Vector2(-1,1)]:
		var d:=Vector3(dir.x*extent.x*.38,0,dir.y*extent.y*.41).rotated(Vector3.UP,heading)
		if not bool(mask.call(p+d)): return false
	return true

func _write(chunk:Dictionary,mark:Dictionary,index:int) -> void:
	var local:Vector3=chunk.node.to_local(mark.p+Vector3.UP*.026)
	var basis:=Basis(Vector3.UP,mark.yaw)*Basis.from_scale(Vector3(mark.extent.x,1.0,mark.extent.y))
	chunk.node.multimesh.set_instance_transform(index,Transform3D(basis,local))
	_update_opacity(chunk,index,mark)

func _update_opacity(chunk:Dictionary,index:int,mark:Dictionary) -> void:
	var opacity:=1.0-smoothstep(LIFE*.5,LIFE,clock-float(mark.time))
	chunk.node.multimesh.set_instance_custom_data(index,Color(0.0,float(mark.wolf),float(mark.right),opacity))

func _refresh(chunk:Dictionary) -> void:
	for i in chunk.marks.size(): _write(chunk,chunk.marks[i],i)
	chunk.node.multimesh.visible_instance_count=chunk.marks.size()

func _drop_oldest() -> void:
	var key:Vector2i=chunks.keys()[0]
	for other:Vector2i in chunks:
		if float(chunks[other].marks.front().time)<float(chunks[key].marks.front().time): key=other
	chunks[key].marks.pop_front()
	total-=1
	_cleanup(key)

func _cleanup(key:Vector2i) -> void:
	var chunk:Dictionary=chunks[key]
	if chunk.marks.is_empty():
		chunk.node.queue_free()
		chunks.erase(key)
	else: _refresh(chunk)

func _trim(recheck:bool) -> void:
	for key:Vector2i in chunks.keys():
		var marks:Array=chunks[key].marks
		var old:=marks.size()
		for i in range(old-1,-1,-1):
			var m:Dictionary=marks[i]
			if clock-m.time>=LIFE or (recheck and not _snow(m.p,m.extent,m.yaw)): marks.remove_at(i)
		if marks.size()!=old:
			total-=old-marks.size()
			_cleanup(key)
		else:
			for i in marks.size():
				if clock-float(marks[i].time)<LIFE*.5: break
				_update_opacity(chunks[key],i,marks[i])

func refresh_surface() -> void:
	_trim(true)
