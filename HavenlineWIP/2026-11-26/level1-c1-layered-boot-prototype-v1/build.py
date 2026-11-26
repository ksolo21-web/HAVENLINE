"""One new detached phased boot-shaft and layered trouser cuff; original source protected."""
import contextlib,io,json
from pathlib import Path
import numpy as np
from collections import defaultdict,Counter
from scipy.spatial import cKDTree
with contextlib.redirect_stdout(io.StringIO()):
 from domain import *
from inspect_source import load
a0,v0,N0,UV0,J0,W0,F0=load(f.STOCK/'assets/characters/Character1.glb')
assert np.array_equal(v0,V) and np.array_equal(F0,F)
orig_n=len(V); Q=V.astype(float); indices=F.astype(np.int64)
exact_cut=np.flatnonzero(replace)
origrow={int(z):int(i) for i,z in reversed(list(enumerate(f.tags)))}
def cyc(g):
 s=min(g);rows=[s];p=None;x=s
 while True:
  n=min(set(g[x])-({p} if p is not None else set()))
  if n==s:break
  rows.append(n);p,x=x,n
 assert len(rows)==len(g)
 return rows
def loop_size(q):
 return np.linalg.norm(q-np.roll(q,-1,axis=0),axis=1).sum()
def clockwise(q):return float(np.sum(np.cross(q,np.roll(q,-1,axis=0),axis=-1)[:,1]))>0
# Align starting station at sideward heel point; whole cycle ordering retained.
def order(x):
 q=np.asarray(x)
 if not clockwise(q):q=q[::-1]
 c=(q.max(0)+q.min(0))*.5
 dx=q-c
 angle=np.angle(dx[:,0]-1j*dx[:,2])
 z=int(np.argmin(abs(np.angle(np.exp(1j*(angle-np.pi))))))
 return np.roll(np.arange(len(x)) if clockwise(np.asarray(x)) else np.arange(len(x))[::-1],-z)
anchors=[]
for G in [gl,gu]:
 ir=np.array([origrow[s] for s in cyc(G)],int)
 anchors.append(ir[order(Q[ir])])
low,high=anchors
def section(y):
 graph=defaultdict(list);coords={}
 Fq=Q[indices]; c=(Fq[:,:,1].min(1)<y)&(Fq[:,:,1].max(1)>y)
 for row in indices[c]:
  found=[]
  for a,b in zip(row,np.roll(row,1)):
   aa,bb=Q[a],Q[b]
   if (aa[1]-y)*(bb[1]-y)>=0:continue
   t=(y-aa[1])/(bb[1]-aa[1]);p=aa*(1-t)+bb*t
   pair=tuple(sorted((int(f.tags[a]),int(f.tags[b]))));coords[pair]=p;found.append(pair)
  if found:assert len(found)==2
  if len(found):g,h=found;graph[g].append(h);graph[h].append(g)
 assert all(len(r)==2 for r in graph.values())
 # Target region is one actual right-leg contour. Fail if source forks rather
 # than hide artifacts by selecting a ray envelope.

 alive=set(graph); rings=[]
 while alive:
  entry={min(alive)}; full=entry.copy()
  while entry:
   entry=set(y for x in entry for y in graph[x])-full
   full|=entry
  alive-=full
  ring=np.array([coords[s] for s in cyc({x:graph[x] for x in full})])
  if ring[:,0].mean()<-.04:rings.append(ring)
 if len(rings)!=1:raise RuntimeError(('source right contour branch',y,len(rings)))
 ring=rings[0]
 return ring[order(ring)]
def stretch(q,amount):
 # Physical constant inset in local radial direction; do not re-sample a
 # polar radius. Existing exact section order retains source contour recesses.
 c=(q.max(0)+q.min(0))*.5; vec=q-c;vec[:,1]=0
 return q+vec/np.linalg.norm(vec,axis=1)[:,None]*amount
def arclen(q):
 d=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
 assert np.min(d)>1e-10
 return np.r_[0.,np.cumsum(d)/d.sum()]
def zipper(a,b,space):
 x,y=arclen(space[a]),arclen(space[b])
 i=j=0;faces=[]
 while i<len(a) or j<len(b):
  ai=a[i%len(a)];bj=b[j%len(b)]
  if i<len(a) and (j==len(b) or x[i+1]<=y[j+1]):
   faces.append((ai,a[(i+1)%len(a)],bj));i+=1
  else:
   faces.append((ai,b[(j+1)%len(b)],bj));j+=1
 return np.asarray(faces,dtype=int)
def skin_dense(js,ws):
 w=np.zeros((len(js),len(f.slots)),float)
 np.add.at(w,(np.arange(len(js))[:,None],js),ws)
 return w
