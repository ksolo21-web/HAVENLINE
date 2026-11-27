extends Node3D
## Workshop state is presentation only. The settlement ledger owns all goods.
const CENTERS = {"wood":Vector3(-3.43,0,-7.35),"stone":Vector3(7.55,0,-7.00)}
const APRONS = {"wood":Vector3(-2.98,0,-5.88),"stone":Vector3(7.80,0,-5.27)}
const ACCESS_RADIUS := .81
const MACHINES = {
	"wood":preload("res://assets/paid_workshops/saw_station.glb"),
	"stone":preload("res://assets/paid_workshops/quarry_drill_station.glb"),
}
const PRODUCTS = {
	"wood":preload("res://assets/shore_workshops/finished_planks.glb"),
	"stone":preload("res://assets/shore_workshops/dressed_block.glb"),
}
const INPUT = {"wood":Vector3(.92,1.00,-.25),"stone":Vector3(-.98,.26,.57)}
const OUTPUT = {"wood":Vector3(-.32,.19,.53),"stone":Vector3(.63,.20,.77)}
const FOOTPRINT = {"wood":Rect2(-1.16,-.85,2.30,1.69),"stone":Rect2(-1.34,-1.10,2.68,2.20)}
var world:Node3D
var machines := {}
var wheels:Dictionary={}
var trays:Dictionary={}
var balances:Dictionary={"wood":-1,"stone":-1}
var active := {"wood":false,"stone":false}
var guards: Dictionary = {}
const Reach = preload("res://field_reach.gd")
var drill_phase := 0.0
var drill_head:Node3D
var stone_dust:Array[Sprite3D]=[]
var stone_chips:Array[Node3D]=[]
const CONTACT := Vector3(-.70,.21,.15)
const DUST_FAN := [Vector3(-.49,.32,.54),Vector3(.08,.46,.68),Vector3(.49,.26,.39)]
const CHIP_FAN := [Vector3(-.38,0,.52),Vector3(-.05,0,.64),Vector3(.34,0,.53),Vector3(.47,0,.20)]
const HEAD_HOME := Vector3(-.70,1.32,-.14)
var available := false

func setup(host:Node3D) -> void:
	world=host
	name="NorthCampWorkshops"
	for kind:String in CENTERS:
		var rig:Node3D=MACHINES[kind].instantiate()
		rig.name="SawBench" if kind=="wood" else "QuarryDrill"
		add_child(rig)
		machines[kind] = rig
		rig.position=CENTERS[kind]+Vector3.UP*.025
		var head:Node3D=rig.find_child("SawRotor" if kind=="wood" else "WinchDrum",true,false)
		wheels[kind]=head
		if kind=="stone":
			drill_head=preload("res://assets/paid_workshops/quarry_spindle.glb").instantiate()
			rig.add_child(drill_head)
			drill_head.position=HEAD_HOME
			_setup_cuttings(rig)
		var base:=StaticBody3D.new()
		base.name="MachineGuard"
		rig.add_child(base)
		var shape:=CollisionShape3D.new()
		var box:=BoxShape3D.new()
		var rect:Rect2=FOOTPRINT[kind]
		var height:=1.85 if kind=="wood" else 2.88
		box.size=Vector3(rect.size.x,height,rect.size.y)
		shape.position=Vector3(rect.get_center().x,height*.5,rect.get_center().y)
		shape.shape=box
		base.add_child(shape)
		guards[kind] = base
		var stock:=Node3D.new()
		stock.name="Outfeed"
		rig.add_child(stock)
		stock.position=OUTPUT[kind]
		trays[kind]=stock
	refresh_ownership(false)
	sync_outputs()

func _setup_cuttings(rig:Node3D) -> void:
	for i in DUST_FAN.size():
		var dust:=Sprite3D.new()
		dust.texture=preload("res://assets/paid_workshops/quarry_dust.png")
		dust.billboard=BaseMaterial3D.BILLBOARD_ENABLED
		dust.pixel_size=.011
		dust.shaded=false
		dust.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		rig.add_child(dust)
		dust.hide()
		stone_dust.append(dust)
	for i in CHIP_FAN.size():
		var chip:Node3D=preload("res://field_art.gd").make("stone",.105+.013*(i%3))
		rig.add_child(chip)
		chip.hide()
		stone_chips.append(chip)

func _show_cuttings(progress:float) -> void:
	# Stone powder escapes between the two front legs as the cutting head
	# reaches its work. All positions are on the station's own fixed plinth.
	for i in stone_dust.size():
		var dust:=stone_dust[i]
		var t:=clampf((progress-.42-i*.028)/.39,0.,1.)
		dust.visible=t>0. and t<1.
		if dust.visible:
			dust.position=CONTACT.lerp(CONTACT+DUST_FAN[i],1.-(1.-t)*(1.-t))
			dust.scale=Vector3.ONE*lerpf(.24,1.04,t)
			dust.modulate.a=minf(1.,t*7.)*(1.-smoothstep(.47,1.,t))
	for i in stone_chips.size():
		var chip:=stone_chips[i]
		var t:=clampf((progress-.46-i*.012)/.29,0.,1.)
		chip.visible=t>0. and t<1.
		if chip.visible:
			chip.position=CONTACT+CHIP_FAN[i]*t+Vector3.UP*(.42*4.*t*(1.-t))
			chip.rotation=Vector3(t*(3.4+i),i+t*2.7,t)

func refresh_ownership(animate := true) -> void:
	available = false
	for kind: String in machines:
		var owned: bool = world.inventory.is_machine_owned(kind)
		var machine: Node3D = machines[kind]
		var previously_built: bool = guards[kind].collision_layer != 0
		machine.visible = owned
		guards[kind].collision_layer = 1 if owned else 0
		available = available or owned
		if owned and not previously_built and animate:
			reveal(machine)
		if not owned: set_running(kind, false)

