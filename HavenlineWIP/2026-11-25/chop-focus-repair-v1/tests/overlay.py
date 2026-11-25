"""Create the optional test seam in an isolated exact opening clone only."""
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
def once(x,y):
 global s
 assert s.count(x)==1,x
 s=s.replace(x,y)
once('const Ledger = preload("res://opening_ledger.gd")','const ChopInputFixture = preload("res://chop_input_router.gd")\nvar detached_test_chop_input: ChopInputFixture\nconst Ledger = preload("res://opening_ledger.gd")')
once('func _input(event: InputEvent) -> void:\n','func _input(event: InputEvent) -> void:\n\tif detached_test_chop_input != null and detached_test_chop_input.release_only(event):\n\t\treturn\n')
once('\t\trequest_tree_contact()\n\t\treturn\n\tif event is InputEventKey','\t\tif detached_test_chop_input != null:\n\t\t\tdetached_test_chop_input.capture_press(event)\n\t\telse:\n\t\t\trequest_tree_contact()\n\t\treturn\n\tif event is InputEventKey')
once('\t\tif touches_tree_button(event.position):\n\t\t\tif event.device != InputEvent.DEVICE_ID_EMULATION:\n\t\t\t\trequest_tree_contact()','\t\tif touches_tree_button(event.position):\n\t\t\tif detached_test_chop_input != null:\n\t\t\t\tdetached_test_chop_input.capture_press(event)\n\t\t\telif event.device != InputEvent.DEVICE_ID_EMULATION:\n\t\t\t\trequest_tree_contact()')
once('\t\tif event.pressed and touches_tree_button(event.position):\n\t\t\tif event.device != InputEvent.DEVICE_ID_EMULATION:\n\t\t\t\trequest_tree_contact()','\t\tif event.pressed and touches_tree_button(event.position):\n\t\t\tif detached_test_chop_input != null:\n\t\t\t\tdetached_test_chop_input.capture_press(event, touch_id)\n\t\t\telif event.device != InputEvent.DEVICE_ID_EMULATION:\n\t\t\t\trequest_tree_contact()')
if "--focus" in sys.argv:
 once("func _input(event: InputEvent) -> void:", """func _notification(what: int) -> void:
	if detached_test_chop_input == null:
		return
	match what:
		NOTIFICATION_APPLICATION_FOCUS_IN:
			detached_test_chop_input.notify_focus(true, true)
		NOTIFICATION_APPLICATION_FOCUS_OUT:
			detached_test_chop_input.notify_focus(true, false)
		NOTIFICATION_WM_WINDOW_FOCUS_IN:
			detached_test_chop_input.notify_focus(false, true)
		NOTIFICATION_WM_WINDOW_FOCUS_OUT:
			detached_test_chop_input.notify_focus(false, false)

func _input(event: InputEvent) -> void:""")
p.write_text(s)
