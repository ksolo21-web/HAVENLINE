class_name HavenlineWorldTransformView
extends Node3D

## T10 presentation lifecycle shell. It never grants resources, advances
## progression, or owns the authoritative transform transaction.

const AUTHORITY_ID := "T10-world-transform-view-v1"
const LIFECYCLE := ["locked", "ready", "preview", "committing", "complete"]

var target_id := ""
var lifecycle := "locked"
var presentation_key := ""
var source_state := ""
var target_state := ""
var target_revision := 0
var update_count := 0

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"lifecycle": LIFECYCLE.duplicate(),
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
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
	_set_lifecycle("preview")
	return true

func show_commit(receipt: Dictionary) -> bool:
	if not bool(receipt.get("passed", false)) or String(receipt.get("target_id", "")) != target_id:
		return false
	if bool(receipt.get("replayed", false)):
		return false
	presentation_key = String(receipt.get("presentation_key", ""))
	source_state = String(receipt.get("source_state", ""))
	target_state = String(receipt.get("target_state", ""))
	target_revision = int(receipt.get("target_revision", 0))
	_set_lifecycle("committing")
	return true

func mark_complete(receipt: Dictionary) -> bool:
	if lifecycle != "committing":
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
		"update_count": update_count,
		"presentation_only": true,
		"mutates_resources": false,
		"advances_progression": false,
	}
