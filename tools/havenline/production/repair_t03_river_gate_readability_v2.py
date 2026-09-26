#!/usr/bin/env python3
"""Scoped T03 repair for the independently confirmed river-gate defects.

Allowed changes: T03 gate visual geometry, T03 integrated packed-lane material,
T03 capture viewpoints and T03 acceptance assertions. T02 river authority,
collision opening widths, T01 assets and T04+ runtime remain untouched.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def patch(rel, changes):
    p=ROOT/rel; s=p.read_text()
    for old,new in changes:
        if s.count(old)!=1: raise SystemExit(f'{rel}: expected exactly one match for {old[:80]!r}, got {s.count(old)}')
        s=s.replace(old,new,1)
    p.write_text(s)
    print(rel)

patch('HavenlineGodot/scripts/camp_boundary.gd',[
('const RIVER_GATE_LEAF_LENGTH := 1.60\nconst RIVER_GATE_OPEN_ANGLE := 1.43\nconst RIVER_APRON_INSET := 0.55',
'''const RIVER_GATE_LEAF_LENGTH := 1.85
const RIVER_GATE_OPEN_ANGLE := 1.48
# River approaches need a broader worn threshold than ordinary camp lanes so
# the three future-crossing entrances read as intentional gates in snow.
const RIVER_LANE_HALF := 1.55
const RIVER_APRON_INSET := 0.55'''),
('static func _river_apron(gate:Dictionary)->Array[Vector2]:\n\tvar a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent\n\treturn [a+tangent*RIVER_APRON_INSET,b-tangent*RIVER_APRON_INSET]',
'''static func _river_apron(gate:Dictionary)->Array[Vector2]:
	# Cross the gate perpendicular to the fence, from the dry bank lane through
	# the threshold and visibly into camp. The old apron ran ALONG the opening,
	# which did not visually communicate an approach/entrance.
	var center:Vector2=gate.center
	var inward:=(CAMP_CENTER-center).normalized()
	var outside:=bank_lane_point(float(gate.reserve_x))
	return [outside,center,center+inward*2.20]'''),
('{"id":"river-apron-west","points":_river_apron(by_id["river--9.0"])},\n\t\t{"id":"river-apron-centre","points":_river_apron(by_id["river-1.5"])},\n\t\t{"id":"river-apron-east","points":_river_apron(by_id["river-10.0"])}',
'{"id":"river-apron-west","points":_river_apron(by_id["river--9.0"]),"half_width":RIVER_LANE_HALF},\n\t\t{"id":"river-apron-centre","points":_river_apron(by_id["river-1.5"]),"half_width":RIVER_LANE_HALF},\n\t\t{"id":"river-apron-east","points":_river_apron(by_id["river-10.0"]),"half_width":RIVER_LANE_HALF}'),
('for lane in lane_polylines():\n\t\tvar points:Array=lane.points\n\t\tfor i in range(points.size()-1):result=minf(result,_distance_to_segment(p,points[i],points[i+1])-LANE_HALF)',
'''for lane in lane_polylines():
		var points:Array=lane.points
		var half_width:=float(lane.get("half_width",LANE_HALF))
		for i in range(points.size()-1):result=minf(result,_distance_to_segment(p,points[i],points[i+1])-half_width)'''),
('\t\t"river_gate_leaf_length":RIVER_GATE_LEAF_LENGTH,"river_gate_open_angle":RIVER_GATE_OPEN_ANGLE,\n\t\t"river_apron_inset":RIVER_APRON_INSET,',
'\t\t"river_gate_leaf_length":RIVER_GATE_LEAF_LENGTH,"river_gate_open_angle":RIVER_GATE_OPEN_ANGLE,\n\t\t"river_lane_half_width":RIVER_LANE_HALF,"river_apron_inset":RIVER_APRON_INSET,')
])

patch('HavenlineGodot/shaders/outpost_snow.gdshader',[
('vec3 packed_snow=mix(vec3(.60,.73,.86),vec3(.75,.84,.92),broad*.5+.5);\n packed_snow+=vec3(.018,.023,.029)*fine*detail_weight;\n vec3 packed_floor=floor*.69+vec3(.055,.031,.021);\n vec3 packed=mix(packed_snow,packed_floor,cleared);\n material=mix(material,packed,lane_mask*.86);\n float lane_edge=(1.-smoothstep(.08,.32,abs(lane)))*smoothstep(-.08,.02,abs(lane));\n material=mix(material,material*.94,lane_edge*.38);',
'''vec3 packed_snow=mix(vec3(.43,.60,.77),vec3(.66,.78,.88),broad*.5+.5);
 packed_snow+=vec3(.026,.032,.038)*fine*detail_weight;
 vec3 packed_floor=floor*.64+vec3(.050,.028,.019);
 vec3 packed=mix(packed_snow,packed_floor,cleared);
 // Stronger value separation plus irregular compressed patches make the route
 // readable in snow while remaining the same terrain surface (never a path plane).
 float wear=clamp(.86+material_noise(p*2.35)*.14,0.,1.);
 material=mix(material,packed,lane_mask*.94*wear);
 float lane_edge=(1.-smoothstep(.07,.34,abs(lane)))*smoothstep(-.09,.015,abs(lane));
 material=mix(material,material*.91,lane_edge*.46);''')
])

patch('HavenlineGodot/tests/capture_task03_boundary.gd',[
('for row in [["river--9.0","west",Vector3(4.4,6.8,6.8)],["river-1.5","centre",Vector3(3.4,6.8,6.8)],["river-10.0","east",Vector3(-4.4,6.8,6.8)]]:\n\t\tvar g:Dictionary=gate(row[0]);focus_at(g.center,row[2],6.7);await snap("river-gate-"+String(row[1]))',
'''for row in [["river--9.0","west",Vector3(3.6,5.4,6.2)],["river-1.5","centre",Vector3(2.8,5.4,6.2)],["river-10.0","east",Vector3(-3.6,5.4,6.2)]]:
		var g:Dictionary=gate(row[0]);focus_at(g.center,row[2],5.7);await snap("river-gate-"+String(row[1]))'''),
('for id_name in [["river--9.0","west",Vector3(4.4,6.8,6.8)],["river-1.5","centre",Vector3(3.4,6.8,6.8)],["river-10.0","east",Vector3(-4.4,6.8,6.8)]]:\n\t\tvar g:Dictionary=gate(id_name[0]);focus_at(g.center,id_name[2],6.7);await snap("native-river-gate-"+String(id_name[1]))',
'''for id_name in [["river--9.0","west",Vector3(3.6,5.4,6.2)],["river-1.5","centre",Vector3(2.8,5.4,6.2)],["river-10.0","east",Vector3(-3.6,5.4,6.2)]]:
		var g:Dictionary=gate(id_name[0]);focus_at(g.center,id_name[2],5.7);await snap("native-river-gate-"+String(id_name[1]))''')
])

patch('HavenlineGodot/tests/test_task03_boundary.gd',[
('is_equal_approx(Boundary.RIVER_GATE_LEAF_LENGTH,1.60) and is_equal_approx(Boundary.RIVER_GATE_OPEN_ANGLE,1.43)',
'is_equal_approx(Boundary.RIVER_GATE_LEAF_LENGTH,1.85) and is_equal_approx(Boundary.RIVER_GATE_OPEN_ANGLE,1.48) and is_equal_approx(Boundary.RIVER_LANE_HALF,1.55)')
])

# Hard scope guards.
river=(ROOT/'HavenlineGodot/scripts/river_geometry.gd').read_text()
assert 'const LAYOUT_VERSION := "river_v1_mapspan"' in river
assert 'Vector2(-31.0,-8.6)' in river and 'Vector2(31.0,-7.3)' in river
print('T03 scoped river-gate readability repair prepared; T02 river authority unchanged.')
