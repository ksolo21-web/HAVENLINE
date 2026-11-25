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
 path=Path(os.environ['C1_LEFT_COARSE_DATA'])
 assert sha(path)=='bf3d6ae3a13f6160ab3f3cacbaca8d7891ffcf01f8c56ecd53275c63f2f0877e'
 sparse=np.load(path)
 fp=Path(os.environ['C1_INTRINSIC_PANELS'])
 assert sha(fp)=='6d9aae39e114ba17d0a30801293278e95a0bd9a4ec0126bbec1a9d2e366575d0'
 rails=np.load(fp)
 U,Q,H,_,_,_,_,_,_,_,no,ix=sets['L'];Hp=np.array(H.matrix);Hb=np.array(H.bone.matrix_local)
 right=np.asarray(Hp[:3,:3]);rest=np.asarray(Hb[:3,:3])
 unpose=lambda z:(z-Hp[:3,3])@right@rest.T+Hb[:3,3]
 faceid=constraints['L']['surface_face_index']
 contact=sparse['locked_left_bearing'];target=TP[T[faceid]]
 q=contact.mean(0);dx=unit(contact[1]-contact[0]);dy=unit(np.cross(no,dx))
 assert (no@(contact-target[0]).T).max()<1e-10
 dor=sparse['sewn_dorsal_open'];dorb=sparse['sewn_dorsal_bind'];D=sparse['sewn_dorsal_faces']
 A=np.array([85,82,79]);assert np.max(A)<len(dor)
 wa=sparse['directional_left_web_open'];wb=sparse['directional_left_web_bind']
 # Widened physical thenar wings are authored in measured facet axes;
 # they stay exterior to the assigned surface and away from nested cuff.
 def wing(x,y,n):return q+.001*(x*dx+y*dy+n*no)
 wings=np.array([wing(-37,-25,30),wing(47,-34,25),wing(92,49,40)])
 W=len(dor);g=len(wa)
 v=np.r_[dor,wa,wings,contact]
 bind=np.r_[dorb,wb,unpose(wings),unpose(contact)]
 # Outer order oppositely traverses original dorsal and actual 4-point web.
 outer=np.array([85,82,79,W+g,W+g+1,W,W+3,W+2,W+1,W+g+2])
 inner=np.arange(len(v)-3,len(v)); ar=np.r_[outer,inner]
 # Explicit widened sewing chart. Sparse boundary section references
 # physically widening thenar. Chart independence avoids translating the
 # earlier dense shell's angular strip topology.
 theta=np.linspace(0,2*np.pi,len(outer),endpoint=False)
 chart=np.r_[np.c_[.10*np.cos(theta),.077*np.sin(theta)],[[.020,-.012],[-.018,-.015],[-.004,.017]]]
 from scipy.spatial import Delaunay
 tri0=Delaunay(chart).simplices
 def signed2(x):
  y=x[1]-x[0];z=x[2]-x[0];return y[0]*z[1]-y[1]*z[0]
 for tt in tri0:
  if signed2(chart[tt])<0:tt[[1,2]]=tt[[2,1]]
 assert all(signed2(chart[tt])>0 for tt in tri0)
 fi0=[j for j,t in enumerate(tri0) if set(t)==set(range(len(outer),len(outer)+3))]
 assert len(fi0)==1
 cfi=int(fi0[0]); new=ar[tri0]
 Wf=sparse['directional_left_web_tri']+W
 def dir_counts(F):
  from collections import Counter
  return Counter((int(a),int(b)) for x in F for a,b in zip(x,np.roll(x,-1)))
 C=dir_counts(new)
 for i,j in zip(outer,np.roll(outer,-1)): assert C[int(i),int(j)]==1
 for i,j in zip(new[cfi],np.roll(new[cfi],-1)):
  assert C[(int(i),int(j))]==C[(int(j),int(i))]==1
 SD=dir_counts(D);SW=dir_counts(Wf)
 assert all(SD[int(j),int(i)]==1 for i,j in zip(A,A[1:]))
 assert all(SW[int(j+W),int(i+W)]==1 for i,j in ((0,3),(3,2),(2,1)))
 # Native held union: range of fully retained source shell from exact left
 # stitch. Right stays completely original. New panels do not take credit
 # for nearby touching triangles of a different held mesh.
 joint_path=Path(os.environ['C1_LEFT_DISTAL_DATA'])/'editable_left_join.npz'
 assert sha(joint_path)=='c809dabd740a5cacab7ce5dff68b7fc50a5cde0f3c378ec6a9673a9eb1e0de6a'
 parent=np.load(joint_path)
 source_org=poses();base=np.r_[source_org,parent['open_additions']]
 bodyf=np.r_[F[parent['retained_source_faces']],parent['clipped_left_source_faces']]
 BT=make_bvh(TP,T);BB=make_bvh(base,bodyf)
 BD=make_bvh(dor,D)
 NC=sparse['nested_open'];NF=sparse['nested_tri'];BN=make_bvh(NC,NF)
 L0=rails['L_0_open'];L0f=rails['L_0_indices'];BC=make_bvh(L0,L0f)
 joined=np.r_[D,Wf,new]
 nm=bpy.data.meshes.new('Left palmar stitched local');nm.from_pydata(v.tolist(),[],joined.tolist());nm.update()
 for mt in skin.data.materials:nm.materials.append(mt)
 # Sparse owned atlas, native preview basis. Previously audited dorsal near
 # corners stay exact. Deliberate border charts use separate new UV rail.
 charts=np.empty((len(joined),3,2),np.float32)
 charts[:len(D)]=.5
 prevuv=sparse['proximal_source_split_uv'];charts[:len(prevuv)]=prevuv
 charts[len(D):len(D)+len(Wf)]=np.array([[[.12,.34],[.18,.38],[.18,.31]],[[.18,.38],[.24,.36],[.18,.31]]])
 charts[-len(new):]=.35+chart[tri0]*2.
 nativeUV=nm.uv_layers.new(name='Original material; split diagnostic atlas');nativeUV.data.foreach_set('uv',charts.ravel())
 V=vec(nm.vertices,'co',3).astype(float)
 assert np.array_equal(V[:len(dor)],dor.astype(np.float32))
 X=make_bvh(V,new); BV=make_bvh(V,joined)
 hits=X.overlap(BT)
 selfJ={(min(len(D)+len(Wf)+i,j),max(len(D)+len(Wf)+i,j)) for i,j in X.overlap(BV) if len(D)+len(Wf)+i!=j and not np.isin(new[i],joined[j]).any()}
 sN=lambda A,F:np.cross(A[F[:,1]]-A[F[:,0]],A[F[:,2]]-A[F[:,0]])
 nb=sN(bind,new)@(right@rest.T).T;nn=sN(V,new)
 den=(nb*nb).sum(1);ratio=(nb*nn).sum(1)/np.maximum(den,1e-20)
 ee=np.unique(np.sort(np.r_[new[:,[0,1]],new[:,[1,2]],new[:,[2,0]]],axis=1),axis=0)
 elen=lambda x:np.linalg.norm(x[ee[:,1]]-x[ee[:,0]],axis=1)
 er=elen(V)/np.maximum(elen(bind),1e-12)
 def diag(shift):return (V[new[cfi]]+shift*no-target[0])@no
 sd=diag(0.);nd=diag(-.002);gap=diag(.002)
 assert nd.max()<-.00199 and gap.min()>.00199
 # Native material atlas leaves absolute distant texture atlas unapproved.
 # All three pressure edges + both dorsal & three web edges are actual
 # indexed two-face seams in the local piece.
 dd=dir_counts(joined)
 assert all(dd[int(i),int(j)]==dd[int(j),int(i)]==1 for i,j in zip(new[cfi],np.roll(new[cfi],-1)))
 assert all(dd[int(i),int(j)]==dd[int(j),int(i)]==1 for i,j in zip(A,A[1:]))
 assert all(dd[int(i+W),int(j+W)]==dd[int(j+W),int(i+W)]==1 for i,j in [(0,3),(3,2),(2,1)])
 out={'status':'HOLD_LOCAL_AUTHORED_PALMAR_BRIDGE','bridge_triangle_count':len(new),'dorsal_two_shared_edges':2,
  'thumb_web_three_shared_edges':3,'pressure_all_three_shared_edges':3,'whole_local_join_triangles':len(joined),
  'inherited_dorsal_uv_exact_rows':bool(np.array_equal(charts[:len(prevuv)],prevuv.astype(np.float32))),
  'distal_color_and_uv_placement_unapproved':True,'exact_per_pose_four_web_points':float(np.linalg.norm(V[W:W+4]-wa,axis=1).max()),
  'explicit_pressure_area_mm2':float(5e5*np.linalg.norm(nn[cfi])),
  'signed_actual_contact_um':(1e6*sd).tolist(),'embedded_negative_mm':float(nd.max()*1000),'gapped_negative_mm':float(gap.min()*1000),
  'left_new_offband_pairs':sum(j not in ix for i,j in hits),'other_shaft_faces_pairs':sum(j!=faceid for i,j in hits),
  'positive_assigned_all_pairs':sum(j==faceid for i,j in hits),'retained_whole_body_pairs':len(X.overlap(BB)),
  'nested_cuff_pairs':len(X.overlap(BN)),'near_outer_source_rail_pairs':len(X.overlap(BC)),
  'new_joint_nonadjacent_pairs':len(selfJ),'signed_face_fail':int(((ratio<.5)|(ratio>2.)).sum()),'orientation_reversals':int((ratio<=0.).sum()),
  'edge_ratio_fail':int(((er<.5)|(er>2.)).sum()),'original_right_unchanged':True,'closure':False}
 from collections import Counter
 def region(i):
  return 'dorsal' if i<len(D) else 'web' if i<len(D)+len(Wf) else 'bearing' if i==len(D)+len(Wf)+cfi else 'bridge'
 out['nonadjacent_pair_regions']=dict(Counter('/'.join(sorted((region(i),region(j)))) for i,j in selfJ))
 out['nonadjacent_exact_index_pairs']=sorted(list(selfJ))
 np.savez_compressed(p/'editable_thenar_join.npz',bind=bind,open=V,faces=joined,chart_xy=chart,local_bridge_faces=new,uv_per_corner=charts,
  bridge_authority_vertex_ids=ar,actual_pressure_triangle=new[cfi],source_web_vertices=np.arange(W,W+4),source_dorsal_authority_path=A)
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
