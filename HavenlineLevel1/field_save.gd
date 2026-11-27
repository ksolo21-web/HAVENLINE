extends RefCounted

# Opt-in, isolated profile. The parent scene's opening save uses its own filename.
const Profile = preload("res://opening_save.gd")
const Inventory = preload("res://field_inventory.gd")
const PRIMARY := "field-inventory-v1.json"
const LOCK := "field-inventory-v1.lock"
const COMPRESS_AT := 256 * 1024
const APP_DIRECTORY := "Havenline-Level-1-Settlement-Trial"
var native_profile := false
var guard := Profile.new()
var directory := ""
var revision := ""
var committed_state := {}
var _verified_file_sha := ""
var _verified_payload_revision := ""
var _receipt_history := {}
var _encoded_receipts := ""

func requested(args: PackedStringArray) -> bool:
	return guard.requested(args)

func configure(args: PackedStringArray) -> bool:
	directory = ""
	revision = ""
	_verified_file_sha = ""
	_verified_payload_revision = ""
	committed_state = {}
	_receipt_history = {}
	_encoded_receipts = ""
	native_profile = not guard.requested(args)
	if native_profile:
		if not ProjectSettings.get_setting("application/config/use_custom_user_dir",false) or ProjectSettings.get_setting("application/config/custom_user_dir_name","") != APP_DIRECTORY:
			return false
		directory = OS.get_user_data_dir().path_join("world-one")
		if DirAccess.make_dir_recursive_absolute(directory) != OK: return false
	else:
		if not guard.configure(args): return false
		directory = guard._dir
	return _safe()

func _safe() -> bool:
	if directory.is_empty():
		return false
	# Re-check the disposable sentinel, including symlink guards, on every I/O.
	if native_profile:
		if directory != OS.get_user_data_dir().path_join("world-one"): return false
		var app_folder := DirAccess.open(OS.get_user_data_dir())
		if not app_folder or app_folder.is_link("world-one"): return false
	elif not guard.configure(PackedStringArray([Profile.FLAG + directory])):
		return false
	var dir := DirAccess.open(directory)
	return dir != null and not dir.is_link(PRIMARY) and not dir.is_link(LOCK)

func _read(inventory: Inventory, path: String, verified_revision := "") -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if not f:
		return {}
	# Small and historical slots are plain JSON. Large receipt histories use
	# Godot's seekable block compression under the same atomic save contract.
	if f.get_buffer(4).get_string_from_ascii() == "GCPF":
		f = FileAccess.open_compressed(path, FileAccess.READ, FileAccess.COMPRESSION_ZSTD)
		if not f: return {}
	else:
		f.seek(0)
	var parsed := JSON.new()
	if parsed.parse(f.get_as_text()) != OK:
		return {}
	var envelope: Variant = parsed.data
	if not envelope is Dictionary or envelope.get("format") != 1 or not envelope.get("payload") is String:
		return {}
	var payload: String = envelope.payload
	var digest := payload.sha256_text()
	if envelope.get("sha256") != digest:
		return {}
	# Both the existing revision and a just-staged payload already passed
	# conservation validation. Still read and hash the actual on-disk bytes.
	if digest == verified_revision:
		return {"revision":digest}
	var next := Inventory.new()
	if parsed.parse(payload) != OK or not next.configure(inventory.configured_costs) or not next.restore(parsed.data):
		return {}
	return {"state":next.snapshot(), "revision":digest}

func load_into(inventory: Inventory) -> Error:
	_verified_file_sha = ""
	_verified_payload_revision = ""
	if not _safe():
		return ERR_UNAUTHORIZED
	var path := directory.path_join(PRIMARY)
	if not FileAccess.file_exists(path):
		revision = ""
		return ERR_FILE_NOT_FOUND
	var current := _read(inventory, path)
	if current.is_empty() or not inventory.restore(current.state):
		return ERR_FILE_CORRUPT
	revision = current.revision
	return OK

func _claim(dir: DirAccess) -> bool:
	var own := "owner-" + str(OS.get_process_id())
	var candidate := LOCK + "-" + str(OS.get_process_id()) + "-" + str(Time.get_ticks_usec())
	if dir.make_dir(candidate) != OK:
		return false
	var marker := FileAccess.open(directory.path_join(candidate).path_join(own), FileAccess.WRITE)
	if not marker:
		dir.remove(candidate)
		return false
	marker.close()
	# Rename a nonempty directory. Concurrent contenders cannot replace an
	# existing nonempty lock. A process killed before this point owns nothing.
	if dir.rename(candidate, LOCK) == OK:
		return true
	dir.remove(candidate.path_join(own))
	dir.remove(candidate)
	if dir.is_link(LOCK):
		return false
	var locked := DirAccess.open(directory.path_join(LOCK))
	if not locked:
		return false
	for name in locked.get_files():
		if not name.begins_with("owner-") or locked.is_link(name):
			continue
		var token := name.trim_prefix("owner-")
		if not token.is_valid_int() or int(token) <= 0 or _owner_alive(int(token)):
			return false
		# One contender can rename this precise dead-owner marker and adopt
		# the interrupted lock. The published primary remains intact.
		return locked.rename(name, own) == OK
	return false

