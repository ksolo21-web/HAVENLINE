extends "res://tests/world_effects_route.gd"

# Record exactly the coordinate and visibility contract used in the prior film.
func read_field() -> Dictionary:
 var state:=super.read_field()
 var carry=field.carry
 var matches:=true
 var limit_min:=100000
 var visible:={}
 for kind in ["wood","stone","meat"]:
  var available:int=carry._available(kind,"carry")
  var cap:int=carry._pack_limit(kind)
  var previously_visible:int=available
  var now_visible:int=carry._visible_units(kind,available,"carry")
  var index:=maxi(0,available-1)
  var before:Vector3=carry.rack.to_global(carry._pack_position(kind,index))
  var after:Vector3=carry._place("carry",kind,index)
  var old_yaw:float=carry.actor.global_rotation.y+carry._tier_yaw(kind,index)
  matches=matches and previously_visible==now_visible and before.distance_to(after)<.00001 and absf(wrapf(carry._heading("carry",kind,index)-old_yaw,-PI,PI))<.00001
  limit_min=mini(limit_min,cap)
  visible[kind]=now_visible
 state["low_load"]={"same_low_load_visibility_and_flight_endpoints":matches,"minimum_render_capacity":limit_min,"visible":visible}
 return state
