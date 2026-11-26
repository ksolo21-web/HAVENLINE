extends SceneTree

var field
var phases:Array
var index:=0
var tick:=0
var first_tick:=0
var stage_tick:=0
var touch_held:=false
var last_input:=Vector2.ZERO
var goal_tap_sent:=false
var camera:Camera3D
var death_movie:=OS.get_environment("FIELD_QA_DEATH_MOVIE")=="1"
var render_begun:=false
var out_dir:=OS.get_environment("FIELD_QA_OUTPUT")
var stream:FileAccess
var events:FileAccess
var origin:=Vector2(150,575)
var dry:=OS.get_environment("FIELD_QA_HEADLESS")=="1"
var replay_camera:=false
var unique_fields:={}
var speakers:Array[Node]=[]
var mixer:Node
var mix_states:= {}
var last_summary:={}
var finished:=false
var replay_drops:=0
var portrait:=OS.get_environment("FIELD_QA_PORTRAIT")=="1"
var stills:Dictionary={}
var taken:Dictionary={}
var review_small:=OS.get_environment("FIELD_QA_SMALL")=="1"
var shot_filter:=OS.get_environment("FIELD_QA_SHOT_FILTER").split(",",false)
var action_stills:=OS.get_environment("FIELD_QA_DYNAMIC_STILLS")=="1"

func _initialize()->void:
 call_deferred("run")

func touch(id:int,pos:Vector2,pressed:bool)->void:
 var e:=InputEventScreenTouch.new()
 e.index=id
 e.position=pos
 e.pressed=pressed
 root.push_input(e,true)

func steer(direction:Vector2)->void:
 if direction.is_zero_approx():
  if touch_held:
   touch(0,origin,false)
   touch_held=false
   last_input=Vector2.ZERO
  return
 if not touch_held:
  touch(0,origin,true)
  touch_held=true
 if last_input.distance_to(direction)<.006: return
 var e:=InputEventScreenDrag.new()
 e.index=0
 e.position=origin+direction*82.
 e.relative=(direction-last_input)*82.
 e.screen_relative=e.relative
 root.push_input(e,true)
 last_input=direction

func pt(x:Vector3)->Array:return [x.x,x.y,x.z]

func event(label:String,data:Dictionary={})->void:
 var row={"tick":tick,"t":tick/60.,"phase":String(phases[index].label) if index<phases.size() else "end","event":label,"data":data}
 events.store_line(JSON.stringify(row));events.flush()
 print("QA ",JSON.stringify(row))

func snapshot()->Dictionary:
 var actor:CharacterBody3D=field.actor
 var state:Dictionary={"engine_process_frame":Engine.get_process_frames(),"pos":pt(actor.global_position),"vel":pt(actor.velocity),"yaw":actor.rotation.y,"stage":String(phases[index].label) if index<phases.size() else "end","hud":field.opening_hud.prompt.text,"same_camera":root.get_camera_3d()==camera or dry,"zoom":field.get_zoom_ratio(),"tool":field.character_kit.equipped,"turn":field.character_kit.turn_id,"contacts":field.contacts.size(),"tree":field.resource_tree.phase,"rock":field.resource_rock.phase,"camp_visible":field.camp_built.visible,"gates":[]}
 for gate in field.gates:
  state.gates.append({"id":gate.gate_id,"open":gate.target_open,"held":gate.holding_for_occupancy})
 if field.has_method("qa_snapshot"):state.field=field.qa_snapshot()
 else: state.field=read_field()
 return state

func read_field()->Dictionary:
 if not "inventory" in field:return {"legacy":field.ledger.stock.duplicate(true)}
 var st:Dictionary=field.inventory.snapshot()
 st["costs"]=field.inventory.costs.duplicate(true)
 st["player_hp"]=field.player_hp
 st["event_count"]=field.events.size()
 st["last_game_event"]=field.events.back() if not field.events.is_empty() else {}
 st["tool_count"]=field.character_kit.count
 st["save_blocked"]=field.persist_blocked
 st["audio_rejected"]=field.sound.rejected_event_count
 st["loose"]={}
 for key in field.drops:
  var unit=field.drops[key]
  st.loose[key]=[unit.kind,pt(unit.mesh.position)]
 var e=field.enemy
 if e and is_instance_valid(e):
  st["wolf"]={"hp":e.hp,"state":e.state,"pos":pt(e.global_position),"visible":e.is_visible_in_tree()}
 if mixer:
  var loops:Dictionary={}
  for name in mixer._loops:
   var sound:AudioStreamPlayer=mixer._loops[name]
   loops[name]=[sound.playing,snappedf(sound.volume_db,.01)]
  st["music"]={"state":mixer._state,"stems":loops}
 if field.carry:
  var items:={}
  for k in field.carry.pieces:
   var group:Array=[]
   for node in field.carry.pieces[k]:
    if is_instance_valid(node) and node.is_visible_in_tree():group.append(pt(node.position))
   if not group.is_empty():items[k]=group
  st["vis_items"]=items
  st["transfers"]=field.carry.flights.size()
 return st

