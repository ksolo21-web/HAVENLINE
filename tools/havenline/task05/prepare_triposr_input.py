#!/usr/bin/env python3
"""Preprocess the exact owner T05 image for single-image TripoSR (not an art pass)."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image

HASHES = {
 "32451.jpg":"70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4",
 "32450.jpg":"5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719",
 "32441.png":"0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510"
}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--image",required=True);ap.add_argument("--out",required=True)
 ap.add_argument("--source",choices=["fixture","owner"],required=True)
 a=ap.parse_args()
 path=Path(a.image)
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 if a.source=="owner":
  assert HASHES.get(path.name)==sha, "owner image source hash mismatch"
 original=Image.open(path)
 rgb=np.asarray(original.convert("RGB")).copy()
 if a.source=="owner" and path.name=="32451.jpg":
  rgb[:round(rgb.shape[0]*.112)]=0 # animated smoke not physical mesh
 if a.source=="owner":
  mask=np.max(rgb,axis=2)>27 # original black render background
 elif original.mode in ("RGBA","LA"):
  mask=np.asarray(original.convert("RGBA"))[:,:,3]>32
 else:
  corners=np.array([rgb[0,0],rgb[0,-1],rgb[-1,0],rgb[-1,-1]],float)
  mask=np.linalg.norm(rgb-np.median(corners,axis=0),axis=2)>25
 mask=ndimage.binary_fill_holes(mask)
 yy,xx=np.where(mask)
 assert len(xx)>1000
 l,r,t,b=int(xx.min()),int(xx.max()+1),int(yy.min()),int(yy.max()+1)
 crop=rgb[t:b,l:r].astype(float)
 al=mask[t:b,l:r].astype(float)
 crop=np.uint8(crop*al[:,:,None]+128*(1-al[:,:,None]))
 h,w=crop.shape[:2]; scale=min(440/w,440/h)
 nw,nh=max(1,round(w*scale)),max(1,round(h*scale))
 canvas=Image.new("RGB",(512,512),(128,128,128))
 canvas.paste(Image.fromarray(crop).resize((nw,nh),Image.Resampling.LANCZOS),((512-nw)//2,(512-nh)//2))
 dest=Path(a.out);dest.mkdir(parents=True,exist_ok=True)
 canvas.save(dest/"image.png")
 report={"input_kind":a.source,"source_name":path.name,"source_sha256":sha,
         "crop_xyxy":[l,t,r,b],"single_view_only":True,"critic_passed":False}
 (dest/"input_receipt.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
