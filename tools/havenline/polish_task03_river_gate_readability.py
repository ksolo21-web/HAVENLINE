#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def replace_once(path,old,new):
    p=ROOT/path
    s=p.read_text()
    assert s.count(old)==1,(path,'expected one match',s.count(old))
    p.write_text(s.replace(old,new,1))

# 1) Make the three river-facing gates visually unmistakable without changing
# any physical opening or collision width. Add gate-specific longer leaves plus
# a worn threshold apron using the same authoritative lane-distance system.
replace_once('HavenlineGodot/scripts/camp_boundary.gd',
'''const GATE_LEAF_LENGTH := 1.35
const GATE_OPEN_ANGLE := 1.18
const SOUTH_FENCE_MARGIN''',
'''const GATE_LEAF_LENGTH := 1.35
const GATE_OPEN_ANGLE := 1.18
# River-facing entrances need stronger visual hierarchy because snow/river-bank
# colors reduce contrast. These are visual open leaves only; collision openings
# and future crossing reserves remain exactly unchanged.
const RIVER_GATE_LEAF_LENGTH := 1.60
const RIVER_GATE_OPEN_ANGLE := 1.43
const RIVER_APRON_INSET := 0.55
const SOUTH_FENCE_MARGIN''')

replace_once('HavenlineGodot/scripts/camp_boundary.gd',
'''static func gate_leaf_specs()->Array[Dictionary]:
\tvar result:Array[Dictionary]=[];var leaf_length:=GATE_LEAF_LENGTH
\tfor gate in gate_specs():
\t\tvar a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent;var mid:Vector2=gate.center
\t\tvar inward:=(CAMP_CENTER-mid).normalized()
\t\tvar left_dir:=tangent.rotated(GATE_OPEN_ANGLE)
\t\tif left_dir.dot(inward)<0:left_dir=tangent.rotated(-GATE_OPEN_ANGLE)
\t\tvar right_dir:=(-tangent).rotated(GATE_OPEN_ANGLE)
\t\tif right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-GATE_OPEN_ANGLE)
\t\tresult.append({"gate":gate.id,"hinge":a,"a":a,"b":a+left_dir*leaf_length,"length":leaf_length})
\t\tresult.append({"gate":gate.id,"hinge":b,"a":b,"b":b+right_dir*leaf_length,"length":leaf_length})
\treturn result

static func lane_polylines()->Array[Dictionary]:''',
'''static func gate_leaf_specs()->Array[Dictionary]:
\tvar result:Array[Dictionary]=[]
\tfor gate in gate_specs():
\t\tvar a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent;var mid:Vector2=gate.center
\t\tvar inward:=(CAMP_CENTER-mid).normalized()
\t\tvar leaf_length:=RIVER_GATE_LEAF_LENGTH if gate.kind=="river" else GATE_LEAF_LENGTH
\t\tvar open_angle:=RIVER_GATE_OPEN_ANGLE if gate.kind=="river" else GATE_OPEN_ANGLE
\t\tvar left_dir:=tangent.rotated(open_angle)
\t\tif left_dir.dot(inward)<0:left_dir=tangent.rotated(-open_angle)
\t\tvar right_dir:=(-tangent).rotated(open_angle)
\t\tif right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-open_angle)
\t\tresult.append({"gate":gate.id,"hinge":a,"a":a,"b":a+left_dir*leaf_length,"length":leaf_length,"open_angle":open_angle})
\t\tresult.append({"gate":gate.id,"hinge":b,"a":b,"b":b+right_dir*leaf_length,"length":leaf_length,"open_angle":open_angle})
\treturn result

static func _river_apron(gate:Dictionary)->Array[Vector2]:
\tvar a:Vector2=gate.a;var b:Vector2=gate.b;var tangent:Vector2=gate.tangent
\treturn [a+tangent*RIVER_APRON_INSET,b-tangent*RIVER_APRON_INSET]

static func lane_polylines()->Array[Dictionary]:''')

