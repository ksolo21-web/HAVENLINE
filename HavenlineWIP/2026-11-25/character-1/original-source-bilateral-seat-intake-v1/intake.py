#!/usr/bin/env python3
"""Exact arm material/cuff custody, with no writes to any source."""
import hashlib,io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
files=[Path(x) for x in sys.argv[1:]]
expected=["7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb",
"d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336","0484d5e1ee3d9b54e67e7eacdd7df0fe9f5ca44fed8485fd09d5715adba8855f",
"14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4","b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed",
"79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e"]
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert [digest(p) for p in files]==expected
def glb(path):
 raw=path.read_bytes(); n,t=struct.unpack_from('<II',raw,12)
 assert raw[:4]==b'glTF' and t==0x4e4f534a
 doc=json.loads(raw[20:20+n]); size,b=struct.unpack_from('<II',raw,20+n)
 assert b==0x004e4942 and len(raw)==28+n+size
 def view(i):
  a=doc['bufferViews'][i]; assert 'byteStride' not in a and a['buffer']==0
  return memoryview(raw)[28+n+a.get('byteOffset',0):28+n+a.get('byteOffset',0)+a['byteLength']]
 def acc(i):
  a=doc['accessors'][i];assert not a.get('sparse')
  shape={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  return np.frombuffer(view(a['bufferView']),dtype={5125:'<u4',5126:'<f4'}[a['componentType']],count=a['count']*shape,offset=a.get('byteOffset',0)).reshape(-1,shape)
 prim=doc['meshes'][0]['primitives'][0]
 x=acc(prim['attributes']['POSITION'])
 return np.column_stack((x[:,0],-x[:,2],x[:,1])),acc(prim['indices']).reshape(-1,3),doc,prim,view,acc
p,f,doc,pr,view,acc=glb(files[0]);A,T,*_=glb(files[5]); assert len(T)==512
b,h,s=[np.load(i,allow_pickle=False) for i in files[1:4]]
J=json.loads(files[4].read_text())
P,F,W,names=(b[k] for k in ('P','F','W','names')); V=h['held'].astype(float)
assert np.array_equal(P,p) and np.array_equal(F,f) and np.array_equal(F,h['faces'])
uv=acc(pr['attributes']['TEXCOORD_0']);mat=doc['materials'][pr['material']]
assert len(doc['materials'])==len(doc['meshes'][0]['primitives'])==1
im=mat['pbrMetallicRoughness']['baseColorTexture']; assert im['texCoord']==0
tex=doc['images'][doc['textures'][im['index']]['source']]
I=np.asarray(Image.open(io.BytesIO(view(tex['bufferView']))).convert('RGB'))
def rgb_samples(ids):
 q=uv[ids]; ih,iw=I.shape[:2]
 px=np.minimum((q[:,0]*iw).astype(int),iw-1)
 py=np.minimum((q[:,1]*ih).astype(int),ih-1)
 return I[py,px].tolist()
M=np.array(J['orientation']);t=np.array(J['zero_depth_tool_origin'])-np.array([0.,J['only_selected_depth_m'],0.])
tool=(A@M.T+t)[T]
bis=np.unique(np.sort(F[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0)
a,z=bis.T
def crosses(first,second):
 o=second[0]; e1,e2=second[1:]-o; hits=[]
 for x,y in zip(first,np.roll(first,-1,axis=0)):
  d=y-x; h=np.cross(d,e2); det=e1@h
  if abs(det)<1e-15:continue
  n=x-o; u=(n@h)/det; q=np.cross(n,e1); v=(d@q)/det; t=(e2@q)/det
  if min(u,v,1-u-v,t,1-t)>1e-8:hits.append(x+t*d)
 return hits
O={"status":"SOURCE_CUSTODY_PASS; NO CANDIDATE OR BILATERAL_GRIP_PASS",
   "source_hashes":expected,"exact_vertex_face_map_rows":[len(P),len(F)],"single_indexed_material":True,
   "image_size":list(I.shape[:2][::-1]),"sides":{}}
for S,sign in [('R',-1),('L',1)]:
 r=J['sides'][S]; pi=r['palm_vertex']; E=s[S+'_loop_source_vertex_edges']; v=s[S+'_loop_source_edge_t']
 held=V[E[:,0]]*(1-v[:,None])+V[E[:,1]]*v[:,None];assert np.array_equal(held,s[S+'_loop_vertices'])
 cp=P[E[:,0]]*(1-v[:,None])+P[E[:,1]]*v[:,None]; c=cp.mean(0); u=np.linalg.svd(cp-c)[2][-1];u*=np.sign((P[pi]-c)@u)
 plane=(P-c)@u; assert abs((cp-c)@u).max()<1e-12
 roles=[i for i,n in enumerate(names) if n.endswith('.01.'+S)]
 prim=W[:,roles].argmax(1); mx=W[:,roles].max(1)
 th,idx=[next(j for j,i in enumerate(roles) if str(names[i]).startswith(k)) for k in ('thumb.','index.')]
 owned=(sign*P[:,0]>.52)&(plane>0)
 ok=owned[a]&owned[z]&(mx[a]>300)&(mx[z]>300)&(((prim[a]==th)&(prim[z]==idx))|((prim[z]==th)&(prim[a]==idx)))
 edges=bis[ok]
 web=[]
 for e in edges:
  intersect=np.flatnonzero(np.isin(F,e).sum(1)==2)
  orient=[(int(f[i]),int(f[(i+1)%3])) for f in F[intersect] for i in range(3) if set((int(f[i]),int(f[(i+1)%3])))==set(e)]
  web.append({"edge":e.tolist(),"incident_faces":intersect.tolist(),"two_sided_reverse_winding":len(orient)==2 and orient[0]==orient[1][::-1],
              "unit_uv_seam_at_indexed_edge":False if len(intersect)==2 else None,"source_uv_edge_length":float(np.linalg.norm(uv[e[0]]-uv[e[1]])),
              "bind_edge_mm":float(1000*np.linalg.norm(P[e[0]]-P[e[1]])),
              "held_edge_mm":float(1000*np.linalg.norm(V[e[0]]-V[e[1]])),
              "sampled_source_rgb":rgb_samples(e)})
 # Route from exact, UV-contiguous native web source to the main shared cuff branch.
 xa=bis[owned[bis].all(1)]
 local=np.flatnonzero(owned)
 ij=np.searchsorted(local,xa)
 length=np.linalg.norm(P[xa[:,0]]-P[xa[:,1]],axis=1)
 g=coo_matrix((length,(ij[:,0],ij[:,1])),shape=(len(local),len(local))).tocsr()
 starts=np.unique(edges)
 dist,prev=dijkstra(g,directed=False,indices=np.searchsorted(local,starts),return_predecessors=True)
 main_n=s[S+'_loop_offsets'][1]; eligible=E[:main_n]
 endpoints=(plane[eligible]>0).argmax(1)
 cuff_near=eligible[np.arange(main_n),endpoints]; pars=np.searchsorted(local,cuff_near)
 cap=np.linalg.norm(P[cuff_near]-cp[:main_n],axis=1)
 best=dist[:,pars]+cap
 si,ti=np.unravel_index(int(best.argmin()),best.shape)
 permit=bool(np.isfinite(best[si,ti]))
 route={"exists_without_uv_welding":permit,"scope":"one traced indexed route, not a complete web seam or proposed glove closure"}
 if permit:
  stop=np.searchsorted(local,starts[si]); j=int(pars[ti]); track=[j]
  while j!=stop:
   j=int(prev[si,j]); assert j>=0
   track.append(j)
  vtx=local[list(reversed(track))]
  assert vtx[0]==starts[si] and vtx[-1]==cuff_near[ti] and owned[vtx].all()
  route.update({"track":vtx.tolist(),"main_source_cuff_loop_point_index":int(ti),
      "preserved_cuff_cut_edge":eligible[ti].tolist(),"path_bind_mm_including_cuff_edge_stub":float(1000*best[si,ti]),
      "path_uv_track_length":float(np.linalg.norm(np.diff(uv[vtx],axis=0),axis=1).sum())})
 # If raw index custody splits, diagnose position- and held-identical aliases ONLY.
 # This virtual graph does not authorize smoothing or welding the atlas.
 exact_rows=np.c_[P[local],V[local]]
 _, first, inv, group_count=np.unique(exact_rows,axis=0,return_index=True,return_inverse=True,return_counts=True)
 q0=np.flatnonzero(np.arange(len(local))!=first[inv]); q1=first[inv[q0]]
 assert np.array_equal(exact_rows[q0],exact_rows[q1])
 g2=coo_matrix((np.r_[length,np.full(len(q0),1e-12)],
                (np.r_[ij[:,0],q0],np.r_[ij[:,1],q1])),shape=g.shape).tocsr()
 ds,ps=dijkstra(g2,directed=False,indices=np.searchsorted(local,starts),return_predecessors=True)
 best2=ds[:,pars]+cap
 si2,ti2=np.unravel_index(int(best2.argmin()),best2.shape)
 alias_route={"exists":bool(np.isfinite(best2[si2,ti2])),"scope":"read-only alias diagnostic; both bind and held positions must be bit-identical; UV may jump"}
 if alias_route['exists']:
  j=int(pars[ti2]); stop=np.searchsorted(local,starts[si2]); track=[j]
  while j!=stop:
   j=int(ps[si2,j]); assert j>=0
   track.append(j)
  seg=local[list(reversed(track))]
  transitions=[]
  for a0,b0 in zip(seg,seg[1:]):
   if np.array_equal(P[a0],P[b0]) and np.array_equal(V[a0],V[b0]):
    transitions.append({"ids":[int(a0),int(b0)],"uv_jump":float(np.linalg.norm(uv[a0]-uv[b0])),
                        "source_base_rgb":rgb_samples(np.array([a0,b0]))})
  alias_route.update({"path_bind_mm":float(1000*best2[si2,ti2]),"alias_transitions":transitions,
       "main_source_cuff_loop_point_index":int(ti2),"preserved_cuff_cut_edge":eligible[ti2].tolist(),"indexed_vertices":seg.tolist()})
 heldface=tool[r['surface_face_index']]
 assert np.array_equal(heldface,s[S+'_compatible_shaft_face']) or abs(heldface-s[S+'_compatible_shaft_face']).max()<1e-8
 q=s[S+'_barycentric']@heldface
 seat_area=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))*0.5*1e6
 assert seat_area>300 and s[S+'_barycentric'].min()>0
 # Trace nine interior bearing points into the actual original distal surface; directional
 # first hits are source correspondence only (not a repaired attached seat or volume-free path).
 n0=np.cross(heldface[1]-heldface[0],heldface[2]-heldface[0]); n0/=np.linalg.norm(n0)
 if n0@np.array(r['outward'])<0:n0=-n0
 eligible_ids=np.flatnonzero(owned[F].all(1)); geom=V[F[eligible_ids]]
 tri_a=geom[:,0]; t1=geom[:,1]-tri_a;t2=geom[:,2]-tri_a
 hv=np.cross(np.broadcast_to(n0,t2.shape),t2)
 ds0=np.einsum('ij,ij->i',t1,hv)
 nz=np.abs(ds0)>1e-15
 weights=[(1/3,1/3,1/3),(.62,.19,.19),(.19,.62,.19),(.19,.19,.62),(.45,.45,.1),(.45,.1,.45),(.1,.45,.45),(.29,.32,.39),(.39,.29,.32)]
 footprint=[]
 for w0 in weights:
  pt=np.array(w0)@q
  ss0=pt-tri_a
  uu=np.einsum('ij,ij->i',ss0,hv)/np.where(nz,ds0,1.)
  x0=np.cross(ss0,t1)
  vv=(x0@n0)/np.where(nz,ds0,1.)
  th=np.einsum('ij,ij->i',t2,x0)/np.where(nz,ds0,1.)
  inside=nz&(uu>1e-8)&(vv>1e-8)&(uu+vv<1-1e-8)
  def best_hit(mask):
   ids=np.flatnonzero(mask)
   if not len(ids):return None
   ix=int(ids[np.argmin(abs(th[ids]))])
   return {"source_face":int(eligible_ids[ix]),"signed_line_gap_mm":float(th[ix]*1e3),
       "source_rgb_at_face_vertices":rgb_samples(F[eligible_ids[ix]])}
  footprint.append({"local_fixture_barycentric":w0,"outward_first_distal_mesh":best_hit(inside&(th>0)&(th<=.035)),
                    "inward_first_distal_mesh":best_hit(inside&(th<0)&(th>=-.035))})

 pairs=s[S+'_forearm_collision_ids']
 allrows=F[pairs[:,0]]; contains=(plane[allrows]>0).all(1)
 assert (owned[allrows]).all()
 out_cross=[]
 for i,j in pairs:
  ha,ta=V[F[i]],tool[j]
  hits=crosses(ha,ta)+crosses(ta,ha)
  out_cross.append({"source_face":int(i),"axe_face":int(j),"strict_crossing":bool(hits),
                    "closest_vertex_to_preserved_cut_mm":float(1000*min(plane[F[i]]))})
 O["sides"][S]={"retained_cuff_plane_residual_m":float(abs((cp-c)@u).max()),"exact_indexed_role_edges":web,"exact_uv_preserved_cuff_route":route,"both_bind_and_held_exact_alias_route":alias_route,
                 "candidate_finite_fixture_area_mm2_not_leather_contact":float(seat_area),
                 "candidate_finite_fixture_source_face":int(r['surface_face_index']),
                 "actual_proposed_pressure_skin_attached":False,"finite_seat_probe_35mm_directed_shell_only":footprint,
                 "old_pairs_entirely_distal_to_cut":int(contains.sum()),
                 "old_pairs_with_strict_hit":sum(x['strict_crossing'] for x in out_cross),
                 "old_pair_distances_not_penetration":out_cross}
print(json.dumps(O,indent=2,sort_keys=True))
