class_name HavenlineSaveStore
extends RefCounted

const Simulation = preload("res://scripts/simulation.gd")
const SAVE_PATH = "user://outpost-v1.json"
const MAX_SAVE_BYTES := 8 * 1024 * 1024

static func write_state(data: Dictionary, path: String = SAVE_PATH) -> Error:
	# A valid checksum is not proof of a playable save. Validate before touching
	# either file, and never overwrite a good backup with a semantically bad save.
	var verifier = Simulation.new()
	if not verifier.restore(data): return ERR_INVALID_DATA
	var text := JSON.stringify(data)
	var envelope := {"schema": 1, "payload": text, "sha256": text.sha256_text()}
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if file == null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify(envelope))
	file.flush()
	file.close()
	var previous := read_one(path)
	if not previous.is_empty() and verifier.restore(previous):
		var copied := DirAccess.copy_absolute(path, path + ".bak.tmp")
		if copied != OK: return copied
		var rotated := DirAccess.rename_absolute(path + ".bak.tmp", path + ".bak")
		if rotated != OK: return rotated
	return DirAccess.rename_absolute(path + ".tmp", path)

static func read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var input := FileAccess.open(path, FileAccess.READ)
	if input == null: return {}
	if input.get_length() > MAX_SAVE_BYTES:
		input.close()
		return {}
	var text := input.get_as_text()
	input.close()
	var parser := JSON.new()
	if parser.parse(text) != OK: return {}
	var parsed = parser.data
	if not parsed is Dictionary or parsed.get("schema") != 1: return {}
	var payload = parsed.get("payload")
	if not payload is String or payload.sha256_text() != parsed.get("sha256", ""): return {}
	if parser.parse(payload) != OK: return {}
	var state = parser.data
	if not state is Dictionary or state.get("schema") != 1: return {}
	return state

static func read_state(path: String = SAVE_PATH) -> Dictionary:
	var verifier = Simulation.new()
	for candidate in [path, path + ".bak"]:
		var state := read_one(candidate)
		if not state.is_empty() and verifier.restore(state): return state
	return {}

static func load_into(simulation, path: String = SAVE_PATH) -> String:
	# Restore is transactional. Failure leaves the live state untouched, and a
	# hash-valid but invalid primary still falls through to the recovery backup.
	for candidate in [path, path + ".bak"]:
		var state := read_one(candidate)
		if not state.is_empty() and simulation.restore(state): return candidate
	return ""
