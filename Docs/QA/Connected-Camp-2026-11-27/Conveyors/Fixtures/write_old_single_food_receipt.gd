extends SceneTree
func _initialize()->void:
 var book=load("res://field_inventory.gd").new()
 var p=load("res://field_progression.gd")
 var store=load("res://field_save.gd").new()
 book.configure(p.offers())
 for id:String in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","watchtower","orbit_upgrade","camp_cooker","saw_bench","quarry_drill","meal_conveyor"]:
  for kind:String in book.remaining(id):
   var need:int=book.remaining(id)[kind]
   for i in need:assert(book.collect(id+kind+str(i),kind))
   assert(book.payment(id,kind,false,need))
 assert(book.collect("single-leg-v8-meal","meat"))
 book.carried.meat-=1
 book.settlement.cooked=1
 book.settlement.line_load.meal=1
 book.settlement.line_progress.meal=.42
 assert(book.snapshot().version==8 and store.configure(OS.get_cmdline_user_args()))
 var result:int=store.commit(book)
 print("LEGACY_WRITER ",result)
 quit(result)
