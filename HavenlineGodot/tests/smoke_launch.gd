extends SceneTree
const Main = preload("res://scripts/main.gd")
func _initialize():
	call_deferred("run")
func run():
	var game = Main.new()
	game.size = Vector2(1280,720)
	root.add_child(game)
	for i in range(8): await process_frame
	print(JSON.stringify({"smoke_launch":true,"crew":game.actors.size(),"native_internal_size":[game.scene_view.size.x,game.scene_view.size.y]}))
	await game.close_game()
