from pathlib import Path
from PIL import Image
import numpy as np, sys,json
from scipy.ndimage import label,find_objects
def read(p):return np.asarray(Image.open(p).convert('RGB')).astype(float)
def diff(img, ground):
 return np.max(np.abs(img-ground),axis=2)>32
def fmt(rgb):return np.round(rgb,1).tolist()
def robust_bounds(mask):
 # Eliminate a few transient exterior pixels due to moving shadow maps.
 H=mask.sum(axis=1); W=mask.sum(axis=0)
 y=np.flatnonzero(H>=2);x=np.flatnonzero(W>=2)
 return [int(x[0]),int(y[0]),int(x[-1]),int(y[-1])]
def bodymask(body,ground):
 m=diff(body,ground)
 sat=body.max(axis=2)-body.min(axis=2)
 y0,x0=body.shape[:2]; y,x=np.indices((y0,x0))
 m &= ((sat>20)|(body.max(axis=2)<133)) & (abs(x-x0/2)<x0*.45)&(y>y0*.30)
 lab,n=label(m)
 ids=np.argsort(np.bincount(lab.ravel())[1:])[::-1]+1
 return lab==ids[0]
def robust(mask):return int(np.sum(mask))
def sampled(img,ground,cargo):
 b=bodymask(img,ground)
 x0,y0,x1,y1=robust_bounds(b)
 y,x=np.indices(b.shape)
 h=y1-y0+1;wid=x1-x0+1
 coat=b & (y>y0+h*.34)&(y<y0+h*.79)
 # Blue material class; berry purple trouser pixels and gray cuff are excluded.
 r,g,bb=img.transpose(2,0,1)
 blue=coat & (bb>r*1.32)&(bb>g*1.22)&(bb-r>19)
 # Bright orange motif; redness alone includes tan skin, leather and snow reflections.
 orange=coat &(r>112)&(r>g*1.72)&(g>bb*1.62)&(r-bb>81)
 bounds=[x0,y0,x1,y1]
 data={'body_bbox':bounds,'body_width':wid,'body_height':h,'coat_blue_pixels':robust(blue),'coat_blue_median_srgb':fmt(np.median(img[blue],axis=0)) if blue.any() else [],'coat_blue_p75_srgb':fmt(np.percentile(img[blue],75,axis=0)) if blue.any() else [],'orange_count':robust(orange),'orange_fraction_of_parka_roi':round(robust(orange)/max(1,robust(coat)),4)}
 return data
if __name__=='__main__':
 for root in map(Path,sys.argv[1:]):
  res={}
  for bodyfile in sorted(root.glob('*-body.png')):
   id=bodyfile.name[:-9]
   try:r=sampled(read(bodyfile),read(root/(id+'-ground.png')),read(root/(id+'-cargo.png')))
   except (IndexError,FileNotFoundError):continue
   res[id]=r
  (root/'plate-measurements.json').write_text(json.dumps(res,indent=2)+'\n')
  for l in ['empty-1-000','empty-1-045','timber-1-045','six-1-045','six-1-180']:
   print(l,res.get(l))
