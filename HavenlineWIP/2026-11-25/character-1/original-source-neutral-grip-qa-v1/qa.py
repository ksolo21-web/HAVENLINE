"""Independent geometry intake, no owner approval, asset/pose edit, native or render."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
P={'bind':'d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336','held':'0484d5e1ee3d9b54e67e7eacdd7df0fe9f5ca44fed8485fd09d5715adba8855f','fixture':'14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4','chest':'b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed','axe':'79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(path):
 for key in P:assert sha(path[key])==P[key],key
 def npz(k):return np.load(path[k],allow_pickle=False)
 B,H,S=[npz(k) for k in ('bind','held','fixture')]
 C=json.loads(path['chest'].read_text())
 raw=path['axe'].read_bytes();n=struct.unpack_from('<I',raw,12)[0]; doc=json.loads(raw[20:20+n]); payload=raw[28+n:]
 assert doc['nodes']==[{'mesh':0,'name':'t09_harvest_axe'}]
 def acc(i,dt,arity):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
  assert 'byteStride' not in v and not a.get('sparse')
  return np.frombuffer(payload,dtype=dt,count=a['count']*arity,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,arity)
 p=doc['meshes'][0]['primitives'][0]
 xyz=acc(p['attributes']['POSITION'],'<f4',3).astype(float)
 xyz=np.column_stack((xyz[:,0],-xyz[:,2],xyz[:,1]))
 xyz=xyz@np.asarray(C['orientation']).T+np.asarray(C['zero_depth_tool_origin'])-np.array([0.,C['only_selected_depth_m'],0.])
 T=xyz[acc(p['indices'],'<u4',1).reshape(-1,3)]
 assert B['F'].shape==H['faces'].shape==(727442,3) and np.array_equal(B['F'],H['faces'])
 assert len(T)==512
 for k,id in [('R',124),('L',276)]:
  assert C['sides'][k]['surface_face_index']==id
  assert np.allclose(T[id],S[k+'_compatible_shaft_face'],atol=1e-8,rtol=0)
 return B,H,S,C,T

def clip(v):
 # Half-plane clips in barycentric coordinates, not projected infinite-plane overlap.
 for idx,offset in [(0,0),(1,0),(2,0)]:
  if not len(v):break
  nxt=[]
  for a,b in zip(v,np.roll(v,-1,axis=0)):
   va=a[idx]-offset;vb=b[idx]-offset
   if va>=0:nxt.append(a)
   if (va<0<vb) or (vb<0<va):nxt.append(a+(b-a)*va/(va-vb))
  v=np.asarray(nxt)
 return v
def bearing(front,facet,outward,tol=0.0001):
 # contact witness defined as local finite support, not signed collision / overall fit.
 A=(facet[1:]-facet[0]).T
 uv=(front-facet[0])@np.linalg.pinv(A).T
 c=np.column_stack((1-uv.sum(1),uv))
 d=(front-facet[0])@outward
 projected=clip(c)
 s=projected@facet if len(projected) else np.empty((0,3))
 area=sum(np.linalg.norm(np.cross(s[i]-s[0],s[i+1]-s[0]))*.5 for i in range(1,len(s)-1))
 full=np.linalg.norm(np.cross(front[1]-front[0],front[2]-front[0]))*.5
 fraction=area/full if full>0 else 0
 flag='FINITE_TANGENT_CONTROL' if np.max(abs(d))<=tol and fraction>=.95 and area>1.e-9 else ('EMBEDDED_SIDE' if d.max() < -tol else ('GAPPED_SIDE' if d.min() > tol else 'WRONG_BAND_OR_OBLIQUE'))
 return {'verdict':flag,'distance_range_mm':[float(d.min()*1000),float(d.max()*1000)],'projected_finite_area_mm2':float(area*1e6),'finite_fraction':float(fraction)}
def controls(H,S,C,T):
 out={}
 for side,id in [('R',124),('L',276)]:
  f=T[id];u=np.array(C['sides'][side]['outward'])
  front=S[side+'_bearing_patch'][:3]
  moved=front+1.1*(f[1]-f[0])
  out[side]={'tangent':bearing(front,f,u),'gapped':bearing(front+.002*u,f,u),'embedded':bearing(front-.002*u,f,u),'same_plane_wrong_band':bearing(moved,f,u),'swapped_anatomy':bearing(S[('L' if side=='R' else 'R')+'_bearing_patch'][:3],f,u),'archived_full_forearm_pairs':int(len(S[side+'_forearm_collision_ids']))}
  assert [out[side][k]['verdict'] for k in ['tangent','gapped','embedded','same_plane_wrong_band']]==['FINITE_TANGENT_CONTROL','GAPPED_SIDE','EMBEDDED_SIDE','WRONG_BAND_OR_OBLIQUE']
  assert out[side]['swapped_anatomy']['verdict']!='FINITE_TANGENT_CONTROL'
 # authentic held array mutation controls for fixed scope, no geometry is written anywhere.
 v=H['held'].copy()
 fixed=np.ones(len(v),bool);fixed[8595]=False
 w=v.copy();w[8595,1]+=.001
 assert np.array_equal(w[fixed],v[fixed])
 w[0,1]+=.001
 assert not np.array_equal(w[fixed],v[fixed])
 return {'fixture_controls':out,'authored_geometry':False,'body_protection_controls':'held reference identity plus rejected out-of-mask motion'}
def motion_custody(H, candidate, allowed):
 V=np.asarray(candidate['posed']); assert np.isfinite(V).all()
 assert np.array_equal(candidate['faces'],H['faces']) and V.shape==H['held'].shape
 assert allowed.ndim==1 and len(np.unique(allowed))==len(allowed) and allowed.min()>=0 and allowed.max()<len(V)
 fixed=np.ones(len(V),bool)
 fixed[allowed]=False
 # Compare exact arrays for fixed-topology intake; not a numerical pose tolerance.
 return np.array_equal(V[fixed],H['held'][fixed])
def overlap(A,B):
 # Exact strict non-coplanar surface intersection detection with conservative AABB pruning.
 amin,amax=A.min(1),A.max(1)
 bmin,bmax=B.min(1),B.max(1)
 def pierce(a,b):
  x=b[:,0]; n=np.cross(b[:,1]-x,b[:,2]-x)
  w=b[:,1]-x; z=b[:,2]-x
  dp=np.einsum('ij,ij->i',w,w);dq=np.einsum('ij,ij->i',z,z);mix=np.einsum('ij,ij->i',w,z)
  det=dp*dq-mix*mix
  ok=np.zeros(len(a),bool)
  for s,t in ((0,1),(1,2),(2,0)):
   ds=np.einsum('ij,ij->i',a[:,s]-x,n);dt=np.einsum('ij,ij->i',a[:,t]-x,n)
   cross=(ds*dt<0)&(det>1.e-20)
   l=np.divide(ds,ds-dt,out=np.zeros_like(ds),where=cross)
   v=a[:,s]+(a[:,t]-a[:,s])*l[:,None]-x
   c=np.einsum('ij,ij->i',v,w);d=np.einsum('ij,ij->i',v,z)
   u=np.divide(c*dq-d*mix,det,out=np.zeros_like(c),where=cross)
   v=np.divide(d*dp-c*mix,det,out=np.zeros_like(d),where=cross)
   ok|=cross&(u>1.e-7)&(v>1.e-7)&(u+v<1-1.e-7)&(l>1.e-7)&(l<1-1.e-7)
  return ok
 count=0
 for start in range(0,len(A),512):
  i,j=np.where(np.all((amin[start:start+512,None,:]<=bmax)&(amax[start:start+512,None,:]>=bmin),axis=2))
  ca,cb=A[start+i],B[j]
  count+=int(np.count_nonzero(pierce(ca,cb)|pierce(cb,ca)))
 return count
def candidate(B,H,S,C,T,D,A):
 if not motion_custody(H,D,A['allowed_vertices']):return {'decision':'HOLD_OUTSIDE_SCOPE_GEOMETRY_CHANGED'}
 F=D['faces'];M=D['posed']
 V=D['rest']; W=D['weights']; allowed=A['allowed_vertices']
 fixed=np.ones(len(M),bool); fixed[allowed]=False
 assert V.shape==B['P'].shape and W.shape==B['W'].shape and np.isfinite(V).all()
 if not np.array_equal(V[fixed],B['P'][fixed]) or not np.array_equal(W[fixed],B['W'][fixed]) or not np.array_equal(D['joint_names'],B['names']):
  return {'decision':'HOLD_PROTECTED_BIND_OR_WEIGHTS_CHANGED'}
 cuff={}
 for side in 'RL':
  edge=S[side+'_loop_source_vertex_edges']; t=S[side+'_loop_source_edge_t'][:,None]
  rebuilt=M[edge[:,0]]*(1-t)+M[edge[:,1]]*t
  cuff[side]=float(np.max(np.linalg.norm(rebuilt-S[side+'_loop_vertices'],axis=1)))
 if max(cuff.values())>1.e-8:return {'decision':'HOLD_LOCKED_CUFF_ANCHORS_CHANGED','cuff_max_delta_m':cuff}
 if not np.allclose(D['tool_triangles'],T,atol=1e-8,rtol=0):return {'decision':'HOLD_AXE_OR_FRAME_CHANGED'}
 witness={}
 for side,id in [('R',124),('L',276)]:
  mask=A[side+'_palm_face_ids']; index=int(D[side+'_witness_ix'])
  assert mask.ndim==1 and len(mask)>0 and 0<=index<len(mask)
  known=mask[index]
  assert np.isscalar(known) and 0<=known<len(F)
  witness[side]=bearing(M[F[known]],T[id],np.array(C['sides'][side]['outward']))
 # No builder-defined masks can hide crossings across retained body or off-band tool faces.
 candidates=M[F]
 near=np.all((candidates.min(1)<=T.max((0,1)))&(candidates.max(1)>=T.min((0,1))),axis=1)
 strict_pairs=overlap(candidates[near],T)
 hold=(strict_pairs or any(w['verdict']!='FINITE_TANGENT_CONTROL' for w in witness.values()))
 return {'decision':'HOLD_OBSERVED_GEOMETRY_FAILURE' if hold else 'HOLD_UNVERIFIED_WEB_CUFF_AND_RENDER_REVIEW','strict_whole_pose_tool_surface_pairs':strict_pairs,'anatomic_facet_witness':witness,'cuff_max_delta_m':cuff}
if __name__=='__main__':
 args=[Path(x) for x in sys.argv[1:]]
 B,H,S,C,T=source(dict(zip(P,args[:5])))
 if len(args)==5:out=controls(H,S,C,T)
 else:
  assert len(args)==8 and sha(args[6])==str(args[7]),'independently issued edit-and-palm witness authority digest required'
  out=candidate(B,H,S,C,T,np.load(args[5],allow_pickle=False),np.load(args[6],allow_pickle=False))
 print(json.dumps(out,sort_keys=True,indent=2))
