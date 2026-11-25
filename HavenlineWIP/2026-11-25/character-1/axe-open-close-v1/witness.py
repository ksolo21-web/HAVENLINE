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
# Author one rigid side-ready station from actual two open metacarpal supports;
# align longitudinal shaft with palms, not arm or hand targets. No fitting
# iterations, socket snapping, thumb edits beyond recorded single closure.
palms={};groups={}; landmarks={}; selected=[]
for side,sg in [('R',-1),('L',1)]:
 hand=(sg*X0>.72)
 candidate=np.flatnonzero(hand&(W[:,lookup['hand.'+side]]>.8)&(sg*X0<.825))
 assert len(candidate)>50
 # Source palm robust near metacarpal seat, not digit tip or virtual ball.
 palms[side]=np.median(original[candidate],axis=0)
 groups[side]={'palm':candidate,'hand':np.flatnonzero(hand),
  'fingers':{d:np.flatnonzero(W[:,lookup[d+'.03.'+side]]>.65) for d in ('thumb','index','middle','ring','pinky')}}
 bones=[np.array(rig.pose.bones[j+'.'+side].head) for j in ('upper_arm','forearm','hand')]
 s,e,w=bones
 def av(x,y):return float(np.rad2deg(np.arccos(np.clip(x@y/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1))))
 hand_axis=np.array(rig.pose.bones['hand.'+side].matrix.to_3x3()@Vector((0,1,0)))
 landmarks[side]={'shoulder':s.tolist(),'elbow':e.tolist(),'wrist':w.tolist(),
 'extension_reserve_m':float(np.linalg.norm(e-s)+np.linalg.norm(w-e)-np.linalg.norm(w-s)),
 'forearm_hand_angle_deg':av(w-e,hand_axis),'palm_sample_count':len(candidate),'open_palm_station_m':palms[side].tolist()}
axis=palms['R']-palms['L']; gap=np.linalg.norm(axis);axis/=gap
n= np.array([0.,-1.,0.]);n-=axis*(n@axis);n/=np.linalg.norm(n)
frame=np.column_stack((n,np.cross(axis,n),axis)); assert np.linalg.det(frame)>.99999
loc=(palms['R']+palms['L'])/2+.18*axis+n*.073
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(g))
axe=next(o for o in bpy.context.scene.objects if o not in before and o.type=='MESH')
A=vec(axe.data.vertices,'co',3).astype(float);T=tri(axe);assert len(T)==512
TP=A@frame.T+loc
BT=make_bvh(TP,T)
band={}
for side,z,r in [('R',-.10,.071),('L',-.26,.073)]:
 fi=np.flatnonzero(((abs(A[T,2]-z)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-r)<3e-5)).all(1));assert len(fi)==28
 N,H=signed_planes(A,T[fi])
 band[side]=(z,fi,N,H,make_bvh(TP,T[fi]))
