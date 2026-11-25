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
 # Positional cut and authored sewn side-panel topology on the actual body.
 # The closed virtual bearing panel uses the exact source shaft facet.
 contact=Path(os.environ['C1_CONTACT_DATA'])
 assert sha(contact)=='14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4'
 fixture=np.load(contact)
 base=poses();BT=make_bvh(TP,T);old=make_bvh(base,F).overlap(BT);assert len(old)==370
 sm=skin.data;uvs=np.zeros((len(sm.uv_layers.active.data),2),np.float32)
 sm.uv_layers.active.data.foreach_get('uv',uvs.ravel())
 form=uvs[vec(sm.loop_triangles,'loops',3,np.int32)]
 expandedP=P.tolist();expandedV=base.tolist()
 keep=np.ones(len(F),bool);takeout={};cuff_tri=[];cuffUv=[]
 sections={}; UVglobal={}; wids={}; report={}
 # Trace all exact colliding retained faces; do not manually exclude any.
 for side,(_,_,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  ee,aa,ww,rr,loops0,cross,far,K,C,Kloc,up=ring[side]
  outer,label,lab=donor[side]
  relevant=lambda ff:(lab[weld[F[ff]]]==label).all(1)
  clip=cross[relevant(cross)];drop=far[relevant(far)]
  keep[np.r_[clip,drop]]=False
  loops_keep=[i for i,L0 in enumerate(loops0) if lab[weld[ee[rr[L0[0]],0]]]==label]
  assert loops_keep==([0,3,4] if side=='R' else [0,1])
  g0=len(expandedP)
  expandedP.extend(K[rr].tolist());expandedV.extend(C[rr].tolist())
  allE={tuple(e):i for i,e in enumerate(ee)}
  oriented={}
  for ff in clip:
   verts=F[ff]; pp=[]
   for j,(a0,b0) in enumerate(zip(verts,np.roll(verts,-1))):
    if not up[a0]:pp.append((int(a0),form[ff,j]))
    if up[a0]!=up[b0]:
     a,b0s=sorted((int(a0),int(b0)));x=allE[(a,b0s)];ii=g0+int(ww[x])
     aa0=aa[x] if a0==a else 1-aa[x]; uv0=form[ff,j]*(1-aa0)+form[ff,(j+1)%3]*aa0
     pp.append((ii,uv0));UVglobal.setdefault(ii,uv0)
   for u,v in zip(pp,pp[1:]+pp[:1]):
    if u[0]>=g0 and v[0]>=g0:oriented[v[0]]=u[0]
   for j in range(1,len(pp)-1):
    tri0=[pp[0],pp[j],pp[j+1]]
    cuff_tri.append([a0 for a0,b0 in tri0]);cuffUv.append([b0 for a0,b0 in tri0])
  seam=[]
  for ln in loops_keep:
   gg=g0+np.asarray(loops0[ln]);s0=int(gg[0]);order=[s0]
   assert all(int(j) in oriented for j in gg)
   while oriented[order[-1]]!=s0:
    order.append(oriented[order[-1]]);assert len(order)<len(gg)+1
   assert set(order)==set(gg.tolist())
   seam.append(order)
  # Each original branch is a stable separate topological boundary.
  sections[side]=seam
  fw=W[:,lookup['forearm.'+side]]>.002
  baseowned=[(i,j) for i,j in old if fw[F[i]].any()]
  takeout[side]={'original_forearm_pairs':len(baseowned),'distal_original_forearm_pairs_deleted_by_exact_cut':sum(not keep[i] for i,j in baseowned),
   'source_collision_face_ids_deleted':sorted(set(int(i) for i,j in baseowned if not keep[i])),
   'all_tipward_faces_replaced':len(drop),'clipped_retained_source_faces':len(clip),'seam_lengths':list(map(len,seam))}
 P0=np.asarray(expandedP);V0=np.asarray(expandedV)
 allnew=[];newuv=[];newscope={};provenance={}; openpatch={}
 for side,(_,_,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  seam=sections[side];m0=np.array(H.bone.matrix_local);m1=np.array(H.matrix)
  open_to_bind=lambda v:(np.asarray(v)-m1[:3,3])@m1[:3,:3]@m0[:3,:3].T+m0[:3,3]
  patch=fixture[side+'_bearing_patch'][:3].astype(float)
  # Analytic exact double positions from original face+barycentric fractions.
  patch=fixture[side+'_barycentric']@fixture[side+'_compatible_shaft_face']; q=patch.mean(0)
  begin=len(allnew);start=len(expandedV)
  palmshade=UVglobal[seam[0][len(seam[0])//2]]
  def append(v,uv=None):
   i=len(expandedV);expandedV.append(np.asarray(v).tolist());expandedP.append(open_to_bind(v).tolist())
   UVglobal[i]=palmshade if uv is None else np.asarray(uv)
   return i
  def face(row,role):
   allnew.append(tuple(row));newuv.append([UVglobal[j] for j in row]);provenance[len(allnew)-1]=role
  def zipper(L,R,role): # both sequences follow same forward path; seam directions inverse
   L=list(L);R=list(R)
   i=j=0
   while i<len(L) or j<len(R):
    li=(i+1)/len(L) if i<len(L) else 2
    rj=(j+1)/len(R) if j<len(R) else 2
    if li<=rj:
     face([L[i%len(L)],L[(i+1)%len(L)],R[j%len(R)]],role);i+=1
    else:
     face([L[i%len(L)],R[(j+1)%len(R)],R[j%len(R)]],role);j+=1
  cuff=np.asarray(expandedV)[seam[0]]
  normal=n;axis=unit(patch[1]-patch[0]);v=unit(np.cross(normal,axis))
  def rotate_seq(L,axisv):
   X=np.asarray(expandedV)[L];j=int(np.argmax((X-X.mean(0))@axisv))
   return L[j:]+L[:j]
  # Planar face to structured collar via deliberate fabric sector panels,
  # not a sampled ring loft. Split medial/lateral bands with separate holes
  # that connect nested followbacks and a sewn thumb-web branch.
  Pids=[append(x) for x in patch]
  if np.cross(patch[1]-patch[0],patch[2]-patch[0])@n>0:Pids=Pids[::-1]
  palmface_idx=len(allnew);face(Pids,'true_assigned_bearing')
  def locations(center,pts):
   return [append(center+x) for x in pts]
  reverse=Pids[::-1]
  pxy=np.asarray(expandedV)[reverse]-q
  pxy2=pxy*1.32+.005*n
  mid_cover=[append(q+x) for x in pxy2]
  zipper(reverse,mid_cover,'palm_support')
  A0=rotate_seq(seam[0],axis)
  mids=np.asarray(expandedV)[mid_cover];ribs=[]
  for j in range(6):
   a=mids[j//2];b=mids[(j//2+1)%3] if j%2 else a
   u0=.5*(a+b)
   # Broad dorsal crease room and room for all independent sewn inserts.
   src=cuff[int(j*len(cuff)/6)%len(cuff)]
   ribs.append(append(.58*u0+.42*src+.019*n))
  # inside rim orientation: choose original seam winding pairing without
  # flipping any clipped original source triangles.
  zipper(A0,ribs,'elastic_collar')
  holes=[]
  for j in range(3):
   a=mid_cover[j];b=mid_cover[(j+1)%3];r=ribs[(2*j+1)%6];s=ribs[(2*j+2)%6];t=ribs[2*j]
   face([b,a,r],'crease_panel');face([a,t,r],'crease_panel')
   holes.append([b,r,s])
  # Each discarded panel was an actual open triangle; the interior branch
  # is sewn into it through a separate foldback, not by filling source ring.
  for j,L0 in enumerate(seam[1:]):
   Hh=holes[j];dst=np.asarray(expandedV)[Hh];src=np.asarray(expandedV)[L0]
   # preserve cuff branch input/order and wettable seam UV for exact rows
   rail=[]
   for i in range(len(L0)):
    alpha=i/len(L0)*3;k=int(alpha)%3;t=alpha-int(alpha)
    f0=(1-t)*dst[k]+t*dst[(k+1)%3]
    rail.append(append(.58*src[i]+.42*f0 + (.010+j*.008)*n,UVglobal[L0[i]]))
   zipper(L0,rail,'nested_foldback_'+str(j));zipper(rail,Hh,'nested_return_'+str(j))
  # Remaining crease hole, if any, receives a real routed thumb shell, not
  # an overlapping primitive. This is modeled open only.
  h=holes[len(seam)-1];hh=np.asarray(expandedV)[h];center=hh.mean(0)
  thumb=np.array(rig.pose.bones['thumb.01.'+side].head)
  thumb_tip=.55*thumb+.45*center+.037*n
  rib0=[append(center+.50*(p-center)+.48*(thumb_tip-center)) for p in hh]
  rib1=[append(thumb_tip+.24*(p-center)) for p in hh]
  zipper(h,rib0,'thumb_web');zipper(rib0,rib1,'thumb_opposed');face(rib1[::-1],'thumb_end')
  for other in holes[len(seam):]:face(other,'unopened_crease')
  ids=np.arange(begin,len(allnew));newscope[side]=ids
  openpatch[side]=palmface_idx
 V=np.asarray(expandedV); B=np.asarray(expandedP); OF=np.asarray(allnew,int); CF=np.asarray(cuff_tri,int)
 FF=np.concatenate([F[keep],CF,OF])
 UV=np.concatenate([form[keep],np.asarray(cuffUv),np.asarray(newuv)])
 # Load actual assembled mesh native, same donor material and source corners.
 O=bpy.data.meshes.new('C1-sewn-test-open');O.from_pydata(V.tolist(),[],FF.tolist());O.update()
 for mat0 in sm.materials:O.materials.append(mat0)
 layer=O.uv_layers.new(name=sm.uv_layers.active.name);layer.data.foreach_set('uv',UV.astype(np.float32).ravel())
 assert len(sm.materials)==1 and len(O.polygons)==len(FF)
 VV=vec(O.vertices,'co',3).astype(float)
 assert np.array_equal(VV[:len(P)],base) and np.array_equal(B[:len(P)],P)
 folded=make_bvh(VV,FF);hit=folded.overlap(BT)
 off=len(FF)-len(OF)
 skinw=np.r_[weld,np.arange(weld.max()+1,weld.max()+1+len(V)-len(P))]
 E=np.concatenate([FF[:,[0,1]],FF[:,[1,2]],FF[:,[2,0]]])
 Q=np.sort(skinw[E],axis=1);keys,cts=np.unique(Q,axis=0,return_counts=True)
 F0=make_bvh(VV,OF)
 self0=set((min(i+off,j),max(i+off,j)) for i,j in F0.overlap(folded) if i+off!=j and not np.isin(skinw[OF[i]],skinw[FF[j]]).any())
 out={'status':'HOLD_NOT_FOR_CLOSURE','original_removed_faces':int((~keep).sum()),'original_untouched_faces':int(keep.sum()),
  'full_tool_contact_pairs_including_assigned_tangent':len(hit),'all_retained_triangle_tool_pairs':sum(i<off for i,j in hit),
  'stitched_nonadjacent_self_pairs':len(self0),'closed_or_animated':False}
 for side,(_,_,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  ind=newscope[side];faces=OF[ind];sects=sections[side]
  sc=[]
  for ls in sects:
   e=np.sort(np.column_stack((ls,np.roll(ls,-1))),axis=1);ex=np.searchsorted(keys[:,0],skinw[e[:,0]])
   cnt=[]
   for a,b1 in np.sort(skinw[e],axis=1):
    look=np.flatnonzero((keys[:,0]==a)&(keys[:,1]==b1));cnt.append(0 if not len(look) else int(cts[look[0]]))
   sc.append({'vertices':len(ls),'incidence_two':cnt.count(2),'min':min(cnt),'max':max(cnt)})
  who=set((ind+off).tolist());contact=[(i,j) for i,j in hit if i in who]
  toolface=TP[T[constraints[side]['surface_face_index']]]
  pin=VV[OF[openpatch[side]]]
  sop=(pin-toolface[0])@n
  ideal=.5*np.linalg.norm(np.cross(pin[1]-pin[0],pin[2]-pin[0]))
  jj=OF[ind];orient=lambda z:np.cross(z[jj[:,1]]-z[jj[:,0]],z[jj[:,2]]-z[jj[:,0]])
  bq=orient(B);vq=orient(VV);xf=np.linalg.norm(bq,axis=1)
  area=np.linalg.norm(vq,axis=1)/np.maximum(xf,1e-20)
  rt=np.array(H.matrix)[:3,:3]@np.array(H.bone.matrix_local)[:3,:3].T
  bd=(bq@rt.T*vq).sum(1)/np.maximum(xf**2,1e-20)
  sa=np.unique(np.sort(np.concatenate([jj[:,[0,1]],jj[:,[1,2]],jj[:,[2,0]]]),axis=1),axis=0)
  edge=lambda z:np.linalg.norm(z[sa[:,1]]-z[sa[:,0]],axis=1)
  frac=edge(VV)/np.maximum(edge(B),1e-12)
  report[side]={'seams':sc,'sole_articulated_pose_depth_fixed':depth,'new_triangles':len(ind),'tool_pairs':len(contact),
   'off_band_pairs':sum(j not in ix for i,j in contact),'off_exact_face_pairs':sum(j!=constraints[side]['surface_face_index'] for i,j in contact),
   'bearing_signed_abs_max_um':float(1e6*np.abs(sop).max()),'bearing_area_mm2':float(1e6*ideal),'signed_area_fail':int(((bd<.5)|(bd>2)).sum()),
   'reversals':int((bd<=0).sum()),'edge_fail':int(((frac<.5)|(frac>2)).sum()),**takeout[side]}
 # Existing web material IDs cannot be claimed mapped by position. Store
 # actual layout ancestry and report mismatch rather than assigning bogus IDs.
 out.update(hands=report,source_left_web_ids=len(fixture['left_web_material_edges']),new_left_web_mapping_validated=False)
 # Explicit material web projection, displacement is evaluated from one
 # authored thumb-web support—not a passed retopology transfer.
 web=fixture['left_web_material_edges'];oldP=fixture['left_web_rest_vertices']
 idx=newscope['L'];idx=np.array([i for i in idx if provenance[i]=='thumb_web']);J=OF[idx]
 WB=make_bvh(B,J)
 corr=[]; bar=[]; distances=[]; mapped0=[];mapped1=[]
 for x in oldP.reshape(-1,3):
  q0,_,j,dm=WB.find_nearest(Vector(x));v=B[J[j]]
  uv0=np.linalg.pinv((v[1:]-v[0]).T)@(np.array(q0)-v[0]);bf=np.r_[1-uv0.sum(),uv0]
  corr.append(int(idx[j]));bar.append(bf);distances.append(float(dm));mapped0.append(bf@v);mapped1.append(bf@VV[J[j]])
 oldmetric=fixture['left_web_rest_lengths_m']
 bdist=np.linalg.norm(np.asarray(mapped0).reshape(-1,2,3)[:,1]-np.asarray(mapped0).reshape(-1,2,3)[:,0],axis=1)
 odist=np.linalg.norm(np.asarray(mapped1).reshape(-1,2,3)[:,1]-np.asarray(mapped1).reshape(-1,2,3)[:,0],axis=1)
 out['left_web_reprojection_negative']={'all_endpoint_count':len(corr),'max_source_to_authored_web_gap_mm':1000*float(max(distances)),
  'endpoints_gt_5mm':sum(v>.005 for v in distances),'mapped_rest_collapsed_edges':int((bdist<1e-7).sum()),
  'mapped_open_outside_reference_.5_to_2':int(((odist<.5*oldmetric)|(odist>2*oldmetric)).sum())}
 from collections import Counter,defaultdict
 out['self_local_new_role_counts']=dict(Counter(provenance[j-off] for i,j in self0 if j>=off)+Counter(provenance[i-off] for i,j in self0 if i>=off))
 # Existing exact retained UV is copied from original. Each newly cut
 # segment can carry multiple UV endpoints; report if generated seam held
 # only its first sample (rather than pretending texture continuity).
 clips=defaultdict(list)
 for row1,uv1 in zip(CF,np.asarray(cuffUv)):
  for k1,g1 in enumerate(row1):
   if g1>=len(P):clips[int(g1)].append(uv1[k1])
 out['all_untouched_UV_rows_exact']=bool(np.array_equal(UV[:int(keep.sum())],form[keep]))
 out['new_splice_multi_uv_vertex_count']=sum(bool(np.max(np.linalg.norm(np.array(xs)-xs[0],axis=1))>1e-5) for xs in clips.values())
 np.savez_compressed(p/'editable_splice.npz',new_bind=B[len(P):],new_open=VV[len(P):],new_faces=OF,clipped_source_faces=CF,
  new_corner_uv=np.asarray(newuv),clipped_source_corner_uv=np.asarray(cuffUv),source_keep=np.flatnonzero(keep),phase_face_roles=np.array(list(provenance.values())),source_left_web=fixture['left_web_material_edges'],web_authoring_face=np.asarray(corr),web_bary=np.asarray(bar),web_gap_m=np.asarray(distances),R_seam=np.concatenate(sections['R']),L_seam=np.concatenate(sections['L']))
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
