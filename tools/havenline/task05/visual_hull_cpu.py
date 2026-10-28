#!/usr/bin/env python3
"""T05 CPU-only silhouette visual hull. NOT a neural image-to-3D model.

Free local/GitHub runner proof. Camera angles are approximate, not calibrated.
This mesh is NOT the cooker release mesh, cannot recover recessed/hidden parts.
Source images are supplied locally and must never enter a public CI artifact.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import trimesh
from scipy import ndimage
from skimage.measure import marching_cubes

CAMERAS = {
    "front": {"angle": 36., "upper": .110, "lower": .75, "width": 4.5},
    "side": {"angle": 90., "upper": .125, "lower": .895, "width": 3.4},
    "rear": {"angle": 180., "upper": .125, "lower": .88, "width": 5.2},
}

def detect_mask(path, view):
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(path)
    H, W = image.shape[:2]
    p = CAMERAS[view]
    y0, y1 = int(H*p["upper"]), int(H*p["lower"])
    gray = cv2.cvtColor(image[y0:y1], cv2.COLOR_BGR2GRAY)
    mask = (gray > 22).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7,7),np.uint8))
    labels, total = ndimage.label(mask > 0)
    counts = np.bincount(labels.ravel())
    if len(counts) < 2:
        raise ValueError("No detected subject in "+str(path))
    mask = ndimage.binary_fill_holes(labels == (np.argmax(counts[1:])+1))
    yy, xx = np.where(mask)
    bbox = (max(0,xx.min()-4),max(0,yy.min()-4),
            min(W,xx.max()+5),min(y1-y0,yy.max()+5))
    mask = np.uint8(mask[bbox[1]:bbox[3],bbox[0]:bbox[2]])
    mask = cv2.resize(mask,(512,512),interpolation=cv2.INTER_NEAREST) > 0
    return mask, {"filename":Path(path).name,
                  "source_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                  "original_dimensions":[W,H],
                  "solid_area_fraction":round(float(mask.mean()),4)}

def reconstruct(inputs, dest, resolution=128):
    masks, metadata = {}, {}
    for view in ("front","side","rear"):
        masks[view],metadata[view] = detect_mask(inputs[view],view)
    xs=np.linspace(-2.6,2.6,resolution,dtype=np.float32)
    ys=np.linspace(0,2.8,int(resolution*.73),dtype=np.float32)
    zs=np.linspace(-1.65,1.65,int(resolution*.73),dtype=np.float32)
    X,Y,Z=np.meshgrid(xs,ys,zs,indexing="ij")
    hull=np.ones(X.shape,dtype=bool)
    for view,mask in masks.items():
        p=CAMERAS[view]
        a=np.deg2rad(p["angle"])
        ui=np.rint(255+(X*np.cos(a)+Z*np.sin(a))/p["width"]*512).astype(np.int32)
        vi=np.rint((2.8-Y)/2.8*511).astype(np.int32)
        valid=(ui>=0)&(ui<512)&(vi>=0)&(vi<512)
        pixels=np.zeros(hull.shape,dtype=bool)
        pixels[valid]=mask[vi[valid],ui[valid]]
        hull &= pixels
    if hull.sum() < 1000:
        raise RuntimeError("No consistent volume; camera registration needed")
    arr=ndimage.gaussian_filter(hull.astype(np.float32),.7)
    arr=np.pad(arr,2,mode="constant",constant_values=0)
    step=(xs[1]-xs[0],ys[1]-ys[0],zs[1]-zs[0])
    vertices,faces,_,_=marching_cubes(arr,.48,spacing=step)
    vertices += [xs[0]-2*step[0],ys[0]-2*step[1],zs[0]-2*step[2]]
    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
    if not mesh.is_watertight:
        raise RuntimeError("Carved hull not watertight")
    out=Path(dest)
    out.mkdir(parents=True,exist_ok=True)
    glb=out/"T05_source_silhouette_visual_hull_UNAPPROVED.glb"
    mesh.export(glb)
    for view,mask in masks.items():
        cv2.imwrite(str(out/(view+"_detected_silhouette.png")),mask.astype(np.uint8)*255)
    receipt={
        "status":"CPU_VISUAL_HULL_GEOMETRY_PROOF__NOT_AI_GENERATION__NOT_T05_APPROVED",
        "triangles":len(mesh.faces),"vertices":len(mesh.vertices),
        "watertight":mesh.is_watertight,"source":metadata,
        "camera_angles_assumed":{v:CAMERAS[v]["angle"] for v in inputs},
        "texture_reconstructed":False,"interior_detail_reconstructed":False,
        "public_reference_upload_authorized":False,
        "warning":"This is a low-information silhouette baseline, NOT the high-fidelity cooker."
    }
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--front",required=True)
    parser.add_argument("--side",required=True)
    parser.add_argument("--rear",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--resolution",type=int,default=128)
    a=parser.parse_args()
    print(json.dumps(reconstruct({"front":a.front,"side":a.side,"rear":a.rear},
                                 a.out,a.resolution),indent=2))
