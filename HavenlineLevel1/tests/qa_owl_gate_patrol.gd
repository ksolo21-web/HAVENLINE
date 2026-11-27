extends "res://tests/field_route.gd"

const Session := preload("res://tests/lifecycle_test_profile.gd")
var states := {}
var log_rows := []
var audit := {}
var checks := {}
var frames_at := 0
var wolf
var study:=OS.get_environment("OWL_STUDY")
var photos:Dictionary={}
var capture_path := OS.get_environment("OWL_EVIDENCE_FRAMES")

func _initialize() -> void:
 var guard=preload("res://opening_save.gd").new()
 if guard.configure(OS.get_cmdline_user_args()): call_deferred("run")
 elif not Session.isolated(self,"res://tests/qa_owl_gate_patrol.gd"): call_deferred("run")

func record() -> void:
 states[field.owl.state] = true
 if not study.is_empty():
  if frames_at<=160 and frames_at%4==0:
   await process_frame
   RenderingServer.force_draw(false)
   root.get_texture().get_image().save_jpg(study.path_join("frames/r%03d.jpg"%int(frames_at/4)),.90)
  var label:="Gate-contact" if field.field_env.is_inside_camp(field.actor.position) else "Field-contact"
  if field.owl.state=="strike" and not photos.has(label):
   photos[label]=true
   for zoom in [1.,2.]:
    field.set_zoom_ratio(zoom)
    await process_frame
    RenderingServer.force_draw(false)
    root.get_texture().get_image().save_jpg(study.path_join(label+"-%dx.jpg"%int(zoom)),.94)
   field.set_zoom_ratio(1.)
 var status = wolf.state if is_instance_valid(wolf) else "retired"
 if frames_at%6==0:
  log_rows.append([frames_at, str(field.actor.position), field.owl.state, str(field.owl.position), status, (wolf.hp if is_instance_valid(wolf) else -1), int(field.inventory.settlement.owl_hits), field.character_kit.active, field.player_hp])
 if not capture_path.is_empty() and frames_at%3==0:
  await process_frame
  RenderingServer.force_draw()
  root.get_texture().get_image().save_jpg(capture_path.path_join("f%04d.jpg"%(frames_at/3)),.90)
 frames_at += 1

