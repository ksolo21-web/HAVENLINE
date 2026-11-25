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
 packet=Path(os.environ['C1_ORDERED_COLLAR'])
 assert sha(packet)=='328d6675586c4d830cd4b3931426dbd4ae76ed894a9900fe27e1e7863ea4628e'
 prev=np.load(packet)
 prevF=prev['combined_local_triangles'];prevV=prev['open'];prevBind=prev['bind']
 olduv=prev['corner_uv']
 U,Q,H,*_,no,ix=sets['L']
 posed=np.array(H.matrix);rest=np.array(H.bone.matrix_local)
 W=posed[:3,:3];R=rest[:3,:3]
 unpose=lambda x:(x-posed[:3,3])@W@R.T+rest[:3,3]
 # Exterior side/back footprint extends the verified ulnar dorsal edge and
 # then joins the two exact thumb-web return edges. Only sparse fingertip
 # silhouette is formed; no circumference and no distal cuff coupling.
 dorsal=[77,80,83,84];web=[97,87,86]
 resolved=[(i,j) for rail in [dorsal,web] for i,j in zip(rail,rail[1:])]
 h0=np.asarray(rig.pose.bones['index.02.L'].head)
 h1=np.asarray(rig.pose.bones['pinky.02.L'].head)
 # Two hand-authored outer contours extending ~14mm along the measured
 # distal finger direction (established world Y in this frozen pose).
 assert h0[1]<-.44 and h1[1]<-.44
 pts=np.asarray([prevV[84]+np.array([.003,-.014,.010]),
                 prevV[83]+np.array([-.012,-.013,.034])])
 V=np.r_[prevV,pts];P0=np.r_[prevBind,unpose(pts)]
 k=len(prevV); contour=dorsal+[k,k+1]+web
 # Fixed sectional projection world Y/Z is based on exact left wrist/data,
 # not a hidden larger shape. Reject invalid physical contours before native.
 xy=1000*V[:,[1,2]]
 det=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
 ar=lambda P:0.5*sum(det(a,c) for a,c in zip(xy[P],np.roll(xy[P],-1,axis=0)))
 if ar(contour)<0:xy[:,0]*=-1
 def cross(a,b,c,d):
  s=det(b-a,c-a);t=det(b-a,d-a);u=det(d-c,a-c);v=det(d-c,b-c)
  return s*t<-1e-10 and u*v<-1e-10
 from itertools import combinations
 assert all(not cross(xy[a],xy[b],xy[c],xy[d]) for (a,b),(c,d) in combinations(zip(contour,np.roll(contour,-1)),2) if len({a,b,c,d})==4)
 faces=[];r=list(contour)
 while len(r)>3:
  for i,b0 in enumerate(r):
   a,c=r[i-1],r[(i+1)%len(r)]
   if ar([a,b0,c])<1e-7:continue
   tt=[a,b0,c]
   def contains(y):
    return min(det(xy[v]-xy[x],xy[y]-xy[x]) for x,v in zip(tt,np.roll(tt,-1)))>=-1e-9
   if any(contains(j) for j in r if j not in tt):continue
   faces.append(tt);r.pop(i);break
  else:raise ValueError('no oriented section ear')
 faces.append(r);faces=np.asarray(faces)
 assert np.isclose(sum(ar(t) for t in faces),ar(contour),atol=1e-8)
 # Directioned material chart boundaries. Existing seam UV at each source
 # corner is used, maintaining a distinct local side chart off this edge.
 lookup={}
 for tri,uv in zip(prevF,olduv):
  for i,j in ((0,1),(1,2),(2,0)):
   lookup[(int(tri[i]),int(tri[j]))]=(uv[i],uv[j])
 from collections import Counter
 ec=lambda F:Counter((int(i),int(j)) for tri in F for i,j in zip(tri,np.roll(tri,-1)))
 before=ec(prevF);after=ec(np.r_[prevF,faces])
 assert all(before[j,i]==1 and before[i,j]==0 and after[i,j]==after[j,i]==1 for i,j in resolved)
 uv=np.empty((len(faces),3,2),np.float32)
 spread=(xy[contour]-xy[contour].min(0)).ptp(0) if hasattr(np.ndarray,'ptp') and np.__version__.startswith('1.') else np.ptp(xy[contour],axis=0)
 for m,t in enumerate(faces):
  local=(xy[t]-xy[contour].min(0))/spread
  uv[m]=np.array([.39,.24])+np.array([.17,.28])*local
  pinned={}
  for i,j in ((0,1),(1,2),(2,0)):
   x,y=t[i],t[j]
   if (x,y) in resolved:
    q1,q0=lookup[y,x]
    for index,z in ((i,q0),(j,q1)):
     if index in pinned:assert np.array_equal(pinned[index],z)
     pinned[index]=z
  for i,z in pinned.items():uv[m,i]=z
 # Full unchanged prior local mesh + actual attached side sheet.
 both=np.r_[prevF,faces];uc=np.r_[olduv,uv]
 mat=bpy.data.meshes.new('C1_L_outer_side_open_diagnostic')
 mat.from_pydata(V.tolist(),[],both.tolist());mat.update()
 for own in skin.data.materials:mat.materials.append(own)
 uvL=mat.uv_layers.new(name='Exact source seams and new sparse side chart')
 uvL.data.foreach_set('uv',uc.astype(np.float32).ravel())
 Vn=vec(mat.vertices,'co',3).astype(float)
 assert np.array_equal(Vn[:len(prevV)],prevV)
 # Check native all contacts across combined old+new against exact retained
 # wardrobe/forearm and original tool. Only source assigned bearing allowed.
 base=poses()
 pp=(Path(os.environ['C1_LEFT_DISTAL_DATA'])/'editable_left_join.npz')
 assert sha(pp)=='c809dabd740a5cacab7ce5dff68b7fc50a5cde0f3c378ec6a9673a9eb1e0de6a'
 plan=np.load(pp)
 retV=np.r_[base,plan['open_additions']]
 retF=np.r_[F[plan['retained_source_faces']],plan['clipped_left_source_faces']]
 rBV=make_bvh(retV,retF);tool=make_bvh(TP,T)
 nBV=make_bvh(Vn,faces);full=make_bvh(Vn,both)
 pp=Path(os.environ['C1_LEFT_COARSE_DATA'])
 assert sha(pp)=='bf3d6ae3a13f6160ab3f3cacbaca8d7891ffcf01f8c56ecd53275c63f2f0877e'
 targets=np.load(pp)
 nested=make_bvh(targets['nested_open'],targets['nested_tri'])
 pp=Path(os.environ['C1_INTRINSIC_PANELS'])
 assert sha(pp)=='6d9aae39e114ba17d0a30801293278e95a0bd9a4ec0126bbec1a9d2e366575d0'
 rr=np.load(pp)
 outer=make_bvh(rr['L_0_open'],rr['L_0_indices'])
 allpaired={(min(i,j),max(i,j)) for i,j in full.overlap(full) if i!=j and not np.isin(both[i],both[j]).any()}
 rook=tool.overlap(nBV);total=full.overlap(tool)
 fid=constraints['L']['surface_face_index']
 def norm(a,f):return np.cross(a[f[:,1]]-a[f[:,0]],a[f[:,2]]-a[f[:,0]])
 NA=norm(Vn,faces);NR=norm(P0,faces)@(W@R.T).T
 d=(NR*NA).sum(1)/np.maximum((NR*NR).sum(1),1e-20)
 E=np.unique(np.sort(np.r_[faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]],axis=1),axis=0)
 el=lambda a:np.linalg.norm(a[E[:,1]]-a[E[:,0]],axis=1)
 dr=el(Vn)/np.maximum(el(P0),1e-12)
 # Neutral mesh independently checked against retained donor and itself.
 nb=make_bvh(P0,both);no0=make_bvh(P0,faces)
 neutralSource=np.r_[P,plan['bind_additions']]
 ns=make_bvh(neutralSource,retF)
 na=nb.overlap(nb)
 nse={(min(i,j),max(i,j)) for i,j in na if i!=j and not np.isin(both[i],both[j]).any()}
 # Negative witness pierces one actual selected nonadjacent surface,
 # confirms coplanar BVH is not the only sensitive test.
 tri=Vn[faces[int(np.argmax(np.linalg.norm(NA,axis=1)))]]
 w=tri.mean(0);u=unit(tri[0]-tri[1]);n=unit(np.cross(tri[1]-tri[0],tri[2]-tri[0]))
 ref=np.stack([w-.001*n-.0001*u,w+.001*n-.0001*u,w+.0002*u])
 neg=len(make_bvh(ref,np.array([[0,1,2]])).overlap(nBV))
 assert neg>0
 exactP=prev['bearing_vertex_indices'];diag=(Vn[exactP]-TP[T[fid]][0])@no
 out={'status':'HOLD_UNTIL_LOCAL_CLEAR_AND_FULL_GLOVE_SEPARATE','new_faces':len(faces),'actual_joined_faces':len(both),'exact_two_face_directed_seams':len(resolved),
  'minimum_section_area_mm2':float(min(ar(t) for t in faces)),'exact_old_geometry_and_material_uv_preserved':True,
  'new_offband_or_not_exact':sum(j not in ix or j!=fid for j,i in rook),'new_tool_pairs':len(rook),'combined_exact_bearing_pairs':sum(j==fid for i,j in total),
  'combined_offband_pairs':sum(j not in ix for i,j in total),'combined_other_tool_faces':sum(j!=fid for i,j in total),
  'bearing_signed_error_m':float(np.abs(diag).max()),'new_retained_source_pairs':len(nBV.overlap(rBV)),'combined_retained_source_pairs':len(full.overlap(rBV)),
  'new_nested_pairs':len(nBV.overlap(nested)),'new_near_rail_pairs':len(nBV.overlap(outer)),
  'combined_open_nonadjacent_pairs':sorted(allpaired),'combined_rest_nonadjacent_pairs':sorted(nse),'new_neutral_retained_pairs':len(no0.overlap(ns)),
  'signed_face_fail':int(((d<.5)|(d>2.)).sum()),'edge_fail':int(((dr<.5)|(dr>2.)).sum()),'reversals':int((d<=0).sum()),
  'negative_transverse_pairs':neg,'full_glove_or_closure':False,'right_unchanged':True}
 np.savez_compressed(p/'editable_left_side.npz',bind=P0,open=Vn,combined_tri=both,outer_tri=faces,corner_uv=uc,author_contour=contour,
  source_open_dorsal_path=dorsal,source_open_web=web,source_exact_pressure=exactP,side_atlas_chart_mm=xy)
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
