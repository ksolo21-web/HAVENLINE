from pathlib import Path
import numpy as np,hashlib,json,math,sys
from PIL import Image
from collections import Counter
from scipy.interpolate import PchipInterpolator
p=Path(__file__).resolve().parent;r=p.parent
f=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R=r/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1'
assert f(R/'SHA256SUMS')=='45c8b73f0463f8158b1985b58ae0fa8f852799c0d57911de41f2e9e0e8a8c845'
scope=r/'hvn-l1-fence-33036-fused-lashing-v1'
assert f(scope/'SHA256SUMS')=='6f6a3d9355b9f5b487f09112c78c6268e320b122bb0f43e11befe7b37cc7a12a'
ctx={'__file__':str(R/'verify.py')}
exec((R/'verify.py').read_text().split('seams=')[0],ctx)
D,mat=ctx['tr'],np.array(ctx['labels'])
W=ctx['panels'](D,True)['SW0'];A,sgn,anchor,Y0=W
assert sgn==1 and np.allclose(anchor,[-7.372,9.80975])
# Exact rounded source posts and crowned geometry retained. Appearance only
# uses original plain owner-family palette; no private grain copied.
selected=np.isin(mat,['amber_logs','meshy_bold_amber_front','soft_snow'])
pr={'body':A[np.isin(mat,['amber_logs','meshy_bold_amber_front'])],'caps':A[mat=='soft_snow']}
X0,X1=-8.349,-6.408
L=X1-X0;N=81
xs=np.linspace(X0,X1,N);wz=9.8
yfull=np.linspace(-.064,.064,11)
T={};uvs={};texmeta={}
def frame(z,y,d):return [z,y,wz+d]
def aobb(R,bands=True):
 F=[];UV=[]
 for i,(a,b) in enumerate(zip(R,R[1:])):
  for s in range(len(a)):
   t=(s+1)%len(a)
   F += [[a[s],a[t],b[t]],[a[s],b[t],b[s]]]
   if bands:
    u,v=i/(len(R)-1),(i+1)/(len(R)-1)
    dy=lambda j:np.clip(j/(len(yfull)-1),0,1)
    UV += [[[u,dy(s)],[u,dy(t)],[v,dy(t)]],[[u,dy(s)],[v,dy(t)],[v,dy(s)]]]
   else:UV += [[[0,0]]*3]*2
 for m,sig in ((0,0),(-1,1)):
  a=R[m]
  for i in range(len(a)):
   j=(i+1)%len(a)
   F.append([a.mean(0),a[i],a[j]] if sig else [a.mean(0),a[j],a[i]])
   UV.append([[0,0]]*3)
 F=np.array(F);U=np.array(UV)
 s=np.einsum('ij,ij->i',F[:,0],np.cross(F[:,1],F[:,2])).sum()
 return (F,U) if s>0 else (F[:,::-1,:],U[:,::-1,:])
def hold(T):
 count=Counter();direction=Counter()
 for tri in np.round(T,8):
  pts=list(map(tuple,tri))
  for a,b in zip(pts,pts[1:]+pts[:1]):
   o=tuple(sorted((a,b)));count[o]+=1;direction[o]+=1 if a==o[0] else -1
 return all(n==2 and direction[o]==0 for o,n in count.items())
