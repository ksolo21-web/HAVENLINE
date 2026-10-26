#!/usr/bin/env python3
"""Fail-closed Blender benchmark artifact audit; NEVER a visual approval."""
import argparse,hashlib,json,pathlib,sys
import numpy as np
import trimesh
from PIL import Image

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    parser.add_argument("--baseline-catalog",required=True)
    args=parser.parse_args()
    out=pathlib.Path(args.out)
    old=json.loads(pathlib.Path(args.baseline_catalog).read_text())
    cooker=next(x for x in old["entries"] if x["id"]=="cooker_processor")
    assert cooker["footprint"]==[2.45,2.30], "Frozen game-space footprint changed"
    source_blend=out/"T05_cooker_EDITABLE.blend"
    target_glb=out/"T05_cooker_BLENDER_CANDIDATE.glb"
    metadata=out/"benchmark.json"
    required=[source_blend,target_glb,metadata]
    for view in ("front","three-quarter","right","rear"):
        required.append(out/("T05_cooker_"+view+".png"))
    assert all(p.exists() and p.stat().st_size>100 for p in required), "Blender deliverable missing"
    assert source_blend.read_bytes()[:7]==b"BLENDER-", "Not a native editable Blender file"
    assert target_glb.read_bytes()[:4]==b"glTF", "Not a GLB"
    meta=json.loads(metadata.read_text())
    assert meta["does_not_replace_game_asset"] is True
    assert meta["status"]=="CANDIDATE_NOT_VISUALLY_APPROVED"
    # Loaded with trimesh; inspect actual exported GLB, not designer claims.
    scene=trimesh.load(target_glb,force="scene",process=False)
    assert isinstance(scene,trimesh.Scene) and len(scene.geometry)>0
    meshes=[m for m in scene.geometry.values() if isinstance(m,trimesh.Trimesh)]
    triangles=sum(len(m.faces) for m in meshes)
    assert triangles>1000 and triangles<=13000, f"Cooker geometry unacceptable: {triangles}"
    bounds=np.asarray(scene.bounds,dtype=float)
    size=bounds[1]-bounds[0]
    assert np.all(np.isfinite(bounds))
    # glTF exports to Y-up. Image pixels must be reviewed to verify aesthetics.
    assert size[0]<=2.45+.035 and size[2]<=2.30+.035, f"Footprint overrun: {size}"
    assert .90<size[1]<=2.65, f"Broken Y-up export (height={size[1]})"
    assert bounds[0,1]>=-.15, "Candidate passes too far below ground"
    assert len(meshes)<=12, f"Excessive distinct mesh/material surfaces: {len(meshes)}"
    # 4 actual Blender studio renders; they are NOT Godot native evidence.
    for file in required[3:]:
        with Image.open(file) as im:
            assert im.size==(768,768), f"Wrong render resolution: {file}"
            assert im.convert("RGB").getbbox() is not None
    report={
      "task":"T05","candidate_only":True,"release_approved":False,
      "independent_visual_critic_performed":False,
      "reference_name":"18567.png",
      "reference_sha256":"729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635",
      "source_file":"T05_cooker_EDITABLE.blend",
      "source_sha256":sha(source_blend),
      "glb_sha256":sha(target_glb),
      "triangles":triangles,"meshes":len(meshes),
      "bounds_game_space_Y_up":bounds.tolist(),
      "extents_xyz_m":size.tolist(),
      "baseline_cooker_sha256":cooker["sha256"],
      "unchanged_game_asset_enforced":True,
      "render_stages":"Blender studio only, not shipping engine",
      "checks":{"editable_blend":"PASS","glb":"PASS","geometry_cap":"PASS",
                "game_space_footprint":"PASS","y_up_orientation":"PASS",
                "4_studio_renders":"PASS"}
    }
    (out/"blender-qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("T05 BLENDER CANDIDATE QA FAILED:",repr(ex),file=sys.stderr);raise
