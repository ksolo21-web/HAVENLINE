extends SceneTree
var w
var q="/tmp/havenline-critic95-post"
func _initialize():call_deferred("run")
func snap(n):
 for i in 4:await process_frame
 RenderingServer.force_draw(false)
 root.get_texture().get_image().save_jpg(q+"/"+n+".jpg",.94)
func run():
 w=load("res://field_opening.tscn").instantiate();root.add_child(w)
 for i in 5:await physics_frame
 w.set_physics_process(false)
 w.actor.position=Vector3(2,0,8);w.actor.rotation.y=deg_to_rad(300)
 w.actor.force_update_transform();w.actor.reset_physics_interpolation()
 w.camera.position=w.actor.position+Vector3(7,11,11);w.camera.force_update_transform();w.camera.reset_physics_interpolation()
 for kind:String in w.Inventory.KINDS:w.inventory.carried[kind]=5
 w.carry.sync();w.character_kit.set_upgraded(false);w.character_kit.reach_scale=1.;w.character_kit.begin("axe");w.character_kit.height=.89;w.character_kit.elapsed=28./120.;w.character_kit.pose()
 for s in w.character_kit.slots:
  s.axe.reset_physics_interpolation()
 await snap("cross-full")
 w.set_zoom_ratio(2.)
 await snap("cross-pinch")
 var target=w.carry.pieces["carry/metal"][1].global_position
 w.camera.size=1.15;w.camera.global_position=target+Vector3(-1.8,1.8,-2.3);w.camera.look_at(target);w.camera.reset_physics_interpolation()
 await snap("cross-detail")
 w.queue_free()
 for i in 8:await process_frame
 quit()
