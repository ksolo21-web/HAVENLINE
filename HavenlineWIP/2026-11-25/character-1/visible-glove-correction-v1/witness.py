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
 base=poses(); BT=make_bvh(TP,T)
 chest=Path(os.environ['C1_CHEST_RESULT'])
 assert sha(chest)=='b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed'
 oldhits=make_bvh(base,F).overlap(BT); assert len(oldhits)==370
 # No posed-bone change. Build one finite local rest-domain panel from all
 # observed collision triangle vertices; weld separate source rows by exact
 # position quantization and use same correction for each position seam.
 uni,first,weld=np.unique(np.rint(P/1e-6).astype(np.int64),axis=0,return_index=True,return_inverse=True)
 delta=np.zeros((len(first),3));patches={}
 direct=np.unique(F[np.unique([i for i,j in oldhits])])
 assert len(direct)>100
 pins=set()
 for side,(_,_,H,_,_,_,_,_,pi,ref,outward,ix) in sets.items():
  ss=-1 if side=='R' else 1
  src=direct[ss*X0[direct]>.58]
  assert len(src)>20
  exact=np.unique(weld[src]);sample=base[first[exact]]
  future=ref+dt
  pins.add(int(weld[pi]))
  # Material-normal push away from exact occupied shaft. The direction for
  # an individual crossing uses nearest surface only to measure distance;
  # a shared outward component is anatomically tied to its assigned palm.
  cmds=[]
  for pp in sample:
   pt,nn,_,dist=BT.find_nearest(Vector(pp))
   # Triangle boundary samples outside and inside both require local
   # clearance. Force no hidden portal/cut or unmatched duplicate seam.
   v=np.asarray(nn); v=v if v@outward>.25 else outward
   direction=unit(.60*outward+.40*v)
   cmds.append(np.clip(dist+.00175,.002,.015)*direction)
  # Small explicit, finite palm patch candidate. This is only an open-preflight
  # target, not contact until full triangles support it independently.
  idxp=np.flatnonzero((W[:,lookup['hand.'+side]]>.8)&(np.linalg.norm(P-P[pi],axis=1)<.010)&(np.abs((base-future)@outward)<.004))
  purpose=np.unique(weld[idxp]);purpose=purpose[~np.isin(purpose,exact)]
  q=base[first[purpose]]
  contact_correction=(.00010-(q-future)@outward)[:,None]*outward
  positions=np.concatenate((P[first[exact]],P[first[purpose]]))
  values=np.concatenate((np.array(cmds),contact_correction))
  tree=cKDTree(positions)
  eligible=np.flatnonzero(ss*P[first,0]>.58)
  # Finite compact C2 kernel. Lock all zeroweight boundaries; no extrapolation.
  ds,where=tree.query(P[first[eligible]],k=8);radius=.019
  rr=np.minimum(ds/radius,1.); wt=(1-rr)**4*(1+4*rr)
  taper=np.minimum(np.maximum(1-ds[:,0]/radius,0.)/.36,1.)
  edge=((ss*P[first[eligible],0]-.58)/.018).clip(0.,1.);edge=edge*edge*(3.-2.*edge)
  values_at=(values[where]*wt[:,:,None]).sum(1)/np.maximum(wt.sum(1)[:,None],1e-30)
  delta[eligible]=values_at*taper[:,None]*edge[:,None]
  patches[side]={'source_collision_welds':len(exact),'contact_patch_seed_welds':len(purpose),'anchor_vertex':int(pi)}
 for ix in pins:delta[ix]=0.
 world=delta[weld]; ids=np.flatnonzero(np.linalg.norm(world,axis=1)>1e-10)
 assert len(ids)>200 and not np.isin(ids,np.flatnonzero(fixed)).any()
 # Inverse skin mapping of visible indexed vertices, verified via Blender
 # modifier and new in-memory Shape Key. Inactive key is the source bind.
 lin=np.asarray([np.array(rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()) for n in names])
 weights=W[ids].astype(float);weights/=weights.sum(1)[:,None]
 aff=np.einsum('ij,jkl->ikl',weights,lin)
 predicted=(aff[:,:3,:3]@P[ids,:,None])[:,:,0]+aff[:,:3,3]
 linear_residual=float(np.linalg.norm(predicted-base[ids],axis=1).max())
 # Calibrate actual Blender modifier differential at the SAME pose.
 # It is spatially pointwise; witness compares native result independently.
 assert not skin.data.shape_keys
 rb=skin.shape_key_add(name='Basis',from_mix=False);rk=skin.shape_key_add(name='Detached_PalmThumbCuff_OpenPanel',from_mix=False)
 measured=np.zeros((len(ids),3,3))
 h=.001
 for axis0 in range(3):
  plus=P[ids].copy();minus=plus.copy();plus[:,axis0]+=h;minus[:,axis0]-=h
  rk.value=1.
  for i,v0 in zip(ids,plus):rk.data[int(i)].co=Vector(v0)
  bpy.context.view_layer.update();plus_eval=poses()[ids]
  for i,v0 in zip(ids,minus):rk.data[int(i)].co=Vector(v0)
  bpy.context.view_layer.update();minus_eval=poses()[ids]
  measured[:,:,axis0]=(plus_eval-minus_eval)/(2*h)
 assert np.linalg.svd(measured,compute_uv=False)[:,-1].min()>.5
 inv_delta=np.linalg.solve(measured,world[ids,:,None])[:,:,0]
 for i,v in zip(ids,P[ids]+inv_delta):rk.data[int(i)].co=Vector(v)
 rk.value=0.;bpy.context.view_layer.update()
 assert np.array_equal(poses(),base)
 rk.value=1.;bpy.context.view_layer.update()
 assert all(np.array_equal(np.array(rig.pose.bones[n].head),np.asarray(data['wrist'],dtype=np.float32)) or np.linalg.norm(np.array(rig.pose.bones[n].head)-data['wrist'])<1e-6 for n,data in [('hand.R',constraints['R']),('hand.L',constraints['L'])])
 result['authored_visible_panel']={'patches':patches,'corrected_vertices':len(ids),'max_correction_mm':float(1000*np.linalg.norm(world[ids],axis=1).max()),'weight_map_residual_mm':1000*linear_residual}
 np.savez_compressed(p/'exact_panel_delta.npz',ids=ids,rest_deltas=inv_delta.astype(np.float32))
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
 # Native checks include all nearby triangles, topology handedness, exact source
 # web and selected plane-bounded bearing triangles, not isolated point counts.
 assert np.array_equal(V[np.setdiff1d(np.arange(len(P)),ids)],base[np.setdiff1d(np.arange(len(P)),ids)])
 result['authored_visible_panel']['max_native_target_error_mm']=float(1000*np.linalg.norm(V[ids]-base[ids]-world[ids],axis=1).max())
 ci=np.flatnonzero(np.isin(F,ids).any(1));localf=F[ci]
 cb=make_bvh(V,localf)
 localself=0
 for i,j in cb.overlap(BV):
  if ci[i]!=j and not np.isin(weld[F[ci[i]]],weld[F[j]]).any():localself+=1
 result['local_nonadjacent_self_ordered_pairs']=localself
 Er=np.unique(np.sort(np.concatenate((localf[:,[0,1]],localf[:,[1,2]],localf[:,[2,0]])),axis=1),axis=0)
 lens=lambda X,E:np.linalg.norm(X[E[:,1]]-X[E[:,0]],axis=1)
 old=len(Er);er=lens(V,Er)/np.maximum(lens(base,Er),1e-12)
 norm=lambda X,ff:np.cross(X[ff[:,1]]-X[ff[:,0]],X[ff[:,2]]-X[ff[:,0]])
 n0=norm(base,localf);n1=norm(V,localf);den=(n0*n0).sum(1);good=den>1e-24
 ar=(n0[good]*n1[good]).sum(1)/den[good]
 result['modified_boundary_geometry']={'faces':len(ci),'edge_gate_fail':int(((er<.5)|(er>2.)).sum()),'signed_area_gate_fail':int(((ar<.5)|(ar>2.)).sum()),'face_reversals':int((ar<=0).sum())}
 bind=Path(os.environ['C1_BIND_EVIDENCE'])
 assert sha(bind)=='d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336'
 legacy=np.load(bind)
 assert np.array_equal(legacy['P'],P.astype(np.float32)) and np.array_equal(legacy['F'],F)
 E=np.unique(np.sort(np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]])),axis=1),axis=0)
 length=lens(P,E);wi=legacy['W']/1000.;ii=[i for i,n in enumerate(legacy['names']) if n.endswith('.01.L')]
 lm=wi[:,ii].argmax(1);wm=wi[:,ii].max(1);l,r=E.T
 v=(X0>.744)&(X0<.850)&(Z0>.387)&(Z0<.503)&(Y0>.028)
 web=v[l]&v[r]&(length>.00045)&(lm[l]!=lm[r])&(wm[l]>.3)&(wm[r]>.3);assert web.sum()==133
 ratio=lens(V,E[web])/length[web]
 result['web_133']={'min':float(ratio.min()),'max':float(ratio.max()),'fail':int(((ratio<.5)|(ratio>2.)).sum())}
 for side,(U,Q,H,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  ff=F[(W[:,lookup['forearm.'+side]][F]>.002).any(1)]
  # Patches require the full triangle within the actual named shaft facet
  # footprint and signed 0–.15mm plane tolerance; not an installable contact.
  tool_face=TP[T[constraints[side]['surface_face_index']]]
  edge=tool_face[1:]-tool_face[0];dual=np.linalg.pinv(edge.T)
  vv=V[localf]-tool_face[0]; signed=vv@n; bc=vv@dual.T
  passed=((signed>=0)&(signed<.00015)&(bc.min(2)>=0)&(bc.sum(2)<=1)).all(1)
  constraints[side].update(all_forearm_weighted_shell_tool_pairs=len(make_bvh(V,ff).overlap(BT)),
   finite_plane_near_patch_triangles=int(passed.sum()),finite_plane_near_patch_area_mm2=float(5e5*np.linalg.norm(n1[passed],axis=1).sum()))
 rk.value=0.
 saved={q.name:q.matrix_basis.copy() for q in rig.pose.bones}
 for q in rig.pose.bones:q.matrix_basis.identity()
 bpy.context.view_layer.update()
 bind_zero=poses()
 skin.shape_key_clear();bpy.context.view_layer.update()
 assert np.array_equal(poses(),bind_zero)
 result['zero_correction_bind_bitwise_exact_vs_unmodified']=True
 result['bind_vs_visible_source_positions_max_mm']=float(1000*np.linalg.norm(bind_zero-P,axis=1).max())
 result['digit_closure']=False
 result['both_hands_overlaps']=len(hands['R'].overlap(hands['L']))
 result["status"]="HOLD_OPEN_STAGE" if hits or result["both_hands_overlaps"] else "OPEN_NEEDS_INDEPENDENT_REVIEW"
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
