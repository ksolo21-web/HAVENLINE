extends RefCounted
const Ledger = preload("res://opening_ledger.gd")
const FLAG := "--l1-disposable-profile="
const PREFIX := "havenline-l1-v3-"
const SENTINEL := "L1-DISPOSABLE"
const MARK := "HAVENLINE-ALFRED-V3-DISPOSABLE\n"
const PRIMARY := "opening-v3.json"
const STAGING := "opening-v3.stage"
const MAX_BYTES := 8192
var _dir := ""

func requested(args: PackedStringArray) -> bool:
	for arg in args:
		if arg.begins_with(FLAG):
			return true
	return false

func configure(args: PackedStringArray) -> bool:
	_dir = ""
	var matches := PackedStringArray()
	for arg in args:
		if arg.begins_with(FLAG):
			matches.append(arg.trim_prefix(FLAG))
	if matches.size() != 1:
		return false
	var path: String = matches[0]
	var leaf := path.get_file()
	var token := leaf.trim_prefix(PREFIX)
	# Explicit single-component disposable /tmp path, no arbitrary save path.
	if not leaf.begins_with(PREFIX) or token.length() < 6 or path != "/tmp/" + leaf:
		return false
	var pattern := RegEx.new()
	if pattern.compile("^[A-Za-z0-9_-]+$") != OK or pattern.search(leaf) == null:
		return false
	var base := DirAccess.open("/tmp")
	if base == null or base.is_link(leaf) or not base.dir_exists(leaf):
		return false
	var content := DirAccess.open(path)
	if content == null or content.is_link(SENTINEL) or not content.file_exists(SENTINEL):
		return false
	var marker := FileAccess.open(path.path_join(SENTINEL), FileAccess.READ)
	if marker == null or marker.get_length() != MARK.length() or marker.get_as_text() != MARK:
		return false
	_dir = path
	if not _paths_safe():
		_dir = ""
		return false
	return true

func _paths_safe() -> bool:
	var base := DirAccess.open("/tmp")
	var dir := DirAccess.open(_dir)
	return not _dir.is_empty() and base != null and not base.is_link(_dir.get_file()) and dir != null and not dir.is_link(PRIMARY) and not dir.is_link(STAGING)

func _decode(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > MAX_BYTES:
		return {}
	var envelope: Variant = JSON.parse_string(file.get_as_text())
	if not envelope is Dictionary or envelope.size() != 3 or envelope.get("version") != 1:
		return {}
	var payload: Variant = envelope.get("payload")
	if not payload is String or payload.sha256_text() != envelope.get("sha256"):
		return {}
	var ledger := Ledger.new()
	if not ledger.restore(JSON.parse_string(payload)):
		return {}
	return ledger.snapshot()

func load_into(ledger) -> Error:
	if not _paths_safe():
		return ERR_UNAUTHORIZED
	var path := _dir.path_join(PRIMARY)
	if not FileAccess.file_exists(path):
		return ERR_FILE_NOT_FOUND
	var state := _decode(path)
	return OK if not state.is_empty() and ledger.restore(state) else ERR_FILE_CORRUPT

func commit(ledger) -> Error:
	if not _paths_safe():
		return ERR_UNAUTHORIZED
	var state := Ledger.new()
	if not state.restore(ledger.snapshot()):
		return ERR_INVALID_DATA
	var primary_path := _dir.path_join(PRIMARY)
	if FileAccess.file_exists(primary_path) and _decode(primary_path).is_empty():
		return ERR_FILE_CORRUPT
	var payload := JSON.stringify(state.snapshot())
	var stage_path := _dir.path_join(STAGING)
	# Unlink a prior stage before write; do not truncate any reused inode.
	var dir := DirAccess.open(_dir)
	if dir.file_exists(STAGING):
		var discarded := dir.remove(STAGING)
		if discarded != OK:
			return discarded
	var file := FileAccess.open(stage_path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify({"version": 1, "payload": payload, "sha256": payload.sha256_text()}))
	file.flush()
	var result := file.get_error()
	file.close()
	if result != OK:
		return result
	var checked := _decode(stage_path)
	if checked != state.snapshot():
		return ERR_FILE_CORRUPT
	# Same-directory promotion; no unlink-primary fallback. Process-restart proof pending.
	return DirAccess.rename_absolute(stage_path, primary_path)
