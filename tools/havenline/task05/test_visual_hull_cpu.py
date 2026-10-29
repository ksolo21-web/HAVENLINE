#!/usr/bin/env python3
"""Synthetic-only test: no original or derived owner images leave local runtime."""
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
import trimesh
from visual_hull_cpu import reconstruct

def test_synthetic_hull():
    with tempfile.TemporaryDirectory(prefix="t05_synthetic_visual_hull_") as work:
        root=Path(work)
        for view,width in (("front",330),("side",190),("rear",375)):
            im=Image.new("RGB",(512,512),"black")
            d=ImageDraw.Draw(im)
            d.rounded_rectangle((256-width//2,185,256+width//2,400),
                                radius=30,fill=(111,134,165))
            d.rectangle((245,135,280,185),fill=(156,163,171))
            im.save(root/(view+".png"))
        path=root/"output"
        receipt=reconstruct({v:root/(v+".png") for v in ("front","side","rear")},
                            path,64)
        mesh=trimesh.load(path/"T05_source_silhouette_visual_hull_UNAPPROVED.glb",
                          force="mesh")
        assert receipt["status"].startswith("CPU_VISUAL_HULL")
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.faces)==receipt["triangles"] and len(mesh.faces)>500
        assert mesh.bounds[:,1].max()>0
        assert not receipt["texture_reconstructed"]
        print(json.dumps({"synthetic_image_to_mesh_cpu":"PASS",
                          "triangles":len(mesh.faces),
                          "watertight":mesh.is_watertight},indent=2))
if __name__ == "__main__":
    test_synthetic_hull()
