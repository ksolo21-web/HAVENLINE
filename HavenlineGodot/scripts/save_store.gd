class_name HavenlineSaveStore
extends RefCounted

const SAVE_PATH = "user://outpost-v1.json"

static func write_state(data: Dictionary, path: String = SAVE_PATH) -> Error:
	var text := JSON.stringify(data)
	var envelope := {"schema": 1, "payload": text, "sha256": text.sha256_text()}
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(envelope))
	file.flush()
	file.close()
	# Retain the last valid save, not a corrupted file.
	if not read_one(path).is_empty():
		var copied := DirAccess.copy_absolute(path, path + ".bak")
		if copied != OK:
			return copied
	return DirAccess.rename_absolute(path + ".tmp", path)

static func read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK:
		return {}
	var parsed = parser.data
	if not parsed is Dictionary or parsed.get("schema") != 1:
		return {}
	var payload = parsed.get("payload")
	if not payload is String or payload.sha256_text() != parsed.get("sha256", ""):
		return {}
	if parser.parse(payload) != OK:
		return {}
	var state = parser.data
	if not state is Dictionary or state.get("schema") != 1:
		return {}
	return state

static func read_state(path: String = SAVE_PATH) -> Dictionary:
	var state := read_one(path)
	return state if not state.is_empty() else read_one(path + ".bak")
