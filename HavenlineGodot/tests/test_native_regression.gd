extends SceneTree

const Sim = preload("res://scripts/native_simulation.gd")
const Saves = preload("res://scripts/save_store.gd")
var failures: Array = []
var checks: Array = []

func check(label: String, passed: bool):
	checks.append({"name": label, "passed": passed})
	if not passed:
		failures.append(label)

func settle(sim, where: Vector2, seconds: float):
	sim.position = where
	sim.velocity = Vector2.ZERO
	for i in range(int(ceil(seconds * 60))):
		sim.step(1.0 / 60.0, Vector2.ZERO)

func _initialize():
	var s = Sim.new()
	check("C1 lead retains C2/C3/C4 companions", s.companions.map(func(c): return c.id) == [2, 3, 4])
	check("C2 lead retains C1/C3/C4 companions", Sim.new({}, 2).companions.map(func(c): return c.id) == [1, 3, 4])
	s.inventory.wood = 10000
	settle(s, s.resources[0].position + Vector2(0, 1.1), 0.7)
	check("gathering continues above 10,000 units", s.inventory.wood > 10000)
	s = Sim.new()
	s.inventory.wood = 18
	settle(s, Sim.point(s.contract.world.furnace) + Vector2(0, 1.5), 3.1)
	check("wood alone cannot unlock furnace L2", s.level == 1 and s.stored.wood == 18)
	s.inventory.stone = 6
	settle(s, s.position, 1.1)
	check("real timed delivery reaches L2 with wood AND stone", s.level == 2 and s.stored.stone == 6 and is_equal_approx(s.warmth(), 8.0))
	settle(s, Sim.point(s.contract.world.survivor) + Vector2(0, 1.1), 2.1)
	check("rescue does not finish early", not s.rescued)
	settle(s, s.position, 0.15)
	check("rescue activates additional helper", s.rescued and s.companions.size() == 4 and s.companions[-1].id == 5)
	s.wave_timer = 0
	s.step(1.0/60, Vector2.ZERO)
	check("wave stays locked without north barricade", not s.wave_active)
	s.inventory.wood = 8
	s.inventory.stone = 2
	settle(s, s.defenses.north.position + Vector2(0, 1.1), 2.6)
	check("barricade does not complete with missing stone", not s.defenses.north.built)
	s.inventory.stone = 1
	s.wave_timer = 48
	settle(s, s.position, 0.3)
	check("north barricade completes through delivery", s.defenses.north.built and s.gate_open())
	check("first wave preserves countdown", not s.wave_active and s.wave_timer > 47.5)
	s.wave_timer = 0
	s.step(1.0/60, Vector2.ZERO)
	check("first wave contains three wolves", s.wave_active and s.enemies.size() == 3)
	for e in s.enemies: e.health = 0
	s.step(1.0/60, Vector2.ZERO)
	check("cleared wave unlocks frontier", s.forest_unlocked and s.completed_waves == 1 and not s.wave_active)
	check("wave delay falls to 45 seconds", is_equal_approx(s.wave_timer, 45))
	s = Sim.new()
	settle(s, s.resources[0].position + Vector2(0, 1.1), 0.3)
	var key: String = "gather:" + s.resources[0].id
	var before: float = s.action_clocks[key]
	s.step(1.0/60, Vector2(0.2, 0))
	check("movement preserves accumulated gather progress", is_equal_approx(s.action_clocks[key], before))
	s.enemies.append({"id":"urgent", "position":s.position, "health":65.0, "cooldown":0.0})
	check("enemy priority interrupts resource target", s.choose_action().kind == "enemy")
	s.position = Vector2(100000, -100000)
	s.step(1.0/60, Vector2.ZERO)
	check("world bounds recover invalid positions", absf(s.position.x) <= 14.20001 and absf(s.position.y) <= 16.20001)
	var path := "user://test-save.json"
	check("atomic save writes successfully", Saves.write_state(s.snapshot(), path) == OK)
	var original := Saves.read_state(path)
	check("save retains exact unlimited inventory", Sim.KINDS.all(func(kind): return original.inventory[kind] == s.inventory[kind]))
	var reloaded = Sim.new()
	check("saved JSON restores playable state", reloaded.restore(original) and reloaded.inventory == s.inventory)
	var invalid := original.duplicate(true)
	invalid.inventory.wood = -1
	check("invalid save rejected without changing live state", not reloaded.restore(invalid) and reloaded.inventory == s.inventory)
	var helper_state = Sim.new()
	helper_state.rescued = true
	helper_state.companions.append({"id":5,"position":Vector2(2,3),"cooldown":.4,"job":"gather","cargo":3})
	var helper_copy = Sim.new()
	check("worker cargo persists across restart", helper_copy.restore(helper_state.snapshot()) and helper_copy.companions[-1].cargo == 3)
	s.inventory.wood += 5
	check("second save creates recovery backup", Saves.write_state(s.snapshot(), path) == OK)
	var broken := FileAccess.open(path, FileAccess.WRITE)
	broken.store_string("interrupted write")
	broken.close()
	check("corrupt primary recovers previous valid save", Saves.read_state(path).inventory == original.inventory)
	for suffix in ["", ".bak", ".tmp"]: DirAccess.remove_absolute(path + suffix)
	print(JSON.stringify({"passed": failures.is_empty(), "checks": checks, "failures": failures}))
	quit(0 if failures.is_empty() else 1)