# Lift current visual lower band only as needed throughout exact soil max strip; keep upper delta.
bound=ctx['height']
S=np.linspace(X0,X1,25)
g=np.array([max(bound(np.array([x,wz+z])) for x in (max(X0,s-.042),s,min(X1,s+.042)) for z in (-.14742,0,.14742))+.077 for s in S])
level=np.maximum(g,.429) # neutral stance of the frame adjusted as source proposal, not original host.
ground=PchipInterpolator(S,level)
coef={};probe=[]
for j,b in enumerate([0,.692]):
 geom=[];rear=[]
 for i,x in enumerate(xs):
  u=(x-X0)/L;c=np.cos(8*np.pi*u);y0=float(ground(x))+b
  front= .066885+.05655*np.sqrt(np.maximum(0,1-(yfull/.064)**2))
  influence=np.maximum(np.maximum(0,1-((yfull-.039*c)/.024)**2),.72*np.maximum(0,1-((yfull+.039*c)/.024)**2))
  # Use 9mm of real wood-surface emboss. Fine relief and fibers are in the atlas.
  push=.009*influence*np.clip((.064-np.abs(yfull))/.012,0,1)
  rail=[frame(x,y+y0,z+q) for y,z,q in zip(yfull,front,push)]
  rail.extend(frame(x,y+y0,.066885-.05655*np.sqrt(max(0,1-(y/.064)**2))) for y in yfull[-2:0:-1])
  geom.append(rail)
  # Single level rope course at the back of the true timbers; intersects their backs deliberately.
  th=np.arange(8)*np.pi/4
  z=-.126 +.0015*np.cos(u*16*math.pi)
  rear.append(np.array([frame(x,y0+.010*np.cos(t),z+.009*np.sin(t)) for t in th]))
 T[f'rail_{j}'],uvs[f'rail_{j}']=aobb(np.array(geom))
 T[f'rear_{j}'],uvs[f'rear_{j}']=aobb(np.array(rear),False)
 assert hold(T[f'rail_{j}']) and hold(T[f'rear_{j}'])
 probe.append({'band':j, 'rail_max_exterior_depth_mm':float((T[f'rail_{j}'][:,:,2].max()-wz)*1000),'rear_min_exterior_depth_mm':float((T[f'rear_{j}'][:,:,2].min()-wz)*1000)})
T.update(pr)
# Exact owner tolerance + actual pair intersection check for installed geometry in separate passes.
cuts={}
checks={}
pos=ctx['culled_intersections']
# Source row y or face orientation not inferred by coloring. Preserve one real structural rail per band and rear line.
for j in range(2):
 aa=T[f'rail_{j}'];bb=T[f'rear_{j}'];P=T['body'];caps=T['caps']
 rr=pos(aa,bb,['front']*len(aa),['rear']*len(bb))
 assert not rr
 k=pos(aa,P,['front']*len(aa),['timber']*len(P))
 l=pos(bb,P,['rear']*len(bb),['timber']*len(P))
 q=pos(aa,caps,['front']*len(aa),['snow']*len(caps)); w=pos(bb,caps,['rear']*len(bb),['snow']*len(caps))
 checks[j]={'intentional_front_timber_seat':k,'intentional_rear_timber_seat':l,'unexpected_snow_contacts':dict(q,**w)}
