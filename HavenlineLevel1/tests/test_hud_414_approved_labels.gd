extends SceneTree
const Opening = preload("res://opening.tscn")
var n := 0
func _initialize():
	call_deferred("go")
func check(ok: bool, label: String):
	print("CRITIC ", "PASS " if ok else "REJECT ", label)
	if not ok:
		n+=1
func touch(idx:int, at:Vector2, down:bool):
	var e:=InputEventScreenTouch.new()
	e.index=idx
	e.position=at
	e.pressed=down
	return e
func go():
	var sub := SubViewport.new()
	sub.size=Vector2i(1280,720)
	root.add_child(sub)
	var game=Opening.instantiate()
	sub.add_child(game)
	game.set_physics_process(false)
	await process_frame
	var old:=Vector2(game.gate_button.size)
	game._input(touch(1,Vector2(1200,680),true))
	check(game.touch_id==1,"wide outside owner acquired")
	sub.size=Vector2i(414,896)
	await process_frame
	await process_frame
	check(game.touch_id==-1,"resize clears captured owner through actual signal")
	check(game.gate_button.size.x<old.x and game.gate_button.size.x==370.0,"actual signal reflows gate width")
	game.gate_button.show()
	game.tree_button.show()
	var cases := []
	for id in ["gate-south", "gate-east"]:
		for held in [false, true]:
			for is_open in [false, true]:
				cases.append([game.gate_button, game.gate_action_label(id, held, is_open)])
	for strikes in range(4):
		cases.append([game.tree_button, game.tree_action_label(strikes)])
	for pair in cases:
		var b:Button=pair[0]
		b.text=pair[1]
		var f := b.get_theme_font("font")
		var sz := b.get_theme_font_size("font_size")
		var text_width := f.get_string_size(b.text,HORIZONTAL_ALIGNMENT_LEFT,-1,sz).x
		var width := b.size.x-b.get_theme_stylebox("normal").get_minimum_size().x
		check(text_width<=width,"414 action fits phrase=%s need=%.2f content=%.2f clip=%s" % [b.text,text_width,width,b.clip_text])
	var clip_button: Button = game.gate_button
	var gate_font := clip_button.get_theme_font("font")
	var gate_font_size := clip_button.get_theme_font_size("font_size")
	var gate_limit := clip_button.size.x - clip_button.get_theme_stylebox("normal").get_minimum_size().x
	check(gate_font.get_string_size("Exit swing area gate-south [E]", HORIZONTAL_ALIGNMENT_LEFT, -1, gate_font_size).x > gate_limit, "historic long-label negative still discriminates")
	check(game.touches_gate_button(game.gate_button.get_global_rect().get_center()) and not game.touches_tree_button(game.gate_button.get_global_rect().get_center()),"exclusive gate hit after resize")
	game.tree_button.hide()
	game._input(touch(2,game.tree_button.get_global_rect().get_center(),true))
	check(game.touch_id==2,"hidden tree rect does not intercept")
	print("CRITIC failures ",n)
	quit(7 if n else 0)
