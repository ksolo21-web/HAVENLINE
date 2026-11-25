extends RefCounted
## Detached proposal. Not instantiated or connected by shipped scenes.
## Asset selection/marker validation are intentionally a future separate owner.
const TreeScript = preload("res://resource_tree.gd")
const CHANNELS := [&"key_f", &"mouse_primary", &"touch_tree"]
var _marker_authority: RefCounted
var _context_provider: Callable
var _held: Dictionary = {}
var _pending: RefCounted
var _impact_consumed := false
var _actor_ref: WeakRef
var _tree_ref: WeakRef
var _owner_ref: WeakRef
var _enabled := false

func configure(marker_authority: RefCounted, scene_owner: Node, current_context: Callable) -> bool:
	if _enabled or not is_instance_valid(marker_authority) or not is_instance_valid(scene_owner) or not current_context.is_valid():
		return false
	_marker_authority = marker_authority
	_owner_ref = weakref(scene_owner)
	_context_provider = current_context
	_enabled = true
	return true

func press(channel: StringName, echo: bool = false, emulated: bool = false) -> RefCounted:
	if not _enabled or channel not in CHANNELS or echo or emulated or _held.has(channel):
		return null
	# Latch even when refused. A press held while busy can't become a new
	# request when the previous swing ends. Touch owner supplies release.
	_held[channel] = true
	if _pending != null:
		return null
	var sw := _live_context()
	if sw.is_empty():
		return null
	var actor: Node3D = sw.actor
	var tree: TreeScript = sw.tree
	if not tree.can_address(actor.global_position, actor.global_transform.basis.z):
		return null
	_actor_ref = weakref(actor)
	_tree_ref = weakref(tree)
	_pending = RefCounted.new()
	return _pending

func release(channel: StringName, emulated: bool = false) -> void:
	if not emulated:
		_held.erase(channel)

## Only a future admitted authored-animation binding may hold this authority.
## A wrong/swapped generation never clears the current legitimate request.
func marker_reached(authority: RefCounted, ticket: RefCounted) -> bool:
	if not _matches(authority,ticket) or _impact_consumed:
		return false
	var actor_at_request: Node3D = _actor_ref.get_ref()
	var tree_at_request: TreeScript = _tree_ref.get_ref()
	_impact_consumed = true # Latch even on live denial; finish owns playback closure.
	var sw := _live_context()
	if sw.is_empty() or actor_at_request == null or tree_at_request == null or sw.actor != actor_at_request or sw.tree != tree_at_request:
		return false
	var tree: TreeScript = sw.tree
	var actor: Node3D = sw.actor
	var facing := actor.global_transform.basis.z
	if not tree.can_address(actor.global_position,facing):
		return false
	# Source's own monotonic sequence, contact cooldown, strike and transit
	# remain authoritative. No credit, fall, clock, debounce duration or save.
	return tree.strike(TreeScript.TREE_ID,tree.last_sequence+1,actor.global_position,facing)

## Must be called by future admitted playback on stop, completion, interruption,
## clip/scene replacement or cancellation, not by an assumed duration timer.
func finish_or_cancel(authority: RefCounted, ticket: RefCounted) -> bool:
	if not _matches(authority,ticket):
		return false
	_clear_pending()
	return true

func disarm(authority: RefCounted) -> bool:
	if not _enabled or authority != _marker_authority:
		return false
	_clear_pending()
	_enabled = false
	_held.clear()
	_marker_authority = null
	_owner_ref = null
	_context_provider = Callable()
	return true

func _matches(authority: RefCounted,ticket: RefCounted) -> bool:
	return _enabled and authority != null and authority == _marker_authority and ticket != null and ticket == _pending

func _clear_pending() -> void:
	_impact_consumed = false
	_pending = null
	_actor_ref = null
	_tree_ref = null

func _live_context() -> Dictionary:
	if not _enabled or _owner_ref == null or not _context_provider.is_valid():
		return {}
	var owner: Node = _owner_ref.get_ref()
	if owner == null or not owner.is_inside_tree() or _queued_in_parent_chain(owner):
		return {}
	var live: Variant = _context_provider.call()
	if not live is Dictionary or live.get("authorized", false) != true:
		return {}
	var actor := live.get("actor") as Node3D
	var tree := live.get("tree") as TreeScript
	if not is_instance_valid(actor) or not is_instance_valid(tree) or not actor.is_inside_tree() or not tree.is_inside_tree():
		return {}
	if not owner.is_ancestor_of(actor) or not owner.is_ancestor_of(tree) or _queued_in_parent_chain(actor) or _queued_in_parent_chain(tree):
		return {}
	return {"actor":actor, "tree":tree}

## queue_free is deferred, but a queued node or parent is already retired
## for transaction purposes. Descendants may still be inside the tree.
static func _queued_in_parent_chain(start: Node) -> bool:
	var node: Node = start
	while node != null:
		if node.is_queued_for_deletion():
			return true
		node = node.get_parent()
	return false
