#!/usr/bin/env python3
"""Patch only Task 3 scene integration. Fail on any unexpected concurrent edit."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'HavenlineGodot/scripts/main.gd'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(p)=='c72a4dfbb1d1b4ecf5bdf60be0e915f40bc7f7e4f9b22f3bc791246069db2e22' or sha(p)=='bd484e532af5660dceeb5a0999be857ce0e844f0', 'main.gd changed; reconcile before Task 3 patch'
s=p.read_text()
s=s.replace('const ENVIRONMENT_REVISION := "0.4.5-environment-candidate"','const ENVIRONMENT_REVISION := "0.5.0-task03-boundary"',1)
needle='const ReferenceForest = preload("res://scripts/reference_forest.gd")\nvar reference_forest_evidence: Dictionary = {}'
assert s.count(needle)==1
s=s.replace(needle,needle+'\nconst CampBoundaryView = preload("res://scripts/camp_boundary_view.gd")\nvar camp_boundary_view: Node3D',1)
needle='\toutpost_view.configure(environment, sun, furnace, heat_light, sim)\n\toutpost_audio = OutpostAudio.new()'
assert s.count(needle)==1
s=s.replace(needle,'\toutpost_view.configure(environment, sun, furnace, heat_light, sim)\n\tcamp_boundary_view = CampBoundaryView.new()\n\tworld.add_child(camp_boundary_view)\n\tcamp_boundary_view.configure(self)\n\toutpost_audio = OutpostAudio.new()',1)
old='''\tfor x in [-6.6, 6.6]:
\t\tvar shelter := model("world/shelter", world, xyz(Vector2(x, -4.8)))
\t\tshelter.rotation.y = -0.12 if x < 0 else 0.12'''
new='''\tfor key in ["leftTent","rightTent"]:
\t\tvar shelter_point := Simulation.point(sim.contract.world[key])
\t\tvar shelter := model("world/shelter", world, xyz(shelter_point))
\t\tshelter.rotation.y = -0.12 if shelter_point.x < 0 else 0.12'''
assert s.count(old)==1
s=s.replace(old,new,1)
needle='\t\treport["outpost"] = outpost_view.evidence(sim)'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n\t\treport["task03_boundary"] = camp_boundary_view.descriptor',1)
p.write_text(s)
print({'main_sha256':sha(p),'task03_scene_integration':True})
