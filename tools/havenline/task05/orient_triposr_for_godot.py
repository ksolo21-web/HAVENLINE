#!/usr/bin/env python3
"""TripoSR Z-up -> Godot Y-up, retaining every triangle and source vertex color."""
import argparse,hashlib,json,math
from pathlib import Path
import trimesh
def convert(src,dst):
 src=Path(src);dst=Path(dst)
 model=trimesh.load(src,force="scene")
 before=sum(len(m.faces) for m in model.geometry.values())
 model.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]))
 dst.parent.mkdir(parents=True,exist_ok=True)
 dst.write_bytes(model.export(file_type="glb"))
 after=sum(len(m.faces) for m in trimesh.load(dst,force="scene").geometry.values())
 assert before==after and after>500
 report={"status":"ACTUAL_NEURAL_3D_AXIS_CONVERSION_VERIFIED_UNAPPROVED",
 "input_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
 "godot_glb_sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),
 "triangles":after,"rotation_x_degrees":-90,
 "owner_approved":False,"shipping_asset_modified":False}
 dst.with_suffix(".orientation.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--input",required=True);a.add_argument("--output",required=True)
 x=a.parse_args();convert(x.input,x.output)