func _owner_alive(pid: int) -> bool:
	if native_profile: return OS.is_process_running(pid)
	if OS.get_name() == "Linux":
		return DirAccess.dir_exists_absolute("/proc/" + str(pid))
	# The disposable-profile policy is Unix-only. Signal zero tests process
	# existence without sending any signal to it.
	return OS.execute("kill", PackedStringArray(["-0", str(pid)])) == 0

func commit(inventory: Inventory) -> Error:
	if not _safe():
		return ERR_UNAUTHORIZED
	var dir := DirAccess.open(directory)
	if not _claim(dir):
		return ERR_BUSY
	var locked := DirAccess.open(directory.path_join(LOCK))
	var result := OK
	if locked.is_link("inventory.stage"):
		result = ERR_UNAUTHORIZED
	elif locked.file_exists("inventory.stage"):
		result = locked.remove("inventory.stage")
	if result == OK:
		result = _write_locked(inventory)
	dir.remove(LOCK.path_join("owner-" + str(OS.get_process_id())))
	dir.remove(LOCK)
	return result

func _write_locked(inventory: Inventory) -> Error:
	var path := directory.path_join(PRIMARY)
	var previous_revision := ""
	if FileAccess.file_exists(path):
		# Compare the complete on-disk file with the last byte-verified stage.
		# A changed primary always takes the checksum and stale-writer path.
		if not _verified_file_sha.is_empty() and FileAccess.get_sha256(path) == _verified_file_sha:
			previous_revision = _verified_payload_revision
		else:
			var current := _read(inventory,path,revision)
			if current.is_empty():
				return ERR_FILE_CORRUPT
			previous_revision = current.revision
	if previous_revision != revision:
		return ERR_BUSY
	var pending := Inventory.new()
	if not pending.configure(inventory.configured_costs) or not pending.restore(inventory.snapshot()):
		return ERR_INVALID_DATA
	var snapshot := pending.snapshot()
	var payload := _encode_snapshot(snapshot)
	var digest := payload.sha256_text()
	if revision == digest:
		committed_state = snapshot
		return OK
	# The stage lives inside the owned lock directory. Only the verified stage
	# replaces PRIMARY, in a single same-filesystem rename.
	var stage := directory.path_join(LOCK).path_join("inventory.stage")
	var envelope := JSON.stringify({"format":1,"sha256":digest,"payload":payload})
	var file: FileAccess
	var compressed := envelope.length() >= COMPRESS_AT
	if compressed:
		file = FileAccess.open_compressed(stage, FileAccess.WRITE, FileAccess.COMPRESSION_ZSTD)
	else:
		file = FileAccess.open(stage, FileAccess.WRITE)
	if not file:
		return FileAccess.get_open_error()
	file.store_string(envelope)
	file.flush()
	var error := file.get_error()
	file.close()
	var stage_sha := ""
	if error == OK:
		stage_sha = _verify_stage(stage,envelope,compressed)
		if stage_sha.is_empty(): error = ERR_FILE_CORRUPT
	if error == OK:
		error = DirAccess.rename_absolute(stage, path)
	if error != OK:
		DirAccess.remove_absolute(stage)
		return error
	_verified_file_sha = stage_sha
	_verified_payload_revision = digest
	committed_state = snapshot
	revision = digest
	return OK

func _encode_snapshot(state: Dictionary) -> String:
	var receipts: Dictionary = state.collected
	if receipts.size() < 512: return JSON.stringify(state)
	# Stock moves often while these immutable, usually much larger receipts
	# stay identical. Preserve the existing sorted JSON and its exact checksum.
	if _encoded_receipts.is_empty() or _receipt_history != receipts:
		receipts.make_read_only()
		_receipt_history = receipts
		_encoded_receipts = JSON.stringify(receipts)
	var keys := state.keys()
	keys.sort()
	var entries := PackedStringArray()
	for key: String in keys:
		var value := _encoded_receipts if key == "collected" else JSON.stringify(state[key])
		entries.append(JSON.stringify(key)+":"+value)
	return "{"+",".join(entries)+"}"

func _verify_stage(path: String, envelope: String, compressed: bool) -> String:
	var reader := FileAccess.open_compressed(path,FileAccess.READ,FileAccess.COMPRESSION_ZSTD) if compressed else FileAccess.open(path,FileAccess.READ)
	var bytes := envelope.to_utf8_buffer()
	if not reader or reader.get_length()!=bytes.size() or reader.get_buffer(bytes.size())!=bytes:
		return ""
	return FileAccess.get_sha256(path) if compressed else envelope.sha256_text()
