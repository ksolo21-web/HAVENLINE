class_name HavenlineTransferFeedback
extends Node3D

# Resource feedback uses the actual authored meshes, not floating counters or
# substitute primitive items. It is presentation only and cannot grant resources.
var loader: Callable
var flights: Array = []
var pools: Dictionary = {"wood":[],"stone":[],"metal":[],"fuel":[]}

func transfer(kind: String, start: Vector3, finish: Vector3):
	if not pools.has(kind) or flights.size() >= 48: return
	var node: Node3D = pools[kind].pop_back() if not pools[kind].is_empty() else loader.call(kind,self)
	node.visible = true
	node.scale = Vector3.ONE * (.55 if kind == "wood" else .24)
	node.position = start
	flights.append({"node":node,"kind":kind,"start":start,"finish":finish,"time":0.0})

func _process(dt: float):
	for index in range(flights.size() - 1,-1,-1):
		var item: Dictionary = flights[index]
		item.time += dt
		var t := minf(1.0,item.time / .42)
		item.node.position = item.start.lerp(item.finish, t) + Vector3.UP * sin(t * PI) * .65
		item.node.rotate_x(dt * 2.5)
		if t >= 1.0:
			item.node.visible = false
			pools[item.kind].append(item.node)
			flights.remove_at(index)
