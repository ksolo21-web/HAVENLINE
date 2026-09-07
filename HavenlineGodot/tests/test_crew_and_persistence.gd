extends SceneTree
const Sim = preload("res://scripts/simulation.gd")
const Work = preload("res://scripts/crew_work.gd")
const Saves = preload("res://scripts/save_store.gd")
var checks: Array = []
var failures: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func frames(s, seconds: float):
	for i in int(round(seconds * 100)): s.step(0.01, Vector2.ZERO)
func worker(s, cargo := 4) -> Dictionary:
	var c: Dictionary = s.companions[0]
	Work.prepare(c)
	c.job = "gather"
	c.cargo = cargo
	c.position = Sim.point(s.contract.world.furnace) + Vector2(1.4, 0)
	s.presented_actor_ids = [c.id]
	return c
func reject(s, state: Dictionary, label: String):
	var before: Dictionary = s.snapshot()
	check(label, not s.restore(state) and s.snapshot() == before)
func envelope(path: String, state: Dictionary):
	var text := JSON.stringify(state)
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify({"schema":1,"payload":text,"sha256":text.sha256_text()})); f.close()
func _initialize():
	var s = Sim.new()
	var c := worker(s)
	frames(s, .15)
	check("helper cannot deposit before 0.16-second beat", c.cargo == 4 and s.stored.wood == 0)
	frames(s, .01)
	check("helper deposit transfers exactly one unit", c.cargo == 3 and s.stored.wood == 1)
	frames(s, .48)
	check("delivery stays latched until last unit instead of oscillating", c.cargo == 0 and s.stored.wood == 4)
	check("completed delivery releases latch", not c.delivering)
	s = Sim.new(); c = worker(s, 3)
	for r in s.resources:
		if r.kind == "wood": r.units = 0
	frames(s, .48)
	check("partial load returns when no resource remains", c.cargo == 0 and s.stored.wood == 3)
	s = Sim.new(); c = worker(s, 10001)
	frames(s, .16)
	check("routing threshold does not discard an oversized worker load", c.cargo == 10000 and s.stored.wood == 1)
	s = Sim.new(); c = worker(s, 0)
	c.position = s.resources[3].position + Vector2(0, 1.1)
	check("worker targets nearest matching node rather than first node", Work.nearest_resource(s, c, "wood").id == s.resources[3].id)
	var units: int = s.resources[3].units
	frames(s, 1.19)
	check("helper harvesting is timed, not immediate", c.cargo == 0)
	frames(s, .01)
	check("one harvest consumes and carries one matching unit", c.cargo == 1 and s.resources[3].units == units - 1)
	check("worker harvest emits a presentation event", s.events.any(func(e): return e.type == "worker_gather" and e.actor_id == c.id))
	frames(s, .3)
	var clock_key: String = "gather:" + s.resources[3].id
	var clock: float = c.work_clocks[clock_key]
	s.enemies.append({"id":"interrupt","health":65.0,"position":c.position,"cooldown":0.0})
	frames(s, .01)
	check("threat interrupts the worker task", c.activity.kind == "enemy")
	check("interrupt preserves worker task progress", is_equal_approx(c.work_clocks[clock_key], clock))
	check("worker combat has a separate cooldown", c.cooldown > 0 and c.cargo == 1)
	s.enemies.clear(); frames(s, .9)
	check("work resumes despite remaining combat cooldown", c.cargo == 2)
	check("lead cannot be assigned as its own companion", not s.assign_job(s.lead, "gather"))
	check("invalid job cannot alter assignment", not s.assign_job(c.id, "teleport") and c.job == "gather")
	check("invalid resource rejected", not s.assign_job(c.id, "gather", "gold"))
	check("valid resource assignment retains old cargo", s.assign_job(c.id, "gather", "stone") and c.cargo == 2 and c.delivering)
	var copy = Sim.new()
	check("job, resource, cargo and interrupted work clocks survive restart", copy.restore(s.snapshot()) and copy.companions[0].work_clocks == c.work_clocks and copy.companions[0].resource_kind == "stone" and copy.companions[0].cargo == 2)
	s = Sim.new(); c = worker(s, 1); c.job = "repair"; s.durability = 210
	frames(s, .33)
	check("repair waits for the material beat", s.durability == 210 and c.cargo == 1)
	frames(s, .01)
	check("repair consumes actual wood and adds contract durability", s.durability == 252 and c.cargo == 0)
	c.cargo = 1; c.position = Sim.point(s.contract.world.furnace) + Vector2(1.4,0)
	frames(s, .34)
	check("repair never overfills furnace durability", s.durability == 260 and c.cargo == 0)
	s = Sim.new(); c = worker(s, 4); c.job = "build"; c["building"] = true
	c.position = s.defenses.north.position + Vector2(0,1.1)
	frames(s, .31)
	check("construction cannot commit before helper 0.32-second beat", s.defenses.north.delivered.wood == 0)
	frames(s, .01)
	check("construction transfers one unit, not a full cargo batch", s.defenses.north.delivered.wood == 1 and c.cargo == 3)
	frames(s, .96)
	check("partial wood construction does not bypass stone requirement", s.defenses.north.delivered.wood == 4 and not s.defenses.north.built)
	# End-to-end worker routing: gather both materials, deliver, build both sides.
	frames(s, 130)
	check("builder completes both defenses from harvested material", s.defenses.north.built and s.defenses.south.built)
	check("builder never overdelivers material requirements", s.defenses.north.delivered == {"wood":8,"stone":3} and s.defenses.south.delivered == {"wood":8,"stone":3})
	check("construction alone never bypasses rescue and furnace wave gates", not s.wave_active)
	s = Sim.new(); s.inventory.stone = 3
	s.position = Sim.point(s.contract.world.storage)
	frames(s, .15)
	check("storage also waits for timed delivery", s.inventory.stone == 3)
	frames(s, .01)
	check("storage routes one carried unit into shared camp materials", s.inventory.stone == 2 and s.stored.stone == 1 and s.action.id == "storage")
	s = Sim.new(); s.position = s.resources[0].position + Vector2(0,1.1)
	frames(s, .3); var saved: Dictionary = s.snapshot(); copy = Sim.new(); copy.restore(saved)
	check("player progress clocks survive a normal restart", copy.action_clocks == s.action_clocks)
	frames(copy, .28)
	check("reloaded progress finishes at original remaining time", copy.inventory.wood == 1)
	var legacy: Dictionary = Sim.new().snapshot(); legacy.erase("action_clocks"); legacy.erase("facing")
	for x in legacy.companions:
		for key in ["cargo_kind","resource_kind","delivering","building","work_clocks"]: x.erase(key)
	check("old schema-1 saves migrate without losing their crew", copy.restore(legacy) and copy.companions.size() == 3)
	var bad := legacy.duplicate(true); bad.companions[0].id = 2.5
	reject(copy,bad,"fractional character identity is rejected transactionally")
	bad = legacy.duplicate(true); bad.companions[1].id = 2
	reject(copy,bad,"duplicate crew identity is rejected transactionally")
	bad = legacy.duplicate(true); bad.companions[0].cargo = -1
	reject(copy,bad,"negative worker cargo rejected transactionally")
	bad = legacy.duplicate(true); bad.companions[0]["work_clocks"] = {"gather:wood0":NAN}
	reject(copy,bad,"non-finite task clocks rejected transactionally")
	bad = legacy.duplicate(true); bad["action_clocks"] = [0.2]
	reject(copy,bad,"malformed progress envelope rejected transactionally")
	bad = legacy.duplicate(true); bad.defenses.north.delivered.wood = 99
	reject(copy,bad,"overdelivered barricade save rejected transactionally")
	s = Sim.new(); s.level = 2; s.rescued = true; s.defenses.north.built = true
	s.wave_active = true; s.wave_timer = 12
	s.enemies.append({"id":"restored_wolf","health":65.0,"position":s.position,"cooldown":0.0})
	s.threats_enabled = false
	var before_health: float = s.health; var before_durability: float = s.durability
	frames(s, 3)
	check("review cannot apply invisible restored-wave damage", s.health == before_health and s.durability == before_durability)
	check("disabled presentation preserves encounter rather than awarding a win", s.enemies[0].health == 65 and s.completed_waves == 0 and s.wave_active and s.wave_timer == 12)
	s = Sim.new(); c = worker(s,4); s.presented_actor_ids = [3,4]
	frames(s,2)
	check("unrendered helper cannot secretly deliver resources", c.cargo == 4 and s.stored.wood == 0)
	s = Sim.new(); s.level = 2; s.rescue_enabled = false
	s.position = Sim.point(s.contract.world.survivor); frames(s,3)
	check("missing rescue presentation cannot silently spawn an invisible worker", not s.rescued)
	s = Sim.new(); c = worker(s,3); c.cargo_kind = "stone"; s.inventory.wood = 10001
	check("only the two approved leads are selectable", not s.select_lead(3) and s.lead == 1)
	check("lead change keeps all four identities", s.select_lead(2) and s.companions.map(func(x): return x.id) == [1,3,4])
	check("lead change conserves player and incoming worker materials", s.inventory.wood == 10001 and s.inventory.stone == 3 and s.companions[0].cargo == 0)
	check("repeat lead selection cannot duplicate the transferred load", s.select_lead(2) and s.inventory.stone == 3)
	s = Sim.new(); s.position = s.resources[0].position + Vector2(0,1.1); frames(s,.3)
	check("nearby task progress exists before leaving its interaction range", not s.action_clocks.is_empty())
	s.position = Vector2(14,16); frames(s,.01)
	check("abandoned target clocks are pruned instead of growing without limit", s.action_clocks.is_empty())
	var path := "user://crew-save-test.json"
	var good: Dictionary = Sim.new().snapshot()
	check("valid save writes with semantic validation", Saves.write_state(good,path) == OK)
	good.inventory.wood = 9; Saves.write_state(good,path)
	bad = good.duplicate(true); bad.inventory.wood = -1
	envelope(path,bad)
	copy = Sim.new()
	check("hash-valid but invalid primary restores from valid backup", Saves.load_into(copy,path) == path + ".bak" and copy.inventory.wood == 0)
	check("invalid outgoing save cannot replace the recovery backup", Saves.write_state(bad,path) == ERR_INVALID_DATA and Saves.read_one(path + ".bak").inventory.wood == 0)
	for suffix in ["", ".bak", ".tmp", ".bak.tmp"]: DirAccess.remove_absolute(path + suffix)
	print(JSON.stringify({"suite":"crew_and_persistence","passed":failures.is_empty(),"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
