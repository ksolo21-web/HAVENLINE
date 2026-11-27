extends SceneTree

var field
var thumb := Vector2(76,565)
var observations := []
var failures := []

func _initialize(): play.call_deferred()

func press(on:bool):
	var ev:=InputEventScreenTouch.new()
	ev.index=0
	ev.position=thumb
	ev.pressed=on
	field._input(ev)

func steer(delta:Vector3):
	var heading:=delta.normalized().rotated(Vector3.UP,-atan2(7.,11.))
	var ev:=InputEventScreenDrag.new()
	ev.index=0
	ev.position=thumb + Vector2(heading.x,heading.z)*75.
	field._input(ev)

func play():
	field=load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(field)
	for i in 5: await physics_frame
	if not field.camp_active or field.field_save.native_profile: quit(2);return
	for gate in field.gates:
		# Place only the starting subject. Subsequent travel, gate movement,
		# combat and camp crossings all use the field's normal physics loop.
		field.actor.position=gate.to_global(Vector3(0,0,-2.6))
		field.previous_dry_position=field.actor.position
		field.actor.velocity=Vector3.ZERO
		for i in 5: await physics_frame
		for side:float in [1.,-1.]:
			var target:Vector3=gate.to_global(Vector3(0,0,side*2.25))
			var ticks:=0
			press(true)
			while ticks<330:
				var direction:Vector3=target-field.actor.position
				direction.y=0
				if direction.length()<.30: break
				steer(direction)
				await physics_frame
				ticks+=1
			press(false)
			for i in 24: await physics_frame
			var inside:bool=field.field_env.is_inside_camp(field.actor.position)
			var label:String=gate.gate_id+(" outbound" if side>0. else " inbound")
			var ok:bool=ticks<330 and inside==(side<0.) and field.character_kit.active!=inside and not field.gate_button.visible
			if not ok: failures.append(label)
			observations.append({"crossing":label,"ticks":ticks,"inside":inside,"orbit":field.character_kit.active,"gate_open_deg":rad_to_deg(gate.angle),"final_feet":str(field.actor.position),"passed":ok})
	print("TOUCH_GATES ",JSON.stringify({"passed":failures.is_empty(),"failures":failures,"crossings":observations}))
	field.sound.stop_playback()
	for i in 10:
		OS.delay_msec(18)
		await process_frame
	field.queue_free()
	for i in 6: await process_frame
	quit(int(not failures.is_empty()))
