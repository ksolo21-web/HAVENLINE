"""Exact C1 cold grip pose replay with read-only geometry ray evidence, no render."""
import bpy,hashlib,math,numpy as np,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree
from collections import Counter
p=Path(__file__).resolve().parent;b=p.parent
pin=b/'hvn-t09-narrow-ready-witness.yFldwO'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(pin/'SHA256SUMS')=='ccd17840ef942d61ba891958a50c7dcfe4b1f9a9263280667ce9dabb50c389d7'
for row in (pin/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(maxsplit=1);assert sha(pin/n)==h
assert sha(b/'c1-full-detail-rig-witness-repair-v2/c1-full-detail-rig-weight-repair-v2.blend')=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert sha(b/'c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb')=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
g=b/'c1-v2-axe-static-witness-v1/axe.glb'
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
 parent=b/'hvn-l1-c1-axe-glove-topology-v1/SHA256SUMS';assert sha(parent)=='b0121718e7e10610220e77dc752de6af3cadee3ab46390a131110d575de38e02'
 for row in parent.read_text().splitlines():
  hh,nn=row.split(maxsplit=1);assert sha(parent.parent/nn)==hh
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
 def packet(name,seal):
  d=b/name;ms=d/'SHA256SUMS';assert sha(ms)==seal
  for line in ms.read_text().splitlines():
   h,f=line.split(maxsplit=1);assert sha(d/f)==h
  return d
 s=packet('hvn-l1-c1-thumb-web-fairing-v1','c4d971587ac27ada549249fbeedd3f3b6e0f58448aaa027a96b6eb4b69711be3')
 railp=packet('hvn-l1-c1-intrinsic-sewing-v1','ea685b7d29314c7ce84d0d1a6bf050028b2786459313cf4115c3072f718ce416')
 pp=packet('hvn-l1-c1-left-distal-glove-v1','570ae531b64054da51d56b1571b1934a86deafd9c7d5fdfad4c8481cc8ca1ca0')
 cp=packet('hvn-l1-c1-left-coarse-sections-v1','3c059bdf29e6f300e2255dc89e1c332dadcbd46f702951373a12719efd4b12cc')
 q=np.load(s/'editable_thumb_web_fairing.npz')
 rail=np.load(railp/'editable_intrinsic_panels.npz');prev=np.load(pp/'editable_left_join.npz')
 coarse=np.load(cp/'editable_left_coarse.npz')
 import gzip
 locked_receipts=json.loads((s/'qualification_readback.json').read_text())['physical_candidate_first_pass_not_a_source_approval']
 locked_hash=sha(s/'qualification_readback.json')
 archived=json.loads(gzip.decompress((s/'native_rays.json.gz').read_bytes()))
 row_ids=np.r_[q['original_face_ids'],q['new_face_ids']]
 def near(tree,X):
  p,n,i,d=tree.find_nearest(Vector(X));return np.array(p,dtype=float),unit(np.array(n,dtype=float)),int(i),float(d)
 def point_uv(X,T):
  uv=np.linalg.lstsq((T[1:]-T[0]).T,X-T[0],rcond=None)[0]
  return np.r_[1-uv.sum(),uv]
 def hit(tree,X,dir):
  x,n,i,d=tree.ray_cast(Vector(X+3.*dir),Vector(-dir),3.15)
  return None if i is None else (np.asarray(x,dtype=float),np.asarray(n,dtype=float),int(i),float(d))
 def hit_info(h):
  if h is None:return None
  x,n,i,d=h
  return {'point':x.tolist(),'normal':n.tolist(),'row':i,'distance_m':d}
 def true_bones(rest):
  return {k: np.array([(getattr((rig.data.bones if rest else rig.pose.bones)[z+'.L'],
                          'head_local' if rest else 'head')) for z in v],dtype=float)
   for k,v in {'thumb':['thumb.01','thumb.02','thumb.03'],'index':['index.01','index.02','index.03'],'neighbor_middle':['middle.01','middle.02','middle.03']}.items()}
 rest_b=true_bones(True); hold_b=true_bones(False)
 def web(bone):
  root,t=bone['thumb'][:2]; i=bone['index'][0]; mid=bone['neighbor_middle'][0]
  return np.stack([root+.6*(t-root),.44*t+.56*i,.76*i+.24*mid,root*.5+i*.5])
 W0,W1=web(rest_b),web(hold_b)
 assert np.array_equal(W0,rail['left_web_bind_anchors'])
 assert np.max(np.linalg.norm(W1-rail['left_web_open_anchors'],axis=1))<1e-6
 O0=make_bvh(P,F); O1=make_bvh(base,F)
 # The same exact material/source triangle IDs are used in both phases. The
 # four rig-supported landmarks label a neutral material branch once; held
 # replay transforms its points, never reassigns a thumb by nearest pose.
 tag=['thumb_proximal_crease','thumb_index_web_ridge','index_proximal_crease','thenar_return']
 anchors=[near(O0,w) for w in W0]
 anchor_ids=[z[2] for z in anchors]
 assert anchor_ids==[712839,713901,715333,714095]
 # Material-topology graph: faces sharing actual two-coordinate welded edges
 # near the left palm/hand, never joining authored shapes or crossing points.
 # ROI is purely a graph bound. Every admission ray uses the full owner BVH.
 o_roi=np.flatnonzero((P[F,0]>.69).all(1))
 owner_bound=F[o_roi]
 ow=weld[owner_bound]
 from collections import defaultdict,Counter,deque
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import dijkstra
 graphs=defaultdict(list)
 for j,f in enumerate(ow):
  for i,k in [(0,1),(1,2),(2,0)]:
   if f[i]!=f[k]:graphs[tuple(sorted((int(f[i]),int(f[k]))))].append(j)
 subidx={int(v):j for j,v in enumerate(o_roi)}
 G={j:set() for j in range(len(o_roi))}
 for vv in graphs.values():
  if len(vv)==2:
   a,c=vv;G[a].add(c);G[c].add(a)
 C=P[owner_bound].mean(1)
 X=np.asarray([(a,c) for a,v in G.items() for c in sorted(v)])
 inv=coo_matrix((np.linalg.norm(C[X[:,0]]-C[X[:,1]],axis=1),(X[:,0],X[:,1])),shape=(len(C),len(C))).tocsr()
 need_idx=[subidx[a] for a in anchor_ids]
 dist,pred=dijkstra(inv,indices=need_idx,return_predecessors=True)
 def route(a,j):
  p=[j]
  while p[-1]!=need_idx[a]:
   assert pred[a,p[-1]]>=0
   p.append(int(pred[a,p[-1]]))
  return p[::-1]
 # Three intrinsic paths confirm all four anatomical anchors through the
 # thumb-to-index ridge. Bound branch support by 6mm from these paths (not
 # arbitrary target-driven selection) and explicitly report disconnected IDs.
 loops=[route(0,need_idx[1]),route(1,need_idx[2]),route(1,need_idx[3])]
 poly=set(sum(loops,[]))
 support=dijkstra(inv,indices=sorted(poly),min_only=True)
 branch_reg=set(int(o_roi[i]) for i in np.where(support<=.006)[0])
 assert all(a in branch_reg for a in anchor_ids)
 def branch_side(P0,i):
  t=P0[F[i]];return unit(np.cross(t[1]-t[0],t[2]-t[0]))
 anchor_authority=[]
 for name,a,(x,n,i,d0) in zip(tag,W0,anchors):
  bc=point_uv(x,P[F[i]])
  assert np.linalg.norm(bc@P[F[i]]-x)<1e-7 and bc.min()>-1e-4
  anchor_authority.append({'role':name,'native_row':i,'projected_neutral':x.tolist(),'bind_3d_gap_mm':d0*1000,
    'held_same_material_point':(bc@base[F[i]]).tolist(),'held_landmark_gap_mm':float(np.linalg.norm(bc@base[F[i]]-W1[tag.index(name)])*1000),
    'material_barycentric':bc.tolist()})
 diagnostics={}
 all_tests={}
 incidence=np.r_[F[prev['retained_source_faces']],prev['clipped_left_source_faces']]
 for phase,stock,full_tree,points,local,rail_pose,ns,anatom in [
     ('neutral',P,O0,np.r_[P,prev['bind_additions']],q['bind'],rail['L_0_bind'],coarse['nested_bind'],rest_b),
     ('open',base,O1,np.r_[base,prev['open_additions']],q['open'],rail['L_0_open'],coarse['nested_open'],hold_b)]:
  t=[('full_local',make_bvh(local,q['combined_faces'])),('retained',make_bvh(points,incidence)),
     ('rail',make_bvh(rail_pose,rail['L_0_indices'])),('nested',make_bvh(ns,coarse['nested_tri']))]
  raw_cut=locked_receipts[phase]['source_direction_failed_by_farther_original_skin']
  assert len(raw_cut)==(11 if phase=='neutral' else 6)
  test={}
  axis=unit(np.cross(anatom['thumb'][1]-anatom['thumb'][0],anatom['index'][0]-anatom['thumb'][0]))
  for c in raw_cut:
   row=c['candidate_row'];slot=c['sample_slot'];cc=archived[phase]['new_exact_test'][str(row)][slot]
   assert cc['owner_first_valid']==c['owner_first_valid']==False
   i=int(c['original_native_nearest_face_row']);lo=int(c['original_native_outward_first_hit']['face_row'])
   assert int(cc['original_native_outward_first_hit']['face_row'])==lo
   # Retain the archived 17 original rows and flags; do not reinterpret them.
   # Deterministic alternate source witnesses use only owner-side materials:
   # exact branch facet, its directly edge-adjacent facets, and bone-derived
   # thumb/index plane directions. Full native mesh validates each trial.
   on_branch=i in branch_reg
   if on_branch:
    ii=subidx[i]
    fan=[i]+[int(o_roi[x]) for x in sorted(G[ii]) if int(o_roi[x]) in branch_reg]
    ref_norms=np.asarray([branch_side(stock,l) for l in fan])
    mean_dir=unit(ref_norms.mean(0))
    side_axis=axis if mean_dir@axis>=0 else -axis
    # Fixed visibility directions; selecting rows does not reference the
    # candidate's result. Both direct bone side and blends are tested.
    family=[('branch_facet_fan_mean',mean_dir),
            *[(f'branch_to_bone_side_{weight:.2f}',unit(mean_dir*(1-weight)+side_axis*weight)) for weight in (.25,.50,.75)],
            ('true_bone_plane_side',side_axis)]
   else:
    fan=[];family=[]
   z=np.asarray(c['original_native_nearest_position_m'])
   x=np.asarray(c['tested_point'])
   vv=local[q['combined_faces'][np.flatnonzero(row_ids==row)[0]]]; n=unit(np.cross(vv[1]-vv[0],vv[2]-vv[0]))
   notes=[]
   for name,u in family:
    fz=hit(full_tree,z,u);fx=hit(full_tree,x,u)
    # Local source must be physically first in the full owner scene both at
    # the exact anatomical point and along the separate candidate target ray.
    # Referring to owner-only first-hit locations does not alter the 18mm,
    # .25 reference-facing condition, or the candidate >.3 condition.
    def admitted(h):
     return bool(h is not None and h[2] in branch_reg and np.linalg.norm(h[0]-z)<.018 and h[1]@u>.25)
    H=[]
    for part,tree in t:
     h=hit(tree,x,u)
     if h is not None:H.append((part,h))
    f_c=min(H,key=lambda a:a[1][-1]) if H else None
    cid=int(row_ids[f_c[1][2]]) if f_c and f_c[0]=='full_local' else None
    can_exact=bool(cid==row and np.linalg.norm(f_c[1][0]-x)<.0001 and n@u>.3)
    notes.append({'direction_named_rule':name,'direction':u.tolist(),'full_owner_reference_origin_first':hit_info(fz),
       'full_owner_candidate_origin_first':hit_info(fx),'original_branch_visibility_admitted':admitted(fz),
       'candidate_line_native_reference_admitted':admitted(fx),
       'candidate_first':[f_c[0],hit_info(f_c[1]),cid] if f_c else None,'candidate_same_front':can_exact,'candidate_outward_dot':float(n@u),
       'source_ref_and_candidate_admitted':admitted(fz) and admitted(fx) and can_exact})
   test[f'{row}:{slot}']={'exact_original_failed_and_unchanged':True,'unchanged_original_first_occluder':lo,
        'source_face':i,'source_face_in_immutable_anatomical_branch':on_branch,'fan_rows':fan,
        'geo_distance_to_landmark_paths_mm':float(support[subidx[i]]*1000) if i in subidx else None,
        'separate_supplement_attempts':notes}
  all_tests[phase]=test
  diagnostics[phase]={'historical_original_gate_failed_count_still':len(raw_cut),
       'source_target_rows_bound_to_branch':sum(x['source_face_in_immutable_anatomical_branch'] for x in test.values()),
       'source_only_unoccluded_support_samples':sum(any(y['original_branch_visibility_admitted'] for y in x['separate_supplement_attempts']) for x in test.values()),
       'separate_joint_source_and_candidate_support_samples':sum(any(y['source_ref_and_candidate_admitted'] for y in x['separate_supplement_attempts']) for x in test.values()),
       'sample_keys_missing_candidate_link':sorted(k for k,x in test.items() if not any(y['source_ref_and_candidate_admitted'] for y in x['separate_supplement_attempts']))}
 A={'status':'SEPARATE_SUPPLEMENTAL_BRANCH_WITNESS_NO_HISTORICAL_FLAGS_CHANGED',
    'admission_rays_use_unmasked_owner_full_native_count':len(F),'role_authority_exact_named_bones':anchor_authority,
    'geodesic_source_triangle_path_neutral':[{ 'anchor_pair':[tag[a],tag[c]], 'length_mm':float(dist[a,need_idx[c]]*1000),
       'true_material_face_path':o_roi[path].tolist()} for (a,c),path in zip([(0,1),(1,2),(1,3)],loops)],
    'branch_rows_bound_to_within_six_mm':len(branch_reg),
    'pose_summaries':diagnostics,'immutable_original_failed_gate_file_sha256':locked_hash,
    'protected_geometry_and_all_old_flags_written':False}
 buf=json.dumps(all_tests,separators=(',',':')).encode();(p/'full_unmasked_samples.json.gz').write_bytes(gzip.compress(buf,mtime=0))
 A['decompressed_full_ray_evidence_sha256']=hashlib.sha256(buf).hexdigest()
 np.savez_compressed(p/'editable_owner_branch_map.npz',frozen_anatomical_source_face_ids=sorted(branch_reg),
     role_face_rows=anchor_ids,neutral_owner_bind_landmarks=W0,exact_held_landmarks=W1,
     actual_bone_thumb_neutral=rest_b['thumb'],actual_bone_index_neutral=rest_b['index'],
     actual_bone_thumb_held=hold_b['thumb'],actual_bone_index_held=hold_b['index'],
     immutable_fairing_bind=q['bind'],immutable_fairing_open=q['open'],immutable_fairing_faces=q['combined_faces'])
 (p/'result.json').write_text(json.dumps(A,indent=2)+'\n')
 print('BRANCH-AUDIT',json.dumps(A),flush=True)
else:raise RuntimeError('exact pose not available')
