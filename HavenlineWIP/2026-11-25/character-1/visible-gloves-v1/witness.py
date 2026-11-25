"""Exact C1 own-geometry cold grip bench; static interpolation snapshots only."""
import bpy,hashlib,math,numpy as np,json,os
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree
from collections import Counter
p=Path(__file__).resolve().parent
pin=Path(os.environ['C1_NARROW_READY_PACKET'])
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(pin/'SHA256SUMS')=='ccd17840ef942d61ba891958a50c7dcfe4b1f9a9263280667ce9dabb50c389d7'
for row in (pin/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(maxsplit=1);assert sha(pin/n)==h
assert sha(Path(os.environ['C1_EXACT_BLEND']))=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert sha(Path(os.environ['C1_EXACT_GLB']))=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
g=Path(os.environ['C1_AXE_GLB'])
assert sha(g)=='79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e'
bpy.ops.wm.open_mainfile(filepath=str(pin/'c1-narrow-ready-witness.blend'))
rig=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
skin=next(x for x in bpy.context.scene.objects if x.type=='MESH')
assert len(rig.pose.bones)==52 and not bpy.data.actions
def vec(xs,k,n,d=np.float32):
 arr=np.empty(len(xs)*n,dtype=d);xs.foreach_get(k,arr);return arr.reshape(-1,n)
def tri(o):
 o.data.calc_loop_triangles();return vec(o.data.loop_triangles,'vertices',3,np.int32)
def poses():return vec(skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices,'co',3).astype(float)
P=vec(skin.data.vertices,'co',3).astype(float);F=tri(skin)
original=poses();names=[q.name for q in skin.vertex_groups]
lookup={n:i for i,n in enumerate(names)}
W=np.zeros((len(P),len(names)),np.float32)
for v in skin.data.vertices:
 for x in v.groups: W[v.index,x.group]=x.weight
dom=np.array(names)[W.argmax(1)]; X0=P[:,0];Y0=P[:,1];Z0=P[:,2]
_,weld=np.unique(np.rint(P/1e-6).astype('int64'),axis=0,return_inverse=True)
def make_bvh(arr, faces):
 ids,local=np.unique(faces.ravel(),return_inverse=True)
 return BVHTree.FromPolygons(arr[ids].tolist(),local.reshape(-1,3).tolist(),all_triangles=True,epsilon=0.)
def signed_planes(a,f):
 t=a[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
 h=(n*t[:,0]).sum(1); n[h<0]*=-1; h=abs(h)
 return n,h
# Body-first held orientation, not inferred from any former wrist or tool position.
# Normals oppose laterally on exact grip facets; digits aim forward, elbows support down and out.
import itertools
unit=lambda a:a/np.linalg.norm(a)
sides=('R','L')
mod={f'{n}.{s}' for n in ('upper_arm','forearm','hand') for s in sides}
for n in mod: rig.pose.bones[n].matrix_basis.identity()
bpy.context.view_layer.update()
rest_upper=poses()
fixed=P[:,2]<-.72
assert np.array_equal(rest_upper[fixed],original[fixed])
obs=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(g))
axe=next(o for o in bpy.context.scene.objects if o not in obs and o.type=='MESH')
A=vec(axe.data.vertices,'co',3).astype(float);T=tri(axe);assert len(T)==512
# Compact frontal diagonal, left tool end lower and handle center around sternum.
axis=unit(np.array([-.42,0.,.91]));r=unit(np.array([axis[2],0.,-axis[0]]))
M=np.column_stack((r,np.cross(axis,r),axis))
assert np.linalg.det(M)>.99999
factory=np.array([0.,0.,.223])+.18*axis
model=A@M.T+factory
# Absolute foreground separation from actual shell, no guessed capsule:
# only full bound on all non-arm triangles, not final clearance by shoulder/cuff.
arm=set(f'{n}.{s}' for s in sides for n in ('upper_arm','forearm','hand','clavicle'))
excluded=np.isin(dom,list(arm)) | (abs(X0)>.48)
garment=F[~excluded[F].any(1)]
# Use exact triangle XZ AABB overlap with projected complete tool AABB. Conservative, no body holes.
triXZ=rest_upper[garment][:,:,[0,2]]
slab=(triXZ.max(1)>=model[:,[0,2]].min(0)).all(1)&(triXZ.min(1)<=model[:,[0,2]].max(0)).all(1)
used=garment[slab]
assert len(used)
miny=float(rest_upper[used,1].min())
max_tool_y=float(model[:,1].max())
# Depth d is subtracted along actor Y. Strict finite 5mm foreground gap.
dmin=max_tool_y-miny+.005
constraints={};sets={}
for side,z,radius,radial in [('R',-.10,.071,-1),('L',-.26,.073,1)]:
 ix=np.flatnonzero(((abs(A[T,2]-z)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-radius)<3e-5)).all(1));assert len(ix)==28
 plane,_=signed_planes(A,T[ix]);i=int(np.argmax(radial*plane[:,0]));fi=int(ix[i])
 face=A[T[fi]]
 # Interior facet target with known barycentric modest third coefficient.
 bary=np.array([.49,.49,.02]);ref=bary@model[T[fi]];outward=M@plane[i]
 h=rig.pose.bones['hand.'+side];bind=np.array(h.bone.matrix_local)
 coords=(P-bind[:3,3])@bind[:3,:3]
 patch=np.flatnonzero((W[:,lookup['hand.'+side]]>.8)&(abs(coords[:,0])<.025)&(abs(coords[:,1]-.061)<.012)&(coords[:,2]>0))
 assert len(patch)>30
 pi=int(patch[np.argmax(coords[patch,2])]);off=coords[pi]
 inward=-outward
 dvec=np.array([0.,-1.,.11 if side=='R' else -.11])
 forward=unit(dvec-inward*(dvec@inward)); hr=np.column_stack((np.cross(forward,inward),forward,inward))
 U,Q,H=(rig.pose.bones[f'{n}.{side}'] for n in ('upper_arm','forearm','hand'))
 shoulder=np.array(U.head)
 a=np.linalg.norm(np.array(Q.head)-shoulder);b2=np.linalg.norm(np.array(H.head)-np.array(Q.head))
 w0=ref+.0015*outward-hr@off
 dx,dy,dz=w0-shoulder
 # 20mm reserve requirement; inner shell separately checked after exact selection.
 delta2=(a+b2-.020)**2-dx*dx-dz*dz
 assert delta2>0.
 maxreach=float(dy+np.sqrt(delta2))
 minreach=float(dy-np.sqrt(delta2))
 constraints[side]={'reach_depth_interval_m':[minreach,maxreach],'shoulder':shoulder.tolist(),'links_m':[float(a),float(b2)],'surface_face_index':fi,'bary':bary.tolist(),'palm_vertex':pi,
  'palm_sample_count':len(patch),'grip_center_in_original_axis':z,'grip_face_z':float(bary@face[:,2]),'outward':outward.tolist()}
 sets[side]=(U,Q,H,a,b2,shoulder,w0,hr,pi,ref,outward,ix)
