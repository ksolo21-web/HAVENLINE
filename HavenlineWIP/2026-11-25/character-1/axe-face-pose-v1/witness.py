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
# Design fixed before measuring: low-front diagonal, top biased to actor's right.
# Both palms approach a nominated forward-facing shaft facet at band midspan.
def unit(v): return v/np.linalg.norm(v)
def mat(v): return Matrix(v.tolist())
axis=unit(np.array([-.69,.0,.72]));rad=np.array([0.,-1.,0.])
frame=np.column_stack((rad,np.cross(axis,rad),axis));loc=np.array([0.,-.415,.205])+.18*axis
ob=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(g))
axe=next(o for o in bpy.context.scene.objects if o not in ob and o.type=='MESH')
A=vec(axe.data.vertices,'co',3).astype(float);T=tri(axe); assert len(T)==512
TP=A@frame.T+loc
fixed=P[:,2]<-.72
modifiable={n+'.'+s for s in 'RL' for n in ('upper_arm','forearm','hand')}
unchanged={q.name:np.array(q.matrix_basis) for q in rig.pose.bones if q.name not in modifiable}
setup={}; blocked={}; authored={}
for s,z,r,t in [('R',-.10,.071,1),('L',-.26,.073,-1)]:
 ix=np.flatnonzero(((abs(A[T,2]-z)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-r)<3e-5)).all(1));assert len(ix)==28
 planes,_=signed_planes(A,T[ix]);q=int(np.argmax(planes[:,0]));fi=int(ix[q]);face=A[T[fi]]
 # Exactly band center and the angular facet centroid (barycentric solution).
 radial_mid=(face[:,:2].min(0)+face[:,:2].max(0))/2
 target=np.r_[radial_mid,z]
 bary=np.linalg.lstsq(np.vstack((face.T,np.ones(3))),np.r_[target,1.],rcond=None)[0]
 assert min(bary)>-1e-6 and np.linalg.norm(bary@face-target)<1e-7
 target=bary@TP[T[fi]]
 normal=frame@planes[q]
 U,Q,H=(rig.pose.bones[f'{n}.{s}'] for n in ('upper_arm','forearm','hand'))
 # Representative palmar surface, exact original skin vertices near palm center.
 bind=np.array(H.bone.matrix_local); coords=(P-bind[:3,3])@bind[:3,:3]
 candidates=np.flatnonzero((W[:,lookup['hand.'+s]]>.8)&(abs(coords[:,0])<.025)&(abs(coords[:,1]-.061)<.012)&(coords[:,2]>0))
 assert len(candidates)>0, (s,len(candidates),coords[W[:,lookup['hand.'+s]]>.8].min(0),coords[W[:,lookup['hand.'+s]]>.8].max(0))
 pi=int(candidates[np.argmax(coords[candidates,2])]); lp=coords[pi]
 # Opposed arms reach across the axis; signed radial normal sets hand roll.
 hand_z=-normal
 wanted=np.array([.83*t,-.12,.24*t]);hand_y=unit(wanted-hand_z*np.dot(wanted,hand_z))
 hand_x=np.cross(hand_y,hand_z);hr=np.column_stack((hand_x,hand_y,hand_z))
 # Offset only the nominated surface by a small known gap: open ready, not a claim of contact.
 wrist=target+.001*normal-hr@lp
 sh=np.array(U.head); el0=np.array(Q.head); w0=np.array(H.head)
 a=np.linalg.norm(el0-sh); d=np.linalg.norm(w0-el0); v=wrist-sh; L=np.linalg.norm(v); n=v/L
 authored[s]={'exact_surface_triangle':fi,'barycentric':bary.tolist(),'surface_actor':target.tolist(),'bodyward_normal':(-normal).tolist(),'palm_source_vertex':pi,'palm_sample_count':int(len(candidates)),
  'palm_local':lp.tolist(),'wrist_actor':wrist.tolist(),'shoulder_actor':sh.tolist(),'hand_axes_actor':hr.tolist(),
  'total_link_length_mm':1000*float(a+d),'required_shoulder_to_wrist_mm':1000*float(L),'hard_extension_reserve_mm':1000*float(a+d-L),
  'nominal_gap_mm':1.0,'negative_60mm_outward_reach_reserve_mm':1000*float(a+d-np.linalg.norm(v+.060*rad))}
 if not abs(a-d)<L<a+d:
  blocked[s]='outside exact two-link reach shell'
  continue
 x=(a*a-d*d+L*L)/(2*L)
 # Body-side bent elbows, biased down and toward the established elbow side.
 pole=np.array([-.88*t,-.19,-.70]); pole=unit(pole-(pole@n)*n)
 el=sh+x*n+np.sqrt(a*a-x*x)*pole
 # Preserve original roll of each segment relative to shortest direction transport.
 UM=U.matrix.copy();QM=Q.matrix.copy()
 def orient(orig,start,end):
  q=(orig.to_3x3()@Vector((0,1,0))).rotation_difference(Vector(end-start))
  m=(q.to_matrix()@orig.to_3x3()).to_4x4();m.translation=Vector(start);return m
 setup[s]=(fi,ix,bary,target,normal,pi,{'elbow':el.tolist(),'wrist':wrist.tolist(),
  'extension_reserve_mm':1000*float(a+d-L),'forearm_to_hand_deg':angle(wrist-el,hand_y) if 'angle' in globals() else float(np.degrees(np.arccos(np.clip(unit(wrist-el)@hand_y,-1,1)))),
  'expected_upper':orient(UM,sh,el),'expected_forearm':orient(QM,el,wrist),'expected_hand':mat(hr).to_4x4()})
 setup[s][-1]['expected_hand'].translation=Vector(wrist)
