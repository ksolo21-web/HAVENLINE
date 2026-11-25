extends "res://test_router.gd"
class FocusProbe extends Node:
	var notes: Array[int] = []
	func _notification(what: int) -> void:
		if what in [NOTIFICATION_APPLICATION_FOCUS_IN, NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_WINDOW_FOCUS_IN, NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
			notes.append(what)

var signals_seen: Array[String] = []

func press_channel(channel: String, index: int) -> void:
	match channel:
		"F": key(KEY_F,true)
		"mouse": mouse(true,tree_at)
		"touch": touch(index,true,tree_at)

func lift_channel(channel: String, index: int) -> void:
	match channel:
		"F": key(KEY_F,false)
		"mouse": mouse(false,out_at)
		"touch": touch(index,false,out_at)

func latch(channel: String) -> int:
	match channel:
		"F": return int(input._key_held)
		"mouse": return int(input._mouse_held)
		"touch": return input._touch_owner
	return -99

func _run() -> void:
	var probe := FocusProbe.new()
	root.add_child(probe)
	root.focus_exited.connect(func(): signals_seen.append("out"))
	root.focus_entered.connect(func(): signals_seen.append("in"))
	var exposures := 0
	for channel: String in ["F","mouse","touch"]:
		input=Router.new()
		impact=Impact.new()
		authority=RefCounted.new()
		issued.clear()
		opening=Open.instantiate()
		root.add_child(opening)
		opening.set_physics_process(false)
		opening.set_process_input(true)
		await process_frame
		opening.actor.position=Vector3(-1.17,0,6)
		opening.actor.rotation_degrees.y=-90.0
		opening.step_tree(0.)
		tree_at=opening.tree_button.get_global_rect().get_center()
		check(impact.configure(authority,opening,ctx) and input.configure(impact,authority,admit) and blank() and not opening.persist_requested,channel+" clean setup")
		opening.detached_test_chop_input=input
		press_channel(channel,4)
		check(issued.size()==1 and latch(channel)==(4 if channel=="touch" else 1),channel+" viewport press admitted")
		if issued.size()!=1:
			quit(2)
			return
		var old_ticket: RefCounted=issued[0]
		await process_frame
		print("UNPROMPTED ",channel," notes=",probe.notes," root_signals=",signals_seen," focused=",root.has_focus()," display=",DisplayServer.get_name())
		probe.notes.clear()
		signals_seen.clear()
		root.focus_exited.emit()
		root.propagate_notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
		root.propagate_notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		await process_frame
		root.focus_entered.emit()
		root.propagate_notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_IN)
		root.propagate_notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
		await process_frame
		check(probe.notes.size()==4 and signals_seen==["out","in"],channel+" synthetic lifecycle reached live scene")
		var before := latch(channel)
		check(impact.finish_or_cancel(authority,old_ticket),channel+" original synthetic playback explicitly retired")
		press_channel(channel,5)
		var after := latch(channel)
		var denied := issued.size()==1
		if denied and before==(4 if channel=="touch" else 1) and before==after:
			exposures+=1
		print("FOCUS_WITNESS ",channel," prior=",before," next=",after," stale_denial=",denied," notes=",probe.notes," signals=",signals_seen)
		check(not impact.marker_reached(authority,old_ticket) and blank(),channel+" no marker strike, sequence or stock")
		if denied:
			lift_channel(channel,4)
			press_channel(channel,6)
			check(issued.size()==2,channel+" exact missing up restores new press (positive discriminator)")
		opening.queue_free()
		await process_frame
		probe.notes.clear()
		signals_seen.clear()
	print("FOCUS_RESULT exposures=",exposures," checks=",number," failures=",failures)
	quit(1 if failures else 0)