low=max(dmin,*(c['reach_depth_interval_m'][0] for c in constraints.values()))
high=min(c['reach_depth_interval_m'][1] for c in constraints.values())
result={'status':'HOLD_EMPTY_BILATERAL_CERTIFIED_DEPTH' if low>=high else 'STATIC_OPEN_EVALUATED','continuous_depth_interval_m':[low,high],'garment_foreground_min_m':dmin,
 'garment_witness_triangles':len(used),'sides':constraints,'unchanged_lower_to_parent_exact':True,
 'orientation':M.tolist(),'zero_depth_tool_origin':factory.tolist(),'negative_control_interval_after_extra_200mm_foreground_m':[low+.200,high]}
if low<high:
 # One stance, center of the demonstrably nonempty interval. No offset sweep.
 depth=(low+high)/2;dt=np.array([0,-depth,0]);TP=model+dt
 result['only_selected_depth_m']=depth
 def orient(m,a,b):
  q=(m.to_3x3()@Vector((0,1,0))).rotation_difference(Vector(b-a))
  h=(q.to_matrix()@m.to_3x3()).to_4x4();h.translation=Vector(a);return h
 for side,(U,Q,H,a,b2,sh,w0,hr,pi,ref,outward,ix) in sets.items():
  wr=w0+dt;v=wr-sh;length=np.linalg.norm(v);n=v/length
  assert abs(a-b2)<length<a+b2
  x=(a*a-b2*b2+length*length)/(2*length)
  pole=np.array([-.89 if side=='R' else .89,-.30,-.78]);pole=unit(pole-(pole@n)*n)
  el=sh+x*n+np.sqrt(a*a-x*x)*pole
  Um,Qm=U.matrix.copy(),Q.matrix.copy()
  U.matrix=orient(Um,sh,el);bpy.context.view_layer.update()
  Q.matrix=orient(Qm,el,wr);bpy.context.view_layer.update()
  h=Matrix(hr.tolist()).to_4x4();h.translation=Vector(wr);H.matrix=h;bpy.context.view_layer.update()
  constraints[side].update(wrist=wr.tolist(),elbow=el.tolist(),reserve_mm=float(1000*(a+b2-length)),
   forearm_to_hand_deg=float(np.degrees(np.arccos(np.clip(unit(wr-el)@hr[:,1],-1,1)))),
   wrist_error_mm=float(1000*np.linalg.norm(np.array(H.head)-wr)),elbow_error_mm=float(1000*np.linalg.norm(np.array(Q.head)-el)))
 base=poses();BT=make_bvh(TP,T)
 parent=Path(os.environ['C1_GLOVE_TOPOLOGY_RESULT'])
 assert sha(parent)=='dc4d419fc34dcf84ff3cd3bdf23d44306831b5fc3dfe5d7772ad45b90022533f'
 assert len(make_bvh(base,F).overlap(BT))==370
 # Clip at proximal cuff plane of the actual existing wrist. Intersections
 # are shared by original garment and replacement, including duplicated UV rows.
 ycut=-.018
 ring={};over={}
 for side,(U,Q,H,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  bind=np.array(H.bone.matrix_local); local=(P-bind[:3,3])@bind[:3,:3]
  D=local[:,1]-ycut
  # Distant head/body can extend across the infinite hand-local cut; restrict
  # ownership to the exact side's arm region, and fail any boundary there.
  sgn=-1 if side=='R' else 1
  owned=(sgn*P[:,0]>.52)
  up=(D>0)&owned
  cross=np.flatnonzero(up[F].any(1)&(~up[F]).any(1))
  out=np.flatnonzero(up[F].all(1))
  assert np.all(owned[F[cross]])
  edges={}; segments=[]
  for k in cross:
   row=F[k];tmp=[]
   for a,c in zip(row,np.roll(row,-1)):
    if up[a]==up[c]:continue
    a,c=sorted((int(a),int(c)));q=(a,c)
    if q not in edges:edges[q]=(-D[a]/(D[c]-D[a]),len(edges))
    tmp.append(edges[q][1])
   assert len(tmp)==2;segments.append(tmp)
  ee=np.asarray(list(edges),int);alpha=np.asarray([v[0] for v in edges.values()])
  K=P[ee[:,0]]*(1-alpha[:,None])+P[ee[:,1]]*alpha[:,None]
  C=base[ee[:,0]]*(1-alpha[:,None])+base[ee[:,1]]*alpha[:,None]
  Kloc=(K-bind[:3,3])@bind[:3,:3]
  # Only weld true geometric UV seams; no shell bridge at other endpoints.
  uk,rr,ww=np.unique(np.rint(K/1e-6).astype(int),axis=0,return_index=True,return_inverse=True)
  ss=np.unique(np.sort(ww[np.asarray(segments)],axis=1),axis=0);ss=ss[ss[:,0]!=ss[:,1]]
  nb={i:set() for i in range(len(uk))}
  for a,c in ss:nb[a].add(c);nb[c].add(a)
  bad=[i for i,x in nb.items() if len(x)!=2]
  loops=[]
  remain={i for i,x in nb.items() if x}
  while remain:
   start=min(remain);walk=[start]
   if any(len(nb[i])!=2 for i in remain):break
   prev=start;cur=min(nb[start])
   while cur!=start and len(walk)<=len(nb):
    walk.append(cur);nex=next(iter(nb[cur]-{prev}));prev,cur=cur,nex
   assert cur==start
   remain-=set(walk);loops.append(walk)
  over[side]={'cross_triangles':len(cross),'remove_triangles':len(out),'bad_degree':len(bad),'loops':[len(i) for i in loops],
   'bind_loop_ranges_local':np.ptp(Kloc,axis=0).tolist(),'exact_native_seam_neutral_mm':float(1000*np.max(np.linalg.norm(K-K[rr[ww]],axis=1))),
   'exact_native_seam_posed_mm':float(1000*np.max(np.linalg.norm(C-C[rr[ww]],axis=1)))}
  ring[side]=(ee,alpha,ww,rr,loops,cross,out,K,C,Kloc,up)
 print(json.dumps(over,indent=2),flush=True)
 # Exact connected distal shell labels. Small seam loops may be accessory
 # components; preserve them only if independent of the outer glove shell.
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 donor={}
 for side,(ee,aa,ww,rr,loops,cross,out,K,C,Kloc,up) in ring.items():
  fs=F[np.r_[cross,out]]
  ed=np.concatenate((fs[:,[0,1]],fs[:,[1,2]],fs[:,[2,0]]),axis=0)
  ii,jj=weld[ed].T
  # Distal welding only, all source rows incident on the cut retained.
  _,labels=connected_components(coo_matrix((np.ones(len(ii)),(ii,jj)),shape=(weld.max()+1,weld.max()+1)).tocsr(),directed=False)
  loop_cs=[int(labels[weld[ee[rr[loop[0]],0]]]) for loop in loops]
  pts=[Kloc[rr[L]][:,[0,2]] for L in loops]
  size=[float(np.ptp(x,axis=0).prod()) for x in pts]
  k=int(np.argmax(size))
  over[side]['loop_component_ids']=loop_cs;over[side]['outer_loop']=k
  over[side]['bounds_per_loop_mm']=[(1000*np.stack((x.min(0),x.max(0)))).tolist() for x in pts]
  over[side]['independent_other_seam_components']=all(c!=loop_cs[k] for i,c in enumerate(loop_cs) if i!=k)
  donor[side]=(k,loop_cs[k],labels)
 print(json.dumps(over,indent=2),flush=True)
 # One actual exterior glove shell per side. The former cuff cut proved
 # branched; do not falsely weld/cap the accessory or co-component loop.
 sourceuv=np.empty((len(skin.data.uv_layers.active.data),2),np.float32)
 skin.data.uv_layers.active.data.foreach_get("uv",sourceuv.ravel())
 triloops=vec(skin.data.loop_triangles,'loops',3,np.int32)
 origFU=sourceuv[triloops]
 package={};reports={}; open_bv={}
 for side,(U,Q,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  ee,aa,ww,rr,loops,cross,out,K,C,Kloc,up=ring[side]
  k,dom_component,labels=donor[side]; ids=np.asarray(loops[k],int)
  bound=Kloc[rr[ids]]
  ctr=np.median(bound[:,[0,2]],axis=0)
  def orientation(points):
   q=points[:,[0,2]];w=np.roll(q,-1,axis=0)
   return np.sum(q[:,0]*w[:,1]-q[:,1]*w[:,0])
  if orientation(bound)<0: ids=ids[::-1];bound=bound[::-1]
  start=int(np.argmax(bound[:,0]));ids=np.roll(ids,-start);bound=np.roll(bound,-start,axis=0)
  ray=np.arctan2(bound[:,2]-ctr[1],bound[:,0]-ctr[0])
  # Map the uninterrupted primary loop to an oval band, preserving its
  # exact geometry + perimeter; no nearest replacement on source boundary.
  leng=np.linalg.norm(np.roll(bound,-1,axis=0)-bound,axis=1);L=len(bound)
  frac=np.r_[0,np.cumsum(leng[:-1])]/leng.sum()
  N=40; angles=np.arange(N)*2*np.pi/N
  layers=[
   (-.008, .056,.051,ctr[0]*.72,ctr[1]*.72),
   (.004, .052,.045,ctr[0]*.37,ctr[1]*.32),
   (.027, .064,.031,0.,-.009),
   (.054, .067,.034,0.,-.008),
   (.083, .066,.028,0.,-.012),
   (.109, .061,.025,0.,-.008),
   (.134, .049,.020,0.,-.002),
   (.146, .029,.012,0.,.002),
   (.150, .008,.006,0.,.002)]
  pos=list(bound); phase=[0]*L
  # Thumb root belongs near the index side (derive sign from original thumb).
  br=np.array(H.bone.matrix_local); thumb_rest=np.array(rig.data.bones['thumb.01.'+side].head_local)
  tx=int(np.sign(((thumb_rest-br[:3,3])@br[:3,:3])[0]))
  for j,(y,w,h,cx,cz) in enumerate(layers):
   for t in angles:
    x0=cx+w*np.cos(t)
    # Concave interior lateral faceting, subtly differentiated knuckle
    # lobes on the closed far-end arc of the insulated mitten treatment.
    bow=.011*max(np.sin(t),0.)*(1.-abs(np.cos(t))) if 2<=j<=5 else 0.
    knuckle=.0035*np.cos(4*np.pi*((x0-cx)/max(w,1e-8))) if 5<=j<=7 else 0.
    pos.append([x0,y+knuckle,cz+h*np.sin(t)-bow]);phase.append(1 if j<3 else 2)
  Faces=[]; face_role=[]
  def quad(a,b,c,d,role):
   Faces.extend(((a,b,c),(a,c,d)));face_role.extend((role,role))
  # Zipper join source contour to fabricated elastic band.
  a=q=0
  while a<L or q<N:
   fa=frac[a+1] if a+1<L else 1. if a<L else 2.
   fq=(q+1)/N if q<N else 2.
   if fa<=fq:
    Faces.append((a%L,(a+1)%L,L+q%N));a+=1
   else:
    Faces.append((a%L,L+(q+1)%N,L+q%N));q+=1
   face_role.append(0)
  cutrows={2,3}; center=0 if tx>0 else N//2
  cutcols={(center+i)%N for i in (-3,-2,-1,0,1,2)}
  def fi(j,k):return L+j*N+k%N
  missing_edges={}
  for j in range(len(layers)-1):
   for q in range(N):
    corners=[fi(j,q),fi(j,q+1),fi(j+1,q+1),fi(j+1,q)]
    if j in cutrows and q in cutcols:
     for f,g in zip(corners,np.roll(corners,-1)):
      p0=tuple(sorted((f,g)))
      if p0 in missing_edges:missing_edges.pop(p0)
      else:missing_edges[p0]=(f,g)
    else:quad(*corners,role=1 if j<=2 else 2)
  tip=len(pos);pos.append([0,.151,.002]);phase.append(2)
  for q in range(N):Faces.append((fi(len(layers)-1,q),fi(len(layers)-1,q+1),tip));face_role.append(2)
  # Connect thumb branch to an actual hole in glove shell (not overlapping
  # separate objects). Root and second ring express independent opposition.
  follow=dict(missing_edges.values()); v0=min(follow);v1=follow[v0];brim=[v0]
  while v1!=v0:
   assert len(brim)<len(follow);brim.append(v1);v1=follow[v1]
  assert len(brim)==len(follow)
  brim=np.array(brim);group_n=len(brim)
  origin=np.asarray(pos)[brim].mean(0)
  target=np.array([tx*.093,.078,.019])
  thumbstart=len(pos)
  for scale,u in [(1.,.18),(.79,.52),(.51,.86),(.21,1.)]:
   new=origin+u*(target-origin)+scale*(np.asarray(pos)[brim]-origin)
   pos.extend(new.tolist());phase.extend([3]*group_n)
  for j0 in range(4):
   for i in range(group_n):
    h0=int(brim[i]) if j0==0 else thumbstart+(j0-1)*group_n+i
    h1=int(brim[(i+1)%group_n]) if j0==0 else thumbstart+(j0-1)*group_n+(i+1)%group_n
    quad(h0,h1,thumbstart+j0*group_n+(i+1)%group_n,thumbstart+j0*group_n+i,role=3)
  end=len(pos);pos.append(target.tolist());phase.append(3)
  for i in range(group_n):
   Faces.append((thumbstart+3*group_n+i,thumbstart+3*group_n+(i+1)%group_n,end));face_role.append(3)
  V0=np.asarray(pos); ff=np.asarray(Faces,int);phase=np.asarray(phase)
  Hm=np.array(H.matrix)
  Vbind=V0@br[:3,:3].T+br[:3,3]
  Vopen=V0@Hm[:3,:3].T+Hm[:3,3]
  bnd0=K[rr[ids]];bnd1=C[rr[ids]]
  assert np.linalg.norm(Vbind[:L]-bnd0,axis=1).max()<2e-7
  Vbind[:L]=bnd0; Vopen[:L]=bnd1
  # Independently opposed thumb and cuff interpolation controls. The cuff
  # holsters measured posed seam shape through two loose wrist rings.
  cmd=np.array([tx*.006,-.003,-.008])@Hm[:3,:3].T
  Vopen[phase==3]+=cmd
  from scipy.interpolate import interp1d
  seam=interp1d(np.r_[frac,1.],np.concatenate([bnd1-(V0[:L]@Hm[:3,:3].T+Hm[:3,3]),(bnd1-(V0[:L]@Hm[:3,:3].T+Hm[:3,3]))[:1]]),axis=0)
  for i,s1 in enumerate([.75,.38,.08]):
   subset=slice(L+N*i,L+N*(i+1));Vopen[subset]+=seam(np.arange(N)/N)*s1
  # New bounded area with its actual assigned shaft facet (no forcing
  # off-band fingers/tool samples inside). Stage only, true bearing requires
  # full patch and intact sleeve. Projectable vertices only.
  face=TP[T[constraints[side]['surface_face_index']]]
  inv=np.linalg.pinv((face[1:]-face[0]).T);fit=Vopen-face[0];uvf=fit@inv.T;dd=fit@n
  chosen=(phase==2)&(uvf.min(1)>.05)&(uvf.sum(1)<.95)&(np.abs(dd)<.018)
  Vopen[chosen]-=(dd[chosen]-.00008)[:,None]*n
  assert np.array_equal(Vopen[:L],bnd1)
  # Exact shade/material provenance; nearest source per-corner UV assignment
  # is diagnostic only until seam and texel continuity can be authored.
  Ksrc=make_bvh(P,F)
  uvs=np.tile([.5,.5],(len(Vbind),1))
  for i,v in enumerate(Vbind):
   pt,_,f,dist=Ksrc.find_nearest(Vector(v))
   p0=P[F[f]];coeff=np.linalg.pinv((p0[1:]-p0[0]).T)@(np.asarray(pt)-p0[0])
   uvs[i]=np.r_[1-coeff.sum(),coeff]@origFU[f]
  def make(name,vt):
   m=bpy.data.meshes.new(name);m.from_pydata(vt.tolist(),[],ff.tolist());m.update()
   for a in skin.data.materials:m.materials.append(a)
   uv=m.uv_layers.new(name=skin.data.uv_layers.active.name);uv.data.foreach_set("uv",uvs[ff].astype(np.float32).ravel())
   return m
  BB=make('Detached-Neutral-'+side,Vbind); OO=make('Detached-Open-'+side,Vopen)
  Open=vec(OO.vertices,'co',3).astype(float)
  boot=make_bvh(Open,ff);open_bv[side]=boot
  cross_t=boot.overlap(BT);selfh={(i,j) for i,j in boot.overlap(boot) if i<j and not np.isin(ff[i],ff[j]).any()}
  def ax(v):
   return np.cross(v[ff[:,1]]-v[ff[:,0]],v[ff[:,2]]-v[ff[:,0]])
  # Compare rigid transported neutral panels to localized shape, ignoring
  # baseline grasp articulation where no driven motion was authorized.
  n0=ax(V0@Hm[:3,:3].T+Hm[:3,3]);n1=ax(Open);ok=(n0*n0).sum(1)>1e-21
  ra=(n0[ok]*n1[ok]).sum(1)/((n0[ok]*n0[ok]).sum(1))
  vs=Open[ff]-face[0];xy=vs@inv.T;ds=vs@n
  yes=((ds>=0)&(ds<=.00015)&(xy.min(2)>=0)&(xy.sum(2)<=1)).all(1)
  ve=(Open-factory-dt)@M;nn,hh=signed_planes(A,T[ix])
  sing=np.maximum(np.max(ve@nn.T-hh,axis=1),abs(ve[:,2]-constraints[side]['grip_center_in_original_axis'])-.05)
  ee2=np.sort(np.concatenate((ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]])),axis=1);ee2=np.unique(ee2,axis=0)
  lam=np.linalg.norm(Vbind[ee2[:,1]]-Vbind[ee2[:,0]],axis=1)
  l1=np.linalg.norm(Open[ee2[:,1]]-Open[ee2[:,0]],axis=1)
  reports[side]={'vertices':len(V0),'triangles':len(ff),'modeled_thumb_faces':face_role.count(3),'exact_original_neutral_contour_mismatch_um':float(1e6*np.linalg.norm(vec(BB.vertices,'co',3)[:L]-bnd0,axis=1).max()),
   'exact_original_open_contour_mismatch_um':float(1e6*np.linalg.norm(Open[:L]-bnd1,axis=1).max()),'projectable_contact_vertices':int(chosen.sum()),
   'open_tool_pairs':len(cross_t),'offband':sum(j not in ix for i,j in cross_t),'tool_vs_elastic_cuff':sum(face_role[i] in (0,1) for i,j in cross_t),
   'deepest_grip_prism_mm':float(1000*min(sing.min(),0)),'self_nonadjacent_pairs':len(selfh),
   'signed_area_gate_fail':int(((ra<.5)|(ra>2.)).sum()),'face_reversals':int((ra<=0.).sum()),
   'edge_gate_fail':int(((l1<.5*lam)|(l1>2*lam)).sum()),'full_near_patch_count':int(yes.sum()),
   'near_patch_area_mm2':float(5e5*np.linalg.norm(n1[yes],axis=1).sum()),
   'left_web_mapping_authority':'old material spans removed from replacement; cannot claim the 133 source IDs passed on this topology'}
  for label,a in [('neutral',Vbind),('open',Open),('triangles',ff),('uv',uvs[ff]),('roles',np.asarray(face_role)),('seam_source_edges',ee[rr[ids]]),('seam_source_edge_weights',aa[rr[ids]])]:
   package[side+'_'+label]=a
 out={'status':'HOLD_NOT_MERGED_BRANCH_SEAMS_AND_OPEN_CLEARANCE','seam':over,'gloves':reports,
  'cross_glove_pairs':len(open_bv['R'].overlap(open_bv['L'])),'closed_or_published':False}
 np.savez_compressed(p/'editable_visible_gloves.npz',**package)
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
