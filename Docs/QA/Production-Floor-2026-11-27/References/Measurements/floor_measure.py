"""Compare occupied ground and walking widths of the same paid camp at two revisions."""
import json, math, heapq, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
from PIL import Image, ImageDraw
root=Path(__file__).resolve().parent
result=root.parent
grid=.075
half_rail=.244
def assess(rev, mode):
 raw=json.loads((root/f'layout-{rev}-{mode}.json').read_text());r=raw['player_radius'];box=raw['bounds'];x0,z0,w,h=box
 xs=np.arange(x0+grid/2,x0+w,grid); zs=np.arange(z0+grid/2,z0+h,grid); X,Z=np.meshgrid(xs,zs)
 field=np.c_[X.ravel(),Z.ravel()]; sh=X.shape
 bounds=np.minimum.reduce([X-x0,x0+w-X,Z-z0,z0+h-Z]); distance=bounds.copy()
 building_mask=np.zeros(sh,bool)
 for k,(x,z,dx,dz) in raw['footprints'].items():
  if k=='center_hearth':ds=np.hypot(X-x-dx/2,Z-z-dz/2)-dx/2
  else:ds=np.hypot(np.maximum.reduce([x-X,X-x-dx,np.zeros(sh)]),np.maximum.reduce([z-Z,Z-z-dz,np.zeros(sh)]))
  building_mask|=ds<.001; distance=np.minimum(distance,ds)
 bare=distance.copy()
 railmask=np.zeros(sh,bool);buried={};span={};low={}
 for lane,pts in raw['routes'].items():
  if len(pts)<2: continue
  cloud=[];under=0.;total=0.;pts=np.asarray(pts,float)
  for a,b in zip(pts,pts[1:]):
   length=float(np.linalg.norm(b-a));count=max(1,math.ceil(length/.04))
   for t in (np.arange(count)+.5)/count:
    v=(1-t)*a+t*b
    if v[1]<0:under+=length/count
    if .04<=v[1]<=1.72:cloud.append(v[[0,2]])
   total+=length
  low[lane]=round(min(pts[:,1]),3);buried[lane]=round(under,3);span[lane]=round(total,3)
  if cloud:
   ds=cKDTree(np.array(cloud)).query(field)[0].reshape(sh)-half_rail;railmask|=ds<0;distance=np.minimum(distance,ds)
 free=(distance>=r)
 def to_rc(x,z):return (int(np.argmin(np.abs(zs-z))),int(np.argmin(np.abs(xs-x))))
 south=raw['gates']['gate-south'];east=raw['gates']['gate-east']
 start=to_rc(south[0],south[2]-1.15);labels,_=ndimage.label(free,np.ones((3,3)));main=labels[start]
 assert main!=0,('South approach blocked',rev,mode)
 reached=(labels==main);cap=np.full(sh,-1.);cap[start]=distance[start];q=[(-cap[start],*start)]
 while q:
  neg,i,j=heapq.heappop(q);score=-neg
  if score+1e-5<cap[i,j]:continue
  for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
   u,v=i+di,j+dj
   if 0<=u<sh[0] and 0<=v<sh[1]:
    limit=min(score,distance[u,v])
    if limit>=.02 and limit>cap[u,v]+.001:cap[u,v]=limit;heapq.heappush(q,(-limit,u,v))
 points={**raw['aprons'],'east':[east[0]-1.10,0,east[2]]}
 widths={}
 for k,(x,y,z) in points.items():
  area=np.hypot(X-x,Z-z)<(.20 if k=='east' else .65)
  widths[k]=round(float(2*cap[area].max()),2) if np.any(area) and cap[area].max()>0 else None
 def metric(mask):return round(np.sum(mask)*grid*grid,2)
 stat={'dimensions_m':[w,round(h,2)],'camp_area_m2':round(w*h,2),'hero_diameter_m':round(2*r,3),'source':rev,'ownership':mode,'routes':len(raw['routes']),'lowest_deck_m':low,'length_by_route_m':span,'below_floor_m':buried,'total_cargo_distance_m':round(sum(span.values()),1),'subfloor_distance_m':round(sum(buried.values()),1),'outdoor_walkable_without_rails_m2':metric(bare>=r),'connected_walkable_floor_m2':metric(reached),'reachable_floor_with_two_actor_diameters_of_free_width_m2':metric(reached&(distance>=2*r)),'broadest_accessible_route_diameter_to_approach_m':widths}
 if "activation_rows" in raw:
  trigger={}
  for key,rows in raw["activation_rows"].items():
   mask=np.zeros(sh,bool)
   for zz,x1,x2 in rows:
    iz,ix1=to_rc(x1,zz);_,ix2=to_rc(x2,zz);mask[iz,ix1:ix2+1]=True
   reachable=mask&reached
   trigger[key]={"reachable_zone_m2":metric(reachable),"widest_passage_m":round(float(2*cap[reachable].max()),2) if np.any(reachable) else 0}
  stat["ordinary_zone"] =trigger
 img=np.zeros((*sh,3),np.uint8);img[:]=(209,198,179);img[~free]=(176,158,134);img[building_mask]=(68,73,76);img[railmask]=(203,105,41);img[reached]=(242,222,180);img[reached&(distance>=2*r)]=(237,242,229)
 img=Image.fromarray(img).resize((sh[1]*3,sh[0]*3),Image.Resampling.NEAREST);draw=ImageDraw.Draw(img)
 for k,(x,y,z) in points.items():
  zz,xx=to_rc(x,z);draw.ellipse((xx*3-3,zz*3-3,xx*3+3,zz*3+3),fill='#054a64');draw.text((xx*3+3,zz*3+3),k,fill='#163b49',stroke_width=1,stroke_fill='#fff7dc')
 img.save(root/f'floor-{rev}-{mode}.png')
 return stat
if __name__=='__main__':
 for rev in sys.argv[1:]:
  j={mode:assess(rev,mode) for mode in ('serial','expanded')}
  (result/f'{rev}-aisle-measurements.json').write_text(json.dumps(j,indent=2)+'\n');print(rev,j['expanded'])
