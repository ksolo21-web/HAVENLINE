extends RefCounted
## A paid twin-inlet receiver. Length runs from the two power heads toward
## the public stock table. Its two roof-height feeds merge on the open slope.
const WIDTH := 2.48
const LENGTH := 4.93
const INLET_SEPARATION := .59
const ROAST := preload("res://field_art.gd").WIDTHS.meal
const CAPACITY := 8
const ROW_PITCH := .61
const STOCK_Y := .66
const PHYSICAL_END := 4.48
var origin := Vector3.ZERO
var flow := Vector3.RIGHT
var shell:Rect2

func point(along:float,height:float,across:float=0.) -> Vector3:
	return origin+flow*along+Vector3.UP*height+Vector3.BACK*across

func along(at:Vector3) -> float:
	return (at-origin).dot(flow)

func inset(at:Vector3) -> bool:
	return along(at)>=.04 and along(at)<=LENGTH+.001 and absf(at.z-origin.z)<=WIDTH*.5+.01

func position_for(world,direction:Vector3,offset:float=.40) -> bool:
	flow=direction
	origin=world.counter.global_position+flow*offset+Vector3.BACK*2.42
	var a:=point(0.,0.,-WIDTH*.5)
	var b:=point(LENGTH,0.,WIDTH*.5)
	shell=Rect2(Vector2(a.x,a.z),Vector2.ZERO).expand(Vector2(b.x,b.z)).abs()
	var layout=world.camp_layout
	if not layout.bounds().grow(-.38).encloses(shell):return false
	for id:String in layout.NAMES:
		if not layout.owned(id):continue
		if layout.footprint(id,layout.center(id)).grow(.18).intersects(shell):return false
		if id=="north_counter":continue
		for work:Rect2 in layout.service_areas(id,layout.center(id)):
			if work.grow(.25).intersects(shell):return false
	return true

func inlet(lane:String) -> Vector3:
	return point(0.,.89,INLET_SEPARATION if lane=="meal" else -INLET_SEPARATION)

func slot(index:int) -> Vector3:
	var row:=clampi(index/2,0,3)
	return point(PHYSICAL_END-ROW_PITCH*row,STOCK_Y,.54 if index%2==0 else -.54)

func travel(lane:String) -> PackedVector3Array:
	var fork:=INLET_SEPARATION if lane=="meal" else -INLET_SEPARATION
	return PackedVector3Array([inlet(lane),point(.56,1.33,fork),point(1.10,1.33,fork),
		point(1.39,1.18,fork),point(1.78,.98,lerpf(fork,.54,.48)),
		point(2.18,.77,lerpf(fork,.54,.92)),point(2.40,STOCK_Y,.54),slot(0)])

func freight_position(canonical:Vector3,index:int) -> Vector3:
	var side:float=-1.08 if index%2==1 else 0.
	return canonical+Vector3.BACK*side*smoothstep(1.10,2.40,along(canonical))

func cargo_basis(at:Vector3,tangent:Vector3) -> Basis:
	# Both intake drives deliver end-first. The broad descending guide turns
	# each roast across its column before the four-deep accumulating table.
	var base:=flow.slerp(Vector3.BACK,smoothstep(1.10,2.40,along(at)))
	var incline:=tangent.y/maxf(.001,absf(tangent.dot(flow)))
	var normal:Vector3=(Vector3.UP-flow*incline).normalized()
	var longitudinal:=base.slide(normal).normalized()
	return Basis(longitudinal,normal,longitudinal.cross(normal))

func position_in_queue(rank:int,sold:int) -> int:
	return (rank+sold)%2+2*clampi(rank/2,0,3)

func at_pickup(feet:Vector3) -> bool:
	var u:=along(feet)
	return u>2.35 and u<LENGTH+.83 and absf(feet.z-origin.z)<WIDTH*.5+.76

func build(art) -> void:
	var chassis=preload("res://field_conveyor_receiver_art.gd").new()
	chassis.mount(self,art)
