"""Run with Blender --background --python. Coordinates are Godot X, up Y, Z."""
import array
import json
import os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

root = Path(os.environ["STOCK_TRIANGLES"])
def tree(name):
    floats = array.array("f")
    floats.frombytes((root / (name + ".f32")).read_bytes())
    points = [tuple(floats[i:i + 3]) for i in range(0,len(floats),3)]
    faces = [(i,i+1,i+2) for i in range(0,len(points),3)]
    return points, BVHTree.FromPolygons(points,faces,all_triangles=True)

def contact(lower,upper):
    vertices,upper_tree = upper
    gaps = []
    width = [(min(p[i] for p in vertices), max(p[i] for p in vertices)) for i in (0,2)]
    possible = 0
    for j in range(33):
        for k in range(33):
            x = width[0][0] + (width[0][1]-width[0][0])*(j+.5)/33
            z = width[1][0] + (width[1][1]-width[1][0])*(k+.5)/33
            bottom = upper_tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))[0]
            if bottom is None:
                continue
            possible += 1
            top = lower[1].ray_cast(Vector((x,bottom.y+.03,z)),Vector((0,-1,0)))[0]
            if top is not None:
                gaps.append(bottom.y - top.y)
    return {"rays_over_packet":possible,"rays_over_support":len(gaps),
            "triangle_surface_crossings":len(upper_tree.overlap(lower[1])),
            "minimum_gap_mm":round(min(gaps)*1000,2) if gaps else None,
            "within_15_mm_of_contact":sum(abs(g)<=.015 for g in gaps),
            "within_30_mm_of_contact":sum(abs(g)<=.03 for g in gaps)}

rack = tree("rack")
data={}
for kind in ("wood","stone","meat","coal","slate","metal"):
    bottom = tree(kind+"0")
    data[kind] = {"rack_to_first":contact(rack,bottom),"first_to_second":contact(bottom,tree(kind+"1"))}
Path(os.environ["STOCK_RESULT"]).write_text(json.dumps(data,indent=2)+"\n")