W=skin_dense(f.J,f.W)
p0=f.slots.index('RHeel')
rigid=np.eye(len(f.slots))[p0]
# Use exact selected witnesses by source y, not another sweep. Cuff and
# boot share heel transport across actual overlap, not welded geometry.
bottom_y=[.045,.059,.076,.094,.108]
top_hip_y=[.119,.134,.147]
boot=[low];pants=[]
X=list(Q);weights=list(W)
class_ids=['source']*len(X)
def near_rail(src,pts):return cKDTree(Q[src][:,[0,2]]).query(pts[:,[0,2]])[1]
def add(points,source,amount,kind):
 s=near_rail(source,points)
 ww=amount*W[source[s]]+(1.-amount)*rigid[None,:]
 ii=np.arange(len(X),len(X)+len(points));X.extend(points);weights.extend(ww);class_ids.extend([kind]*len(points))
 return ii
for y,mix in zip(bottom_y,[.55,.20,0,0,0]):
 boot.append(add(section(y),low,mix,'boot-exterior'))
# The boot opening narrows physically under the lined cuff; the shaft wall
# transitions inward before the cuff overlaps, maintaining visible outer
# donor shape via the separate cuff rather than an intersecting hidden fan.
for y,inset in [(.115,-.003),(.121,-.007),(.127,-.009)]:
 boot.append(add(stretch(section(y),inset),low,0,'boot-exterior-overlap'))
# Independent thickness: offset outer hem 1 mm outward, turned lining
# consumes 3 mm, while boot has at least its own 3–9 mm inward staging.
cuff_low_y=.117
outer_hem=stretch(section(cuff_low_y),.001)
pants.append(add(outer_hem,high,0,'cuff-outer'))
for y,mix in zip(top_hip_y,[0,.40,.80]):
 pants.append(add(section(y),high,mix,'cuff-outer'))
pants.append(high)
# Boot solid wall: top lip bends inward to a real tapered liner with footbed;
# liner is entirely another material surface, not an invented adjacent cap
# claimed inside an original fused cavity. Verify all areas and overlap below.
lip=np.array([X[i] for i in boot[-1]])
liners=[]
for y,shrink in [(.127,-.004),(.116,-.004),(.095,-.006),(.075,-.007),(.052,-.011),(.045,-.027)]:
 orig=section(y)
 # Physical liner routed inside current boot wall and tapering onto a rounded
 # convex footbed above the untouched heel/tread. Rings maintain orders.
 if y>=.115: inset=-.009+shrink
 else:inset=shrink
 liners.append(add(stretch(orig,inset),low,0,'boot-liner'))
heelbed=np.mean([X[i] for i in liners[-1]],axis=0)[None,:]; heelbed[:,1]=.043
flooridx=add(heelbed,low,0,'footbed')
# Cuff low end has a directly returned physical liner. Its far inward edge
# remains an explicitly recorded interior sewing termination (not hidden).
turn=[]
for y,inset in [(.117,-.0014),(.119,-.0025),(.127,-.0025)]:
 turn.append(add(stretch(section(y),inset),high,0,'cuff-liner'))
X=np.asarray(X);WW=np.asarray(weights)
lf=lambda s:np.concatenate([zipper(a,b,X) for a,b in zip(s,s[1:])])
boot_faces=lf(boot+liners)
ring=liners[-1]
boot_faces=np.concatenate((boot_faces,np.array([[int(ring[i]),int(ring[(i+1)%len(ring)]),int(flooridx[0])] for i in range(len(ring))])))
garment_faces=lf(pants)
garment_faces=np.concatenate((garment_faces,lf(turn[::-1]+[pants[0]])))
# Derive global winding by opposite incidence on the true immutable existing
# lower/upper cuts, then keep the entire sleeve's internal winding fixed.
def match(FNew,ref):
 def ed(x):
  return defaultdict(list,((k,v) for k,v in x.items()))
 d=defaultdict(list);g=defaultdict(list)
 for i,a,b in [(int(i),a,b) for i in ref for a,b in zip(f.tags[F[i]],np.roll(f.tags[F[i]],-1))]:d[tuple(sorted((int(a),int(b))))].append((int(a),int(b)))
 for j in FNew:
  for a,b in zip(j,np.roll(j,-1)):
   if a<orig_n and b<orig_n:
    ac,bc=int(f.tags[a]),int(f.tags[b]);g[tuple(sorted((ac,bc)))].append((ac,bc))
 shared=[(d[k][0],w[0]) for k,w in g.items() if len(w)==1 and len(d[k])==1]
 assert len(shared)>10 and len({a==b for a,b in shared})==1
 return (FNew[:,[0,2,1]] if shared[0][0]==shared[0][1] else FNew),len(shared)
