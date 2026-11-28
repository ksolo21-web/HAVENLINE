extends RefCounted
## Cast cowl and powder-coated cabinet around original D01 rollers, gearboxes,
## bolted collars and feet. The visible shelves carry the same physical queue.
var station
var kit
var surfaces:Dictionary={}

func _paint(color:String,metal:float,rough:float) -> StandardMaterial3D:
	var m:=StandardMaterial3D.new()
	m.albedo_color=Color(color)
	m.metallic=metal
	m.roughness=rough
	m.cull_mode=BaseMaterial3D.CULL_DISABLED
	return m

func _quad(st:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,d:Vector3,inside:Vector3) -> void:
	var normal:Vector3=(b-a).cross(c-a).normalized()
	if normal.is_zero_approx():return
	if ((a+b+c+d)*.25-inside).dot(normal)<0:normal=-normal
	var vertices:=[a,c,b,a,d,c] if (b-a).cross(c-a).dot(normal)>0 else [a,b,c,a,c,d]
	for p:Vector3 in vertices:
		st.set_normal(normal)
		st.add_vertex(p)

# Each ring is (along the receiver, sole height, top height, half-width).
# Chamfers on both lips of each panel catch the frozen camp's low sunlight.
func _panel(material:String,across:float,rings:Array,edge:float=.04) -> void:
	var st:SurfaceTool=surfaces[material]
	var prev:=PackedVector3Array()
	var previous_center:=Vector3.ZERO
	for r:Vector4 in rings:
		var bevel:=minf(edge,minf((r.z-r.y)*.42,r.w*.42))
		var profile:=[Vector2(-r.w+bevel,r.y),Vector2(-r.w,r.y+bevel),Vector2(-r.w,r.z-bevel),Vector2(-r.w+bevel,r.z),
			Vector2(r.w-bevel,r.z),Vector2(r.w,r.z-bevel),Vector2(r.w,r.y+bevel),Vector2(r.w-bevel,r.y)]
		var ring:=PackedVector3Array()
		for xy:Vector2 in profile:ring.append(station.point(r.x,xy.y,across+xy.x))
		var center:Vector3=station.point(r.x,(r.y+r.z)*.5,across)
		if prev.is_empty() or r==rings.back():
			# The caps are convex bevelled octagons.
			var inside:Vector3=center+station.flow*(.05 if prev.is_empty() else -.05)
			for i in 8:_quad(st,center,ring[i],ring[(i+1)%8],center,inside)
		if not prev.is_empty():
			for i in 8:
				var j:=(i+1)%8
				_quad(st,prev[i],prev[j],ring[j],ring[i],previous_center.lerp(center,.5))
		prev=ring
		previous_center=center

func _beam(material:String,start:float,finish:float,across:float,half_width:float,bottom:float,top:float) -> void:
	var r:=minf(.042,(finish-start)*.09)
	var small:=maxf(.022,half_width-r)
	_panel(material,across,[Vector4(start,bottom+r,top-r,small),Vector4(start+r,bottom,top,half_width),
		Vector4(finish-r,bottom,top,half_width),Vector4(finish,bottom+r,top-r,small)])

