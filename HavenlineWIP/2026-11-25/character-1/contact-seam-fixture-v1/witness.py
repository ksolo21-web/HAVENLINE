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
 # Map exact source web material borders, do not relabel all edges as a
 # single invented border; preserve indexed components and lengths.
 bind=Path(os.environ['C1_BIND_EVIDENCE'])
 assert sha(bind)=='d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336'
 legacy=np.load(bind)
 assert np.array_equal(legacy['P'],P.astype(np.float32)) and np.array_equal(legacy['F'],F)
 E=np.unique(np.sort(np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]])),axis=1),axis=0)
 lengths=np.linalg.norm(P[E[:,1]]-P[E[:,0]],axis=1)
 wi=legacy['W']/1000.; num=[i for i,n in enumerate(legacy['names']) if n.endswith('.01.L')]
 lm=wi[:,num].argmax(1);wm=wi[:,num].max(1);l,r=E.T
 v=(X0>.744)&(X0<.850)&(Z0>.387)&(Z0<.503)&(Y0>.028)
 mask=v[l]&v[r]&(lengths>.00045)&(lm[l]!=lm[r])&(wm[l]>.3)&(wm[r]>.3)
 assert mask.sum()==133
 webids=np.unique(E[mask]); Wsource=E[mask]
 # Exact paired common frame; all separately preserved cuff/trim/wardrobe
 # clipped-retention decisions are geometric, not guessed by the loop count.
 base=poses(); BT=make_bvh(TP,T); old=make_bvh(base,F).overlap(BT);assert len(old)==370
 sm=skin.data; uvbase=np.empty((len(sm.uv_layers.active.data),2),np.float32)
 sm.uv_layers.active.data.foreach_get('uv',uvbase.ravel())
 loops=vec(sm.loop_triangles,'loops',3,np.int32); UVF=uvbase[loops]
 packs={};summary={};meshpatch={}
 for side,(U,Q,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  ee,aa,ww,rr,fronts,cross,far,K,C,Kloc,up=ring[side]; k,common,labels=donor[side]
  connected=[j for j,L in enumerate(fronts) if labels[weld[ee[rr[L[0]],0]]]==common]
  assert connected==([0,3,4] if side=='R' else [0,1]),connected
  # Connected cuff branches require a return with exact distal source, or
  # propose a bounded proximal join preserving them as an uncut assembly.
  # This fixture proves the branch constraint without manufacturing return topology.
  handmat=np.array(H.matrix); local=(base-handmat[:3,3])@handmat[:3,:3]
  side_mask=(-1 if side=='R' else 1)*X0>.51
  # Inner palm attachment lies on exact nominated virtual shaft facet.
  fi=constraints[side]['surface_face_index'];face=TP[T[fi]]
  bary=np.array([[.67,.20,.13],[.19,.67,.14],[.19,.20,.61]])
  q=bary@face
  assert min(bary.ravel())>0 and np.max(np.abs(bary.sum(1)-1))<1e-12
  # A small watertight backing plate exterior to the exact assigned facet.
  # It is a fixture: no claim that it is a viable hand mesh.
  mini=np.r_[q,q+.003*n]
  mt=np.array([[0,2,1],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]],int)
  def normalized_facet_offset(step):
   wr=mini+step*n
   signed=(wr-face[0])@n
   offband=sum(j not in ix for i,j in make_bvh(wr,mt).overlap(BT))
   return {'nearest_signed_face_mm':float(1000*signed.min()),'far_signed_mm':float(1000*signed.max()),'off_assigned_face_pairs':int(offband)}
  tangent=normalized_facet_offset(0.); pen=normalized_facet_offset(-.002);gap=normalized_facet_offset(.002)
  assert abs(tangent['nearest_signed_face_mm'])<.0001 and pen['nearest_signed_face_mm']<-1.99 and gap['nearest_signed_face_mm']>1.99
  rawarea=float(.5*np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0])))
  assert rawarea>1e-6
  # Visible authored open guide graph: paired crease rails from assigned
  # palm toward two actual seam landmarks plus a thumb saddle. These are
  # open landmark edges, not finished glove or pressure material.
  outer=fronts[k]; outp=C[rr[outer]]
  orient=np.array(H.matrix)[:3,:3]
  axis=orient[:,0]; span=(outp-outp.mean(0))@axis
  ic=[int(np.argmin(span)),int(np.argmax(span))]
  qcenter=q.mean(0)
  thumb=rig.pose.bones['thumb.01.'+side]; tx=np.asarray(thumb.head)
  # Fixture interior control points remain on the actual projected palm
  # half-plane, each anchored at a traced seam edge.
  roof=.5*(qcenter+outp[ic])+np.tile(.016*n,(2,1))
  crease=np.r_[outp[ic],roof,q[:2],[qcenter],[(tx+qcenter)/2+.018*n]]
  links=np.array([[0,2],[2,4],[1,3],[3,5],[4,6],[5,6],[5,7],[7,3]])
  # Geometric guard: check collar/forearm before spending on a shell.
  # Proximal original source collar controlled by cut, plus exact forearm
  # weights. If it intersects, simply holding it fixed is unsound.
  fw=W[:,lookup['forearm.'+side]]>.002
  proximal=np.flatnonzero((side_mask[F]&(~up[F])).any(1))
  retained=set(proximal.tolist())
  common_cross=np.array([i for i in cross if (labels[weld[F[i]]]==common).any()])
  all_branch_set=set(np.concatenate((proximal,common_cross)).tolist())
  hit0=[(i,j) for i,j in old if i in retained]
  broad=[(i,j) for i,j in old if fw[F[i]].any()]
  inherited=[(i,j) for i,j in old if i in all_branch_set]
  # Encode material correspondence for exact loop edges; identify every
  # source face at segment, preserving original UV parity on each row.
  all_L=[]; all_idx=[];all_t=[];all_cf=[];all_uv=[];offs=[0]
  e2f={}
  for kk in cross:
   for x,y in zip(F[kk],np.roll(F[kk],-1)):
    zz=tuple(sorted((int(x),int(y))))
    if zz not in e2f:e2f[zz]=int(kk)
  for j in connected:
   L=np.asarray(fronts[j],int);original_rows=rr[L]
   all_L.extend(C[original_rows]);all_idx.extend(ee[original_rows]);all_t.extend(aa[original_rows])
   for e0,u0 in zip(ee[original_rows],aa[original_rows]):
    ff0=e2f[tuple(e0)]; src=F[ff0]; j0=np.flatnonzero(src==e0[0])[0];j1=np.flatnonzero(src==e0[1])[0]
    all_cf.append(ff0);all_uv.append((1-u0)*UVF[ff0,j0]+u0*UVF[ff0,j1])
   offs.append(len(all_L))
  # Editable native fixture, no scene saves. Archive axis positions,
  # loop branches and topology intact as compact indexed arrays.
  ob=bpy.data.meshes.new('SeamContact-'+side)
  ob.from_pydata(mini.tolist(),[],mt.tolist());ob.update()
  checked=vec(ob.vertices,'co',3).astype(float)
  assert np.linalg.norm(checked-mini,axis=1).max()<1e-7 and len(ob.polygons)==8
  for label,x in [('bearing_patch',checked),('bearing_indices',mt),('barycentric',bary),('guide_vertices',crease),('guide_edges',links),('loop_vertices',all_L),('loop_offsets',offs),('loop_source_vertex_edges',all_idx),('loop_source_edge_t',all_t),('loop_source_faces',all_cf),('loop_source_uv',all_uv),('proximal_collision_ids',hit0),('forearm_collision_ids',broad),('compatible_shaft_face',face)]:
   packs[side+'_'+label]=np.asarray(x)
  summary[side]={'exact_shaft_face':fi,'ideal_finite_fixture_area_mm2':rawarea*1e6,'original_component_loops':connected,
   'material_correspondence_rows':len(all_L),'exact_tangent':tangent,'negative_embedded_2mm':pen,'negative_gap_2mm':gap,
   'retained_proximal_source_pairs_before_any_new_mesh':len(hit0),'full_forearm_weighted_pairs_at_compact_pose':len(broad),
   'potential_retained_branch_pairs':len(inherited),'nearest_palm_reference_to_true_patch_mm':float(1000*np.linalg.norm(base[pi]-qcenter))}
  meshpatch[side]=make_bvh(checked,mt)
 # Map all exact 133 source edges through the same original UV and pose
 # correspondence; do not invent weights/length on an unfinished replacement.
 packs['left_web_material_edges']=Wsource
 packs['left_web_rest_vertices']=P[Wsource]
 packs['left_web_open_vertices']=base[Wsource]
 packs['left_web_two_source_group_roles']=lm[Wsource]
 packs['left_web_rest_lengths_m']=lengths[mask]
 left_fit=np.linalg.norm(base[Wsource[:,1]]-base[Wsource[:,0]],axis=1)/lengths[mask]
 out={'status':'HOLD_LAYOUT_NOT_COMPLETE_NO_GLOVE_MODEL','branch_and_contact_witness':summary,
  'fixture_cross_hand_pairs':len(meshpatch['R'].overlap(meshpatch['L'])),
  'original_left_web_correspondence_edges':int(mask.sum()),'original_left_web_compact_posed_ratio_range':[float(left_fit.min()),float(left_fit.max())],
  'closed_or_animated':False,'left_web_on_new_mesh_proven':False}
 np.savez_compressed(p/'editable_seam_bearing_landmarks.npz',**packs)
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda a:a.item())+'\n');print(json.dumps(out,indent=2,default=lambda a:a.item()),flush=True)