func begin_phase()->void:
 stage_tick=tick
 goal_tap_sent=false
 event("enter",phases[index])

func advance()->void:
 event("complete",snapshot())
 index+=1
 if index>=phases.size():
  steer(Vector2.ZERO);finished=true;return
 begin_phase()

func move_to(p:Array,tol:float)->bool:
 var pos:Vector3=field.actor.global_position
 var delta:=Vector3(float(p[0])-pos.x,0.,float(p[1])-pos.z)
 if delta.length()<=tol:
  steer(Vector2.ZERO);return true
 var right:=camera.global_basis.x
 var near:=right.cross(Vector3.UP)
 var d:=Vector2(delta.dot(right),delta.dot(near)).normalized()
 steer(d*clampf(delta.length()*1.25,.3,.98))
 return false

func circle_around(center:Vector3,radius:float,clockwise:float)->void:
 var radial:Vector3=field.actor.global_position-center
 radial.y=0.
 if radial.length_squared()<.01:radial=Vector3.RIGHT
 var velocity:=Vector3.UP.cross(radial.normalized())*.44*clockwise+radial.normalized()*clampf((radius-radial.length())*1.2,-.75,.75)
 var right:=camera.global_basis.x
 var near:=right.cross(Vector3.UP)
 steer(Vector2(velocity.dot(right),velocity.dot(near)).limit_length(.92))

func execute(row:Dictionary)->void:
 if tick-stage_tick>int(row.get("timeout",18))*60:
  event("timeout",snapshot());finished=true;quit(4);return
 match String(row.action):
  "pinch":
   steer(Vector2.ZERO)
   var since:=tick-stage_tick
   var center:=Vector2(405,702) if portrait else Vector2(830,390)
   var initial:=200.
   var wanted:=float(row.ratio)
   if since==1:
    touch(5,center-Vector2.RIGHT*initial*.5,true)
    touch(6,center+Vector2.RIGHT*initial*.5,true)
   elif since>1 and since<35:
    var span:=lerpf(initial,initial*wanted,float(since-1)/33.)
    for sign_index in [5,6]:
     var g:=InputEventScreenDrag.new();g.index=sign_index
     g.position=center+Vector2.RIGHT*span*.5*(-1 if sign_index==5 else 1)
     root.push_input(g,true)
   elif since==35:
    touch(5,center,false);touch(6,center,false)
   elif since>45:advance()
  "loot":
   if int(field.inventory.carried[row.kind])>=int(row.count):
    steer(Vector2.ZERO)
    if field.carry.flights.is_empty():advance()
   else:
    var nearest=Vector3.INF
    for entry in field.drops.values():
     if entry.kind!=row.kind:continue
     var point:Vector3=entry.at
     if nearest==Vector3.INF or point.distance_squared_to(field.actor.position)<nearest.distance_squared_to(field.actor.position):nearest=point
    if nearest!=Vector3.INF:
     move_to([nearest.x,nearest.z],.30)
    else:
     move_to([float(row.p[0])+.9,float(row.p[1])+.9],.28)
  "plot":
   var destination:Vector2=field.field_env.receiver_position(String(row.kind))
   if move_to([destination.x,destination.y],float(row.get("tol",.18))):advance()
  "walk":
   if move_to(row.p,float(row.get("tol",.20))):advance()
  "facepack":
   if field.events.any(func(e):return e.event=="reset"):
    steer(Vector2.ZERO);advance()
   elif field.reset_time>0:
    steer(Vector2.ZERO)
   else:
    var n=field.enemy
    for wolf in field.enemies:
     if wolf.hp>0 and (n.hp<=0 or wolf.global_position.distance_squared_to(field.actor.global_position)<n.global_position.distance_squared_to(field.actor.global_position)):n=wolf
    if n and n.hp>0:
     move_to([n.global_position.x,n.global_position.z],.55)
  "hunt":
   var e=field.enemy
   if e.hp<=0:
    steer(Vector2.ZERO);advance()
   elif tick-stage_tick<90 and row.get("seek_bite",true):
    move_to([e.global_position.x,e.global_position.z],.70)
   else:
    circle_around(e.global_position,float(row.get("radius",2.52)),1.)
  "orbit":
   var body=field.resource_tree if row.target=="tree" else field.resource_rock
   if row.target=="tree" and body.phase=="falling":
    if body.sweep_clear(field.actor.global_position,.31):steer(Vector2.ZERO)
    else:move_to([body.global_position.x+2.1,body.global_position.z+1.6],.18)
   else:
    circle_around(body.global_position,float(row.get("radius",2.60)),float(row.get("direction",1.)))
   if (row.has("s") and tick-stage_tick>=int(round(float(row.s)*60.))) or (row.has("test") and matches_observation(String(row.test),row)):
    steer(Vector2.ZERO);advance()
  "hold":
   steer(Vector2.ZERO)
   if tick-stage_tick>=int(round(float(row.s)*60.)):advance()
  "gate":
   steer(Vector2.ZERO)
   if goal_tap_sent and tick-stage_tick>30:advance();return
   if not goal_tap_sent and field.gate_button.visible and field.nearest_gate!=null and field.nearest_gate.gate_id==row.gate:
    if not field.nearest_gate.target_open:
     var center:Vector2=field.gate_button.get_global_rect().get_center()
     touch(3,center,true);touch(3,center,false)
    goal_tap_sent=true
  "wait":
   steer(Vector2.ZERO)
   if matches_observation(String(row.test),row):advance()
  _:
   event("invalid_route",row);finished=true;quit(5)