func _feed_and_ramp() -> void:
	for side:float in [-1.,1.]:
		var fork:float=side*station.INLET_SEPARATION
		kit.fitted.receiver_span(station.point(0,.89,fork),station.point(.56,1.33,fork),1.00,1.00)
		kit.fitted.receiver_span(station.point(.56,1.33,fork),station.point(1.10,1.33,fork),1.00,1.00)
		var cap:Vector3=station.point(.29,.84,side*1.06)
		kit.component("VentedDrive",cap,Vector3.BACK*side,Vector3(1.96,2.22,1.38))
		kit.component("Socket",station.point(.02,.89,fork),station.flow,Vector3(1.78,.92,.72))
	# One descending bed accepts both powered heads. Its two shoulders
	# taper into the lower cabinet without another frame at the merge.
	kit.fitted.receiver_span(station.point(1.10,1.33),station.point(2.40,.66),2.28,2.28)
	_panel("orange",0.,[Vector4(.01,.72,.94,.052),Vector4(.49,.86,1.37,.055),Vector4(.96,1.02,1.39,.055),
		Vector4(1.12,1.09,1.35,.048),Vector4(1.32,1.17,1.22,.016)],.025)
	for side:float in [-1.,1.]:
		var center:=side*1.154
		_panel("orange",center,[Vector4(-.02,.62,.93,.046),Vector4(.05,.48,1.01,.075),
			Vector4(.44,.44,1.37,.084),Vector4(.57,.48,1.43,.086),Vector4(1.01,.54,1.43,.086),
			Vector4(1.14,.55,1.39,.084),Vector4(2.28,.16,.80,.082),Vector4(2.42,.18,.74,.068),
			Vector4(2.48,.25,.72,.038)],.038)
		_panel("edge",center,[Vector4(.03,.944,.979,.060),Vector4(.49,1.35,1.389,.072),
			Vector4(.59,1.392,1.43,.075),Vector4(1.01,1.392,1.43,.075),Vector4(1.15,1.345,1.383,.070),
			Vector4(2.30,.756,.792,.065),Vector4(2.43,.700,.737,.05)],.015)
		kit.component("VentedDrive",station.point(.89,.77,side*1.02),station.flow,Vector3(1.45,1.80,1.4))
	# A bolted seam marks the real transition from the twin heads.
	kit.component("Coupler",station.point(1.12,1.33),station.flow,Vector3(4.48,1.5,.83))
	kit.component("Arrows",station.point(1.76,.99),station.flow,Vector3(4.62,1.90,1.9))

func _cabinet() -> void:
	# Continuous blue plinth, lowered bright steel landing and drip tray.
	_panel("blue",0.,[Vector4(.03,.15,.63,.84),Vector4(.16,.09,.65,1.01),Vector4(1.46,.09,.67,1.115),
		Vector4(2.22,.09,.58,1.12),Vector4(2.42,.09,.60,1.18),Vector4(4.82,.09,.60,1.18),
		Vector4(4.93,.16,.56,1.10)],.068)
	_panel("steel",0.,[Vector4(2.35,.59,.656,.98),Vector4(2.42,.57,.66,1.168),
		Vector4(4.82,.57,.66,1.168),Vector4(4.91,.60,.653,1.08)],.026)
	for rib in 14:
		var x:=2.51+.166*rib
		_beam("rib",x-.026,x+.026,0.,1.074,.654,.667)
	for s:float in [-1.,1.]:
		_beam("blue_dark",2.49,4.78,s*1.174,.038,.21,.43)
		_beam("steel",2.45,4.85,s*1.155,.046,.662,.746)
		_beam("orange",2.46,4.74,s*1.155,.052,.493,.566)
		# Side-panel vent and zinc bumper bolts stay outside the food paths.
		kit.component("VentedDrive",station.point(3.1,.46,s*1.094),Vector3.BACK*s,Vector3(2.17,.91,.69))
	for along:float in [.26,2.15,4.59]:
		kit.component("Trestle",station.point(along,.006),station.flow,Vector3(4.06,.65,1.70))
	kit.component("Pickup",station.point(4.84,.66),station.flow,Vector3(4.52,.90,1.25))
	kit.component("Arrows",station.point(2.53,.70),station.flow,Vector3(4.45,1.55,1.55))

func mount(receiver,art) -> void:
	station=receiver
	kit=art
	var finish:={"orange":_paint("f78020",.11,.40),"edge":_paint("ffae35",.12,.4),"blue":_paint("2568a8",.22,.36),
		"blue_dark":_paint("26465d",.24,.40),"steel":_paint("9caec0",.36,.46),"rib":_paint("c8d7db",.29,.45)}
	for kind:String in finish:
		var builder:=SurfaceTool.new()
		builder.begin(Mesh.PRIMITIVE_TRIANGLES)
		surfaces[kind]=builder
	_feed_and_ramp()
	_cabinet()
	for kind:String in surfaces:
		var rendered:=MeshInstance3D.new()
		rendered.name="ReceivingMachine"+kind.capitalize()
		rendered.mesh=surfaces[kind].commit()
		rendered.material_override=finish[kind]
		art.add_child(rendered)