if blocked:
 assert np.array_equal(poses(),original)
 out={'status':'HOLD_OPEN_TARGET_OUTSIDE_REACH','hands':authored,'blocked':blocked,'tool_basis':frame.tolist(),'tool_station':loc.tolist(),
  'finger_edits':0,'any_pose_applied':False,'actual_skin_collision_measured':False,'closure_allowed':False}
 (p/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True);raise SystemExit(0)
for s,row in setup.items():
 ar=row[-1]
 for bn,x in [('upper_arm','expected_upper'),('forearm','expected_forearm'),('hand','expected_hand')]:
  rig.pose.bones[f'{bn}.{s}'].matrix=ar.pop(x)
  bpy.context.view_layer.update()
V=poses();assert np.array_equal(V[fixed],original[fixed])
assert all(np.array_equal(np.array(rig.pose.bones[n].matrix_basis),m) for n,m in unchanged.items())
G=make_bvh(V,F);BT=make_bvh(TP,T)
contacts=G.overlap(BT)
ca={}
for s,(fi,ix,ba,target,n,pi,ar) in setup.items():
 incident=np.flatnonzero((F==pi).any(1))
 palmdelta=V[pi]-target
 hand=np.flatnonzero(((-1 if s=='R' else 1)*X0)>.72)
 hf=F[np.isin(F,hand).all(1)]
 H=make_bvh(V,hf)
 bodyf=F[(np.abs(X0[F])<.26).all(1)]
 ca[s]={'arm':ar,'exact_surface_triangle':fi,'barycentric':ba.tolist(),'surface_actor':target.tolist(),'bodyward_normal':(-n).tolist(),
  'palm_source_vertex':pi,'palm_faces':incident.tolist(),'signed_vertex_normal_gap_mm':1000*float(palmdelta@n),
  'tangent_vertex_deviation_mm':1000*float(np.linalg.norm(palmdelta-n*(palmdelta@n))),
  'hand_own_grip_pairs':len(H.overlap(make_bvh(TP,T[ix]))),
  'hand_to_body_core_pairs':len(H.overlap(make_bvh(V,bodyf)))}
buckets=Counter(str(dom[F[i][0]]) for i,j in contacts)
result={'status':'HOLD_OPEN_STAGE_NO_CLOSURE','anchor_is_kinematic_only':True,'finger_edits':0,'original_lower_equal':True,
        'source_axes':frame.tolist(),'tool_station':loc.tolist(),'hands':ca,'actual_tool_skin_crossings':len(contacts),'first_vertex_group_counts':dict(buckets)}
(p/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
