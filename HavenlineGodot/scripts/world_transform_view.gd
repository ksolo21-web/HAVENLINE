class_name HavenlineWorldTransformView
extends Node3D

## T10 presentation lifecycle shell. It never grants resources, advances
## progression, or owns the authoritative transform transaction. Completion is
## allowed only after simulation confirms the debit transaction was applied.

const AUTHORITY_ID := "T10-world-transform-view-v1"
const LIFECYCLE := ["locked", "ready", "preview", "committing", "complete"]

var target_id := ""
var lifecycle := "locked"
var presentation_key := ""
var source_state := ""
var target_state := ""
var target_revision := 0
var transaction_id := ""
var update_count := 0

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"lifecycle": LIFECYCLE.duplicate(),
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
		"complete_requires_simulation_receipt": true,
		"t11_owns_final_camp_content": true,
	}

func configure(next_target_id: String) -> bool:
	if next_target_id.is_empty():
		return false
	target_id = next_target_id
	return true

func set_locked() -> void:
	_set_lifecycle("locked")

func set_ready() -> void:
	_set_lifecycle("ready")

func show_preview(preview: Dictionary) -> bool:
	if not bool(preview.get("passed", false)) or String(preview.get("target_id", "")) != target_id:
		return false
	presentation_key = String(preview.get("presentation_key", ""))
	source_state = String(preview.get("source_state", ""))
	target_state = String(preview.get("target_state", ""))
	target_revision = int(preview.get("target_revision", 0))
	transaction_id = ""
	_set_lifecycle("preview")
	return true

func show_commit(intent: Dictionary) -> bool:
	if not bool(intent.get("passed", false)) or String(intent.get("target_id", "")) != target_id:
		return false
	if bool(intent.get("replayed", false)) or bool(intent.get("authoritative_applied", false)):
		return false
	var next_transaction_id := String(intent.get("transaction_id", ""))
	if next_transaction_id.is_empty() or not bool(intent.get("submit_debit_transaction", false)):
		return false
	presentation_key = String(intent.get("presentation_key", ""))
	source_state = String(intent.get("source_state", ""))
	target_state = String(intent.get("target_state", ""))
	target_revision = int(intent.get("target_revision", 0))
	transaction_id = next_transaction_id
	_set_lifecycle("committing")
	return true

func mark_complete(receipt: Dictionary) -> bool:
	if lifecycle != "committing":
		return false
	if not bool(receipt.get("authority_applied", false)) or String(receipt.get("authority_source", "")) != "simulation":
		return false
	if String(receipt.get("transaction_id", "")) != transaction_id:
		return false
	if String(receipt.get("target_id", "")) != target_id or int(receipt.get("target_revision", -1)) != target_revision:
		return false
	_set_lifecycle("complete")
	return true

func _set_lifecycle(next: String) -> void:
	if next not in LIFECYCLE or next == lifecycle:
		return
	lifecycle = next
	update_count += 1

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"target_id": target_id,
		"lifecycle": lifecycle,
		"presentation_key": presentation_key,
		"source_state": source_state,
		"target_state": target_state,
		"target_revision": target_revision,
		"transaction_id": transaction_id,
		"update_count": update_count,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
	}
