import numpy as np,json,hashlib
from pathlib import Path
from itertools import permutations
P=Path(__file__).resolve().parent
path=P.parent/'hvn-l1-c1-newer-knee-flex-v1/poses.npz'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
a=np.load(path); V=a['rest'].astype(float); E=a['E']; W=a['weights']; xs=V[:,0]; z=V[:,2]
_,rep,iw=np.unique(np.rint(V/1e-6).astype('int64'),axis=0,return_index=True,return_inverse=True)
R=V[rep];z0=R[:,2]; x0=R[:,0]
payload={}; records={}
# Rest cage only. A prescribed whole thigh/ankle/shin mesh that extends
# to the dorsal root of the fixed boots, not a posterior sleeve.
N=np.array([6,6,14]); grid=np.indices(tuple(N+1)).reshape(3,-1).T
def gn(x):return np.ravel_multi_index(np.asarray(x).T,tuple(N+1))
def metric(v):return np.linalg.norm(v,axis=-1)
for j,s in enumerate('LR'):
 H,K,A,T=a['joints'][j]; w=W[:,j*4:j*4+4]
 group=(w.sum(1)>.85)&((1 if s=='L' else -1)*xs>.025)&(z>.075)&(z<float(H[2])+.02)
 fixed=(z<=.075)|(w[:,2:].sum(1)>=.99999)
 fixed[a['footprint'+s]]=1
 guard=np.zeros(len(R),bool);guard[iw[fixed|~group]]=True
 edit=group&~guard[iw]; assert np.array_equal(edit,edit[rep][iw])
 ui=R[edit[rep]]
 lo=ui.min(0)-.008;hi=ui.max(0)+.008
 dd=(hi-lo)/N
 knots=lo+grid*dd
 x=(ui-lo)/dd; cell=np.floor(x).astype(int); frac=x-cell
 order=np.argsort(-frac,axis=1,kind='stable')
 e=np.eye(3,dtype=int)
 t=np.stack((cell,cell+e[order[:,0]],cell+e[order[:,0]]+e[order[:,1]],cell+1),axis=1)
 tids=np.stack([gn(t[:,j]) for j in range(4)],axis=1)
 ff=np.take_along_axis(frac,order,axis=1)
 bar=np.column_stack((1-ff[:,0],ff[:,0]-ff[:,1],ff[:,1]-ff[:,2],ff[:,2]))
 rest_repro=(knots[tids]*bar[:,:,None]).sum(1)
 err=np.max(metric(rest_repro-ui))
 delta_frozen=np.zeros_like(V)
 delta_frozen[edit]=(rest_repro-ui)[np.searchsorted(np.flatnonzero(edit[rep]),iw[edit])]
 assert err<1e-12 and np.array_equal(delta_frozen[~edit],np.zeros_like(V[~edit]))
 # Freudenthal global diagonal: shared cube-face triangulation, volume
 # connectivity and signed winding established on immutable rest.
 cells=np.indices(tuple(N)).reshape(3,-1).T; tets=[]
 for q in permutations(range(3)):
  tet=np.stack([gn(cells),gn(cells+e[q[0]]),gn(cells+e[q[0]]+e[q[1]]),gn(cells+1)],axis=1)
  b=knots[tet]
  sig=np.linalg.det((b[:,1:]-b[:,0:1]).transpose(0,2,1))
  if sig[0]<0:tet=tet[:,[0,2,1,3]]
  tets.append(tet)
 tet=np.concatenate(tets)
 k=knots[tet]; dv=np.linalg.det((k[:,1:]-k[:,0:1]).transpose(0,2,1))
 assert np.all(dv>0)
 bc=(np.any((grid==0)|(grid==N),axis=1))
 ee=a['edge'+s]; er=E[ee]; L=metric(V[er[:,1]]-V[er[:,0]])
 coverage=[]
 for pose in a['frames']:
  q=metric(pose[er[:,1]]-pose[er[:,0]])/L; bad=(q<.5)|(q>2)
  coverage.append({'phase_fail_count':int(sum(bad)),'rest_proxy_uncovered':int(sum(bad&~edit[er].any(1)))})
 payload.update({s+'nodes':knots,s+'tets':tet,s+'fixed_outer_cage_nodes':bc,s+'welded_material_ids':np.flatnonzero(edit[rep]),s+'interpolation_tet_nodes':tids,s+'barycentric_weights':bar})
 records[s]={'cage_nodes':len(knots),'tetrahedra':len(tet),'min_rest_signed_tet_volume_m3':float(dv.min()/6),'rest_max_error_m':float(err),'mapped_welded':len(ui),'min_barycentric':float(bar.min()),'all_cage_boundary_nodes_marked_fixed':int(sum(bc)),'phases':coverage,'anchor_contract':'fixed outsole/forefoot and Foot/Toe controls; rigid hardware region irreconcilable with conservative all-boot proxy, needs exact IDs before motion'}
(P/'rest-proxy.json').write_text(json.dumps(records,indent=2));np.savez_compressed(P/'conditional-rest-only-proxy.npz',**payload);print(records)
