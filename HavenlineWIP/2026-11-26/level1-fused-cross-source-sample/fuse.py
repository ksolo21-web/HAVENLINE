from pathlib import Path
import hashlib,json,numpy as np
from collections import Counter
R=Path(__file__).resolve().parent;P=R.parent
f=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E=P/'hvn-l1-fence-33036-continuous-run-envelope-v1'
if f(E/'SHA256SUMS')!='05b2c988c45e439ab0d1c4df715ec44bbfdbbc138c1c9614df5d6587d5f5064f':raise ValueError('source mismatch')
refs=P/'hvn-owner-fence-33036-33035'
assert [f(refs/(k+'.png'))[:8] for k in ('33036','33037','33038')]==['067b1e9f','a20a48ef','1be05c57']
ax=.3676125*1.956/2.9409
rad_y=.064;rad_z=.05655;base=.066885;G=.14742
# Mesh is a longitudinal loft of closed cross-sections. There is one surface to
# let rope emboss into rounded timber without a second intersecting limb.
u=np.linspace(0,1,35); yy=np.linspace(-rad_y,rad_y,27)
K=['rail','warm','cream']
rings=[]; colors=[]; evidence=[]
for s in u:
 shape=.044*np.cos(np.pi*s);mid=.001*np.sin(s*2*np.pi)
 top=shape+mid;under=-shape-mid
 def limb(y,c,peak,wide):
  t=(y-c)/wide
  return np.maximum(0.,1-t*t)**1.65*peak
 shell_end=np.clip((rad_y-np.abs(yy))/.012,0,1)
 lifted=limb(yy,top,.0208,.0218)*shell_end
 below=(limb(yy,under,.0140,.0218)*shell_end)
 # A dark warm band at the interrupted crossing lies under the projecting light
 # limb. The fused blend uses a deterministic max geometry, not hidden interpenetration.
 front=base+np.sqrt(np.maximum(0.,1-(yy/rad_y)**2))*rad_z
 add=np.maximum(lifted,below)
 geom=np.r_[[[ax*s,y,d] for y,d in zip(yy,front+add)],
            [[ax*s,y,base-rad_z*np.sqrt(max(0.,1-(y/rad_y)**2))] for y in yy[-2:0:-1]]]
 rings.append(geom); colors.append((lifted,below))
 evidence.append(float(np.interp(top,yy,lifted)-np.interp(under,yy,below)))
tri=[];material=[]
for i in range(len(rings)-1):
 x,y=rings[i:i+2]; a,b=colors[i];c,d=colors[i+1]
 for j in range(len(x)):
  k=(j+1)%len(x)
  ww='rail'
  if j<len(yy)-1:
   h1=(a[j]+a[k]+c[j]+c[k])/4;h2=(b[j]+b[k]+d[j]+d[k])/4
   if max(h1,h2)>.0021:ww='cream' if h1>h2 else 'warm'
  tri.extend([[x[j],x[k],y[k]],[x[j],y[k],y[j]]]);material.extend([ww,ww])
for i,d in [(0,-1),(-1,1)]:
 q=rings[i];c=np.average(q,axis=0)
 for j in range(len(q)):
  k=(j+1)%len(q);tri.append([c,q[j],q[k]] if d==1 else [c,q[k],q[j]]);material.append('rail')
T=np.array(tri)
volume=np.einsum('ji,ji->j',T[:,0],np.cross(T[:,1],T[:,2])).sum()
if volume<0:T=T[:,::-1]
a=Counter();z=Counter()
for x in np.round(T,9):
 for m,n in zip(x,np.roll(x,-1,axis=0)):
  m,n=tuple(m),tuple(n);k=tuple(sorted((m,n)))
  a[k]+=1;z[k]+=1 if m==k[0] else -1
assert all(v==2 and z[k]==0 for k,v in a.items())
area=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)
assert np.min(area)>1e-8
# Exact stock projection; do not infer readability from number or zoomed raster.
camera=np.array([7.,11.,11.]);camera/=np.linalg.norm(camera)
dx=np.cross([0,1,0],camera);dx/=np.linalg.norm(dx);dy=np.cross(camera,dx)
Q=np.array([dx,dy]);scale=720/13
def project(A):return A@Q.T*scale
st=np.array([[ax*t,.044*np.cos(np.pi*t),base+.0208+rad_z] for t in u]);ut=st.copy();ut[:,1]*=-1;ut[:,2]-=.0068
pix=project(T.reshape(-1,3))
# In-memory pixel-center visible-face counts under exact normal camera geometry;
# no screenshot, lighting or anti-aliasing. Two offsets catch single-pixel dependence.
pts=project(T)
dep=T@camera
def face_samples(off):
 mins=np.floor(pts.reshape(-1,2).min(0));maxs=np.ceil(pts.reshape(-1,2).max(0))
 a,b,c=pts[:,0],pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]
 det=b[:,0]*c[:,1]-b[:,1]*c[:,0];use=abs(det)>1e-12
 det=np.where(use,det,1); counts=Counter()
 for xx in np.arange(mins[0],maxs[0])+off:
  for yy2 in np.arange(mins[1],maxs[1])+off:
   d=np.array([xx,yy2])-a
   s=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det
   t=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det
   ok=use&(s>=0)&(t>=0)&(s+t<=1)
   if ok.any():
    z=np.where(ok,dep[:,0]+s*(dep[:,1]-dep[:,0])+t*(dep[:,2]-dep[:,0]),-1e6)
    counts[material[int(np.argmax(z))]]+=1
 return dict(counts)
print(json.dumps(dict(source='one detached fused exterior geometry on owner-sized rounded rail, no rear mirror/program',
 triangles=len(T),closed_single_directed_surface=True,rear_limb_material_count=0,
 front_peak_depth_m=float(T[:,:,2].max()),minimum_positive_guard_mm=(G-T[:,:,2].max())*1000,
 stock_projected_box_px=np.ptp(pix,axis=0).tolist(),
 stock_opposed_center_distance_px_samples=np.linalg.norm(project(st)-project(ut),axis=1).tolist(),
 wood_and_original_rope_pigment_only=True, stock_visible_material_pixel_samples=[face_samples(q) for q in (.125,.375,.625,.875)], estimated_tile_cost_for_8_knots_each_of_two_bands=16*len(T),
 emboss_center_relief_cream_vs_lower_mm=evidence[len(u)//2]*1000,
 full_owner_bulk_principal_yzm=[.128,.1131],
 paid_height_mount_or_true_camera_readability_status='HOLD not native, not seated, LOD unknown'),indent=2))
W=['# Detached fused relief only, not ready for game.','mtllib FusedRails.mtl','s 1']; i=1; last=''
for f,k in zip(T,material):
 if last!=k:W.append('usemtl '+k);last=k
 for v in f:W.append('v '+' '.join(f'{x:.9f}' for x in v))
 W.append(f'f {i} {i+1} {i+2}');i+=3
(R/'FusedRails_SourceOnly.obj').write_text('\n'.join(W)+'\n')
# Same exact previously viewed owner-family rope shades; wood stays plain.
(R/'FusedRails.mtl').write_text('newmtl rail\nKd .69 .34 .15\nPr .85\nnewmtl warm\nKd .86 .65 .38\nPr .87\nnewmtl cream\nKd .98 .87 .63\nPr .87\n')
