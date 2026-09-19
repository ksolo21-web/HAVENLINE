class_name HavenlineStorageStockpile
extends Node3D

## Grounded T08 destination display. It derives entirely from sim.stored and
## deliberately owns no storage value or transfer outcome.

const CarryStack = preload("res://scripts/carry_stack.gd")
const AUTHORITY_ID := "T08-destination-stockpile-v1"

var stack: HavenlineCarryStack
var destination_id := "camp_storage"

func _ready() -> void:
	if stack == null:
		stack = CarryStack.new()
		stack.name = "PhysicalStoredMaterials"
		stack.configure_grounded(true)
		add_child(stack)

func configure(id: String, stored: Dictionary) -> bool:
	if id.is_empty():
		return false
	destination_id = id
	if stack == null:
		_ready()
	return stack.update_inventory(stored)

func sync(stored: Dictionary) -> bool:
	if stack == null:
		_ready()
	return stack.update_inventory(stored)

func descriptor() -> Dictionary:
	var row := stack.descriptor() if stack != null else {}
	row["authority_id"] = AUTHORITY_ID
	row["destination_id"] = destination_id
	row["grounded"] = true
	row["simulation_authoritative"] = true
	return row
