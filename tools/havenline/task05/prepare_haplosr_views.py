#!/usr/bin/env python3
"""T05 exact three-view sources -> separate source masks and approximate camera poses.

Owner's three original images are authoritative. Camera angles are hypotheses;
no synthesized reference images and no promotion to shipping art.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from PIL import Image
VIEWS={
 "front":{"name":"32451.jpg","sha256":"70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4","azimuth_deg":0.,"elevation_deg":18.,"smoke_clip_y":181,"chimney_x":[625,815],"chimney_keep_y":278},
 "right":{"name":"32450.jpg","sha256":"5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719","azimuth_deg":91.,"elevation_deg":9.,"smoke_clip_y":165,"chimney_x":[705,895],"chimney_keep_y":255},
 "rear":{"name":"32441.png","sha256":"0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510","azimuth_deg":181.,"elevation_deg":9.,"smoke_clip_y":123,"chimney_x":[686,843],"chimney_keep_y":190}
}
def prepare(root,out,resolution=512):
 root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 poses=[];checks=[]
 for side,spec in VIEWS.items():
  path=root/spec["name"];digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest!=spec["sha256"]:raise ValueError(f"Not the owner's exact {side} source")
  rgb=np.asarray(Image.open(path).convert("RGB"))
  h,w=rgb.shape[:2]
  mask=np.max(rgb,axis=2)>30
  mask[:spec["smoke_clip_y"],:]=False
  left,right=spec["chimney_x"]
  mask[:spec["chimney_keep_y"],:left]=False
  mask[:spec["chimney_keep_y"],right:]=False
  lab,count=ndi.label(mask)
  counts=np.bincount(lab.ravel());counts[0]=0
  mask=ndi.binary_fill_holes(ndi.binary_closing(lab==counts.argmax(),iterations=2))
  yy,xx=np.nonzero(mask)
  if len(xx)<1000:raise ValueError(f"No object silhouette in {side}")
  x0,x1=max(0,int(xx.min()-10)),min(w,int(xx.max()+11))
  y0,y1=max(0,int(yy.min()-10)),min(h,int(yy.max()+11))
  fragment=rgb[y0:y1,x0:x1]
  alpha=np.uint8(mask[y0:y1,x0:x1])*255
  hh,ww=fragment.shape[:2]
  sc=resolution*.82/max(hh,ww)
  sz=(max(1,round(ww*sc)),max(1,round(hh*sc)))
  im=Image.fromarray(fragment).resize(sz,Image.Resampling.LANCZOS)
  m=Image.fromarray(alpha,"L").resize(sz,Image.Resampling.NEAREST)
  canvas=Image.new("RGB",(resolution,resolution),(128,128,128))
  mask_out=Image.new("L",(resolution,resolution),0)
  pos=((resolution-sz[0])//2,(resolution-sz[1])//2)
  canvas.paste(im,pos,m);mask_out.paste(m,pos)
  canvas.save(out/f"{side}.png");mask_out.save(out/f"{side}_mask.png")
  poses.append({"image":f"{side}.png","mask":f"{side}_mask.png","azimuth_deg":spec["azimuth_deg"],"elevation_deg":spec["elevation_deg"]})
  checks.append({"side":side,"original":spec["name"],"sha256":digest,
   "crop_xyxy":[x0,y0,x1,y1],"silhouette_fraction":round(float((np.asarray(mask_out)>0).mean()),4)})
 (out/"poses.json").write_text(json.dumps(poses,indent=2)+"\n")
 receipt={"status":"ALL_THREE_AUTHENTIC_IMAGE_MASKS_SOURCE_VERIFIED",
  "camera_poses_calibrated":False,"views_are_illustrations_not_photogrammetry":True,
  "neural_inference_completed":False,"source":checks}
 (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 return receipt
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--source-dir",required=True)
 a.add_argument("--out",required=True);a.add_argument("--resolution",type=int,default=512)
 args=a.parse_args()
 print(json.dumps(prepare(args.source_dir,args.out,args.resolution),indent=2))
