"""One exact source mapped internal eyelet plus compliant authored backing, not asset export."""
from pathlib import Path
import numpy as np, json, hashlib, os
P=Path(__file__).resolve().parent
prior=Path(os.environ['C1_MOUNT_DIR'])
source=Path(os.environ['C1_KNEE_DATA'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(prior/'mounts.json')=='b8e8ef8d0b67722b94b56222ad26547958e13bbce43b3f081f70f20ac3a6c062'
assert sha(source/'poses.npz')=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert sha(Path(os.environ['C1_EXACT_BLEND']))=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert sha(Path(os.environ['C1_EXACT_GLB']))=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
A=np.load(source/'poses.npz'); R=A['rest'].astype(float); E=A['E']; T=A['tri']; X=A['frames'].astype(float)
m=json.loads((prior/'mounts.json').read_text())['staged_islands'][13]
assert (m['side'],m['aspect'],m['label'],m['pixel_seed_face'])==('R','medial','lace port 3',186633)
core=np.array(m['core_raw_aliases']); backing=np.array(m['backing_raw_aliases'])
part=np.r_[core,backing]; assert len(set(part))==len(part)
assert R[part,2].min()>.13
o=np.array(m['rest_bary_center_m']); Q=np.array(m['rest_surface_frame_columns'])
assert np.linalg.det(Q)>.999999 and np.max(abs(Q.T@Q-np.eye(3)))<1e-6
L=(R[part]-o)@Q
assert L[:,2].min()>-.004
# Authored (not observed) closed internal metal eyelet and hidden soft
# backing membrane. Circumferential separate local layer, never rendered.
n=24; th=np.arange(n)*2*np.pi/n
ring=lambda r,z:np.column_stack((r*np.cos(th),r*np.sin(th),np.full(n,z)))
def strip(a,b,front=True):
 f=[]
 for i in range(n):
  j=(i+1)%n
  f.extend([[a*n+i,b*n+i,b*n+j],[a*n+i,b*n+j,a*n+j]])
 if not front:return [[a,c,b] for a,b,c in f]
 return f
eye=np.vstack([ring(r,z) for r,z in [( .0016,-.005),(.0046,-.005),(.0046,-.007),(.0016,-.007)]])
et=np.array(sum([strip(0,1),strip(1,2),strip(2,3),strip(3,0)],[]))
edge,ct=np.unique(np.sort(et[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1),axis=0,return_counts=True)
assert np.all(ct==2)
G=np.vstack([ring(r,z) for r,z in [(.0046,-.005),(.00645,-.0051),(.0084,-.0053)]])
GT=np.array(strip(0,1)+strip(1,2))
Ga=o+G@Q.T; eyed=o+eye@Q.T
# Exact visible identity mapping: core bound rigidly in frame; soft polygon
# associates each raw alias to one internal triangle and carried residual.
# Inner residual is not erased; overshoot outside ring poly solved by
# nearest edge projection, then store original residual exactly.
G2=G[:,:2]
def best_bary(x):
 best=None
 for i,t in enumerate(GT):
  a,b,c=G2[t]; mat=np.column_stack((b-a,c-a))
  s=np.linalg.solve(mat,x-a); w=np.r_[1-s.sum(),s]
  if min(w)>=-1e-9:return i,w
  for j,k in ((0,1),(1,2),(2,0)):
   u,v=G2[t[[j,k]]]
   h=np.clip(np.dot(x-u,v-u)/np.dot(v-u,v-u),0,1)
   z=u+(v-u)*h
   cost=np.linalg.norm(z-x)
   if best is None or cost<best[0]:
    w=np.zeros(3);w[j]=1-h;w[k]=h;best=cost,i,w
 return best[1],best[2]
ref=[best_bary(x) for x in L[len(core):,:2]]
faces=np.array([i for i,w in ref]); bw=np.array([w for i,w in ref]); assert np.allclose(bw.sum(1),1) and bw.min()>-1e-9
anchors=np.einsum('ij,ijk->ik',bw,Ga[GT[faces]])
residual=R[backing]-anchors
assert np.max(abs(anchors+residual-R[backing]))<1e-10 and np.max(np.abs(o+L[:len(core)]@Q.T-R[core]))<1e-10
# Continuously interpolated inner → outer geometric carrier; outer ring
# follows nearby untouched backing, never modifies a lace span globally.
# Any seam mutation is confined to matched seed-connected raw IDs.
dist=np.linalg.norm((Ga[:,None,:]-R[backing][None,:,:])@Q[:,:2],axis=-1)
near=np.argsort(dist,axis=1)[:,:5]
cost=np.take_along_axis(dist,near,axis=1)
influence=(cost+.0006)**-2;influence/=influence.sum(axis=1,keepdims=True)
def valid(x):
 v=x[T[adj]]; return np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0])
em=np.isin(E,part).any(1);ee=E[em];eids=np.flatnonzero(em)
both=np.isin(ee,core).all(1)
adj=np.flatnonzero(np.isin(T,part).any(1))
rest_n=valid(R);area=np.linalg.norm(rest_n,axis=1)
rest_len=np.linalg.norm(R[ee[:,1]]-R[ee[:,0]],axis=1); ok=rest_len>.0008
held=[]
for k,raw in enumerate(X):
 A0=R[backing]; B0=raw[backing]; mu=A0.mean(0);nu=B0.mean(0)
 U,S,V=np.linalg.svd((A0-mu).T@(B0-nu)); C=np.diag([1.,1.,np.sign(np.linalg.det(U@V))]); q=U@C@V
 t=nu-mu@q
 assert np.linalg.det(q)>.999999
 rigid_eye=eyed@q+t
 original_edges=np.linalg.norm(eyed[edge[:,1]]-eyed[edge[:,0]],axis=1)
 moved_edges=np.linalg.norm(rigid_eye[edge[:,1]]-rigid_eye[edge[:,0]],axis=1)
 assert np.max(abs(original_edges-moved_edges))<1e-10
 rig_g=Ga@q+t
 sample=np.einsum('ij,ijk->ik',influence,(raw[backing]-R[backing])[near])
 # inboard ring one mechanical boundary, mid ring guided, outside skin compliance.
 mix=np.repeat([1.,.55,0.],n)
 pos=rig_g*mix[:,None]+(Ga+sample)*(1-mix[:,None])
 Y=raw.copy()
 Y[core]=R[core]@q+t
 emb=np.einsum('ij,ijk->ik',bw,pos[GT[faces]])+residual@q
 radii=np.linalg.norm(L[len(core):,:2],axis=1)
 p=np.clip((.0084-radii)/.0038,0,1)
 p=p*p*(3-2*p)
 Y[backing]=raw[backing]+p[:,None]*(emb-raw[backing])
 non=~np.isin(np.arange(len(R)),part)
 assert np.array_equal(Y[non],raw[non])
 for side in ('L','R'):
  pin=A['footprint'+side];boot=A['boot'+side]
  sole=boot[R[boot,2]<.040]
  assert np.array_equal(Y[pin],raw[pin]) and np.array_equal(Y[sole],raw[sole])
  assert Y[boot,2].min()==raw[boot,2].min()
 rb=[np.linalg.norm(x[ee[:,1]]-x[ee[:,0]],axis=1)[ok]/rest_len[ok] for x in (raw,Y)]
 nn=rest_n@q
 keep=area>2e-8
 quot=[(valid(g)[keep]*nn[keep]).sum(1)/(area[keep]**2) for g in (raw,Y)]
 bv1=np.cross((pos[GT])[:,1]-(pos[GT])[:,0],(pos[GT])[:,2]-(pos[GT])[:,0])
 bv0=np.cross((Ga[GT])[:,1]-(Ga[GT])[:,0],(Ga[GT])[:,2]-(Ga[GT])[:,0])
 backing_signed=(bv1*(bv0@q)).sum(1)/(np.linalg.norm(bv0,axis=1)**2)
 held.append({'t_ms':[0,75,150][k],'det_proper':float(np.linalg.det(q)),
   'core_internal_guarded_edges':int((both&ok).sum()),'core_length_ratio_error_max':float(np.max(abs(rb[1][both[ok]]-1.))),
   'edge_bad_before_after':[int(((v<.5)|(v>2)).sum()) for v in rb],
   'signed_area_bad_before_after':[int(((v<.5)|(v>2)).sum()) for v in quot],
   'signed_area_reversals_before_after':[int((v<=0).sum()) for v in quot],
   'failed_edge_ids_after':eids[ok][(rb[1]<.5)|(rb[1]>2)].tolist(),'extremal_signed_face_ijk':int(adj[keep][quot[1].argmin()]),
   'backing_signed_min':float(backing_signed.min()),'backing_signed_max':float(backing_signed.max()),
   'floor_min_exact':True,'maximum_local_change_mm':float(np.linalg.norm(Y[part]-raw[part],axis=1).max()*1e3),
   'source_outside_exact':True})
 held[-1]['hidden_kinematics_only_no_global_visibility']=True
 if k==0: yr=Y[part][None,:,:]; all_eye=rigid_eye[None,:,:]; all_back=pos[None,:,:]
 else: yr=np.concatenate((yr,Y[part][None,:,:]));all_eye=np.concatenate((all_eye,rigid_eye[None,:,:]));all_back=np.concatenate((all_back,pos[None,:,:]))
# Store exact patch carrier mapping and introduced internal geometry separately;
# raw index/UV arrays remain from source and no mesh/rig exporter is present.
np.savez_compressed(P/'internal-design-diagnostic.npz',local_part=part,core_raw=core,backing_raw=backing,tri_assoc=faces,tri_bary=bw,residual_m=residual,
 source_rest_visible=R[part],posed_visible_patches=yr,mount_rest=eyed,mount_tri=et,backing_rest=Ga,backing_tri=GT,mount_pose=all_eye,backing_pose=all_back)
(P/'result.json').write_text(json.dumps({'status':'HOLD_VISIBLE_AND_BACKING_GUARDS_FAIL','scope':'R medial port 3 only','actual_mesh_core_vertices':len(core),
 'backing_vertices':len(backing),'hidden_parts_authored_not_observed':True,'eyelet_watertight':True,'source_pose_count':len(held),
 'unchanged_source_rest_reconstruction_error_m':float(np.max(abs(anchors+residual-R[backing]))),
 'input_atlas_or_outside_unchanged':True,'poses':held},indent=2)+'\n')
