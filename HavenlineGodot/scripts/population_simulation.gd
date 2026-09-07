extends "res://scripts/simulation.gd"

const Population = preload("res://scripts/npc_population.gd")
const BaseSimulation = preload("res://scripts/simulation.gd")
var population = Population.new()
var encounter_sites_seeded := false
var seeded_sites: Dictionary = {}

func choose_action() -> Dictionary:
	var original: Dictionary = super.choose_action()
	var extra: Dictionary = population.action_for(self)
	if extra.is_empty(): return original
	if original.is_empty() or extra.score > original.score: return extra
	return original

func perform_action(dt: float):
	if not population.perform(self, dt): super.perform_action(dt)

func step(dt: float, input_vector: Vector2, sprint := false):
	if dt <= 0 or not is_finite(dt): return
	super.step(dt, input_vector, sprint)
	if rescued and level >= 2 and not encounter_sites_seeded:
		# Dedicated additional survivors/pets; never repurpose C1-C4 or NPC5.
		var sites := {"survivor_male_01": Vector2(-10, 7), "survivor_female_01": Vector2(10, -7),
			"pet_dog_01": Vector2(-8, -9), "pet_cat_01": Vector2(8, 10)}
		for template in sites:
			if template in seeded_sites or not population.template_available(template): continue
			var id: int = population.add_encounter(template, sites[template])
			if id >= 100: seeded_sites[template] = id
		encounter_sites_seeded = seeded_sites.size() == sites.size()
	population.step(self, minf(dt, 0.1))

func assign_job(id: int, job: String, resource_kind := "wood") -> bool:
	if id < 100: return super.assign_job(id, job, resource_kind)
	return population.assign_job(id, job, resource_kind)

func snapshot() -> Dictionary:
	var data: Dictionary = super.snapshot()
	data["population"] = population.snapshot()
	data["encounter_sites_seeded"] = encounter_sites_seeded
	data["seeded_sites"] = seeded_sites.duplicate()
	return data

func restore(data: Dictionary) -> bool:
	var candidate = Population.new()
	if data.has("population"):
		if not data.population is Dictionary or not candidate.restore(data.population): return false
	if not data.get("encounter_sites_seeded", false) is bool: return false
	var saved_sites = data.get("seeded_sites", {})
	if not saved_sites is Dictionary or saved_sites.size() > 4: return false
	for template in saved_sites:
		if template not in ["survivor_male_01", "survivor_female_01", "pet_dog_01", "pet_cat_01"]: return false
		if not Population.count(saved_sites[template]): return false
		var found := false
		for c in candidate.encounters + candidate.recruits + candidate.pets:
			if c.id == saved_sites[template] and c.template == template: found = true
		if not found: return false
	if data.get("encounter_sites_seeded", false) != (saved_sites.size() == 4): return false
	# Validate legacy and extension independently, then commit once. Invalid NPC
	# data must not partially overwrite inventory, core identities or backups.
	var base = BaseSimulation.new()
	if not base.restore(data): return false
	candidate.presentation_required = population.presentation_required
	candidate.presented_ids = population.presented_ids.duplicate()
	candidate.enabled_templates = population.enabled_templates.duplicate()
	if not super.restore(data): return false
	population = candidate
	encounter_sites_seeded = data.get("encounter_sites_seeded", false)
	seeded_sites = saved_sites.duplicate()
	return true