static func reveal(machine: Node3D) -> void:
	var size := machine.scale
	machine.scale = size * .12
	var tween := machine.create_tween()
	tween.tween_property(machine,"scale",size,.32).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	# The paid structure breaks through a short vertically moving fan of light.
	# Attach to the floor, preserving the original beam proportions as the mesh rises.
	var stage := machine.get_parent_node_3d()
	for i in 6:
		var angle := TAU * i / 6.
		var beam := Sprite3D.new()
		beam.texture = preload("res://assets/paid_workshops/completion_light.svg")
		beam.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		beam.shaded = false
		beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		beam.pixel_size = .019
		stage.add_child(beam)
		beam.position = machine.position + Vector3(cos(angle)*.74,.69,sin(angle)*.64)
		var lift := beam.create_tween().set_parallel(true)
		lift.tween_property(beam,"position:y",beam.position.y + 1.07,.40).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		lift.tween_property(beam,"modulate:a",0.,.26).set_delay(.14)
		lift.chain().tween_callback(beam.queue_free)

func input_position(kind:String) -> Vector3:
	return machines[kind].to_global(INPUT[kind])

func apron_position(kind:String) -> Vector3:
	var at:Vector3 = machines[kind].global_position + APRONS[kind] - CENTERS[kind]
	return Vector3(at.x,0,at.z)

func output_position(kind:String) -> Vector3:
	return trays[kind].global_position

func at_station(at:Vector3) -> String:
	var camp = world.get("field_env")
	if not available or (camp and not camp.is_inside_camp(at)): return ""
	var p:=Vector2(at.x,at.z)
	for kind:String in APRONS:
		if not world.inventory.is_machine_owned(kind): continue
		var box := _rect(kind,0.)
		if not box.has_point(p) and Reach.distance_to_rect(p,box) <= Reach.NEAR:
			return kind
	return ""

func set_running(kind:String,running:bool) -> void:
	if not active.has(kind): return
	running = running and world.inventory.is_machine_owned(kind)
	if active[kind] == running: return
	active[kind] = running
	if kind == "stone" and not running:
		drill_phase = 0.
		wheels.stone.rotation.x = 0.
		drill_head.position = HEAD_HOME
		_show_cuttings(-1.)

func sync_outputs() -> void:
	if not world or not world.get("inventory"):return
	var settlement:Dictionary=world.inventory.settlement
	for kind:String in CENTERS:
		var count:=preload("res://field_logistics.gd").rack(settlement,kind) if settlement.has("product_store") else int(settlement.get("processed_"+kind,0))
		if balances[kind]==count:continue
		balances[kind]=count
		var stock:Node3D=trays[kind]
		# Four representative lots fit the bin. The HUD keeps exact totals.
		var visible_lots:=mini(count,4)
		for i in maxi(stock.get_child_count(),visible_lots):
			if i>=visible_lots:
				stock.get_child(i).visible=false
			else:
				var item:Node3D
				if i>=stock.get_child_count():
					item=PRODUCTS[kind].instantiate()
					stock.add_child(item)
				else:item=stock.get_child(i)
				item.visible=true
				item.position=Vector3(0,i*.25,0) if kind=="wood" else Vector3(0,(i/2)*.235,(i%2-.5)*.33)

func tick(dt:float) -> void:
	sync_outputs()
	if active.wood:
		wheels.wood.rotate_z(7.4*dt)
	if active.stone:
		drill_phase=fmod(drill_phase+dt,300.)
		wheels.stone.rotate_x(dt*4.8)
		var progress:float=world.inventory.settlement.work_seconds.stone / preload("res://field_settlement.gd").CYCLE_SECONDS.stone
		var plunge:=smoothstep(.10,.58,progress)*(1.-smoothstep(.66,.96,progress))
		drill_head.position = HEAD_HOME + Vector3.DOWN*(.54*plunge)
		drill_head.rotate_y(dt*11.)
		_show_cuttings(progress)

func _rect(kind:String,radius:float) -> Rect2:
	var rect:Rect2=FOOTPRINT[kind]
	var c:Vector3=machines[kind].global_position
	return Rect2(rect.position+Vector2(c.x,c.z),rect.size).grow(radius)

func reserves(at:Vector3) -> bool:
	if not available: return false
	var p:=Vector2(at.x,at.z)
	for kind:String in APRONS:
		if not world.inventory.is_machine_owned(kind): continue
		if _rect(kind,.35).has_point(p) or at.distance_to(apron_position(kind))<=ACCESS_RADIUS:return true
	return false

func constrain_motion(from:Vector3,to:Vector3,radius:float) -> Vector3:
	if not available: return to
	var start:=Vector2(from.x,from.z)
	var end:=Vector2(to.x,to.z)
	var path:=Rect2(start,Vector2.ZERO).expand(end).grow(.01)
	for kind:String in CENTERS:
		if not world.inventory.is_machine_owned(kind): continue
		var box:=_rect(kind,radius)
		if not path.intersects(box):continue
		var steps:=maxi(1,ceili(start.distance_to(end)/.15))
		var delta:=(end-start)/steps
		var point:=start
		if box.has_point(point):
			# Restore an old pose directly into the open aisle in front of the machine.
			point.y = box.end.y+.004
		for i in steps:
			point+=delta
			if not box.has_point(point):continue
			var c:=point-box.get_center()
			var overlap:=box.size*.5-c.abs()
			if overlap.x<overlap.y:point.x=box.end.x+.001 if c.x>=0 else box.position.x-.001
			else:point.y=box.end.y+.001 if c.y>=0 else box.position.y-.001
		end=point
	return Vector3(end.x,to.y,end.y)