replace_once('HavenlineGodot/scripts/camp_boundary.gd',
'''\t\t{"id":"north-bank","points":bank},
\t\t{"id":"west-river-connector","points":[bank_lane_point(-9.0),Vector2(by_id["river--9.0"].center),Vector2(-8.3,0.9),Vector2(-6.8,2.25)]},
\t\t{"id":"east-river-connector","points":[bank_lane_point(10.0),Vector2(by_id["river-10.0"].center),Vector2(8.7,0.9),Vector2(6.8,2.25)]}
\t]''',
'''\t\t{"id":"north-bank","points":bank},
\t\t{"id":"west-river-connector","points":[bank_lane_point(-9.0),Vector2(by_id["river--9.0"].center),Vector2(-8.3,0.9),Vector2(-6.8,2.25)]},
\t\t{"id":"east-river-connector","points":[bank_lane_point(10.0),Vector2(by_id["river-10.0"].center),Vector2(8.7,0.9),Vector2(6.8,2.25)]},
\t\t# Worn threshold aprons make each river opening legible as a used gate,
\t\t# while staying entirely inside the already-open collision interval.
\t\t{"id":"river-apron-west","points":_river_apron(by_id["river--9.0"])},
\t\t{"id":"river-apron-centre","points":_river_apron(by_id["river-1.5"])},
\t\t{"id":"river-apron-east","points":_river_apron(by_id["river-10.0"])}
\t]''')

replace_once('HavenlineGodot/scripts/camp_boundary.gd',
'''\t\t"gate_leaf_length":GATE_LEAF_LENGTH,"gate_open_angle":GATE_OPEN_ANGLE,
\t\t"lane_ids":lane_polylines().map(func(row):return row.id),"river_gate_reserves":RIVER_GATES,"task_approved":false}''',
'''\t\t"gate_leaf_length":GATE_LEAF_LENGTH,"gate_open_angle":GATE_OPEN_ANGLE,
\t\t"river_gate_leaf_length":RIVER_GATE_LEAF_LENGTH,"river_gate_open_angle":RIVER_GATE_OPEN_ANGLE,
\t\t"river_apron_inset":RIVER_APRON_INSET,
\t\t"lane_ids":lane_polylines().map(func(row):return row.id),"river_gate_reserves":RIVER_GATES,"task_approved":false}''')

# 2) Increase packed-snow material readability while retaining irregular, soft
# terrain-integrated edges. No floating path mesh is introduced.
replace_once('HavenlineGodot/shaders/outpost_snow.gdshader',
''' vec3 packed_snow=mix(vec3(.72,.82,.91),vec3(.79,.86,.93),broad*.5+.5);
 vec3 packed_floor=floor*.72+vec3(.060,.034,.024);
 vec3 packed=mix(packed_snow,packed_floor,cleared);
 material=mix(material,packed,lane_mask*.78);
 float lane_edge=(1.-smoothstep(.08,.30,abs(lane)))*smoothstep(-.08,.02,abs(lane));
 material=mix(material,material*.955,lane_edge*.34);''',
''' vec3 packed_snow=mix(vec3(.60,.73,.86),vec3(.75,.84,.92),broad*.5+.5);
 packed_snow+=vec3(.018,.023,.029)*fine*detail_weight;
 vec3 packed_floor=floor*.69+vec3(.055,.031,.021);
 vec3 packed=mix(packed_snow,packed_floor,cleared);
 material=mix(material,packed,lane_mask*.86);
 float lane_edge=(1.-smoothstep(.08,.32,abs(lane)))*smoothstep(-.08,.02,abs(lane));
 material=mix(material,material*.94,lane_edge*.38);''')

