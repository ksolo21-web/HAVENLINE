extends "res://tests/world_route.gd"

# The unmodified committed controller still drives each physics tick. Only capture windows are changed.
const WINDOWS := {
 "The untouched snowfield":["Fresh snowfield",0.18,0.86],
 "The hearth turns the clearing into camp":["First hearth and palisade",0.25,1.20],
 "The first expansion reveals the corner offers":["First camp expansion",0.08,1.12],
 "Wood corner before spending":["Wood on the timber floor",0.04,1.17],
 "Stone corner before spending":["Stone on the quarry floor",0.04,1.12],
 "Meat corner before spending":["Meat on the food floor",0.04,1.12],
 "Follow the south side to the reserved bay":["Reserved southeast corner",0.9,1.95],
 "Expanded camp with relocated east gate":["Second expansion",0.04,1.28],
 "Build the eastern watchtower":["Building the eastern watchtower",0.0,1.6],
 "Pay for additional orbiting axes":["Pay for the ten-axe upgrade",0.0,1.5],
 "Three axes secured and sheathed inside camp":["Ten purchased axes at rest",0.02,1.16],
 "Furthest earned excursion":["Tracks beyond 100 metres",0.00,1.15],
 "Expanded east gate outward onto snow":["East gate to snow",0.08,1.59],
 "Expanded east gate inward to safety":["East gate to safety",0.08,1.60],
 "Final south gate outward":["South gate to snow",0.08,1.52],
 "Final south gate inward":["South gate to safety",0.08,1.52]
}
var previous_inside:=false
var previous_stage:=-1
func _plate(id:String) -> void:
 var selected:=OS.get_environment("WORLD_NATIVE_SHOTS").split(",",false)
 if selected.is_empty() or id in selected:super._plate(id)

func observe_clip(row:Dictionary) -> void:
 _discover(row)
 var current_stage:int=field.field_env.perimeter_stage
 var current_inside:bool=field.field_env.is_inside_camp(field.actor.position)
 if plate_enabled and current_stage>0 and current_stage==previous_stage and previous_inside!=current_inside:
  var gate_id=""
  var closest=INF
  for gate in field.gates:
   var point:Vector3=gate.global_position
   var gap:=point.distance_to(field.actor.position)
   if gap<closest:
    gate_id=String(gate.gate_id).replace("gate-","");closest=gap
  if closest<1.6:_plate("stage-%d-%s-%s"%[current_stage,gate_id,"in" if current_inside else "out"])
 previous_inside=current_inside
 previous_stage=current_stage
 if not clip_enabled:return
 for e in tick_events:
  match String(e.event):
   "impact_wood":_trigger_clip("Axe bites the pine",1.50)
   "impact_stone":_trigger_clip("Pick strikes the quarry",1.45)
   "spend_wood":
    if row.get("id","")=="center_hearth":_trigger_clip("Earned logs buy the hearth",1.25)
 var clip=""
 if WINDOWS.has(row.label):
  var window:Array=WINDOWS[row.label]
  var elapsed:=float(tick-stage_tick)/60.
  if elapsed>=float(window[1]) and elapsed<float(window[2]):clip=String(window[0])
 if tick<event_clip_end:clip=event_clip
 _set_clip(clip)

func _trigger_clip(id:String,seconds:float) -> void:
 if id=="Alpha wolf encounter":seconds=2.15
 if id=="Wild wolf encounter":seconds=1.55
 if id=="Watchtower bolts at the eastern threat":seconds=2.15
 super._trigger_clip(id,seconds)