func matches_observation(test:String,row:Dictionary)->bool:
 match test:
  "tree_felled":return field.resource_tree.phase=="credited"
  "rock_mined":return field.resource_rock.phase=="mined" or field.resource_rock.strikes>=3
  "earned":return field.inventory.carried[row.kind]>=row.count
  "stored":return field.inventory.stored[row.kind]>=row.count
  "built":return field.inventory.complete(row.id) and field.carry.flights.is_empty()
 return false

func natural_plate()->void:
 var name:=""
 var stage:=String(phases[index].label)
 var elapsed:=tick-stage_tick
 if stage=="Close-range pack attacks and recovery" or stage=="Recovered with prior inventory":
  if field.player_hp==0 and not taken.has("defeated-player"):
   taken["defeated-player"]=true;take_still("defeated-player",tick)
  elif stage=="Recovered with prior inventory" and elapsed>24 and not taken.has("recovered-player"):
   taken["recovered-player"]=true;take_still("recovered-player",tick)
  return
 var ev:Dictionary=field.events.back() if not field.events.is_empty() else {}
 var age:float=field.simulation_time-float(ev.get("t",-99.))
 if stage.begins_with("Fresh snowfield") and elapsed>=26:name="01-before"
 elif stage=="Cut the starter pine" and field.resource_tree.strikes==1:name="02-tree"
 elif stage=="Break the mine with the pickaxe" and field.resource_rock.strikes>=1:name="03-mine"
 elif stage.begins_with("Wolf encounter") and field.enemy.state=="lunge":name="04-wolf-lunge"
 elif stage.begins_with("Collect the wolf meat") and elapsed>=4:name="05-wolf-defeat"
 elif stage=="Read all three carried stacks" and elapsed>=22:name="06-loaded"
 elif stage=="Completed hearth, fence and gates" and elapsed>=45:name="07-built"
 elif field.inventory.paid.center_hearth.wood==1:name="07a-payment"
 elif field.reveal_countdown>=0 and field.reveal_countdown<=.245:name="07b-reveal-start"
 elif field.camp_active and ev.get("event","")=="reveal" and age>=.08:name="07c-reveal-rise"
 elif stage=="Three dedicated floor stacks" and elapsed>=28:name="08-stocks"
 elif stage=="Approach the two-material upgrade" and elapsed>=2:name="08b-stocks-clear"
 elif stage=="Upgrade applied and visible" and elapsed>=28:name="09-upgraded"
 elif field.inventory.paid.orbit_upgrade.stone==1:name="09a-upgrade-payment"
 elif stage=="Unbroken snow outside the eastern fence" and elapsed>=27:name="10-gate-exterior"
 if name!="" and not taken.has(name) and (shot_filter.is_empty() or name in shot_filter):
  taken[name]=true;take_still(name,tick)