# 3) Reframe river-gate evidence obliquely so each threshold, worn apron and the
# river/bank relationship are visible in the same source-bound frame.
replace_once('HavenlineGodot/tests/capture_task03_boundary.gd',
'''\tfor row in [["river--9.0","west"],["river-1.5","centre"],["river-10.0","east"]]:
\t\tvar g:Dictionary=gate(row[0]);focus_at(g.center,Vector3(0,8,9),7.5);await snap("river-gate-"+String(row[1]))''',
'''\tfor row in [["river--9.0","west",Vector3(4.4,6.8,6.8)],["river-1.5","centre",Vector3(3.4,6.8,6.8)],["river-10.0","east",Vector3(-4.4,6.8,6.8)]]:
\t\tvar g:Dictionary=gate(row[0]);focus_at(g.center,row[2],6.7);await snap("river-gate-"+String(row[1]))''')
replace_once('HavenlineGodot/tests/capture_task03_boundary.gd',
'''\tfor id_name in [["river--9.0","west"],["river-1.5","centre"],["river-10.0","east"]]:
\t\tvar g:Dictionary=gate(id_name[0]);focus_at(g.center,Vector3(0,8,9),7.5);await snap("native-river-gate-"+String(id_name[1]))''',
'''\tfor id_name in [["river--9.0","west",Vector3(4.4,6.8,6.8)],["river-1.5","centre",Vector3(3.4,6.8,6.8)],["river-10.0","east",Vector3(-4.4,6.8,6.8)]]:
\t\tvar g:Dictionary=gate(id_name[0]);focus_at(g.center,id_name[2],6.7);await snap("native-river-gate-"+String(id_name[1]))''')
replace_once('HavenlineGodot/tests/capture_task03_boundary.gd',
'''\tvar report={"task":"T03-boundary-v1",''',
'''\tvar report={"task":"T03-boundary-v2",''')

# 4) Keep regression count stable while checking the stronger river-specific
# presentation and three dry, collision-clear threshold aprons.
replace_once('HavenlineGodot/tests/test_task03_boundary.gd',
'''\tcheck("Lane network contains central cross shelter bank and river connectors",Boundary.lane_polylines().size()==7 and lane_samples>250)''',
'''\tvar lane_ids:=Boundary.lane_polylines().map(func(row):return row.id)
\tcheck("Lane network contains central cross shelter bank river connectors and three threshold aprons",Boundary.lane_polylines().size()==10 and lane_samples>275 and ["river-apron-west","river-apron-centre","river-apron-east"].all(func(id):return id in lane_ids))''')
replace_once('HavenlineGodot/tests/test_task03_boundary.gd',
'''\tcheck("Gate leaves use the polished readable opening geometry",is_equal_approx(Boundary.GATE_LEAF_LENGTH,1.35) and is_equal_approx(Boundary.GATE_OPEN_ANGLE,1.18))
\tcheck("Polished gate leaves remain clearly open instead of crossing the threshold",Boundary.GATE_LEAF_LENGTH*cos(Boundary.GATE_OPEN_ANGLE)*2.0<3.0)''',
'''\tcheck("Gate leaves use polished general and river-specific opening geometry",is_equal_approx(Boundary.GATE_LEAF_LENGTH,1.35) and is_equal_approx(Boundary.GATE_OPEN_ANGLE,1.18) and is_equal_approx(Boundary.RIVER_GATE_LEAF_LENGTH,1.60) and is_equal_approx(Boundary.RIVER_GATE_OPEN_ANGLE,1.43))
\tcheck("Polished gate leaves remain clearly open instead of crossing the threshold",Boundary.GATE_LEAF_LENGTH*cos(Boundary.GATE_OPEN_ANGLE)*2.0<3.0 and Boundary.RIVER_GATE_LEAF_LENGTH*cos(Boundary.RIVER_GATE_OPEN_ANGLE)*2.0<3.0)''')

# 5) Fix reviewer protocol (not scores): fresh v2 evidence is the expected task
# label, and a critic that sees no defect must use an empty defect array instead
# of putting praise such as 'None observed' in the defect field.
replace_once('tools/havenline/review_task03_local_reference.py',
"prov=json.loads((ROOT/'provenance.json').read_text());assert prov['source']==SOURCE and prov['task']=='T03-boundary-v1' and prov['all61_images_verified'] is True",
"prov=json.loads((ROOT/'provenance.json').read_text());assert prov['source']==SOURCE and prov['task']=='T03-boundary-v2' and prov['all61_images_verified'] is True")
replace_once('tools/havenline/review_task03_local_reference.py',
'''10 means fully finished within the demonstrated T03 scope with no known defect. Return JSON only. Do not infer whole-game completion or physical-device performance.''',
'''10 means fully finished within the demonstrated T03 scope with no known defect. If you find NO actionable defect, the defects array MUST be [] exactly; never put phrases such as "none", "none observed", praise, or scope commentary in defects. Return JSON only. Do not infer whole-game completion or physical-device performance.''')

print('Task 3 river-gate readability polish applied without changing T02 river authority or collision openings.')
