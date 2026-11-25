import hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import label
q=Path('../hvn-l1-storage-reference-scale-v1')
r=Path('../havenline-tree-regrow.IVOMrj/repo/Docs/Production/T05/ReferenceFrames')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(q/"SHA256SUMS")=="a142a105af37cdc3c81d988f4afa2af717870b04108b3fdd74879ff63da9a431"
for z in (q/"SHA256SUMS").read_text().splitlines():
 h,n=z.split(); assert sha(q/n)==h
pins={
 'B008':(r/'B-008.00.png','8544aee9feba9bdb5d3060ec8449bd2ba07f7ad4092c70599979120e3d09c65b',(268,545,562,749),(360,656), (1152,1288)),
 'B010':(r/'B-010.00.png','10e434c1b949d18f76e9a510c8376895e4996413d7f8ae1b2f3df924aa848e8c',(499,746,795,953),(580,846), (1152,1274)),
 '124510-27.5':(q/'b27.5-LOCAL.png','71f9ab0e599c661b7e2a9082e96058781fd82ea6ca1f90e2599698fd71f664b8',(547,826,848,1040),(643,939), (1178,1285))}
assert sha(q/'b27-LOCAL.png')=='4434403f962cbce176cc3a40e5f3053da80c6d130e11ec9f5d00db4cedaa3c5a'
assert sha(q/'b28-LOCAL.png')=='3e983101885a727eb32fcc0d132fcacf8be8c439d2dfefcb267b45326065ee18'
out={}
for label0,(p,h,roi,seed,bind) in pins.items():
 assert sha(p)==h
 a=np.asarray(Image.open(p).convert('RGB'),dtype=float)
 lx,ly,rx,ry=roi;x,y=seed
 bg=np.median(a[y-3:y+4,x-3:x+4].reshape(-1,3),axis=0)
 d=np.linalg.norm(a[ly:ry,lx:rx]-bg,axis=2)
 # Color-distance seed-connected field, no old intensity/head-count thresholds.
 cc=label(d<=31)[0]; tag=cc[y-ly,x-lx];assert tag>0
 yy,xx=np.where(cc==tag)
 WH=np.array([np.ptp(xx)+1,np.ptp(yy)+1]); h0=bind[1]-bind[0]; assert h0>100
 out[label0]={'independent_seed_connected_field_px':WH.tolist(),'manual_hood_to_boot_px':h0,'field_to_avatar_screen_ratios':(WH/h0).tolist(),
  'ratio_with_5px_avatar_height_tolerance':[ (WH/(h0+5)).tolist(),(WH/(h0-5)).tolist() ]}
# Exact game camera projection using three dot products from geometric
# silhouette edges and 66-joint unedited actual captured pose. Uses GLB point
# array only for shape ratio, never back-projects advertisement pixels.
import struct
asset=Path('../hvn-l1-wood-storage-paint-repair-v2/wood_storage_empty.glb')
assert sha(asset)=='3db8ed722b3a41b31003a7a43b85c1b1344fc3e98dcd3c9c94a9f96d34838045'
g=asset.read_bytes(); n=struct.unpack_from('<I',g,12)[0]; D=json.loads(g[20:20+n]); base=memoryview(g)[28+n:]
a=D['accessors'][D['meshes'][0]['primitives'][0]['attributes']['POSITION']]; bv=D['bufferViews'][a['bufferView']]
V=np.frombuffer(base,dtype='<f4',count=a['count']*3,offset=bv['byteOffset']+a.get('byteOffset',0)).reshape(-1,3).astype(float)
right=np.array([11,0,-7],float)/np.sqrt(170); up=np.array([-77,170,-121],float)/np.sqrt(170*291)
plane=np.c_[right,up]
raw=Path(__import__('sys').argv[1])/'funded'/'far.json';assert sha(raw)=='566ffdd64dbd85e36f1ce6d4d58aeefd9509af95bbe0594e30d690c5f379d718'
H=np.vstack([np.array(x['positions'])[np.unique(x['triangles'])] for x in json.loads(raw.read_text())])
B=np.ptp(V@plane,axis=0)*(720/13); hero=np.ptp(H@plane,axis=0)*(720/13)
proposal=V*[4.4,1,4.4]; ppx=np.ptp(proposal@plane,axis=0)*(720/13)
print(json.dumps({'reference_independent_crops':out,'source_flat_projected_plate_px':B.tolist(),'exact_actual_source_far_hero_projected_px':hero.tolist(),'source_ratio_plate_w_h_to_avatar_h':(B/hero[1]).tolist(),
 'detached_xz_only_optical_comparison_ratio_w_h_to_hero_h':(ppx/hero[1]).tolist(),'projected_comparison_bounding_pixels':ppx.tolist()},indent=2,sort_keys=True))
