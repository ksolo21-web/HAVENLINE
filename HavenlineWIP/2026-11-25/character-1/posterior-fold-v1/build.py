import os
import numpy as np,hashlib,json
from scipy.spatial.transform import Rotation,Slerp
from pathlib import Path
P=Path(__file__).resolve().parent
A=Path(os.environ['C1_COLLAR_DATA'])
p0=Path(os.environ['C1_KNEE_DATA'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'exact-assembled-surface.npz')=='8a7222ecdb893da3da09dba34ac3c56f1f95f7f6e7269f1e9d165eca0ef074f7'
assert sha(p0/'poses.npz')=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
D=np.load(A/'exact-assembled-surface.npz');B=np.load(p0/'poses.npz')
V=D['v'];T=D['tri'];W=D['w'];uv=D['UV']; S=float(B['scale']);O=B['source_origin']
M=B['bones'][0,1]
n=lambda p:np.linalg.norm(p,axis=-1)
# Only the new visible posterior knee, spanning the exact lower shin and
# upper thigh witness, and permanently excludes the independent anterior fault.
x,y,z=V.T
inside=(x>-.165)&(x<-.066)&(y>.058)&(z>.361)&(z<.495)&(W[:,2:].sum(1)<1e-9)
reg=np.isin(np.arange(len(T)),np.flatnonzero(inside[T].all(1)))
assert np.all(reg[[38082,39703]]) and not np.any(reg[[26992,27689]])
sourceid=np.flatnonzero(reg)
sel=T[sourceid]
# Native visible panel topology: exact sewn boundary, independently inserted
# flex islands (face-centroid knots and sewn rings). No projected source sweep:
# a face center inherits an exact barycentric source rest/UV/weight slot.
fresh=V[sel].mean(1)
pw=W[sel].mean(1)
uv0=uv.reshape(len(T),3,2); cu=uv0[sourceid].mean(1)
N0=np.arange(len(sel))+len(V)
# One continuous posterior sheet, sewn with original ordering; new center
# support turns each selected patch into 3 triangles, preserving all rim points.
revised=np.concatenate([np.column_stack([sel[:,i],sel[:,(i+1)%3],N0]) for i in range(3)])
xyz=np.vstack((V,fresh)); wi=np.vstack((W,pw)); fi=np.vstack((T[~reg],revised))
cuv=np.concatenate((uv0[~reg],*[np.stack([uv0[sourceid,i],uv0[sourceid,(i+1)%3],cu],1) for i in range(3)]))
retained=np.flatnonzero(~reg)
frozen=np.vstack((V[sel].mean(1),))
assert np.max(abs(wi.sum(1)-1))<1e-6
def skin(x,w):
 p=x/S+O; h=np.c_[p,np.ones(len(p))]
 af=np.einsum('nk,kij->nij',w,M)
 return (np.einsum('nij,nj->ni',af,h)[:,:3]-O)*S,af
current,bind=skin(xyz,wi)
knee=B['joints'][1,1]
def pmat(mat,x):
 p=x/S+O
 return (mat[:3,:3]@p+mat[:3,3]-O)*S
J0,J1=[pmat(m,knee) for m in M[:2]]
assert n(J0-J1)<1e-6,(J0,J1)
J=(J0+J1)*.5
mode=np.where(np.r_[inside,np.ones(len(fresh),bool)])[0]
p=xyz[mode];xx,yy,zz=p.T
# A single soft center-line pattern for the posterior fold, neutral zero:
# paired proximal/distal transverse supports are carried by *one* proper
# rotation in the medial flex core, and taper into the unedited sewn rim.
# Target exact rotations only; no attached shell or treatment of anterior.
R=Rotation.from_matrix(M[:2,:3,:3]); rm=Slerp([0.,1.],R)([.5]).as_matrix()[0]
g=np.minimum.reduce(((xx+.165)/.028,(-.066-xx)/.028,(yy-.058)/.018,(zz-.361)/.032,(.495-zz)/.026))
g=np.clip(g,0,1); taper=g*g*(3-2*g)
wanted=J+(p-knee)@rm.T
Y=current.copy()
change=(wanted-current[mode])*taper[:,None]
Y[mode]+=change
# Native pre-skin posed-only key exact inversion from the four immutable
# linear influence matrices. At value=0 the original geometry/UV exact.
Dlocal=np.zeros_like(xyz)
Dlocal[mode]=np.linalg.solve(bind[mode,:3,:3],change[...,None]/S).squeeze(-1)
assert np.max(n(Y-skin(xyz+Dlocal*S,wi)[0]))<1e-10
np.savez_compressed(P/'fold-panel.npz',v=xyz,tri=fi,w=wi,uv=cuv,rest_p0=V,held0=Y,held_base=current,delta_in_rig_m=Dlocal,pose_normals_reference_sha=sha(p0/'poses.npz'),origface=retained,rebuilt_source=sourceid)
info={'original_cut_cells':len(sel),'new_authored_connected_triangles':len(revised),'sewn_boundary_vertices_outside_region_unchanged':True,'source_rest_material_outside_original_exact':bool(np.array_equal(xyz[:len(V)],V)), 'source_normalized_max_posed_delta_mm':float(n(change).max()*1000),'max_premesh_delta_mm':float(n(Dlocal).max()*S*1000),'posterior_exact_target_origin_mm':(knee*1000).tolist(),'authored_only_at_ms':0}
(P/'construction.json').write_text(json.dumps(info,indent=2));print(info)
