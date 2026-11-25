import hashlib,json,sys
from pathlib import Path
from PIL import Image
from scipy.ndimage import label,find_objects
import numpy as np
old,new=map(Path,sys.argv[1:3]); a,b=map(lambda p:json.loads(p.read_bytes()),(old,new))
assert a.pop('per_log_pose_godot')!=b.pop('per_log_pose_godot') and a==b
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(old.parent/'paint-inlay.png')==h(new.parent/'paint-inlay.png')=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
im=Image.open(sys.argv[3]).convert('RGB');assert im.size==(1280,720)
p=Path('stocked-near-row-stage-1280x720.jpg');im.save(p,quality=96,optimize=True,subsampling=0);assert p.stat().st_size<140000
c=np.array(im,dtype=float)[216:263,551:640];mask=(c[:,:,0]-c[:,:,2]>29)&(c[:,:,0]>95)
l,n=label(mask); sw=[]
for i,((y,x)) in enumerate(find_objects(l),1):
 count=int((l==i).sum())
 if count>8:sw.append([x.start+551,y.start+216,x.stop+551,y.stop+216,count])
assert any(row[:4]==[608,239,621,253] for row in sw) and any(row[:4]==[621,244,633,258] for row in sw)
print(json.dumps(dict(nonpose_fields_identical=True,full_frame=[1280,720],threshold_components_bbox_and_area=sw,threshold_heuristic_includes_cream_border_not_segmentation=True),indent=2))
