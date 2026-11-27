extends SceneTree
func _initialize():
 var save_ = load("res://field_save.gd").new()
 var book = load("res://field_inventory.gd").new()
 var rules = load("res://field_progression.gd")
 book.configure(rules.offers())
 for id:String in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","watchtower","orbit_upgrade","camp_cooker","saw_bench","quarry_drill"]:
  if "--partial" in OS.get_cmdline_user_args() and id in ["saw_bench","quarry_drill"]:continue
  for kind:String in book.remaining(id):
   var due:int=book.remaining(id)[kind]
   for i in due: assert(book.collect(id+kind+str(i),kind))
   assert(book.payment(id,kind,false,due))
 for kind:String in ["wood","stone","meat"]:
  for i in (3 if kind!="meat" else 6):
   assert(book.collect("baseline-stock-"+kind+str(i),kind))
   assert(book.deposit(kind))
 assert(book.collect("baseline-roast","meat")); book.carried.meat-=1; book.settlement.cooked=1
 assert(book.snapshot().version==7 and save_.configure(OS.get_cmdline_user_args()))
 var status:int=save_.commit(book);print("BASELINE ",status);quit(status)
