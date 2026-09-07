extends SceneTree
const Sim = preload("res://scripts/population_simulation.gd")
const Base = preload("res://scripts/simulation.gd")
const Pop = preload("res://scripts/npc_population.gd")
const View = preload("res://scripts/population_view.gd")
const RenderPolicy = preload("res://scripts/render_policy.gd")
const Saves = preload("res://scripts/save_store.gd")
var checks: Array = []
var failures: Array = []
func check(label: String, passed: bool):
	checks.append({"name": label, "passed": passed})
	if not passed: failures.append(label)
func frames(s, seconds: float):
	for i in int(round(seconds * 100)): s.step(0.01, Vector2.ZERO)
func ready_sim():
	var s = Sim.new()
	s.stored.wood = 18
	s.stored.stone = 6
	s.update_level()
	s.threats_enabled = false
	s.presented_actor_ids = [1, 2, 3, 4]
	return s
func customer_at_counter(s, amount := 3) -> Dictionary:
	s.population.spawn_customer()
	var c: Dictionary = s.population.customers.back()
	c.position = Pop.COUNTER
	c.state = "waiting"
	c.order_kind = "wood"
	c.price = 1
	c.remaining = amount
	s.position = Pop.COUNTER
	return c
func reject(s, state: Dictionary, label: String):
	var before: Dictionary = s.snapshot()
	check(label, not s.restore(state) and s.snapshot() == before)
