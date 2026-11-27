extends "res://tests/qa_crew_haul.gd"
## Observe a worker whose raw cargo was actually harvested during Field-haul.
func run()->void:
 if not Save.Profile.new().configure(OS.get_cmdline_user_args()):quit(2);return
 game=load("res://field_opening.tscn").instantiate()
 root.add_child(game);current_scene=game;worker=game.survivor
 game.set_physics_process(false);game.set_process(false)
 for i in 3:await process_frame
 var aisles=game.settlement_loop.conveyors.network.aisles
 var apron:Vector3=worker._shelf_apron()
 var found:=false
 for offset in [Vector3(.7,0,-.65),Vector3(-.9,0,-.15),Vector3(.35,0,.85),Vector3(.1,0,.45),Vector3.ZERO]:
  var candidate:Vector3=apron+offset
  if aisles.resume_position(candidate,float(game.layout.actor_radius)).is_equal_approx(candidate):
   game.actor.global_position=candidate
   found=true
   break
 game.camera.global_position=game.actor.global_position+game.camera_follow_offset
 var feet:Vector3=game.actor.global_position
 var initial:=units()
 var first:=-1
 var finish:=-1
 var interval:=5
 DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
 for frame in 2400:
  tick(1./60.)
  if first<0 and worker.phase=="carrying" and game.actor.position.distance_to(worker.actor.position)<2.2:
   first=frame
   await zooms("Loaded-return")
  if worker.phase=="bin_delivery" and not worker.delivery_stream.is_empty():
   await zooms("Shelf-transfer")
  if first>=0 and (frame-first)%interval==0 and frames<34:
   if recording:await record_frame()
   else:frames+=1
  if initial.wood>0 and units().wood+units().stone==0 and finish<0:finish=frame
  if finish>=0 and frames>=34:break
 var doc:={"initial":initial,"start_frame":first,"discharged_at":finish,"frame_count":frames,"photos":cameras,"initial_player":str(feet),"final_player":str(game.actor.global_position),"located":found,"natural_receipts":game.inventory.settlement.worker_deliveries}
 var f:=FileAccess.open(output.path_join("Earned-return-photos.json"),FileAccess.WRITE);f.store_string(JSON.stringify(doc," "));f.close()
 print("EARNED_RETURN ",JSON.stringify(doc))
 await Session.drain_field_audio(self,game);game.queue_free()
 for i in 3:await process_frame
 quit(0 if found and initial.wood>=100 and initial.stone>=100 and (not recording or cameras.size()==2) and frames>=34 and finish>=0 else 1)
