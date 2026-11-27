extends SceneTree
const Session=preload("res://tests/lifecycle_test_profile.gd")
const Guard=preload("res://opening_save.gd")
const Save=preload("res://field_save.gd")
const SelfPath="res://tests/qa_field_camp_controls.gd"
const PaidFixture="res://tests/fixtures/camp_hud_paid.json"

var g
var results:Dictionary={}
func _initialize():
 if "--camp-hud-fixture" in OS.get_cmdline_user_args():
  if not Guard.new().configure(OS.get_cmdline_user_args()):
   quit(2)
   return
  call_deferred("run")
  return
 var directory:=Session.make_directory()
 if directory.is_empty():
  quit(2)
  return
 var receipt:=FileAccess.get_file_as_bytes(PaidFixture)
 var file:=FileAccess.open(directory.path_join(Save.PRIMARY),FileAccess.WRITE)
 if receipt.is_empty() or not file:
  Session.remove_owned(directory)
  quit(2)
  return
 file.store_buffer(receipt)
 file.close()
 var code:=Session.child(SelfPath,directory,"--camp-hud-fixture")
 Session.remove_owned(directory)
 quit(code)
func tap(at:Vector2):
 for value in [true,false]:
  var e:=InputEventScreenTouch.new()
  e.index=3;e.pressed=value;e.position=at
  root.push_input(e,true)
  await physics_frame
func require(key:String,ok:bool):
 results[key]=ok
 if not ok:push_error(key)
func run():
 g=load("res://field_opening.tscn").instantiate()
 root.add_child(g);current_scene=g
 for i in 4:await physics_frame
 var d=g.opening_hud.camp_dock
 var h=g.opening_hud
 require("hud visible",d.visible and d.build.is_visible_in_tree())
 for tab in ["Camp","Storage","Survivors","Build"]:
  var btn:Control=d.build if tab=="Build" else d.tabs[tab]
  await tap(btn.get_global_rect().get_center())
  require("touch opens "+tab,d.tab==tab and d.sheet.visible and d.commands.size()>0)
  if d.commands.size():
   var id=d.commands[0][1]
   await tap(d.commands[0][0].get_global_rect().get_center())
   require("touch executes "+tab,d.tab=="" and (d.tracked_point().is_finite() or (g.camp_layout.active and id=="move") or (id=="home" and g.field_env.is_inside_camp(g.actor.position))))
   if g.camp_layout.active:g.camp_layout.close()
  else:d.dismiss()
 await tap(d.tabs.Camp.get_global_rect().get_center())
 for p in d.commands:
  if p[1]=="move":
   await tap(p[0].get_global_rect().get_center())
   require("move opens native equipment placement",g.camp_layout.active)
   if g.camp_layout.active:g.camp_layout.close()
   break
 root.content_scale_size=Vector2i(720,720)
 root.content_scale_aspect=Window.CONTENT_SCALE_ASPECT_EXPAND
 root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
 root.size=Vector2i(360,840)
 for i in 4:await process_frame
 h.reflow()
 var safe:Rect2=h._safe_rect()
 var dp_per_unit:=360./root.get_visible_rect().size.x
 var hit_rects:Dictionary={}
 var buttons:Array=[d.build,d.pack_button,h.quality]
 buttons.append_array(d.tabs.values())
 for button in buttons:
  var rect:Rect2=button.get_global_rect()
  hit_rects[button.name]={"usable_width":snappedf(rect.size.x*dp_per_unit,.1),"usable_height":snappedf(rect.size.y*dp_per_unit,.1),"safe":safe.encloses(rect)}
  require("48-unit cover target "+str(button.name),minf(rect.size.x,rect.size.y)*dp_per_unit>=47.99 and safe.encloses(rect))
 print("TARGETS ",JSON.stringify(hit_rects))
 for kind:String in ["coal","slate","metal"]:g.inventory.collect("hud-cover-"+kind,kind)
 h.field_status(g.inventory.carried,g.build_hint(g.Progress.AXES))
 h.reflow()
 require("narrow cover shows additional stocks",h.overflow.visible)
 await tap(d.pack_button.get_global_rect().get_center())
 require("overflow opens all exact mineral amounts",d.tab=="Pack" and d.subtitle.text.contains("10 coal") and d.subtitle.text.contains("10 slate") and d.subtitle.text.contains("10 metal ore"))
 await tap(d.close.get_global_rect().get_center())
 var kept:int=g.player_hp
 var at:Vector3=g.actor.global_position
 var q=g.graphics.ultra
 await tap(h.quality.get_global_rect().get_center())
 require("quality touch toggles",q!=g.graphics.ultra)
 require("no HP loss or walking during UI taps",g.player_hp==kept and g.actor.global_position.distance_to(at)<.12)
 print("RESULT ",JSON.stringify(results))
 await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,g)
 g.queue_free()
 for i in 5:await process_frame
 quit(1 if false in results.values() else 0)
