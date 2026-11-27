extends "res://tests/qa_paid_conveyors.gd"

func run()->void:
 for arg:String in OS.get_cmdline_user_args():
  if arg.begins_with("--l1-disposable-profile="):profile_path=arg.trim_prefix("--l1-disposable-profile=")
 field=load("res://field_opening.tscn").instantiate()
 root.add_child(field)
 park(Vector3(1.15,0,.9))
 var journal:Dictionary=field.inventory.settlement
 var counter=field.counter
 if "--retry" in OS.get_cmdline_user_args():
  check("load failed counter sale as unpaid",journal.served==1 and journal.counter_stock>=1 and not field.persist_blocked)
  check("original queued second meal sold once and last orders clear",await until(func():return journal.served==7,3500) and journal.cooked==7 and journal.counter_stock==0)
 else:
  check("entered real pending FIFO exchange",await until(func():return counter.belt_serving and counter.sale_order==2 and counter.sale_elapsed+1./60.>=counter.FOOD_TO_BOARD and not counter.sale_committed,3500))
  var bytes:=FileAccess.get_file_as_bytes(profile_path.path_join(Store.PRIMARY))
  var sale_before:int=journal.served
  lock_save()
  await ticks(5)
  check("rejected sale cannot add cash or debit the durable counter item",field.persist_blocked and FileAccess.get_file_as_bytes(profile_path.path_join(Store.PRIMARY))==bytes and field.inventory.settlement.served==sale_before and field.inventory.settlement.counter_stock>=1)
  unlock_save()
 print("CONVEYOR_QA ",JSON.stringify({"phase":"sale_retry" if "--retry" in OS.get_cmdline_user_args() else "sale_lock","checks":results,"receipts":[snapshot_values()]}))
 field.set_physics_process(false)
 await Session.drain_field_audio(self,field)
 field.queue_free()
 await process_frame
 quit(1 if false in results.values() else 0)