func take_still(id:String,at:int)->void:
 await process_frame
 RenderingServer.force_draw(false,1./24.)
 var img:Image=root.get_texture().get_image()
 var dims:=Vector2i(2160,3840) if portrait else Vector2i(3840,2160)
 if review_small:dims=Vector2i(720,1280) if portrait else Vector2i(1280,720)
 if img.get_size()!=dims or root.size!=dims or root.scaling_3d_scale!=1.:
  event("invalid4k",{"size":[img.get_width(),img.get_height()],"scale":root.scaling_3d_scale,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"adapter":RenderingServer.get_video_adapter_name(),"actual_screen":str(DisplayServer.screen_get_size())});quit(7);return
 img.convert(Image.FORMAT_RGB8)
 img.save_png(out_dir.path_join(id+".png"))
 event("native_still",{"game_state":read_field(),"hud_hint":field.opening_hud.prompt.text,"name":id,"requested_tick":at,"at_engine_tick":Engine.get_physics_frames()-first_tick,"width":img.get_width(),"height":img.get_height(),"scale":root.scaling_3d_scale,"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"adapter":RenderingServer.get_video_adapter_name(),"actual_screen":str(DisplayServer.screen_get_size())})
 
func observe_sound_node(node:Node)->void:
 if node.has_signal("cue_started"):
  mixer=node
  node.connect("cue_started",func(key:String,clock:float,voice:int):event("runtime_cue",{"cue":key,"audio_clock":clock,"voice":voice}))
 if node is AudioStreamPlayer or node is AudioStreamPlayer2D or node is AudioStreamPlayer3D:
  speakers.append(node)

func observe_audio()->void:
 for i in range(speakers.size()-1,-1,-1):
  var node=speakers[i]
  if not is_instance_valid(node):
   speakers.remove_at(i)
   continue
  var id:int=node.get_instance_id()
  var stream_id:String=node.stream.resource_path if node.stream and node.playing else ""
  if stream_id!=String(mix_states.get(id,"")):
   mix_states[id]=stream_id
   if not stream_id.is_empty():
    event("audio_stream",{"path":stream_id,"bus":String(node.bus),"gain_db":float(node.volume_db),"player":str(node.get_path())})

func run()->void:
 var shots:=OS.get_environment("FIELD_QA_STILLS")
 if not shots.is_empty():stills=JSON.parse_string(FileAccess.get_file_as_string(shots))
 var route_file:=OS.get_environment("FIELD_QA_PLAN")
 phases=JSON.parse_string(FileAccess.get_file_as_string(route_file))
 stream=FileAccess.open(out_dir.path_join("observations.jsonl"),FileAccess.WRITE)
 events=FileAccess.open(out_dir.path_join("events.jsonl"),FileAccess.WRITE)
 var entry:=OS.get_environment("FIELD_QA_SCENE")
 node_added.connect(observe_sound_node)
 field=load(entry if not entry.is_empty() else "res://field_opening.tscn").instantiate()
 root.add_child(field)
 current_scene=field
 camera=field.camera
 for j in 12:await physics_frame
 if portrait:origin=Vector2(126,1060)
 first_tick=Engine.get_physics_frames()
 begin_phase()
 while not finished:
  tick=Engine.get_physics_frames()-first_tick
  if death_movie and not render_begun and field.player_hp<field.MAX_HP:
   render_begun=true
   RenderingServer.set_render_loop_enabled(true)
   event("clip_render_started",{"source_frame":Engine.get_process_frames(),"hp":field.player_hp})
  if action_stills:natural_plate()
  if stills.has(str(tick)) and not taken.has(str(tick)):
   taken[str(tick)]=true;take_still(stills[str(tick)],tick)
  observe_audio()
  var state:=snapshot()
  state["tick"]=tick
  if not state.same_camera:
   event("camera_changed",state);quit(6);return
  stream.store_line(JSON.stringify(state))
  if tick%120==0:stream.flush()
  execute(phases[index])
  if not finished:await physics_frame
 stream.close()
 events.close()
 if index>=phases.size():
  print("PASS elapsed game seconds ",tick/60.)
  if "events" in field:
   var export:=FileAccess.open(out_dir.path_join("game-events.json"),FileAccess.WRITE)
   export.store_string(JSON.stringify(field.events));export.close()
  field.queue_free()
  for n in 12:
   OS.delay_msec(20)
   await process_frame
  quit()
