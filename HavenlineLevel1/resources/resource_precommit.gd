extends RefCounted
## Pure single-writer compare-and-swap gate, not a save or lock.
const Ledger = preload("res://opening_ledger.gd")
const Receiver = preload("res://resources/typed_receiver.gd")
const RESERVED_MATERIAL := "wood"
const RESERVED_RECEIVER := Ledger.OFFER
const MAX_VALUE_DEPTH := 8
const TOKEN_BYTES := ["legacy", "state", "order", "policy", "request"]

static func _value_type(kind: int) -> bool:
	return kind in [TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING, TYPE_ARRAY, TYPE_DICTIONARY]

# Validate before serialization, replay normalization or deep duplication.
# Bound traversal depth so cycles and recursive aliases fail without serializing.
static func _canonical_value(value: Variant, remaining: int = MAX_VALUE_DEPTH) -> bool:
	var kind := typeof(value)
	match kind:
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return true
		TYPE_FLOAT:
			return is_finite(float(value))
		TYPE_ARRAY:
			if remaining <= 0 or not _value_type(value.get_typed_builtin()):
				return false
			for entry: Variant in value:
				if not _canonical_value(entry, remaining - 1):
					return false
			return true
		TYPE_DICTIONARY:
			if remaining <= 0 or value.get_typed_key_builtin() not in [TYPE_NIL, TYPE_STRING] or not _value_type(value.get_typed_value_builtin()):
				return false
			for key: Variant in value:
				if typeof(key) != TYPE_STRING or not _canonical_value(value[key], remaining - 1):
					return false
			return true
	return false

# Packed byte arrays are canonical ONLY in these named token fields.
static func _token_shape(expected: Dictionary) -> bool:
	if expected.size() != 7 or expected.get_typed_key_builtin() not in [TYPE_NIL, TYPE_STRING] or expected.get_typed_value_builtin() != TYPE_NIL:
		return false
	for key: Variant in expected:
		if typeof(key) != TYPE_STRING:
			return false
	if typeof(expected.get("generation")) != TYPE_INT or typeof(expected.get("receiver")) != TYPE_STRING:
		return false
	for key: String in TOKEN_BYTES:
		if typeof(expected.get(key)) != TYPE_PACKED_BYTE_ARRAY:
			return false
	return true

static func _paid_legacy(raw: Variant) -> Dictionary:
	var ledger := Ledger.new()
	if not ledger.restore(raw) or ledger.receipt.is_empty():
		return {}
	return ledger.snapshot()

static func _owned_identity(value: Variant) -> bool:
	return typeof(value) == TYPE_STRING and not value.is_empty()

# This V1 boundary deliberately allows no alternate owner of legacy hearth
# or its wood stock; a real cross-ledger wood mapping must be reviewed first.
static func _disjoint(order: Array, state: Dictionary, policy: Dictionary, receiver: String) -> bool:
	if order.has(RESERVED_MATERIAL) or receiver == RESERVED_RECEIVER or policy.has(RESERVED_RECEIVER):
		return false
	var targets: Variant = state.get("receivers")
	var receipts: Variant = state.get("receipts")
	if typeof(targets) != TYPE_DICTIONARY or typeof(receipts) != TYPE_DICTIONARY or targets.has(RESERVED_RECEIVER):
		return false
	for key in targets:
		var stock: Variant = targets[key]
		if not _owned_identity(key) or typeof(stock) != TYPE_DICTIONARY or stock.has(RESERVED_MATERIAL):
			return false
	for key in policy:
		var rule: Variant = policy[key]
		if not _owned_identity(key) or typeof(rule) != TYPE_DICTIONARY:
			return false
		var limits: Variant = rule.get("limits")
		if typeof(limits) != TYPE_DICTIONARY or limits.has(RESERVED_MATERIAL):
			return false
	for key in receipts:
		var row: Variant = receipts[key]
		if not _owned_identity(key) or typeof(row) != TYPE_ARRAY or row.size() != 3:
			return false
		if not _owned_identity(row[0]) or not _owned_identity(row[1]):
			return false
		if row[0] == RESERVED_RECEIVER or row[1] == RESERVED_MATERIAL:
			return false
		if typeof(row[2]) != TYPE_INT or row[2] <= 0:
			return false
	return true

# Tokens capture value bytes, not object identity. Conservative exact matching
# means even insertion-order drift is a no-op rejection. Only legacy is
# normalized by its existing replay validator (JSON int/float representation).
static func capture(generation: Variant, legacy: Variant, state: Dictionary, order: Array, policy: Dictionary, active_receiver: String, request: Dictionary) -> Dictionary:
	if typeof(generation) != TYPE_INT or generation < 0 or not _owned_identity(active_receiver):
		return {}
	for input: Variant in [legacy, state, order, policy, request]:
		if not _canonical_value(input):
			return {}
	var paid := _paid_legacy(legacy)
	if paid.is_empty() or not _disjoint(order, state, policy, active_receiver):
		return {}
	if Receiver.project_rows(state, order).is_empty():
		return {}
	return {
		"generation": generation,
		"legacy": var_to_bytes(paid),
		"state": var_to_bytes(state),
		"order": var_to_bytes(order),
		"policy": var_to_bytes(policy),
		"receiver": active_receiver,
		"request": var_to_bytes(request),
	}

# Caller must run synchronously inside its eventual single-writer transaction.
# No canonical save, generation or effect is modified by this API.
static func prepare(expected: Dictionary, generation: Variant, legacy: Variant, state: Dictionary, order: Array, policy: Dictionary, active_receiver: String, request: Dictionary) -> Dictionary:
	if typeof(generation) != TYPE_INT or generation >= 9223372036854775807 or not _token_shape(expected):
		return {}
	var current := capture(generation, legacy, state, order, policy, active_receiver, request)
	if current.is_empty() or var_to_bytes(expected) != var_to_bytes(current):
		return {}
	var next := Receiver.plan_transfer(state, order, policy, active_receiver, request)
	if next.is_empty() or not _canonical_value(next):
		return {}
	next["next_generation"] = generation + 1
	return next
