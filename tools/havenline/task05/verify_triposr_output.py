#!/usr/bin/env python3
"""Audit genuine TripoSR output. This never passes the T05 art/release critic."""
import argparse, hashlib, json
from pathlib import Path
import trimesh

def verify(candidate, input_receipt, destination):
 p=Path(candidate); raw=p.read_bytes()
 receipt=json.loads(Path(input_receipt).read_text())
 scene=trimesh.load(p,force="scene")
 models=[m for m in scene.geometry.values() if isinstance(m,trimesh.Trimesh)]
 triangles=sum(len(m.faces) for m in models)
 assert models and 500<=triangles<=2500000, "Invalid neural mesh output"
 assert all(m.is_winding_consistent for m in models), "Bad mesh winding"
 result={
  "status":"NEURAL_IMAGE_TO_3D_MESH_TECHNICAL_PASS_NOT_ART_APPROVAL",
  "model":"MIT-licensed TripoSR, single-image reconstruction, CPU",
  "original_reference_sha256":receipt["source_sha256"],
  "reference_image_name":receipt["source_name"],
  "reference_kind":receipt["input_kind"],
  "mesh_count":len(models),"triangle_count":triangles,
  "generated_glb_sha256":hashlib.sha256(raw).hexdigest(),
  "multi_view_reconstruction_verified":False,
  "source_fidelity_critic_passed":False,"owner_approved":False,
  "shipping_asset_modified":False,
  "physical_android_performance_passed":False
 }
 out=Path(destination);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result,indent=2))
 return result
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--candidate",required=True)
 a.add_argument("--input-receipt",required=True)
 a.add_argument("--output",required=True)
 args=a.parse_args()
 verify(args.candidate,args.input_receipt,args.output)
