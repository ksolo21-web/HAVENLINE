"""Native Blender 4.3.2 geometry proof for an invariant pose-local collision. No mesh writes."""
from pathlib import Path
import bpy, numpy as np, json, hashlib
from mathutils import Matrix
from scipy.spatial.transform import Rotation
from mathutils.bvhtree import BVHTree

p=Path(__file__).resolve().parent; base=p.parent
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
def packet(n,h):
    d=base/n;assert sha(d/'SHA256SUMS')==h
    for row in (d/'SHA256SUMS').read_text().splitlines():
        a,b=row.split(maxsplit=1);assert sha(d/b)==a,b
    return d
rear=packet('hvn-l1-c1-approved-rear-fold-v1.kD1WNv','1a64d744fc99d4b3cc1af7e7e4d790aa1611fc0b9b929f1659c7c33c5a348e30')
collar=packet('hvn-l1-c1-collar-assembly-v1.wWohSk','75655f24db49c3e5be34a1dcd9f3c25b44c4b717efab453fe2873fd08b158aa4')
anterior=packet('hvn-l1-c1-anterior-seam-binding-v1.ZeubUc','aaa19c60d3aab56082ca7290e0c28cbef85d48938381452027b0a5d40e47a9ac')
hold=packet('hvn-l1-c1-garment-td-handoff-v1.u5TyEs','e966c85b84355f314414452f172297ed42b940ccb8ae0770d60f362081ea4b1f')
pose=base/'hvn-l1-c1-newer-knee-flex-v1/poses.npz'; assert sha(pose)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
S=np.load(pose); A=np.load(rear/'new-rear-panel.npz'); protected=np.load(anterior/'exact-native-witness.npz')
core=np.load(collar/'exact-assembled-surface.npz')
T=A['tri']; W=A['w']; V=A['v']; metric=float(S['scale']); O=S['source_origin']
region=set(map(int,A['region'])); assert len(region)==147
assert np.array_equal(core['v'],V[:len(core['v'])])
lockedR=set(A['boundary'].tolist())
carrier=json.loads((rear/'build.json').read_text())['outline_carrier_edges']; lockedS=set(sum(carrier,[]))
assert len(lockedR)==41 and len(lockedS)==18
allowed=np.array([v for v in sorted(set(T[A['region']].ravel())) if v>=len(core['v']) and v not in lockedR|lockedS],dtype=int)
assert len(allowed)==47 and set(allowed)==set(T[A["region"]].ravel())-(lockedR|lockedS)
assert not (set(T[np.flatnonzero(~np.isin(np.arange(len(T)),list(region)))].ravel())&set(allowed))
P0=np.asarray(json.loads((hold/'sections-and-motion.json').read_text())['collar_boundary_edge_vertex_ids'])
assert len(P0)==162 and not set(P0.ravel())&set(allowed)
assert not set(protected['i'])&set(allowed)
sole=np.flatnonzero(core['v'][:,2]<=.075); assert not set(sole)&set(allowed)
assert np.count_nonzero(W[allowed][:,2:])==0
# Verify live Blender binding: shape delta in MESH DATA LOCAL (raw source),
# not authored meters or model world. The exact frozen held proof uses the
# four normalized vertex groups and ordinary linear Armature deformation.
bpy.ops.wm.open_mainfile(filepath=str(rear/'c1-visible-rear-knee-redesign-proof.blend'))
o=bpy.data.objects['Right boot new visible rear fold candidate']
arm=next(t for t in bpy.context.scene.objects if t.type=='ARMATURE')
mod=list(o.modifiers)
assert len(mod)==1 and mod[0].type=='ARMATURE' and mod[0].object==arm
am=mod[0]; assert am.use_vertex_groups and not am.use_bone_envelopes and not am.use_deform_preserve_volume
assert not getattr(am,'vertex_group','') and o.data.shape_keys is None
names=('thigh.R','shin.R','foot.R','toe.R')
mobj=np.asarray(o.matrix_world);marm=np.asarray(arm.matrix_world)
O2A=np.linalg.inv(marm)@mobj
assert np.array_equal(O2A,np.eye(4))
def pts(data):
    out=np.empty((len(data.vertices),3),np.float32)
    data.vertices.foreach_get('co',out.ravel())
    return out
def eval_raw():
    return pts(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data)
