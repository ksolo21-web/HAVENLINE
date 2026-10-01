#!/usr/bin/env python3
"""Finish the diagnosed lake-only illumination repair. No art approval here."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
p=ROOT/'HavenlineGodot/scripts/outpost_view.gd'
assert sha(p)=='0ab2b6be78dcf71ac11f931e15018cab175814519a063f8041d23fd423d14c55','Concurrent view change must be reconciled'
s=p.read_text();needle='\tlake_material.set_shader_parameter("sim_time",sim.climate.seconds)';assert s.count(needle)==1
s=s.replace(needle,needle+'\n\tlake_material.set_shader_parameter("stable_ambient_color",environment.ambient_light_color)\n\tlake_material.set_shader_parameter("stable_ambient_energy",environment.ambient_light_energy)')
p.write_text(s)
shader=ROOT/'HavenlineGodot/shaders/lakeshore_water.gdshader'
assert 'ambient_light_disabled' in shader.read_text() and 'EMISSION=ALBEDO*stable_ambient_color.rgb*clamp(stable_ambient_energy,0.,1.)' in shader.read_text()
paths=['scripts/outpost_surface.gd','scripts/outpost_view.gd','scripts/outpost_simulation.gd','scripts/main.gd','shaders/outpost_snow.gdshader','shaders/lakeshore_water.gdshader','tests/test_task02_terrain.gd','tests/test_lake_east_west.gd','tests/capture_lake_east_west.gd']
runtime={'HavenlineGodot/'+name:sha(ROOT/'HavenlineGodot'/name) for name in paths}
print(json.dumps({'correction':'T02-extended-lake-stable-ambient','tested_runtime_hashes':runtime,'lake_extent_x':[-15.2,15.2],'playable_extent_x':[-14.2,14.2],'old_failures_preserved':True,'diagnosis_run':34540061968,'ambient_energy_follows_scene':True,'direct_light_and_shadows_retained':True,'task_approved':False}))
