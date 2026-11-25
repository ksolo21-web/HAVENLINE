extends RefCounted
## Narrow disposable proof, not a production format, authentication or secure save API.
const Planner = preload("res://planner_upstream.gd")
const MARKER := "TRANSFER-FIXTURE-ONLY"
const MARK := "DETACHED HAVENLINE TRANSFER COLD FIXTURE V1\n"
const PRIMARY := "transfer-fixture-v1.primary"
const STAGE := "transfer-fixture-v1.stage"
const READY := "transfer-fixture-v1.cut-ready"
const PREFIX := "hvn-transfer-cold-profile."
const RECEIVER := "receiver_test"
const MATERIAL := "wood"
const OTHER := "red_test_only"
const MAX_BYTES := 4096
var _dir := ""

func configure(path: String) -> bool:
	_dir = ""
	var leaf := path.get_file()
	var pattern := RegEx.new()
	if pattern.compile("^hvn-transfer-cold-profile[.][A-Za-z0-9]{8}$") != OK or pattern.search(leaf) == null or path != "/tmp/" + leaf:
		return false
	_dir = path
	if not paths_safe() or FileAccess.get_file_as_string(_dir.path_join(MARKER)) != MARK:
		_dir = ""
		return false
	return true

func paths_safe() -> bool:
	if _dir.is_empty():
		return false
	var parent := DirAccess.open("/tmp")
	var dir := DirAccess.open(_dir)
	if parent == null or dir == null or parent.is_link(_dir.get_file()):
		return false
	for leaf in [MARKER, PRIMARY, STAGE, READY]:
		if dir.is_link(leaf) or dir.dir_exists(leaf):
			return false
	return true

static func initial() -> Dictionary:
	return {"seq":0,"ledger":{"carry":{MATERIAL:104,OTHER:7},"receivers":{RECEIVER:{MATERIAL:0}},"receipts":{}}}

static func valid(state: Variant) -> bool:
	if typeof(state) != TYPE_DICTIONARY or state.size() != 2 or typeof(state.get("seq")) != TYPE_INT or state.seq < 0 or state.seq > 2:
		return false
	var ledger: Variant = state.get("ledger")
	if typeof(ledger) != TYPE_DICTIONARY or ledger.size() != 3:
		return false
	var rows: Array = Planner.project_rows(ledger,[MATERIAL,OTHER])
	if rows.is_empty() or rows[0][1] != 104-52*state.seq or rows[1][1] != 7:
		return false
	var receivers: Variant = ledger.get("receivers")
	if typeof(receivers) != TYPE_DICTIONARY or receivers.size() != 1 or typeof(receivers.get(RECEIVER)) != TYPE_DICTIONARY:
		return false
	var target: Dictionary = receivers[RECEIVER]
	if target.size() != 1 or typeof(target.get(MATERIAL)) != TYPE_INT or target[MATERIAL] != 52*state.seq:
		return false
	var receipts: Variant = ledger.get("receipts")
	if typeof(receipts) != TYPE_DICTIONARY or receipts.size() != state.seq:
		return false
	for id in receipts:
		if typeof(id) != TYPE_STRING or id.is_empty():
			return false
		var row: Variant = receipts[id]
		if typeof(row) != TYPE_ARRAY or row.size() != 3 or typeof(row[2]) != TYPE_INT or row != [RECEIVER,MATERIAL,52]:
			return false
	return true

static func digest(data: PackedByteArray) -> String:
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	ctx.update(data)
	return ctx.finish().hex_encode()

static func encode(state: Dictionary) -> PackedByteArray:
	var payload := var_to_bytes(state)
	return var_to_bytes({"version":1,"payload":payload,"digest":digest(payload)})

func bytes(leaf: String) -> PackedByteArray:
	if not paths_safe() or leaf not in [PRIMARY,STAGE]:
		return PackedByteArray()
	var path := _dir.path_join(leaf)
	var handle := FileAccess.open(path,FileAccess.READ)
	if handle == null or handle.get_length() > MAX_BYTES or handle.get_length() == 0:
		return PackedByteArray()
	return handle.get_buffer(handle.get_length())

func decode(leaf: String) -> Dictionary:
	var raw := bytes(leaf)
	if raw.is_empty():
		return {}
	# Explicitly use the non-object variant decoder; this is fixture data only.
	var envelope: Variant = bytes_to_var(raw)
	if typeof(envelope) != TYPE_DICTIONARY or envelope.size() != 3 or typeof(envelope.get("version")) != TYPE_INT or envelope.version != 1:
		return {}
	var payload: Variant = envelope.get("payload")
	if typeof(payload) != TYPE_PACKED_BYTE_ARRAY or digest(payload) != envelope.get("digest"):
		return {}
	var state: Variant = bytes_to_var(payload)
	if not valid(state) or encode(state) != raw:
		return {}
	return state

func load_primary() -> Dictionary:
	return decode(PRIMARY) # Orphan stage is specifically not read, removed or promoted on cold open.

func stage(state: Dictionary) -> bool:
	if not paths_safe() or not valid(state):
		return false
	var dir := DirAccess.open(_dir)
	if dir.file_exists(PRIMARY) and load_primary().is_empty():
		return false
	if dir.file_exists(STAGE) and dir.remove(STAGE) != OK:
		return false
	var dst := FileAccess.open(_dir.path_join(STAGE),FileAccess.WRITE)
	if dst == null:
		return false
	dst.store_buffer(encode(state))
	dst.flush()
	var status := dst.get_error()
	dst.close()
	return status == OK and decode(STAGE) == state

func promote() -> bool:
	if not paths_safe():
		return false
	return DirAccess.rename_absolute(_dir.path_join(STAGE),_dir.path_join(PRIMARY)) == OK

func signal_cut_ready(text: String) -> bool:
	if not paths_safe() or FileAccess.file_exists(_dir.path_join(READY)):
		return false
	var ready := FileAccess.open(_dir.path_join(READY), FileAccess.WRITE)
	if ready == null:
		return false
	ready.store_string(text)
	ready.flush()
	var result := ready.get_error()
	ready.close()
	return result == OK
