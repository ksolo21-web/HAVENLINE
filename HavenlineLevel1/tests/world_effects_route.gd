extends "res://tests/world_route.gd"

var first_pine_frame:=-1
var regrown_tick:=-1

func read_field() -> Dictionary:
 var state:=super.read_field()
 var tree=field.resource_tree
 var hud=field.opening_hud
 var visible_chips:=0
 for chip in tree.chips:
  if chip.is_visible_in_tree():visible_chips+=1
 state["chop"]={"strikes":tree.strikes,"phase":tree.phase,"recoil_elapsed":tree.recoil_elapsed,"recoil_direction":pt(tree.recoil_direction),"tilt":pt(tree._pivot.rotation),"chips":visible_chips}
 state["vitality"]={"hp":field.player_hp,"maximum":field.MAX_HP,"hud_text":hud.health_text.text,"hud_value":hud.health_bar.value,"hud_visible":hud.health_bar.is_visible_in_tree(),"recoil_z":field.hero_model.rotation.z,"reset_clock":field.reset_time,"inside":field.field_env.is_inside_camp(field.actor.position)}
 var near:=[]
 for wolf in field.enemies:
  if is_instance_valid(wolf) and wolf.position.distance_squared_to(field.actor.position)<100:
   near.append({"id":wolf.spawn_id,"hp":wolf.hp,"state":wolf.state,"visible":wolf.visual.is_visible_in_tree(),"hurt":wolf.hurt_timer,"bar":wolf.health_bar.is_visible_in_tree(),"scale_y":wolf.visual.scale.y})
 state["nearby_combat"]=near
 return state

func observe_clip(row:Dictionary) -> void:
 if not clip_enabled and not plate_enabled:return
 if row.get("kind","")=="wood" and row.action=="farm" and first_pine_frame<0 and field.actor.position.distance_to(field.resource_tree.position)<3.4:
  first_pine_frame=tick
 for e in tick_events:
  if e.event=="regrow_wood" and regrown_tick<0:regrown_tick=tick
  if e.event=="player_hurt":_trigger_clip("Wolf bite and visible HP loss",1.45)
  if e.event=="defeat" or e.event=="boss_defeat":_trigger_clip("Enemy falls and dissolves",2.05)
  if e.event=="player_fall":_trigger_clip("Knockdown and health restored at the camp" if field.camp_active else "Knockdown and health restored at the first buy plot",2.45)
 if row.action=="facepack":
  for wolf in field.enemies:
   if is_instance_valid(wolf) and wolf.hp>0 and wolf.state=="windup" and wolf.position.distance_squared_to(field.actor.position)<10:
    _trigger_clip("Wolf braces and lunges",1.7)
 var clip: String = row.get("shot","")
 if float(tick-stage_tick)/60.0>float(row.get("length",.9)):clip=""
 if tick<event_clip_end:clip=event_clip
 if row.get("source_id","")=="starter-stone" and field.lifecycle.cooling.has(row.source_id) and field.lifecycle.cooling[row.source_id]<.9:
  _trigger_clip("Quarry regrows",2.0)
 if first_pine_frame>=0 and (regrown_tick<0 or tick-regrown_tick<60) and OS.get_environment("WORLD_CHOP_PROOF")=="1":
  clip="Two axe recoils, tree fall and five-second return"
 if clip_enabled:_set_clip(clip)
