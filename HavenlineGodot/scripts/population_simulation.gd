extends "res://scripts/simulation.gd"

const Population = preload("res://scripts/npc_population.gd")
const BaseSimulation = preload("res://scripts/simulation.gd")
const ENCOUNTER_SITES := {
	"survivor_male_01": Vector2(-10, 7), "survivor_female_01": Vector2(10, -7),
	"pet_dog_01": Vector2(-8, -9), "pet_fox_01": Vector2(8, 10),
	"pet_lion_01": Vector2(-13, 3), "pet_tiger_01": Vector2(13, -3),
	"pet_bear_01": Vector2(-12, -11), "pet_wolf_01": Vector2(12, 11),
	"pet_owl_01": Vector2(3, 13)
}
const LEGACY_SITES := ["survivor_male_01", "survivor_female_01", "pet_dog_01", "pet_cat_01"]
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
		var sites := ENCOUNTER_SITES
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
	data["encounter_sites_revision"] = 2
	data["encounter_sites_seeded"] = encounter_sites_seeded
	data["seeded_sites"] = seeded_sites.duplicate()
	return data

func restore(data: Dictionary) -> bool:
	var candidate = Population.new()
	if data.has("population"):
		if not data.population is Dictionary or not candidate.restore(data.population): return false
	if not data.get("encounter_sites_seeded", false) is bool: return false
	var revision = data.get("encounter_sites_revision", 1)
	if not Population.count(revision, 2) or int(revision) < 1: return false
	revision = int(revision)
	var raw_sites = data.get("seeded_sites", {})
	var expected_size: int = LEGACY_SITES.size() if revision == 1 else ENCOUNTER_SITES.size()
	if not raw_sites is Dictionary or raw_sites.size() > expected_size: return false
	var saved_sites: Dictionary = {}
	for original_template in raw_sites:
		if not original_template is String: return false
		if revision == 1 and original_template not in LEGACY_SITES: return false
		var template: String = "pet_fox_01" if revision == 1 and original_template == "pet_cat_01" else original_template
		if not ENCOUNTER_SITES.has(template) or saved_sites.has(template): return false
		if not Population.count(raw_sites[original_template]): return false
		var found := false
		for c in candidate.encounters + candidate.recruits + candidate.pets:
			if c.id == raw_sites[original_template] and c.template == template: found = true
		if not found: return false
		saved_sites[template] = int(raw_sites[original_template])
	if data.get("encounter_sites_seeded", false) != (raw_sites.size() == expected_size): return false
	# Validate legacy and extension independently, then commit once. Invalid NPC
	# data must not partially overwrite inventory, core identities or backups.
	var base = BaseSimulation.new()
	if not base.restore(data): return false
	candidate.presentation_required = population.presentation_required
	candidate.presented_ids = population.presented_ids.duplicate()
	candidate.enabled_templates = population.enabled_templates.duplicate()
	if not super.restore(data): return false
	population = candidate
	encounter_sites_seeded = saved_sites.size() == ENCOUNTER_SITES.size()
	seeded_sites = saved_sites.duplicate()
	return true
