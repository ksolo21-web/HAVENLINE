extends "res://tests/world_final_route.gd"

const STORY_ROWS := {
 "The first expansion opens the house project":"The first expansion reveals the corner offers",
 "Inspect the earned shelves inside tier 1":"Wood corner before spending",
 "Inspect the earned shelves inside tier 2":"Stone corner before spending",
 "Inspect the earned shelves inside tier 3":"Meat corner before spending",
}
const CAPTIONS := {
 "Wood on the timber floor":"Starter storehouse and timber bay",
 "Stone on the quarry floor":"Reinforced storehouse and stone bay",
 "Meat on the food floor":"Advanced storehouse and food bay",
}

func observe_clip(row:Dictionary) -> void:
 if STORY_ROWS.has(row.label):
  var view:=row.duplicate()
  view.label=STORY_ROWS[row.label]
  super.observe_clip(view)
 else:
  super.observe_clip(row)

func _set_clip(id:String) -> void:
 super._set_clip(CAPTIONS.get(id,id))

func read_field() -> Dictionary:
 var state:=super.read_field()
 if not field or not field.depot or not field.depot.house:return state
 var house=field.depot.house
 var counts:={}
 for kind in ["wood","stone","meat"]:
  var visible_count:=0
  for unit in field.carry.pieces.get("storage/"+kind,[]):
   if unit.is_visible_in_tree():visible_count+=1
  counts[kind]=visible_count
 state["house"]={"tier":house.tier,"cutaway":house.is_interior_visible(),"door":snappedf(house.open_amount,.001),"roof_visible":house.parts.Roof.is_visible_in_tree(),"offer":field.depot.offer,"visit":field.depot.visit,"shelves":counts}
 if field.opening_hud.health_text:
  state["hp_hud"]={"text":field.opening_hud.health_text.text,"value":field.opening_hud.health_bar.value,"visible":field.opening_hud.health_bar.is_visible_in_tree()}
 return state
