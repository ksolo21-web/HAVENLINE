extends "res://tests/field_route.gd"
const Session := preload("res://tests/lifecycle_test_profile.gd")
var mine
var sampled := {}
var steps_used := 0
var route := []
var hits_at_start := 0

func step() -> void:
	await physics_frame
	steps_used+=1
	var hits := []
	for e in field.events:
		if e.event=="impact_stone" and Vector2(e.x,e.z).distance_to(Vector2(mine.position.x,mine.position.z))<.03:hits.append(e.t)
	if hits.size()>=1 and not sampled.has("first"):sampled["first"]={"time":hits[0],"inside":field.field_env.is_inside_camp(field.actor.position)}
	if mine.phase=="mined" and not sampled.has("break"):
		var ids:=[]
		for key in field.drops:
			var d:Dictionary=field.drops[key]
			if d.kind=="stone" and d.at.distance_to(mine.position)<1.75:ids.append(key)
		sampled["break"]={"hits":hits.size(),"tokens":ids,"inside":field.field_env.is_inside_camp(field.actor.position),"time":steps_used/60.}

func journey(xz:Vector2) -> void:
	var arrived := false
	for i in 260:
		arrived=move_to([xz.x,xz.y],.25)
		await step()
		if arrived or sampled.has("break"):break
	steer(Vector2.ZERO)
	route.append({"goal":str(xz),"actor":str(field.actor.position),"arrived":arrived})
	
func run() -> void:
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.size.x*.28,root.size.y*.70)
	mine=field.resource_rock
	hits_at_start=mine.strikes
	var expected:=int(OS.get_environment("EXPECTED_HITS"))
	var at:Vector2=Vector2(mine.position.x,mine.position.z)
	var clear:bool=not field.field_env.occupies_camp_ground(mine.position,1.15)
	var gate=field.gates[0]
	for destination:Vector2 in [Vector2(1.62,2.45),Vector2(gate.position.x,gate.position.z-.5),Vector2(gate.position.x,gate.position.z+1.8),Vector2(.35,9.6),at+Vector2(1.9,-.5)]:
		await journey(destination)
		if sampled.has("break"):break
	for i in 230:
		await step()
		if sampled.has("break"):break
	var ok:bool=field.camp_active and not field.persist_blocked and clear and hits_at_start==expected and sampled.has("break")
	if sampled.has("break"):ok=ok and not sampled["break"].inside and sampled["break"].hits==3-expected and sampled["break"].tokens.size()==3
	print("EARNED_MINE ",JSON.stringify({"passed":ok,"camp_stage":field.field_env.perimeter_stage,"saved_hits_before_travel":hits_at_start,"expected":expected,"source_at":str(mine.position),"clear_of_perimeter":clear,"route":route,"mining":sampled,"uses_live_touchscreen":true}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(0 if ok else 1)