E=np.unique(np.sort(np.stack((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]),axis=1).reshape(-1,2),axis=1),axis=0)
edge=np.linalg.norm(P[E[:,1]]-P[E[:,0]],axis=1)
# Critic's exact source-fixed old proximal influence membership, not erased by newer weights.
legacy=np.load(b/'c1-full-detail-rig-witness-v1/bind-evidence.npz')
assert np.array_equal(legacy['P'],P.astype(np.float32)) and np.array_equal(legacy['F'],F)
wi=legacy['W']/1000.; wei=[i for i,n in enumerate(legacy['names']) if n.endswith('.01.L')]
lm=wi[:,wei].argmax(1);wm=wi[:,wei].max(1)
v=(X0>.744)&(X0<.850)&(Z0>.387)&(Z0<.503)&(Y0>.028)
l,r=E.T; left_web=(v[l]&v[r])&(edge>.00045)&(lm[l]!=lm[r])&(wm[l]>.3)&(wm[r]>.3)
assert int(left_web.sum())==133
allpart={s:F[np.isin(F,groups[s]['hand']).all(1)] for s in ('R','L')}
bodymask=(abs(X0)<.28)&(Z0>-.24)&(Z0<.61)&~np.char.startswith(dom,'upper_arm.')&~np.char.startswith(dom,'forearm.')&~np.char.startswith(dom,'hand.')
torso=F[bodymask[F].all(1)]
fixed=P[:,2]<-.72
lower=original[fixed].copy()
digit_bones={q.name:q for q in rig.pose.bones if q.name.split('.')[0] in ('pinky','index','middle','ring','thumb')}
protected={q.name:np.array(q.matrix_basis) for q in rig.pose.bones if q.name not in digit_bones}
records=[]
for alpha in (0.,.25,.5,.75,1.):
 for name,bone in digit_bones.items():
  d,j,s=name.split('.');dg=[14.,12.,8.][int(j)-1]*alpha*(.65 if d=='thumb' else 1.)
  bone.rotation_mode='QUATERNION'
  bone.rotation_quaternion=Quaternion((1,0,0),math.radians(dg))
 bpy.context.view_layer.update()
 V=poses()
 assert np.array_equal(V[fixed],lower) and all(np.array_equal(np.array(rig.pose.bones[k].matrix_basis),m) for k,m in protected.items())
 G=make_bvh(V,F)
 contacts=G.overlap(BT)
 # Regional checks on actual triangles; overlaps include any undesired body and hand contacts.
 groups_cross=Counter(str(k) for i,j in contacts for k in [dom[F[i][0]]])
 stages={}
 for side,(z,ids,N,H,B) in band.items():
  group=groups[side];local=(V[group['hand']]-loc)@frame
  signed=np.maximum(np.max(local@N.T-H,axis=1),abs(local[:,2]-z)-.05)
  def nearest(index):
   return min(B.find_nearest(Vector(V[i]))[3] for i in index)*1e3
  hand_tree=make_bvh(V,allpart[side])
  self_hits=hand_tree.overlap(hand_tree);fs=weld[allpart[side]]
  ns=sum(1 for i,j in self_hits if i<j and not np.isin(fs[i],fs[j]).any())
  stages[side]={'glove_surface_to_assigned_band_all_pairs':len(hand_tree.overlap(B)),
    'stock_palm_vertex_closest_unsigned_mm':nearest(group['palm']),
    'digit_tip_min_assigned_band_mm':{di:nearest(ix) for di,ix in group['fingers'].items()},
    'glove_deep_signed_samples_at_0_2mm':int((signed<-.0002).sum()),'glove_nonadjacent_pairs':ns,
    'hand_to_torso_pairs':len(hand_tree.overlap(make_bvh(V,torso)))}
 lr=len(make_bvh(V,allpart['R']).overlap(make_bvh(V,allpart['L'])))
 we=np.linalg.norm(V[E[left_web][:,1]]-V[E[left_web][:,0]],axis=1)/edge[left_web]
 bad=E[left_web][we.argmin()]
 records.append({'command_fraction':alpha,'full_tool_skin_pairs':len(contacts),'pose_unchanged_lower':True,
    'full_tool_skin_overlap_groups_first_vertex':dict(groups_cross),'left_source_web_min':float(we.min()),'left_web_under_.5':int((we<.5).sum()),
    'left_web_exact_worst_edge_raw_vertex_ids':bad.tolist(),'interhand_pairs':lr,'hands':stages})
 print('stage',alpha,'crossings',len(contacts),'web',float(we.min()),flush=True)
assert np.array_equal(vec(skin.data.vertices,'co',3),P) and np.array_equal(tri(skin),F)
(p/'result.json').write_text(json.dumps({'status':'STATIC_GEOMETRY_ONLY_HOLD_UNLESS_INDEPENDENT_CONTACT_EVIDENCE','virtual_axe_sha':sha(g),
 'scope':'same exact originally authored narrow body, new fixed proper rigid shaft, no gameplay/timing',
 'tool_station_m':loc.tolist(),'tool_basis':frame.tolist(),'original_tool_scale':1.0,'open_palms_span_m':float(gap),'fixed_assigned_band_span_m':.16,
 'unchanged_source_chain':landmarks,'parallel_stage_samples_not_continuous_clip':records},indent=2)+'\n')
