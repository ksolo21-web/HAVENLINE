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
 path=Path(os.environ['C1_DISTAL_TIP_DATA'])
 assert sha(path)=='1507f8e1fc51ced1c4cc0bfe9b4873ab1ed5cb097385b76e4ad437e625b8da61'
 donor=np.load(path)
 tri=donor['combined_tri'].copy();oldtri=tri.copy()
 uc=donor['corner_uv'].copy();oldUV=uc.copy()
 assert tri[[116,117]].tolist()==[[95,100,99],[95,99,84]]
 newc=np.array([[95,100,84],[100,99,84]])
 # These two same-chart faces use identical samples at both ends of the
 # old internal diagonal. Boundary UV on these four vertices is exact.
 chart={}
 for j0 in (116,117):
  for j,u in zip(tri[j0],uc[j0]):
   if j in chart:assert np.array_equal(chart[j],u)
   chart[j]=u.copy()
 tri[[116,117]]=newc
 for j in (116,117):uc[j]=[chart[i] for i in tri[j]]
 unmodified=np.ones(len(tri),bool);unmodified[[116,117]]=False
 assert np.array_equal(tri[unmodified],oldtri[unmodified]) and np.array_equal(uc[unmodified],oldUV[unmodified])
 from collections import Counter
 def directed(F):return Counter((int(x),int(y)) for f in F for x,y in zip(f,np.roll(f,-1)))
 def outside(F):return {e for e,c in directed(F).items() if c and not directed(F)[e[::-1]]}
 # O(n^2) trivial at 120 only, useful as independent orientation boundary check.
 a=directed(tri);d=directed(oldtri)
 assert {e for e,c in a.items() if c and not a[e[::-1]]}=={e for e,c in d.items() if c and not d[e[::-1]]}
 assert a[100,84]==a[84,100]==1 and not a[95,99] and not a[99,95]
 outline=donor['author_boundary'];assert all(a[i,j]==a[j,i]==1 for i,j in zip(outline,np.roll(outline,-1)))
 V=donor['open'];PB=donor['bind'];U,Q,H,*_,no,ix=sets['L'];matrix=np.array(H.matrix)[:3,:3];rest=np.array(H.bone.matrix_local)[:3,:3]
 def native(name,positions):
  bm=bpy.data.meshes.new(name)
  bm.from_pydata(positions.tolist(),[],tri.tolist());bm.update()
  for m in skin.data.materials:bm.materials.append(m)
  tex=bm.uv_layers.new(name='Exact donor chart with single internal flip')
  tex.data.foreach_set('uv',uc.astype(np.float32).ravel())
  uvread=np.empty(uc.size,np.float32);tex.data.foreach_get('uv',uvread)
  assert np.array_equal(uvread.reshape(uc.shape),uc)
  return vec(bm.vertices,'co',3).astype(float)
 vn=native('Ltip-open-diagonal',V);bn=native('Ltip-neutral-diagonal',PB)
 assert np.array_equal(vn,V) and np.array_equal(bn,PB.astype(np.float32))
 def nonadj(tree,F):
  return sorted({tuple(sorted((i,j))) for i,j in tree.overlap(tree) if i!=j and not np.isin(F[i],F[j]).any()})
 beforeV=make_bvh(V,oldtri);beforeB=make_bvh(PB,oldtri)
 assert nonadj(beforeV,oldtri)==nonadj(beforeB,oldtri)==[(82,116)]
 opened=make_bvh(vn,tri);closed=make_bvh(bn,tri)
 tp=make_bvh(TP,T);hits=opened.overlap(tp)
 fx=constraints['L']['surface_face_index']
 exact=donor['exact_pressure_source']
 signed_contact=(vn[exact]-TP[T[fx]][0])@no
 # Compare whole unchanged local area against exact retained material.
 source=poses()
 previous=np.load((Path(os.environ['C1_LEFT_DISTAL_DATA'])/'editable_left_join.npz'))
 f0=np.r_[F[previous['retained_source_faces']],previous['clipped_left_source_faces']]
 whole=make_bvh(np.r_[source,previous['open_additions']],f0)
 wholeB=make_bvh(np.r_[P,previous['bind_additions']],f0)
 nr=np.load(Path(os.environ['C1_LEFT_COARSE_DATA']))
 n0=make_bvh(nr['nested_open'],nr['nested_tri']);n1=make_bvh(nr['nested_bind'],nr['nested_tri'])
 rs=np.load(Path(os.environ['C1_INTRINSIC_PANELS']))
 r0=make_bvh(rs['L_0_open'],rs['L_0_indices']);r1=make_bvh(rs['L_0_bind'],rs['L_0_indices'])
 # Tested new face interactions with separate rails not just prior shape.
 newV=make_bvh(vn,newc);newB=make_bvh(bn,newc)
 normal=lambda x,f:np.cross(x[f[:,1]]-x[f[:,0]],x[f[:,2]]-x[f[:,0]])
 nB=normal(bn,tri)@(matrix@rest.T).T;nO=normal(vn,tri)
 ratio=(nB*nO).sum(1)/np.maximum((nB*nB).sum(1),1e-24)
 ed=np.unique(np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1),axis=0)
 dist=lambda a:np.linalg.norm(a[ed[:,1]]-a[ed[:,0]],axis=1)
 ratioe=dist(vn)/np.maximum(dist(bn),1e-20)
 rows=(np.arange(len(tri))>=112);ce=ed[(np.isin(ed,tri[112:]).all(1))]
 z=lambda a:np.linalg.norm(a[ce[:,1]]-a[ce[:,0]],axis=1)
 rz=z(vn)/np.maximum(z(bn),1e-20)
 report={'exact_bounded_case':'local native diagonal only; whole glove hold','changed_faces':np.where(~unmodified)[0].tolist(),
  'to_faces':newc.tolist(),'preserved_vertices_every_pose':True,'preserved_all_unchanged_faces_and_corner_uv':True,
  'old_known_crossing_native_each_pose':[82,116],'open_nonadjacent_pairs':nonadj(opened,tri),'neutral_nonadjacent_pairs':nonadj(closed,tri),
  'assigned_contact_pairs':sum(j==fx for i,j in hits),'off_band':sum(j not in ix for i,j in hits),'other_shaft_faces':sum(j!=fx for i,j in hits),
  'new_two_faces_tool_pairs':len(newV.overlap(tp)), 'signed_contact_error_m':float(np.max(np.abs(signed_contact))),
  'native_open_combined_retained_pairs':len(opened.overlap(whole)),'native_neutral_combined_retained_pairs':len(closed.overlap(wholeB)),
  'new_near_rail_open_neutral_pairs':[len(newV.overlap(r0)),len(newB.overlap(r1))],'new_nested_open_neutral_pairs':[len(newV.overlap(n0)),len(newB.overlap(n1))],
  'distal_signed_area_fail':int(((ratio[rows]<.5)|(ratio[rows]>2.)).sum()),'distal_signed_reversals':int((ratio[rows]<=0.).sum()),
  'distal_edge_ratio_fail':int(((rz<.5)|(rz>2.)).sum()),'distal_face_ratio_range':[float(ratio[rows].min()),float(ratio[rows].max())],
  'new_diagonal_endpoints':[100,84],'right_or_close':False}
 np.savez_compressed(p/'editable_left_tip_flip.npz',bind=PB,open=V,combined_tri=tri,corner_uv=uc,
  author_boundary=outline,exact_pressure_source=exact,original_locked_outer_edges=donor['outer_locked_edges'])
 (p/'result.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(report,indent=2,default=lambda x:x.item()),flush=True)
