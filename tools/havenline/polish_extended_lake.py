#!/usr/bin/env python3
"""Repair observed extended-lake defects; preserve the failed first render record.
Short water triangles replace the giant fan; this is a measured topology change,
not a lower resolution or a material-score workaround. No character GLB changes.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={
'HavenlineGodot/scripts/outpost_surface.gd':'75c92cccf39d1446d6f9cbf6262aaf92b4400ce4018226fdce307794ebf4850e',
'HavenlineGodot/scripts/main.gd':'c176a5d1e10abd3c5f0db591e8b617af98eb65e88f64d35b2ded228d48c84332',
'HavenlineGodot/tests/test_task02_terrain.gd':'1b891ac7cafd03f4d257e72a94136702ab97cb0a499d9fae98f6ea52e3c3b0fd'}
for n,h in before.items():assert sha(ROOT/n)==h,'Concurrent change: '+n
p=ROOT/'HavenlineGodot/scripts/outpost_surface.gd';text=p.read_text();text=text[:text.index('static func water_mesh()')]+'''static func water_mesh() -> ArrayMesh:
	if _water_mesh!=null: return _water_mesh
	# Short, regular triangles prevent vertex fog/light interpolation from exposing
	# the old giant triangle fan when the lake is extended across the entire map.
	# One opaque surface and one draw submission; no transparent plane overlays.
	var radius := LAKE_HALF.y+0.20
	var straight_half := LAKE_HALF.x-LAKE_HALF.y
	var xs := PackedFloat32Array()
	for i in range(25): xs.append(-straight_half-radius*cos(PI*.5*float(i)/24.0))
	for i in range(1,61): xs.append(-straight_half+2.0*straight_half*float(i)/60.0)
	for i in range(1,25): xs.append(straight_half+radius*sin(PI*.5*float(i)/24.0))
	var vertices := PackedVector3Array();var normals := PackedVector3Array()
	var uv := PackedVector2Array();var tangents := PackedFloat32Array()
	var indices := PackedInt32Array();var rows := 13
	for x in xs:
		var cap_x := maxf(absf(x)-straight_half,0.0)
		var half_depth := sqrt(maxf(radius*radius-cap_x*cap_x,0.0))
		for j in range(rows):
			var p := LAKE_CENTER+Vector2(x,lerpf(-half_depth,half_depth,float(j)/12.0))
			vertices.append(Vector3(p.x,WATER_Y,p.y));normals.append(Vector3.UP)
			uv.append(p*.1);tangents.append_array(PackedFloat32Array([1.,0.,0.,1.]))
	for x in range(xs.size()-1):
		for z in range(rows-1):
			var a := x*rows+z;var b := (x+1)*rows+z
			for triangle in [[a,b,a+1],[b,b+1,a+1]]:
				var area: Vector3=(vertices[triangle[1]]-vertices[triangle[0]]).cross(vertices[triangle[2]]-vertices[triangle[0]])
				if area.length_squared()>.0000000001:
					for index in triangle: indices.append(index)
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals
	arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_TANGENT]=tangents;arrays[Mesh.ARRAY_INDEX]=indices
	_water_mesh=ArrayMesh.new();_water_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return _water_mesh
''';p.write_text(text)
p=ROOT/'HavenlineGodot/scripts/main.gd';text=p.read_text();needle='\t\tif absf(p.x) < 3.5: continue\n\t\tvar blocked := false';assert text.count(needle)==1
text=text.replace(needle,'\t\tif absf(p.x) < 3.5: continue\n\t\t# The extended lake must not leave shrub/rock tops protruding through water.\n\t\tif Surface.lake_distance(p) < 1.0: continue\n\t\tvar blocked := false');p.write_text(text)
p=ROOT/'HavenlineGodot/tests/test_lake_east_west.gd';text=p.read_text();old='check("Water triangles unchanged at 192",game.outpost_view.lake.mesh.get_faces().size()/3==192)';assert text.count(old)==1
text=text.replace(old,'''var faces: PackedVector3Array=game.outpost_view.lake.mesh.get_faces()
	var short_edges:=true
	for i in range(0,faces.size(),3):
		for j in range(3):
			short_edges=short_edges and faces[i+j].distance_to(faces[i+(j+1)%3])<.61
	check("Single water surface uses short coherent triangles under 3000",short_edges and faces.size()/3>2000 and faces.size()/3<3000 and game.outpost_view.lake.mesh.get_surface_count()==1)''');p.write_text(text)
p=ROOT/'HavenlineGodot/tests/test_task02_terrain.gd';text=p.read_text();old='check("Water is a bounded custom contour under 256 triangles",water.get_faces().size()/3==192)';assert text.count(old)==1
p.write_text(text.replace(old,'check("Extended water is a bounded custom surface under 3000 triangles",water.get_faces().size()/3>2000 and water.get_faces().size()/3<3000)'))
expected={
'HavenlineGodot/scripts/outpost_surface.gd':'c91b31b23777cc98d4ffbd4819e92ad19823b873eebe7f60bc7df4eac08a37df',
'HavenlineGodot/scripts/main.gd':'8c77fa365c4b1ab56bbf5af4e4542ca864abe26e376282fcad290d30098684f0',
'HavenlineGodot/tests/test_lake_east_west.gd':'01f39a114088ed6b8d24dc4c8dc424ac80f7e81f9ca1d00f24f8780445c1e398',
'HavenlineGodot/tests/test_task02_terrain.gd':'e6da71b5d7e0a9021a955ef4f066bf0ee1ae6287ca9732b0eff6401e85f7c352'}
for n,h in expected.items():assert sha(ROOT/n)==h,'Repair differs from locally tested source: '+n
# The first exact-day comparison failed because unrelated characters kept
# animating. Freeze their current poses ONLY during the six matched diagnostics;
# all normal gameplay captures and game runtime still retain real animation.
p=ROOT/'HavenlineGodot/tests/capture_lake_east_west.gd';text=p.read_text();needle='\t# Match the same view under recorded clear/night/weather states.';assert text.count(needle)==1
text=text.replace(needle,'''\t# Hold unrelated actor poses for the controlled lighting comparison only.
	var held_animations := 0
	for animation in game.world.find_children("*","AnimationPlayer",true,false):
		animation.pause();held_animations+=1
'''+needle)
needle='\t\trecords[-1]["hour"]=game.sim.climate.hour()';assert text.count(needle)==1
text=text.replace(needle,'\t\trecords[-1]["held_unrelated_animation_players"]=held_animations\n'+needle);p.write_text(text)
expected[str(p.relative_to(ROOT))]=sha(p)
for name in ['HavenlineGodot/scripts/outpost_view.gd','HavenlineGodot/scripts/outpost_simulation.gd','HavenlineGodot/shaders/outpost_snow.gdshader','HavenlineGodot/shaders/lakeshore_water.gdshader']:
 expected[name]=sha(ROOT/name)
print(json.dumps({'correction':'T02-east-west-lake-seam-repair','tested_runtime_hashes':expected,'lake_extent_x':[-15.2,15.2],'playable_extent_x':[-14.2,14.2],'water_triangle_budget':3000,'old_fan_interpolation_repaired':True,'unrelated_poses_held_only_in_lighting_diagnostics':True,'first_failed_run_preserved':34536420376,'task_approved':False}))