func _initialize():
	var p = Pop.new()
	check("four reusable customer bases", p.catalog.customer_template_pool.size() == 4)
	check("two male and two female customer bases", p.catalog.customer_template_pool.filter(func(k): return p.catalog.templates[k].gender == "male").size() == 2 and p.catalog.customer_template_pool.filter(func(k): return p.catalog.templates[k].gender == "female").size() == 2)
	check("separate male/female survivor pool", p.catalog.survivor_template_pool == ["survivor_male_01", "survivor_female_01"])
	check("pet archetypes are separate from human crew", p.catalog.pet_template_pool == ["pet_dog_01", "pet_cat_01"])
	var paths: Array = []
	for spec in p.catalog.templates.values(): paths.append(spec.model)
	var distinct := true
	for path in paths:
		if paths.count(path) != 1 or not path.begins_with("res://assets/npcs/"): distinct = false
	check("NPC model slots are distinct and never alias custom character GLBs", distinct)
	var p2 = Pop.new()
	var a: Dictionary = p.make_person("survivor_male_01", Vector2.ZERO)
	var b: Dictionary = p2.make_person("survivor_male_01", Vector2.ZERO)
	check("appearance and name are deterministic for saved seed and identity", a == b)
	check("dynamic identities cannot collide with custom crew or opening survivor", a.id >= 100)
	check("unknown archetype cannot allocate an identity", p.make_person("Character1", Vector2.ZERO).is_empty() and p.next_id == 101)
	p = Pop.new()
	for i in 4: p.spawn_customer()
	check("active customer queue is bounded at four", p.customers.size() == 4 and not p.spawn_customer())
	var ids: Array = p.customers.map(func(c): return c.id)
	check("reused models still have unique persistent people", ids == [100, 101, 102, 103])
	var no_repeat := true
	for i in range(1, 4):
		if p.customers[i].template == p.customers[i - 1].template: no_repeat = false
	check("adjacent customers do not repeat the same available base", no_repeat)
	p.customers.clear(); p.spawn_customer()
	check("recycling a visitor does not recycle their identity", p.customers[0].id == 104)
	p.presentation_required = true
	check("empty presentation capability list disables new customers", not p.spawn_customer())
	check("missing survivor model disables a new encounter", p.add_encounter("survivor_male_01", Vector2.ZERO) == -1)
	var s = ready_sim()
	var c := customer_at_counter(s)
	s.inventory.wood = 5
	var stored: Dictionary = s.stored.duplicate()
	frames(s, 0.39)
	check("customer transfer waits for its 0.4-second beat", s.inventory.wood == 5 and s.population.credits == 0)
	frames(s, 0.01)
	check("one sale consumes exactly one real carried unit", s.inventory.wood == 4 and c.remaining == 2 and s.population.credits == 1)
	check("customer sales never debit furnace or construction materials", s.stored == stored and s.level == 2)
	check("customer sale emits a visible transfer event", s.events.any(func(e): return e.type == "customer_sale"))
	frames(s, 0.8)
	check("completed customer leaves without a second whole-order payment", c.state == "leaving" and s.population.credits == 3 and s.inventory.wood == 2)
	frames(s, 2.0)
	check("departing customer cannot be served twice", s.population.credits == 3)
	s = ready_sim(); c = customer_at_counter(s); s.inventory.wood = 0
	frames(s, 1.0)
	check("out-of-stock customer cannot create resources or money", c.remaining == 3 and s.population.credits == 0)
	s = ready_sim(); c = customer_at_counter(s); s.inventory.wood = 3
	s.population.presentation_required = true
	var before_position: Vector2 = c.position
	frames(s, 1.0)
	check("unrendered customer cannot trade, move or time out", s.population.credits == 0 and s.inventory.wood == 3 and c.position == before_position and c.patience == 90.0)
	s = ready_sim(); c = customer_at_counter(s); s.inventory.wood = 3
	frames(s, 0.25)
	var state: Dictionary = s.snapshot()
	var copy = Sim.new()
	check("partial service and identity restore", copy.restore(state) and copy.population.customers[0].appearance == c.appearance and is_equal_approx(copy.population.service_clock, 0.25))
	frames(copy, 0.15)
	check("restored partial service finishes once at remaining duration", copy.population.credits == 1 and copy.inventory.wood == 2)
	var serial: int = copy.population.next_id
	copy.population.spawn_customer()
	check("restored serial never collides with saved customers", copy.population.customers.back().id == serial)
	s = ready_sim(); c = customer_at_counter(s); c.patience = 0.02
	s.position = Vector2(-10, -10); frames(s, 0.02)
	check("unserved customers depart at patience expiry", c.state == "leaving" and s.population.credits == 0)
	s = ready_sim()
	var id: int = s.population.add_encounter("survivor_female_01", Vector2(11, 8))
	s.position = Vector2(11, 8)
	frames(s, 2.19)
	check("additional rescue requires full interaction duration", s.population.recruits.is_empty())
	frames(s, 0.01)
	check("female survivor becomes an additional recruit", s.population.recruits.size() == 1 and s.population.recruits[0].id == id)
	check("additional rescue does not replace the four core characters", s.companions.size() == 3 and s.lead == 1 and s.companions.map(func(x): return x.id) == [2, 3, 4])
	check("additional rescue does not falsely complete opening rescue", not s.rescued and not s.gate_open())
	check("recruited human can receive existing worker jobs", s.assign_job(id, "gather", "stone") and s.population.recruits[0].resource_kind == "stone")
	check("random recruit cannot become a custom playable lead", not s.select_lead(id) and s.lead == 1)
	check("customers cannot be assigned as survivor workers", not s.assign_job(99999, "gather"))
	var recruit: Dictionary = s.population.recruits[0]
	recruit.position = Base.point(s.contract.world.furnace) + Vector2(1.4, 0)
	recruit.cargo = 3; recruit.cargo_kind = "wood"; recruit.delivering = true
	var wood: int = s.stored.wood
	frames(s, 0.16)
	check("additional recruit uses the timed conserved delivery system", recruit.cargo == 2 and s.stored.wood == wood + 1)
	check("reassignment preserves old cargo before new resource", s.assign_job(id, "gather", "metal") and recruit.cargo == 2 and recruit.delivering)
	s.population.presentation_required = true
	frames(s, 0.5)
	check("hidden recruit cannot secretly work", recruit.cargo == 2 and s.stored.wood == wood + 1)
	s = ready_sim()
	id = s.population.add_encounter("pet_dog_01", Vector2(11, 8)); s.position = Vector2(11, 8)
	frames(s, 2.2)
	check("pet rescue creates a pet, not a human worker", s.population.pets.size() == 1 and s.population.recruits.is_empty())
	check("pet rejects human labor assignments", not s.assign_job(id, "gather") and not s.assign_job(id, "build") and not s.assign_job(id, "repair"))
	check("pet accepts species-appropriate follow/scout jobs", s.assign_job(id, "scout") and s.population.pets[0].job == "scout")
	var pet: Dictionary = s.population.pets[0]
	var old: Vector2 = pet.position
	frames(s, 0.5)
	check("pet follows without inventing carried resources", pet.position != old and pet.cargo == 0)
	s.threats_enabled = true
	s.enemies.append({"id": "pet_test_wolf", "position": pet.position, "health": 65.0, "cooldown": 1.0})
	frames(s, 0.01)
	check("scout pet alerts on a nearby visible threat", s.events.any(func(e): return e.type == "pet_alert"))
	frames(s, 0.01)
	check("pet alert cooldown prevents event spam", not s.events.any(func(e): return e.type == "pet_alert"))
	copy = Sim.new()
	check("pet identity and assigned job persist", copy.restore(s.snapshot()) and copy.population.pets[0].id == id and copy.population.pets[0].job == "scout")
	s = ready_sim(); c = customer_at_counter(s); s.inventory.wood = 3
	frames(s, 0.2); state = s.snapshot()
	var bad := state.duplicate(true); bad.population.customers[0].id = 2
	reject(s, bad, "custom identity collision rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].id = 100.5
	reject(s, bad, "fractional NPC identity rejected transactionally")
	bad = state.duplicate(true); bad.population.customers.append(bad.population.customers[0].duplicate(true))
	reject(s, bad, "duplicate NPC identity rejected transactionally")
	bad = state.duplicate(true); bad.population.credits = -1
	reject(s, bad, "negative customer credit rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].price = 10000
	reject(s, bad, "tampered trade price rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].remaining = -1
	reject(s, bad, "negative customer order rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].template = "Character1"
	reject(s, bad, "custom model substitution rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].role = "survivor"
	reject(s, bad, "customer masquerading as recruit rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].position[0] = NAN
	reject(s, bad, "non-finite NPC position rejected transactionally")
	bad = state.duplicate(true); bad.population.customers[0].appearance.palette = 100
	reject(s, bad, "invalid appearance slot rejected transactionally")
	bad = state.duplicate(true); bad.population.service_id = 9999
	reject(s, bad, "orphan service clock rejected transactionally")
	bad = state.duplicate(true); bad.population.rescue_clocks["9999"] = 0.1
	reject(s, bad, "orphan rescue clock rejected transactionally")
	bad = state.duplicate(true); bad.population.next_id = 100
	reject(s, bad, "reused next identity rejected transactionally")
	bad = state.duplicate(true); bad.encounter_sites_seeded = "true"
	reject(s, bad, "invalid expansion state rejected transactionally")
	copy = Sim.new()
	check("legacy saves migrate without changing core progress", copy.restore(Base.new().snapshot()) and copy.population.actor_records().is_empty() and copy.lead == 1 and copy.companions.size() == 3)
	var save_path := "user://population-test.json"
	check("population save uses semantic validation", Saves.write_state(state, save_path) == OK)
	state.inventory.wood = 4; Saves.write_state(state, save_path)
	bad = state.duplicate(true); bad.population.credits = -1
	var text := JSON.stringify(bad)
	var file := FileAccess.open(save_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"schema": 1, "payload": text, "sha256": text.sha256_text()})); file.close()
	copy = Sim.new()
	check("hash-valid corrupted NPC save recovers verified backup", Saves.load_into(copy, save_path) == save_path + ".bak" and copy.inventory.wood == 3)
	check("invalid NPC save cannot overwrite recovery files", Saves.write_state(bad, save_path) == ERR_INVALID_DATA)
	for suffix in ["", ".bak", ".tmp", ".bak.tmp"]: DirAccess.remove_absolute(save_path + suffix)
	for aspect in [1.0, 4.0 / 3.0, 16.0 / 9.0, 21.0 / 9.0, 32.0 / 9.0]:
		var size := RenderPolicy.internal_size(aspect)
		check("native dimensions each meet 4K at aspect %.4f" % aspect, size.x >= 3840 and size.y >= 2160)
	check("review rendering remains explicitly lower resolution", RenderPolicy.internal_size(16.0 / 9.0, true) == Vector2i(1280, 720))
	check("invalid aspect cannot produce invalid render dimensions", RenderPolicy.internal_size(NAN).y >= 2160)
	# Partial art delivery must not block unrelated survivor archetypes.
	s = ready_sim(); s.rescued = true
	s.companions.append({"id": 5, "position": Vector2.ZERO, "job": "follow", "cooldown": 0.0})
	s.population.presentation_required = true
	s.population.enabled_templates = ["survivor_male_01"]
	frames(s, 0.01)
	check("one available survivor template is not blocked by missing pet art", s.population.encounters.size() == 1 and s.seeded_sites.size() == 1)
	s.population.enabled_templates.append("survivor_female_01")
	frames(s, 0.01)
	check("later template availability adds only its own encounter", s.population.encounters.size() == 2 and s.seeded_sites.size() == 2)
	frames(s, 0.03)
	check("repeated spawn checks cannot duplicate seeded survivors", s.population.encounters.size() == 2)
	copy = Sim.new()
	check("partially seeded world survives restart", copy.restore(s.snapshot()) and copy.seeded_sites.size() == 2 and not copy.encounter_sites_seeded)
	bad = s.snapshot(); bad.seeded_sites.survivor_male_01 = 9999
	reject(s, bad, "orphaned seeded encounter identity rejected transactionally")
	bad = s.snapshot(); bad.encounter_sites_seeded = true
	reject(s, bad, "missing encounter sites cannot be marked fully seeded")
	s = ready_sim(); c = customer_at_counter(s); s.inventory.wood = 3; s.threats_enabled = true
	s.enemies.append({"id": "priority_wolf", "position": s.position, "health": 65.0, "cooldown": 10.0})
	frames(s, 0.4)
	check("nearby danger interrupts trade before resources change", s.population.credits == 0 and s.inventory.wood == 3 and s.action.kind == "enemy")
	var view = View.new()
	root.add_child(view)
	view.configure(Sim.new(), Callable())
	check("missing art produces no primitive fallback nodes", view.nodes.is_empty() and view.scenes.is_empty() and view.get_child_count() == 0)
	check("missing art explicitly blocks runtime rescue", not view.sim.rescue_enabled and view.sim.population.presentation_required)
	check("missing model evidence lists all eight required templates", view.evidence().missing_templates.size() == 8 and not view.evidence().final_art_approved)
	view.free()
	print(JSON.stringify({"suite": "population", "passed": failures.is_empty(), "checks": checks, "failures": failures}))
	quit(0 if failures.is_empty() else 1)
