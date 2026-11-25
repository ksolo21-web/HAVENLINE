import os
import numpy as np,json
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,binary_erosion
from pathlib import Path
P=Path(__file__).resolve().parent
d=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz')); out=np.load(P/'new-surface.npz')
v=d['rest']; g=(out['v']-d['source_origin'])*d['scale']; source=d['tri'][out['original_face_ids']]; target=out['tri']; U={}
def contain(V,F,orient,origin,dim,limit):
 ix=F[(V[F,2]<limit).all(1)]
 sz=(V[:,orient]-origin)*2000 # raster 0.5mm
 a=Image.new('1',tuple(dim),0);ent=ImageDraw.Draw(a)
 for pp in sz[ix]:ent.polygon([tuple(t) for t in pp],fill=1)
 return np.asarray(a).astype(bool)
for (tag,axis) in [('front',(0,2)),('side',(1,2)),('sole_top',(0,1))]:
 aa=v[np.unique(source)][:,axis];lo=aa.min(0)-.003;hi=aa.max(0)+.003
 dim=np.ceil((hi-lo)*2000).astype(int)+2
 limit=.065 if tag=='sole_top' else .49; L=contain(v,source,axis,lo,dim,limit);R=contain(g,target,axis,lo,dim,limit)
 bL=L&~binary_erosion(L);bR=R&~binary_erosion(R)
 e1=distance_transform_edt(~bR)[bL]*.5;e2=distance_transform_edt(~bL)[bR]*.5
 U[tag]={'IoU':float((L&R).sum()/(L|R).sum()),'bounds_nominal_mm':.5,'boundary_hausdorff_mm_sampled':max(float(e1.max()),float(e2.max())),'source_side_p95_mm':float(np.quantile(e1,.95)),'retopo_side_p95_mm':float(np.quantile(e2,.95))}
(P/'silhouette.json').write_text(json.dumps(U,indent=2));print(U)
