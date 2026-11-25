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
 chest=Path(os.environ['C1_CHEST_RESULT'])
 assert sha(chest)=='b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed'
 base=poses();BT=make_bvh(TP,T)
 assert len(make_bvh(base,F).overlap(BT))==370
 assert (M==np.asarray(json.loads(chest.read_text())['orientation'])).all()
 # Preserve all forearms, wrists, and parent chains; isolate two palm rolls and
 # one thumb opposition layer. Base palm vertex and wrist define each roll axis.
 pm={}; changed={f'{n}.{side}' for side in sides for n in ('hand','thumb.01')}
 frozen={q.name:np.array(q.matrix_basis) for q in rig.pose.bones if q.name not in changed}
 wrist0={s:np.array(rig.pose.bones['hand.'+s].head) for s in sides}
 for side,(_,_,H,_,_,_,_,_,pi,ref,outward,ix) in sets.items():
  near=np.flatnonzero((W[:,lookup['hand.'+side]]>.8)&(np.linalg.norm(P-P[pi],axis=1)<.020)&(((P-P[pi])@np.array(H.bone.matrix_local)[:3,2])>-.008))
  assert len(near)>12
  vm=base[near]-base[near].mean(0)
  _,_,vt=np.linalg.svd(vm,full_matrices=False);palm=vt[-1]
  if palm@outward>0:palm=-palm
  ax=unit(base[pi]-wrist0[side]); aa=unit(palm-(palm@ax)*ax); bn=-outward; bb=unit(bn-(bn@ax)*ax)
  full=float(np.arctan2(ax@np.cross(aa,bb),aa@bb))
  turn=float(np.clip(full,-np.deg2rad(12),np.deg2rad(12)))
  rot=Quaternion(Vector(ax),turn).to_matrix()
  old=H.matrix.copy();hm=(rot@old.to_3x3()).to_4x4();hm.translation=old.translation
  H.matrix=hm;bpy.context.view_layer.update()
  pm[side]={'patch_count':int(len(near)),'axis_wrist_palm':ax.tolist(),'normal':palm.tolist(),
   'requested_roll_deg':float(np.degrees(full)),'applied_roll_deg':float(np.degrees(turn))}
 palm_stage=poses()
 def total(V):return len(make_bvh(V,F).overlap(BT))
 for side,(_,_,_,_,_,_,_,_,pi,ref,outward,ix) in sets.items():
  th=rig.pose.bones['thumb.01.'+side];tip=rig.pose.bones['thumb.03.'+side]
  root=np.array(th.head);u=unit(np.array(tip.tail)-root);aim=unit(outward-(outward@u)*u)
  target=u*np.cos(np.deg2rad(20))+aim*np.sin(np.deg2rad(20))
  rot=Vector(u).rotation_difference(Vector(target)).to_matrix()
  m=(rot@th.matrix.to_3x3()).to_4x4();m.translation=th.head
  th.matrix=m;bpy.context.view_layer.update()
  pm[side]['thumb_abduction_deg']=20.
 assert all(np.array_equal(np.array(rig.pose.bones[n].matrix_basis),x) for n,x in frozen.items())
 assert max(np.linalg.norm(np.array(rig.pose.bones['hand.'+s].head)-wrist0[s]) for s in sides)<1e-6
 result['separate_open_stages']={'compact_baseline_total_pairs':370,'palm_roll_only_total_pairs':total(palm_stage),'parameters':pm}
 V=poses();assert np.array_equal(V[fixed],original[fixed]);assert not bpy.data.actions
 BT=make_bvh(TP,T); BV=make_bvh(V,F);hits=BV.overlap(BT)
 result.update(actual_tool_skin_pairs=len(hits),groups_first_vertex=dict(Counter(str(dom[F[i][0]]) for i,j in hits)),
  exact_all_unchanged_lower_vertex_count=int(fixed.sum()),actual_tool_above_below_coat_not_inferred=True,
  applied_upper_bones=sorted(mod))
 hands={}
 for side,(_,_,_,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  Hf=F[((-1 if side=='R' else 1)*X0[F]>.72).all(1)]
  hf=make_bvh(V,Hf);hands[side]=hf
  delta=V[pi]-ref-dt
  constraints[side].update(actual_palm_signed_normal_gap_mm=float(delta@n*1000),
   actual_palm_tangent_error_mm=float(np.linalg.norm(delta-(delta@n)*n)*1000),
   hand_torso_pairs=len(hf.overlap(make_bvh(V,garment))),hand_assigned_band_pairs=len(hf.overlap(make_bvh(TP,T[ix]))))
 result["actual_tool_vs_verified_garment_pairs"]=len(BT.overlap(make_bvh(V,garment)))
 side_faces=set()
 for side,(_,_,_,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  hi=np.flatnonzero(((-1 if side=='R' else 1)*X0[F]>.72).all(1));side_faces.update(int(i) for i in hi)
  actual=np.unique(F[hi]);local=(V[actual]-factory-dt)@M
  N,H=signed_planes(A,T[ix]);z=constraints[side]["grip_center_in_original_axis"]
  signed=np.maximum(np.max(local@N.T-H,axis=1),abs(local[:,2]-z)-.05)
  handhits=[(i,j) for i,j in hits if ((-1 if side=='R' else 1)*X0[F[i]]>.72).all()]
  constraints[side].update(all_exact_hand_tool_pairs=len(handhits),out_of_assigned_band_pairs=sum(j not in ix for i,j in handhits),
   deepest_exact_vertex_in_assigned_grip_prism_mm=float(1000*min(0.,signed.min())),vertices_below_minus_point2mm=int((signed<-.0002).sum()))
 result["pairs_outside_both_open_hand_regions"]=sum(i not in side_faces for i,j in hits)
 # Include any forearm-driven vertex or any sleeve-shell face at the
 # measured forearm segment, no partial triangles culled from the witness.
 for side,(U,Q,H,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  e=np.array(Q.head);w=np.array(H.head);u=unit(w-e);t=(V-e)@u;dist=np.linalg.norm(V-e-t[:,None]*u,axis=1)
  influence=(W[:,lookup['forearm.'+side]]>.002)
  full=influence|((t>-.012)&(t<np.linalg.norm(w-e)+.015)&(dist<.115))
  ff=F[full[F].any(1)]
  result['sides'][side]['broad_forearm_cuff_triangles']=len(ff)
  result['sides'][side]['broad_forearm_cuff_tool_pairs']=len(make_bvh(V,ff).overlap(BT))
  strict=F[influence[F].any(1)]
  result['sides'][side]['all_forearm_weighted_shell_tool_pairs']=len(make_bvh(V,strict).overlap(BT))
 bind=Path(os.environ['C1_BIND_EVIDENCE'])
 assert sha(bind)=='d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336'
 legacy=np.load(bind)
 assert np.array_equal(legacy['P'],P.astype(np.float32)) and np.array_equal(legacy['F'],F)
 E=np.unique(np.sort(np.stack((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]),axis=1).reshape(-1,2),axis=1),axis=0)
 lengths=np.linalg.norm(P[E[:,1]]-P[E[:,0]],axis=1)
 wi=legacy['W']/1000.; ids=[i for i,n in enumerate(legacy['names']) if n.endswith('.01.L')]
 lm=wi[:,ids].argmax(1);wm=wi[:,ids].max(1)
 vv=(X0>.744)&(X0<.850)&(Z0>.387)&(Z0<.503)&(Y0>.028)
 l,r=E.T;web=(vv[l]&vv[r])&(lengths>.00045)&(lm[l]!=lm[r])&(wm[l]>.3)&(wm[r]>.3)
 assert web.sum()==133
 result['exact_left_133_edge_web']={}
 for label,arr in [('compact',base),('palm_only',palm_stage),('both_open_layers',V)]:
  rr=np.linalg.norm(arr[E[web,0]]-arr[E[web,1]],axis=1)/lengths[web]
  result['exact_left_133_edge_web'][label]={'min':float(rr.min()),'max':float(rr.max()),'fail':int(((rr<.5)|(rr>2.)).sum()),'worst':E[web][rr.argmin()].tolist()}
 result['digit_closure_run']=False
 result['both_hands_overlaps']=len(hands['R'].overlap(hands['L']))
 result["status"]="HOLD_OPEN_STAGE" if hits or result["both_hands_overlaps"] else "OPEN_NEEDS_INDEPENDENT_REVIEW"
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