boot_faces,nb=match(boot_faces,np.flatnonzero(lower))
garment_faces,nu=match(garment_faces,np.flatnonzero(top))
YR=Q[indices[replace]]
cent=YR.mean(1); tree=cKDTree(cent)
# Actual source face-side UV on every authored corner: exact vertices use
# existing UV; new positions choose nearest constrained source triangles and
# transfer barycentrically, with explicit max donor offset in verifier.
def transfer():
 ids0=np.flatnonzero(replace)
 todo=np.arange(orig_n,len(X))
 near=tree.query(X[todo],k=12)[1]
 vals=[];fd=[];dist=[]
 for i,k in zip(todo,near):
  arr=YR[k]; v=arr[:,1]-arr[:,0]; w=arr[:,2]-arr[:,0]; p=X[i]-arr[:,0]
  vv=(v*v).sum(1);ww=(w*w).sum(1);vw=(v*w).sum(1)
  pv=(p*v).sum(1);pw=(p*w).sum(1)
  de=vv*ww-vw**2
  z=np.maximum(de,1e-22)
  u=(pv*ww-pw*vw)/z;l=(pw*vv-pv*vw)/z
  coeff=np.maximum(np.stack((1-u-l,u,l),axis=1),0);coeff/=coeff.sum(1)[:,None]
  q=(arr*coeff[:,:,None]).sum(1)
  rk=np.linalg.norm(q-X[i],axis=1).argmin()
  donor=ids0[k[rk]]
  vals.append(coeff[rk]@UV0[indices[donor]])
  fd.append(int(donor));dist.append(float(np.linalg.norm(q[rk]-X[i])))
 return np.concatenate((UV0,np.array(vals))),np.array(fd),np.array(dist)
uv,donor,errors=transfer()
# Preserve original rigid trim triangles exactly as original art surfaces;
# they are not presented as physically seated or closed absent proof below.
trim=np.flatnonzero(replace & np.all(np.stack([np.where(f.J==i,f.W,0.).sum(1)==1 for i,name in enumerate(f.slots) if name.startswith("Rigid_R_BootFastener")],axis=1).any(1)[F],axis=1))
keep=np.flatnonzero(~replace)
faces=np.concatenate((indices[keep],boot_faces,garment_faces,indices[trim]))
cat=np.concatenate((np.zeros(len(keep),int),np.ones(len(boot_faces),int),np.full(len(garment_faces),2),np.full(len(trim),3)))
posed=np.einsum('nk,kij,nj->ni', WW,M[:,:3,:],np.c_[X,np.ones(len(X))]) * f.S+f.base
assert np.max(np.abs(posed[:orig_n]-P))<1e-13
Rnew=X*f.S+f.base
out=Path('candidate');out.mkdir()
np.savez_compressed(out/'detached-assembly.LOCAL.npz',vertices=X,faces=faces,pose=posed,neutral_world=Rnew,weights_dense=WW,uv=uv,
 face_category=cat,source_texel_donor_face=donor,source_texel_donor_distance_m=errors,keep_original_source_face_ids=keep,retained_trim_source_ids=trim,
 sole_support_original_rows=np.unique(f.bounds['R']['faces']),low_ring=low,upper_ring=high,original_lower_face_ids=np.flatnonzero(lower),
 original_replaced_face_ids=exact_cut)
# Actual editable OBJ pair; posed version remains evidence only.
def obj(p,x):
 with p.open('w') as o:
  o.write('# Detached Character 1 purpose-built right boot / separate cuff. No native release.\n')
  for i in x:o.write('v %.9f %.9f %.9f\n'%tuple(i))
  for i in uv:o.write('vt %.9f %.9f\n'%tuple(i))
  p=-1
  for row,k in zip(faces,cat):
   if k!=p:o.write('g '+['ExactOriginalKept','IndependentBootShell','IndependentCuff','ExactTrimFitWitness'][k]+'\n');p=k
   o.write('f '+' '.join(f'{j+1}/{j+1}' for j in row)+'\n')
obj(out/'detached-rest.LOCAL.obj',X)
obj(out/'detached-held.LOCAL.obj',(posed-f.base)/f.S)
receipt=dict(no_engine_or_install=True,art_sha256="95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099",original_exact_neutral_rest_rows=orig_n,
 authored_vertex_count=len(X)-orig_n,asset_part_triangle_counts=dict(original_unchanged=len(keep),boot=len(boot_faces),cuff=len(garment_faces),original_trim_in_fit=int(len(trim))),
 intact_original_right_lower_triangles=int(lower.sum()),right_boot_retained_attachment_edges=nb,upper_trouser_retained_attachment_edges=nu,
 arbitrary_hidden_caps_used=False,closed_world_rig_install=False,notes="Original rigid trim surfaces kept detached for fit qualification; not presumed seated or closed. Physical inner sleeve mouth recorded explicitly.")
receipt['private_payload_hashes']={p.name:h(p) for p in sorted(out.iterdir())}
(out/'build.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