# Straight-on normalized rail projection. Geometry only; no compositor, screenshots or mock approval.
normal=np.array([7,11,11],float);normal/=np.linalg.norm(normal);xx=np.cross([0,1,0],normal);xx/=np.linalg.norm(xx);yb=np.cross(normal,xx)
Q=np.array([xx,yb])*(720/13)
view={k:np.ptp(v.reshape(-1,3)@Q.T,axis=0).tolist() for k,v in T.items()}
# Atlas is physically new/artist-authored, not copied owner or Meshy. Project
# ribbons from exact phase to both height and RGB rough fiber. No fake render.
u,v=np.meshgrid(np.linspace(0,1,1024),np.linspace(.064,-.064,128))
c=.039*np.cos(8*np.pi*u)
q1=np.maximum(0,1-((v-c)/.020)**2);q2=np.maximum(0,1-((v+c)/.020)**2)
noise=.48*np.sin(2*np.pi*(173*u+29*v))+.32*np.cos(2*np.pi*(117*u+199*v))
B=np.zeros((*u.shape,3),float)+np.array([176,87,38])
cre=np.array([250,222,161]);wam=np.array([219,166,97])
alpha2=np.clip(q2*2,0,1);alpha1=np.clip(q1*2,0,1)
B+=alpha2[:,:,None]*(wam-B);B+=alpha1[:,:,None]*(cre-B)
B+=noise[:,:,None]*np.maximum(alpha1,alpha2)[:,:,None]*5
Image.fromarray(np.rint(B).clip(0,255).astype(np.uint8)).save(p/'RopeFiberBaseColor.png')
ht=((.72*q2+q1)+noise*.08)*np.maximum(alpha1,alpha2)
gx=np.gradient(ht,axis=1);gy=np.gradient(ht,axis=0)
nrm=np.dstack([-gx*.35,gy*.35,np.ones_like(gx)])
nrm/=np.linalg.norm(nrm,axis=-1,keepdims=True)
Image.fromarray(np.rint((nrm*.5+.5)*255).astype(np.uint8)).save(p/'RopeFiberNormal.png')
gsrc=r/'hvn-l1-fence-33036-west-lower-grade-v1/grade.py'; gtxt=gsrc.read_text()
G={'height':bound,'np':np}
exec('def h(p):return height(np.asarray(p))\n'+gtxt[gtxt.index('def cross(a,b)'):gtxt.index('vals=[]')],G)
exec(gtxt[gtxt.index('from functools'):gtxt.index('for i,tr in enumerate(lower):')],G)
def terrain_clip(T):
 minimum=[1e3,None]; n=0
 for j,tri in enumerate(T):
  U=tri[:,[0,2,1]]; lo,hi=np.floor(U[:,:2].min(0)*4).astype(int),np.floor(U[:,:2].max(0)*4).astype(int)
  for x,z in __import__('itertools').product(range(lo[0],hi[0]+1),range(lo[1],hi[1]+1)):
   for tile,coef in G['grids'](x,z):
    for p in G['clip'](U,tile):
     y=float(p[2]-(p[:2]@coef[:2]+coef[2]));n+=1
     if y<minimum[0]:minimum=[y,[int(j),*p.tolist()]]
 return [n,*minimum]
foot={k:terrain_clip(T[k]) for k in sorted(T) if k.startswith(('rail_','rear_'))}
out={'state':'one detached source proposal; not material/native approved','exact_original_body_cap_tri_count':int(selected.sum()),'world_root_xz_and_y':[*anchor.tolist(),Y0],
    'exact_new_band_terrain_clip_count_gap_point':foot,'actual_panel_triangles':sum(len(t) for t in T.values()),'by_component':{k:len(t) for k,t in T.items()},'near_stock_geom_projected_bounds_px':view,
    'width_bounds':probe,'actual_cross_component_contacts':checks,
    'material_caveat':'Base-color and tangent normal are newly authored; OD normal size/orientation, Gamma import, and local shader need actual approval. Wood core retains nominal rounded shape. This receipt has no existing private Meshy map.'}
(p/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
rows=['# Source-only author diagnostic. No native installed material.','mtllib RootedFence.mtl','s 1'];i=1
for k,t in T.items():
 rows.append('o '+k)
 marker=''; UU=uvs.get(k)
 for n,q in enumerate(t):
  if k.startswith('rail_'):
   color='emboss_atlas' if (n<80*40 and n%40<20) else 'rail_wood'
  else:color=k if not k.startswith('rear_') else 'one_hemp_rear'
  if color!=marker:rows.append('usemtl '+color);marker=color
  for c in q:rows.append('v '+' '.join(f'{d:.9f}' for d in c))
  for s in (UU[n] if UU is not None else ((0,0),)*3): rows.append('vt '+' '.join(f'{d:.9f}' for d in s))
  rows.append(f'f {i}/{i} {i+1}/{i+1} {i+2}/{i+2}');i+=3
(p/'RootedEmbossedFence_SourceOnly.obj').write_text('\n'.join(rows)+'\n')

(p/'RootedFence.mtl').write_text('newmtl emboss_atlas\nKd 1 1 1\nPr .85\nmap_Kd RopeFiberBaseColor.png\nnewmtl rail_wood\nKd .69 .34 .15\nPr .85\nnewmtl one_hemp_rear\nKd .88 .69 .43\nPr .87\nnewmtl body\nKd .81 .43 .17\nPr .83\nnewmtl caps\nKd .94 .956 .99\nPr .79\n')
