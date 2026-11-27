extends SceneTree
var field
var camera: Camera3D
var origin := Vector2.ZERO
var touch_held := false
var last_input := Vector2.ZERO
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


var mode:=OS.get_environment("FIELD_CASE")
var entered:=0
var changes:=0
var max_flights:=0
var peak_ms:=0.
var milestones:={}
var prior:int
var hand0:int
var store0:int
var frame_costs:=[]
var capture:=OS.get_environment("FIELD_PHOTOS")
var photo_marks:={}
var validation:={}
var intake_ids:=[]
var current_tools:=0
func photo(label:String)->void:
 if capture.is_empty() or photo_marks.has(label):return
 photo_marks[label]=true
 for scale:float in [1.,2.]:
  field.set_zoom_ratio(scale)
  RenderingServer.force_draw(false,1./60.)
  root.get_texture().get_image().save_jpg(capture.path_join(mode+"-"+label+"-"+str(int(scale))+"x.jpg"),.93)
 field.set_zoom_ratio(1.)
func conserved()->bool:
 var fresh:=preload("res://field_inventory.gd").new()
 return fresh.configure(field.inventory.configured_costs) and fresh.restore(field.inventory.snapshot())

func balance(d:Dictionary)->int:
 var s:=0
 for n in d.values(): s+=int(n)
 return s
func seconds()->float:return (Engine.get_physics_frames()-entered)/60.
func stats()->Dictionary:
 return {"mode":mode,"blocked":field.persist_error,"three_tools":field.character_kit.count,"drops":field.drops.size(),"held":field.inventory.carried.duplicate(),"stored":field.inventory.stored.duplicate(),"all_credits":field.inventory.collected.size(),"field_time":seconds(),"real_s":(Time.get_ticks_msec()-prior)*.001,"peak_frame_ms":peak_ms,"inventory_signals":changes,"max_flights":max_flights,"position":pt(field.actor.position),"hp":field.player_hp,"wolves":field.enemies.size(),"receiver":field.carry.visit_target}
func run()->void:
 field=load("res://field_opening.tscn").instantiate();root.add_child(field);current_scene=field;camera=field.camera
 origin=Vector2(root.size.x*.28,root.size.y*.7)
 field.carry.inventory_changed.connect(func():changes+=1)
 entered=Engine.get_physics_frames();prior=Time.get_ticks_msec()
 milestones.start=stats()
 for token in field.drops: intake_ids.append(token)
 validation["all building receipts and legacy rescue, production, meal and pet restore"]=field.inventory.complete("orbit_upgrade") and field.inventory.Settlement.ready_to_continue(field.inventory.settlement,field.inventory.build_order) and field.inventory.settlement.rescued
 hand0=balance(field.inventory.carried);store0=balance(field.inventory.stored)
 var prev:=Time.get_ticks_usec()
 var stock0:=balance(field.inventory.carried)
 for n in (1370 if mode=="repeat" else (650 if mode=="store" else 480)):
  if not capture.is_empty() and n<35:
   steer(Vector2.ZERO)
  elif not capture.is_empty() and mode=="pile" and n<=210:
   move_to([24.,11.],.15)
  elif mode=="store":move_to([field.depot.APRON.x,field.depot.APRON.z],.13)
  elif mode=="repeat":
   if n<1090: move_to([-.4,11.25],.2)
   else:
    var goal:Vector3=field.resource_rock.position
    var closest:=INF
    for entry:Dictionary in field.drops.values():
     if entry.kind!="stone" or entry.at.distance_squared_to(goal)>4.: continue
     var distance:float=entry.at.distance_squared_to(field.actor.position)
     if distance<closest: closest=distance; goal=entry.at
    move_to([goal.x,goal.z],.22)
  elif n>210:
   var home=Vector2(24,11)
   var phase=(n-211)/60.
   var to=home+Vector2(cos(phase),sin(phase))*1.24
   move_to([to.x,to.y],.12)
  await physics_frame
  if n==24: photo("starting")
  if capture.ends_with("/After") and n>=24 and n<=144 and n%4==0:
   var frames:=capture.path_join(mode+"-frames")
   DirAccess.make_dir_recursive_absolute(frames)
   RenderingServer.force_draw(false,1./60.)
   root.get_texture().get_image().save_jpg(frames.path_join("frame-%03d.jpg"%((n-24)/4)),.90)
  var now:=Time.get_ticks_usec(); var ms:float=(now-prev)/1000.
  peak_ms=maxf(peak_ms,ms);prev=now
  max_flights=maxi(max_flights,field.carry.flights.size())
  current_tools=maxi(current_tools,field.character_kit.count)
  frame_costs.append(ms)
  if mode=="store" and not field.carry.flights.is_empty(): photo("sending")
  elif mode!="store" and not field.carry.flights.is_empty(): photo("collecting")
  var b:=balance(field.inventory.carried)
  if mode=="store" and b<stock0 and not milestones.has("start_landing"):milestones.start_landing=stats()
  if mode=="store" and b==0 and not milestones.has("all_landed"):
   milestones.all_landed=stats()
   photo("stocked")
  if mode in ["overflow","pile"] and n==170: photo("carried")
  if n in [0,30,60,120,200]:milestones[str(n)]=stats()
  if (mode=="store" and milestones.has("all_landed") and field.carry.flights.is_empty()) or field.persist_blocked:break
 milestones.end=stats()
 validation["journal and all material balances remain usable"]=not field.persist_blocked and conserved()
 validation["three orbiting tools were equipped"]=current_tools==3
 if mode in ["pile","overflow"]:
  validation["all deliberately scattered receipts collected exactly once"]=intake_ids.size()==(72 if mode=="pile" else 128) and intake_ids.all(func(token):return field.inventory.collected.get(token)==token.get_slice("-",0))
 if mode=="store":
  validation["all 5200 carried bundles reached storage and operating workshops"]=balance(field.inventory.carried)==0 and hand0==5200 and balance(field.inventory.stored)-store0>=5190
 if mode=="repeat":
  var depletion=field.events.filter(func(e):return e.event=="deplete_stone" and Vector2(e.x,e.z).distance_to(Vector2(-2.3,11.75))<.1)
  validation["same quarry paid three times across regrowth"]=depletion.size()>=3 and int(field.inventory.carried.stone)>=9
  milestones["harvest_times"]=depletion.map(func(e):return e.t)
  photo("harvested")
 field._persist_world()
 var cold:=preload("res://field_inventory.gd").new()
 cold.configure(field.inventory.configured_costs)
 var result=field.field_save.load_into(cold)
 validation["cold reopened checksummed credit and raw balances"]=result==OK and cold.carried==field.inventory.carried and cold.collected==field.inventory.collected and cold.stored==field.inventory.stored
 milestones["checks"]=validation
 if not frame_costs.is_empty():
  var sorted:=frame_costs.duplicate();sorted.sort()
  milestones["wall_frame_ms"]={"samples":sorted.size(),"median":sorted[sorted.size()/2],"p95":sorted[floori((sorted.size()-1)*.95)],"maximum":sorted[-1],"first_ten":frame_costs.slice(0,10)}

 print("FIELD_HISTORY ",JSON.stringify(milestones))
 field.sound.stop_playback()
 for tick in 12:
  OS.delay_msec(20)
  await process_frame
 field.queue_free();await process_frame;quit()