base_raw=pts(o.data)
tri=np.array([tuple(f.vertices) for f in o.data.polygons]);assert np.array_equal(tri,T)
w_native=np.zeros(W.shape,np.float64)
for v in o.data.vertices:
    for z in v.groups:
        name=o.vertex_groups[z.group].name
        assert name in names
        w_native[v.index,names.index(name)]=z.weight
assert np.max(np.abs(w_native-W))<1.e-7 and np.max(abs(w_native.sum(1)-1.))<1.e-7
base_neutral_raw=eval_raw();native_transforms={}
for x,h in zip(names,S['bones'][0,1]):
    b=arm.pose.bones[x]
    b.matrix=Matrix(h.tolist())@b.bone.matrix_local
    bpy.context.view_layer.update()
for x in names:
    bb=arm.pose.bones[x]
    native_transforms[x]=np.asarray(bb.matrix@bb.bone.matrix_local.inverted())
MAT=np.stack([native_transforms[k] for k in names])
assert np.max(np.abs(MAT-S['bones'][0,1]))<5e-7
held_raw=eval_raw()
neutral=(base_neutral_raw-O)*metric;held=(held_raw-O)*metric
assert np.array_equal(held[protected['i']],protected['after'][1][protected['i']])
assert np.array_equal(held[sole],protected['after'][1][sole])
wn=w_native/w_native.sum(1)[:,None]
# Precisely separate analytic operator audit from actual native pose coordinates:
# the strict collision proof below uses the evaluated Blender arrays, not
# a forecast from these matrices or the older analytical pocket cache.
L=np.einsum('vb,bij->vij',wn,MAT[:,:3,:3])
t0=np.einsum('vb,bi->vi',wn,MAT[:,:3,3])
audit_raw=np.einsum('nij,nj->ni',L,base_raw)+t0
audit_diff=float(np.linalg.norm(audit_raw-held_raw,axis=1).max()*metric)
assert audit_diff<1.e-6
assert np.linalg.det(L[allowed]).min()>.5
th0,sh0=[np.asarray(arm.data.bones[n].matrix_local) for n in names[:2]]
th1,sh1=[np.asarray(arm.pose.bones[n].matrix) for n in names[:2]]
restrel=np.linalg.inv(th0)@sh0;posedrel=np.linalg.inv(th1)@sh1
reldelta=posedrel@np.linalg.inv(restrel)
relative_angle=float(np.degrees(Rotation.from_matrix(reldelta[:3,:3]).magnitude()))
# Exact positive surface witness: compute plane crossings in both directions,
# keep only barycentrically admitted intersection, prove proper interior at
# the common segment midpoint and signed straddling on both triangles.
def super(a,b):
    vx=np.cross(b[1]-b[0],b[2]-b[0]);n=vx/np.linalg.norm(vx)
    ds=(a-b[0])@n
    return ds,n
def bary(p,T):
    u,v=np.linalg.lstsq((T[1:]-T[0]).T,p-T[0],rcond=None)[0]
    return np.array([1-u-v,u,v])
def strict(A,B):
    u=[]; distA,_=super(A,B);distB,_=super(B,A)
    for X,Y,dd in [(A,B,distA),(B,A,distB)]:
        for k,t in [(0,1),(1,2),(2,0)]:
            if dd[k]*dd[t]>=0:continue
            u0=X[k]+(X[t]-X[k])*dd[k]/(dd[k]-dd[t])
            if bary(u0,Y).min()>-1e-8 and not any(np.linalg.norm(u0-v)<1e-8 for v in u):u.append(u0)
    if len(u)<2:return None
    span=sorted(((float(np.linalg.norm(a-b)),a,b) for i,a in enumerate(u) for j,b in enumerate(u[:i])),key=lambda x:x[0])[-1]
    m=(span[1]+span[2])*.5;ba=bary(m,A);bb=bary(m,B)
    return {'signed_plane_distances_m_from_A_to_B':distA.tolist(),'signed_plane_distances_m_from_B_to_A':distB.tolist(),
        'intersection_segment_xyz_m':[span[1].tolist(),span[2].tolist()],'segment_length_mm':span[0]*1000,
        'midpoint_pose_m':m.tolist(),'midpoint_triangle_A_barycentric':ba.tolist(),'midpoint_triangle_B_barycentric':bb.tolist(),
        'strict_triangle_interior_both':bool(min(ba)>1e-7 and min(bb)>1e-7 and min(distA)<0<max(distA) and min(distB)<0<max(distB))}