func run() -> void:
 if not study.is_empty():DirAccess.make_dir_recursive_absolute(study.path_join("frames"))
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 await physics_frame
 camera=field.camera
 origin=Vector2(root.size.x*.20,root.size.y*.72)
 if not field.field_ready or field.persist_blocked:quit(1);return
 for w in field.enemies.duplicate(): field.encounters._remove(w)
 for j in field.inventory.costs.center_hearth.wood:
  field.inventory.collect("owl-funding-"+str(j),"wood")
  field.inventory.payment("center_hearth","wood",false)
 field._finish_purchase("center_hearth")
 field._apply_hearth(true,false)
 field.actor.position=field.owl.Crew.ROOST_AT
 for j in field.owl.Crew.OWL_MEAT:field.inventory.collect("owl-fee-"+str(j),"meat")
 field.carry.sync(true)
 for j in 140:await physics_frame
 checks["purchase_unlocks_owl"]=not field.inventory.settlement.survivor_paid and field.owl.Crew.owns_owl(field.inventory.settlement) and field.owl.visible and field.inventory.carried.meat==0 and not field.settlement_loop.works.owl_plot.visible
 if not checks.purchase_unlocks_owl: print("FAILED_UNLOCK ",field.inventory.settlement);quit(2);return
 for w in field.enemies.duplicate(): field.encounters._remove(w)
 var gate:Vector3=field.gates[1].global_position
 field.actor.position=gate-Vector3.RIGHT*2.2
 field.encounters.remaining=55.
 for i in 110: await physics_frame
 var pos:Vector3=gate+Vector3(4.8,0,.81)
 field.encounters.serial+=1
 wolf=field.encounters._add(pos,false,field.encounters.serial,pos)
 var events_at:int=field.events.size()
 var waiting := false
 for j in 290:
  if not waiting:
   if field.actor.position.x > gate.x-1.28:
    waiting=true
    steer(Vector2.ZERO)
   else: move_to([gate.x-.9,gate.z],.12)
  await physics_frame
  await record()
 steer(Vector2.ZERO)
 checks["held_player_inside_without_autoattack"] = log_rows.all(func(row): return not row[7])
 checks["owl_scores_from_safe_gate_without_hero_or_tower"]=field.inventory.settlement.owl_hits>0 and not field.character_kit.active and not field.inventory.complete("watchtower") and field.field_env.is_inside_camp(field.actor.global_position)
 audit["inside_gate"]={"owl_hits":field.inventory.settlement.owl_hits,"wolf_hp":(wolf.hp if is_instance_valid(wolf) else -1),"player_at":str(field.actor.position),"perch":str(field.owl.position)}
 for i in 250:
  move_to([gate.x+4.1,gate.z+1.25],.27)
  await physics_frame
  await record()
 steer(Vector2.ZERO)
 audit["after_exit"]={"sound":field.sound._counts,"sound_focus":field.sound._focused,"sound_ready":field.sound._ready_to_play,"owl_hits":field.inventory.settlement.owl_hits,"states":states.keys(),"player_hp":field.player_hp,"events":field.events.slice(events_at)}
 checks["controller_exits_the_gate"]=not field.field_env.is_inside_camp(field.actor.position)
 checks["dive_strike_recovery_are_visible"]=states.has_all(["windup","dive","strike","recover"])
 checks["dive_and_contact_each_emit_their_native_cue"] = field.events.any(func(row): return row.event=="owl_hit") and field.events.any(func(row): return row.event=="owl_dive") and field.sound._bank.has("owl_hit") and field.sound._bank.has("owl_dive")
 # The player remains outside until an actual live wolf injures them. Spawn
 # another ordinary threat well outside the orbit of a stationary explorer.
 var hurt_before:int=field.player_hp
 if hurt_before==field.MAX_HP:
  var near:Vector3=field.actor.position+Vector3(1.2,0,.15)
  field.encounters.serial+=1
  wolf=field.encounters._add(near,true,field.encounters.serial,near)
  for i in 270:
   await physics_frame;await record()
   if field.player_hp<hurt_before:break
 checks["explorer_wounded_in_a_live_encounter"]=field.player_hp<field.MAX_HP and field.events.any(func(row):return row.event=="player_hurt")
 var wounded_hp:int=field.player_hp
 var hits_before:int=field.inventory.settlement.owl_hits
 var wide:Vector3=field.actor.position+Vector3(6.0,0,0.9)
 field.encounters.serial+=1
 wolf=field.encounters._add(wide,true,field.encounters.serial,wide)
 for i in 540:
  await physics_frame;await record()
  if field.inventory.settlement.owl_hits>hits_before:break
 checks["bird_intercepts_while_owner_is_wounded"]=field.inventory.settlement.owl_hits>hits_before and field.player_hp>0 and field.player_hp<field.MAX_HP
 for w in field.enemies.duplicate():field.encounters._remove(w)
 field.encounters.remaining=400.
 for i in 320:
  if move_to([gate.x-2.65,gate.z],.25):break
  await physics_frame;await record()
 steer(Vector2.ZERO)
 for i in 390:
  await physics_frame;await record()
  if field.owl.state=="perched" and field.player_hp>wounded_hp:break
 checks["controller_returns_into_sanctuary"]=field.field_env.is_inside_camp(field.actor.position)
 checks["calm_bird_returns_to_post_as_owner_heals"]=field.owl.state=="perched" and not field.character_kit.active and field.player_hp>wounded_hp
 # A threat at a different live gate should draw the owl off the post even
 # when its owner stays well inside, clear of either gate activation radius.
 field.actor.position=Vector3(-1.4,0,-1.95)
 var south:Vector3=field.gates[0].global_position
 var intrusion:Vector3=south+Vector3(.35,0,3.15)
 field.encounters.serial+=1
 wolf=field.encounters._add(intrusion,false,field.encounters.serial,intrusion)
 var safe_hits:int=field.inventory.settlement.owl_hits
 var safe_hp:int=field.player_hp
 for i in 590:
  await physics_frame;await record()
  if field.inventory.settlement.owl_hits>safe_hits:break
 checks["distant_second_gate_is_guarded_with_owner_stationary"]=field.inventory.settlement.owl_hits>safe_hits and not field.character_kit.active and field.player_hp>=safe_hp
 audit.full_shift={"shelter_hp":safe_hp,"wounded_hp":wounded_hp,"total_contacts":field.inventory.settlement.owl_hits,"seconds":float(frames_at)/60.}
 var res={"phase_frames":log_rows,"checks":checks,"audit":audit}
 if not OS.get_environment("OWL_EVIDENCE_JSON").is_empty():
  var f=FileAccess.open(OS.get_environment("OWL_EVIDENCE_JSON"),FileAccess.WRITE)
  f.store_string(JSON.stringify(res," "));f.close()
 print("OWL_PATROL ",JSON.stringify(checks))
 await Session.drain_field_audio(self,field)
 field.queue_free()
 for i in 4:await process_frame
 quit(int(false in checks.values()))
