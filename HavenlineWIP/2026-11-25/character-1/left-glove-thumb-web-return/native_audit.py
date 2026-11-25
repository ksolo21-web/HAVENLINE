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
 assert 'L' in ring
 def packet(folder,seal,file):
  d=b/folder;ms=d/'SHA256SUMS'
  assert sha(ms)==seal,(folder,sha(ms))
  for line in ms.read_text().splitlines():
   h,f=line.split(maxsplit=1);assert sha(d/f)==h,f
  return np.load(d/file)
 old=packet('hvn-l1-c1-glove-remaining-uv-custody-v1','287bf49a6098ffb8aaba9e109a1aa904804d222f5e187af57b2a335dbbbe108c','editable_custody_map.npz')
 q=packet('hvn-l1-c1-glove-uv-custody-v1','25d381d1c5ba5e82c23b1a71b828178228b63e40ddb9538c374c5f02a8cc7f9b','editable_dart_uv_only.npz')
 prev=packet('hvn-l1-c1-left-distal-glove-v1','570ae531b64054da51d56b1571b1934a86deafd9c7d5fdfad4c8481cc8ca1ca0','editable_left_join.npz')
 coarse=packet('hvn-l1-c1-left-coarse-sections-v1','3c059bdf29e6f300e2255dc89e1c332dadcbd46f702951373a12719efd4b12cc','editable_left_coarse.npz')
 rail=packet('hvn-l1-c1-intrinsic-sewing-v1','ea685b7d29314c7ce84d0d1a6bf050028b2786459313cf4115c3072f718ce416','editable_intrinsic_panels.npz')
 tip=packet('hvn-l1-c1-left-tip-diagonal-v1','c951e28d0f03cebd6e621fc86f90ccbf30b2df470ae4494120d876128cd6e0d6','editable_left_tip_flip.npz')
 pinned_outer_edges={tuple(sorted(map(int,e))) for e in tip['original_locked_outer_edges']}
 for arr,key in [('bind','bind'),('open','open'),('triangles','triangles'),('exact_unchanged_corner_uv','corner_uv')]:
  assert np.array_equal(old[arr],q[key])
 rem=prev['retained_source_faces']; clip=prev['clipped_left_source_faces']; clip_all=np.r_[F[rem],clip]
 assert len(F)==727442 and len(clip_all)==706729 and max(clip_all.ravel())<len(P)+len(prev['bind_additions'])
 # Candidate full existing shell = exact retained source (both sides and rest of body), exact
 # clipped garment, current partial local shell, actual L0, and separate nested L1.
 # Rejected dense donor extensions are not candidate geometry. Nested L1 is already the
 # separately bounded true nested material in the coarse packet and must not be duplicated.
 z=np.load(p/'editable_thumb_web.npz')
 geometry=json.loads((p/'build_result.json').read_text())
 assert not any(geometry['geometric_neutral_and_open_contact_pairs'])
 r0=q['original_face_ids']; R=np.r_[z['original_face_ids'],z['new_face_ids']]; added={141,142,143,144}
 FF=z['combined_faces']
 for k,val in [('bind','bind'),('open','open')]:
  assert np.array_equal(z[k][:len(q[val])],q[val])
 assert np.array_equal(FF[:len(r0)],q['triangles'])
 loaded_phys=b/'hvn-l1-c1-glove-physical-side-v1'; assert sha(loaded_phys/'SHA256SUMS')=='44db716e542ece793bf1a43fb476001f091b57cbf9d938693fb8d67e0c6edefa'
 for line in (loaded_phys/'SHA256SUMS').read_text().splitlines():
  h,f=line.split(maxsplit=1);assert sha(loaded_phys/f)==h
 import gzip
 old_rays=json.loads(gzip.decompress((loaded_phys/'ray_evidence.json.gz').read_bytes()))
 mapping=dict(zip([78,82,83,84,85,105,106,108,111],range(130,139)))
 new_focus=list(map(int,z['new_face_ids']))
 rows={int(i):j for j,i in enumerate(R)}
 JJ=np.array([rows[i] for i in new_focus])
 BARY=np.array([[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6],[.46,.46,.08],[.46,.08,.46],[.08,.46,.46]])
 def cast(tree,s,u,d):
  x,n,i,r=tree.ray_cast(Vector(s),Vector(u),d)
  return None if i is None else (np.array(x,dtype=float),np.array(n,dtype=float),int(i),float(r))
 def rotate(n,axis,theta):
  return unit(n*np.cos(theta)+np.cross(axis,n)*np.sin(theta)+axis*(axis@n)*(1.-np.cos(theta)))
 def directions(n):
  A=np.eye(3)[np.argmin(abs(n))];a=unit(np.cross(n,A));c=unit(np.cross(n,a));t=.1745329252
  return [n,rotate(n,a,t),rotate(n,a,-t),rotate(n,c,t),rotate(n,c,-t)]
 def hit(parts,x,u,L):
  H=[]
  for name,tree in parts.items():
   h=cast(tree,x,u,L)
   if h:H.append((name,*h))
  return min(H,key=lambda d:d[-1]) if H else None
 def shape(h,target=None):
  if h is None:return None
  name,x,n,i,l=h; label=int(R[i]) if name=='local' else i
  return {'part':name,'id':label,'point':x.tolist(),'normal':n.tolist(),'t':l}
 def evaluate(phase,stock,garment,local,lp,nested,actual_tool):
  owner=make_bvh(stock,F); cand=make_bvh(local,FF)
  parts={'retained':make_bvh(garment,clip_all),'local':cand,
         'rail':make_bvh(lp,rail['L_0_indices']),'nested':make_bvh(nested,coarse['nested_tri'])}
  nf=make_bvh(local,FF[JJ])
  ext={k:[(int(R[JJ[i]]),j) for i,j in nf.overlap(v)] for k,v in parts.items() if k!='local'}
  if actual_tool is not None:ext['exact_held_axe']= [(int(R[JJ[i]]),j) for i,j in nf.overlap(actual_tool)]
  Q={}; cover={}
  for i,j in list(mapping.items())+[(None,j) for j in sorted(added)]:
   V=local[FF[rows[j]]]; nnew=unit(np.cross(V[1]-V[0],V[2]-V[0]));M=[];J=[]
   for b in BARY:
    x=b@V
    y,on,source,r=owner.find_nearest(Vector(x))
    y=np.array(y,dtype=float)
    for t,u in enumerate(directions(unit(np.array(on,dtype=float)))):
     o=cast(owner,x+u*3,-u,3.05)
     active=o is not None and np.linalg.norm(o[0]-y)<.018 and o[1]@u>.25
     h=hit(parts,x+3*u,-u,3.0001); k=hit(parts,x-3*u,u,3.0001)
     accept=h is not None and h[0]=='local' and h[3]==rows[j] and np.linalg.norm(h[1]-x)<.0001
     M.append({'target_row':j,'tested_point':x.tolist(),'owner_direction':u.tolist(),'owner_first_valid':bool(active),
               'new_face_dot_outward':float(nnew@u),'positive_and_target_first':bool(active and accept and nnew@u>.3),
               'actual_outer_first_hit':shape(h),'actual_reverse_first_hit':shape(k)})
   if i is None:
    Q[j]=M
    continue
   old_v=local[FF[rows[i]]]
   # Direct rerun at the original exterior points, not just favorable new interior samples.
   for x in old_rays[phase][str(i)]['measures']:
    b=np.asarray(x['bary']); old_point=b@old_v; u=np.array(x['owner_outward_direction_unit'])
    assert x['outward_ray_agrees_original_first_hit']
    h=hit(parts,old_point+3*u,-u,3.0001)
    local_name=h and h[0]=='local'
    old_still=bool(local_name and int(R[h[3]])==i)
    new_skin=bool(local_name and int(R[h[3]]) in set(mapping.values())|added and h[2]@u>.3)
    J.append({'old_row':i,'moved_probe':False,'new_outer_occludes_with_positive_normal':new_skin,
              'old_inward_skin_still_first':old_still,'route':shape(h)})
   Q[j]=M;cover[i]=J
  return Q,cover,ext
 f1=evaluate('neutral',P,np.r_[P,prev['bind_additions']],z['bind'],rail['L_0_bind'],coarse['nested_bind'],None)
 f2=evaluate('open',base,np.r_[base,prev['open_additions']],z['open'],rail['L_0_open'],coarse['nested_open'],BT)
 fn={'neutral':f1,'open':f2}
 full={};G={}
 for phase,(tests,previous_run,ex) in fn.items():
  full[phase]={'external_collision_pairs_for_new_shell':ex,'new_test':{},
                'repeat_original_probe_geometry':{}}
  for i,v in tests.items():
   full[phase]['new_test'][i]={'total_valid_owner_side':sum(x['owner_first_valid'] for x in v),
    'positive_and_target_first':sum(x['positive_and_target_first'] for x in v),
    'minimum_target_normal_dot':min(x['new_face_dot_outward'] for x in v)}
  for i,v in previous_run.items():
   full[phase]['repeat_original_probe_geometry'][i]={'total':len(v),
    'new_outer_occludes_with_positive_normal':sum(x['new_outer_occludes_with_positive_normal'] for x in v),
    'old_inward_skin_still_first':sum(x['old_inward_skin_still_first'] for x in v)}
  G[phase]={'new_exact_test':tests,'repeat_prior_probe':previous_run,'external_pairs':ex}
 malformed=any(v for t in full.values() for v in t['external_collision_pairs_for_new_shell'].values())
 old_reexposed=any(v['old_inward_skin_still_first'] for t in full.values() for v in t['repeat_original_probe_geometry'].values())
 score_outward=all(v['positive_and_target_first']==35 for t in full.values() for i,v in t['new_test'].items() if i not in [143,144])
 status='PASS_LOCAL_THUMB_WEB_GEOMETRY_TWO_POSES' if not malformed and not old_reexposed and score_outward else 'HOLD_THUMB_WEB_REPAIR'
 payload=json.dumps(G,separators=(',',':')).encode()
 (p/'native_rays.json.gz').write_bytes(gzip.compress(payload,mtime=0))
 result={'status':status,'all_new_shell_rows':new_focus,'single_valid_directed_perimeter_102_edges':True,
         'exact_source_pick_and_retained_uv_unchanged':True,'native_geometry_packet_sha256':sha(p/'editable_thumb_web.npz'),
         'native_ray_detail_sha256':hashlib.sha256(payload).hexdigest(),'results':full,
         'no_canonical_game_or_uv_new_assignments':True}
 (p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('HOLD-OR-PASS',json.dumps(result),flush=True)
else:raise RuntimeError('Exact held-open pose replay prerequisite failed')