pair=[27920,42401]
actual_bv=BVHTree.FromPolygons(held.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
local=BVHTree.FromPolygons(held.tolist(),T[pair].tolist(),all_triangles=True,epsilon=0.)
raw=local.overlap(actual_bv);assert (0,pair[1]) in raw and (1,pair[0]) in raw
assert pair[0] not in region and pair[1] in region
aIDs,bIDs=T[pair]
assert not set(aIDs)&set(bIDs) and set(bIDs)<=lockedS and not set(T[pair].ravel())&set(allowed)
x=strict(held[aIDs],held[bIDs]);assert x and x['strict_triangle_interior_both'] and x['segment_length_mm']>.05
assert strict(neutral[aIDs],neutral[bIDs]) is None
pair2=[28093,42401]
x2=strict(held[T[pair2[0]]],held[T[pair2[1]]]);assert x2 and x2['strict_triangle_interior_both']
assert not set(T[pair2].ravel())&set(allowed)
out={'status':'HOLD_IMMUTABLE_NATIVE_0MS_POSTERIOR_COLLISION_NO_CORRECTIVE_TARGET_AUTHORED',
 'exact_pose_source_sha256':sha(pose),'native_raw_to_model_convention':'read exact evaluated mesh-local RAW XYZ, then (RAW-O)*scale; correctives would be input mesh-local RAW, no world-space/post-modifier transformations',
 'native_semantics':{'preserve_volume':am.use_deform_preserve_volume,'vertex_groups':am.use_vertex_groups,'bone_envelopes':am.use_bone_envelopes,
    'armature_mesh_local_mapping':O2A.tolist(),'max_raw_linear_operator_audit_error_model_m':audit_diff,
    'smallest_editable_blended_rot_linear_operator_determinant':float(np.linalg.det(L[allowed]).min()),
    'actual_collision_arrays_are_blender_evaluated_not_analytic':True,
    'source_binding_transform_from_native_blender':{n:f.tolist() for n,f in native_transforms.items()},
    'exact_relative_thigh_shin_frame_rest':restrel.tolist(),'exact_relative_thigh_shin_frame_0ms':posedrel.tolist(),
    'relative_change_degrees':relative_angle},
 'protected_id_counts':{'approved_seam':len(lockedR),'protected_side_carrier':len(lockedS),
   'unchanged_protected_collar_edges':len(P0),'same_native_outsole_rows':len(sole),'anterior_rows':protected['i'].tolist(),
   'candidate_permission_editable_posterior_ids':allowed.tolist()},
 'primary_exact_obstruction':{'face_rows':pair,'regions':['immutable_retained','inside_posterior_authorized_but_all_three_vertices_are_protected_side_carriers'],
  'source_face_vertex_ids':T[pair].tolist(),'vertex_weights_exact_source':w_native[T[pair]].tolist(),
  'native_held_coordinates_m':held[T[pair]].tolist(),'protected_endpoints_locked_R_S':[[int(v),bool(v in lockedR),bool(v in lockedS)] for v in T[pair].ravel()],
  'exact_first_pose_strict_cross':x,'neutral_strict_cross':None},
 'additional_fixed_obstruction':{'face_rows':pair2,'source_face_vertex_ids':T[pair2].tolist(),'strict_contact':x2},
 'impossibility_in_this_method': 'Per-point normalized linear skinning means allowed input deltas can only move the same 47 permitted native vertices. All six exact vertices of the primary intersecting pair are pinned by retained-region and protected side-carrier constraints. Both triangles remain identical at exact 0ms for any amplitude/trigger of a corrective on other vertices. These valid positive native intersections bypass an optimizer entirely.',
 'not_universal_geometry_impossibility':True,'needed_new_dependency':'A purpose-authored local side-carrier/topology repair that preserves the exact protected projected outline while changing normal-side occupied face connectivity may be possible. It is not the requested fixed-topology vertex-local corrective. If it cannot preserve existing protection, ask the owner with exact carrier edge/face evidence rather than changing gait or outline.'}
np.savez_compressed(p/'editable_native_pair_witness.npz',native_0ms_pair_triangles_m=held[T[pair]],neutral_pair_triangles_m=neutral[T[pair]],
    relative_thigh_shin_neutral=restrel,relative_thigh_shin_0ms=posedrel,pose_bone_matrices_native=MAT,face_pair_indices=pair,
    exact_locked_vertex_indices=T[pair],editable_fresh_vertex_indices=allowed)
(p/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print('POSE-FIXED-OBSTRUCTION',json.dumps(out),flush=True)
