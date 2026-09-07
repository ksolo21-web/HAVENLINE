class_name HavenlineNativeCollision
extends RefCounted

const BODY_RADIUS := 0.28
const MAX_STEP := 0.10

static func solve(origin: Vector2, displacement: Vector2, obstacles: Array, bounds: Vector2) -> Vector2:
	# Small bounded sweeps prevent crossing thin barricades at sprint speed.
	var steps := clampi(int(ceil(displacement.length() / MAX_STEP)), 1, 256)
	var step := displacement / steps
	var p := project(origin, obstacles, bounds)
	for index in range(steps):
		p = project(p + step, obstacles, bounds)
	return p

static func project(point: Vector2, obstacles: Array, bounds: Vector2) -> Vector2:
	var p := point
	for iteration in range(4):
		for obstacle in obstacles:
			var center: Vector2 = obstacle.center
			if obstacle.has("half"):
				var half: Vector2 = obstacle.half
				var nearest := p.clamp(center - half, center + half)
				var delta := p - nearest
				if delta.length_squared() > 0.0000001:
					if delta.length() < BODY_RADIUS: p = nearest + delta.normalized() * BODY_RADIUS
				else:
					var depths := half + Vector2.ONE * BODY_RADIUS - (p - center).abs()
					if depths.x < depths.y: p.x = center.x + (half.x + BODY_RADIUS) * (-1.0 if p.x < center.x else 1.0)
					else: p.y = center.y + (half.y + BODY_RADIUS) * (-1.0 if p.y < center.y else 1.0)
			else:
				var delta := p - center
				var radius: float = obstacle.radius + BODY_RADIUS
				if delta.length_squared() < radius * radius:
					p = center + (delta.normalized() if delta.length_squared() > .0000001 else Vector2.DOWN) * radius
		p = p.clamp(-bounds, bounds)
	return p

static func outpost(sim) -> Array:
	var result: Array = [
		{"center": sim.point(sim.contract.world.furnace), "radius": 0.94},
		{"center": sim.point(sim.contract.world.storage), "half": Vector2(.86, .67)},
		{"center": Vector2(-6.6, -4.8), "half": Vector2(1.32, 1.05)},
		{"center": Vector2(6.6, -4.8), "half": Vector2(1.32, 1.05)}
	]
	for index in range(38):
		var angle := index * TAU / 38.0
		var center := Vector2(cos(angle)*(15.5+sin(index*12.2)),sin(angle)*18.8)
		result.append({"center":center,"radius":.26*(.85+fmod(index*.17,.5))})
	for resource in sim.resources:
		if resource.units > 0:
			result.append({"center": resource.position, "radius": .26 if resource.kind == "wood" else .67})
	for side in sim.defenses:
		var defense: Dictionary = sim.defenses[side]
		if defense.built and defense.health > 0:
			result.append({"center": defense.position, "half": Vector2(1.50, .18)})
	return result
