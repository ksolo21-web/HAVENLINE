#!/usr/bin/env python3
"""Read exact serialized chest source; extract only, without DCC or edits."""
import hashlib,itertools,json,struct,sys
from pathlib import Path
import numpy as np
paths=[Path(q) for q in sys.argv[1:]]
assert len(paths)==6, "bind.npz held.npz frozen-section.npz chest.json original_axe.glb output-dir"
want=[
"d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336",
"0484d5e1ee3d9b54e67e7eacdd7df0fe9f5ca44fed8485fd09d5715adba8855f",
"14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4",
"b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed",
"79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e"]
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
assert [sha(q) for q in paths[:5]]==want
bind,held,prior=[np.load(q,allow_pickle=False) for q in paths[:3]]
J=json.loads(paths[3].read_text())
raw=paths[4].read_bytes(); n,t=struct.unpack_from('<II',raw,12)
assert raw[:4]==b'glTF' and t==0x4e4f534a
meta=json.loads(raw[20:20+n]); size,bintype=struct.unpack_from('<II',raw,20+n)
assert bintype==0x004e4942 and len(raw)==28+n+size and meta['nodes']==[{'mesh':0,'name':'t09_harvest_axe'}]
def accessor(idx,dtype,arity):
 a=meta['accessors'][idx]; v=meta['bufferViews'][a['bufferView']]
 assert not a.get('sparse') and 'byteStride' not in v and v['buffer']==0
 return np.frombuffer(raw,dtype=dtype,count=a['count']*arity,offset=28+n+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,arity)
prim=meta['meshes'][0]['primitives'][0]; assert prim['mode']==4
G=accessor(prim['attributes']['POSITION'],'<f4',3).astype(np.float64)
GF=accessor(prim['indices'],'<u4',1).reshape(-1,3)
assert GF.shape==(512,3)
A=np.column_stack((G[:,0],-G[:,2],G[:,1]))
M=np.asarray(J['orientation'])
tool_offset=np.asarray(J['zero_depth_tool_origin'])-np.array([0.,J['only_selected_depth_m'],0.])
tool_triangles=(A@M.T+tool_offset)[GF]

P,F,W,names=(bind[k] for k in ('P','F','W','names'))
V=held['held'].astype(np.float64)
assert np.array_equal(F,held['faces']) and F.shape==(727442,3) and P.shape==V.shape==(425291,3)
dom=np.asarray(names)[W.argmax(1)]
whole_edges=np.unique(np.sort(F[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0)
arm_weights=[f'{bone}.{s}' for bone in ('upper_arm','forearm','hand','clavicle') for s in 'RL']
coat=~(np.isin(dom,arm_weights)|(abs(P[:,0])>.48))[F].any(1)
out={"inputs":dict(zip(("bind","held","prior_seam","chest_coordinates","original_axe"),want)),
     "source_faces":len(F),"source_vertices":len(P),"strict_retained_coat_face_count":int(coat.sum()),"sides":{}}
data={}
unit=lambda u:u/np.linalg.norm(u)
def f(x): return np.asarray(x).round(9).tolist()
def section(face_ids, d, vertices):
 rv=[]; ids=[]
 for i in face_ids[(d[F[face_ids]].min(1)<=1e-12)&(d[F[face_ids]].max(1)>=-1e-12)]:
  face=F[i]; values=d[face]; coords=vertices[face]
  points=[coords[j] for j in range(3) if abs(values[j])<=1e-12]
  for a,b in ((0,1),(1,2),(2,0)):
   if values[a]*values[b]<-1e-24:
    t=values[a]/(values[a]-values[b]); points.append(coords[a]+t*(coords[b]-coords[a]))
  if len(points)==2 and np.linalg.norm(points[0]-points[1])>1e-10:
   ids.append(i);rv.append(points)
 return np.asarray(ids,dtype=np.int32),np.asarray(rv).reshape(-1,2,3)
for S,sgn in [('R',-1),('L',1)]:
 r=J['sides'][S]; wrist=np.array(r['wrist']); outward=np.array(r['outward']); Z=-outward
 seed=np.array([0,-1,.11*-(sgn)]); Y=unit(seed-Z*(seed@Z)); X=unit(np.cross(Y,Z))
 B=np.column_stack((X,Y,Z)); assert np.allclose(B.T@B,np.eye(3),atol=1e-12) and np.linalg.det(B)>0
 local=(V-wrist)@B; palm=int(r['palm_vertex'])
 axis_label={'X':'transverse','Y':'longitudinal toward digits','Z':'inward palm normal'}
 cuff_ids=prior[S+'_loop_source_vertex_edges']; cuff_t=prior[S+'_loop_source_edge_t']
 cuff_V=V[cuff_ids[:,0]]*(1-cuff_t[:,None])+V[cuff_ids[:,1]]*cuff_t[:,None]
 cuff_old=prior[S+'_loop_vertices']
 assert np.array_equal(cuff_V,cuff_old) and np.isfinite(prior[S+'_loop_source_uv']).all()
 face=prior[S+'_compatible_shaft_face']; N=unit(np.cross(face[1]-face[0],face[2]-face[0]))
 # Original vertex winding is retained; only normal sign is recovered from exact assigned facet outward.
 if N@outward<0:N=-N
 assert np.allclose(N,outward,atol=1e-8)
 matching=np.min(np.stack([np.linalg.norm(tool_triangles[:,order]-face,axis=-1).max(1)
                  for order in itertools.permutations(range(3))]),axis=0)
 hits=np.flatnonzero(matching<1e-8)
 assert len(hits)==1
 original_index=int(hits[0])
 source_tri=tool_triangles[original_index]
 source_normal=unit(np.cross(source_tri[1]-source_tri[0],source_tri[2]-source_tri[0]))
 assert abs(source_normal@N)>1.-1e-12
 ownership=(sgn*P[:,0]>.52)
 hand_ids=np.flatnonzero(ownership[F].all(1))
 lr=whole_edges.T
 g=[i for i,n in enumerate(names) if n.endswith('.01.'+S)]
 primary=W[:,g].argmax(1); max_weight=W[:,g].max(1)
 t=next(j for j,i in enumerate(g) if names[i].startswith('thumb.')); k=next(j for j,i in enumerate(g) if names[i].startswith('index.'))
 e0,e1=lr
 web_mask=ownership[e0]&ownership[e1]&(max_weight[e0]>300)&(max_weight[e1]>300)&(((primary[e0]==t)&(primary[e1]==k))|((primary[e1]==t)&(primary[e0]==k)))
 web_edges=whole_edges[web_mask]
 assert len(web_edges)==({'R':1,'L':6}[S])
 # Measure original joined mesh at two fixed stations: actual palm site and centroid
 # of source thumb-index role-transition geometry. No pose, fingers or axis sweep.
 palm_y=local[palm,1]; web_y=local[web_edges,1].mean()
 side={"wrist_center_m":f(wrist),"wrist_axes_columns_in_chest_frame":f(B),"axis_semantics":axis_label,
       "palm_vertex":palm,"wrist_to_palm_m_chest":f(V[palm]-wrist),"wrist_to_palm_m_local":f(local[palm]),
       "tool_exact_face":r['surface_face_index'],"tool_glb_source_facet":original_index,
       "source_triangle_max_match_error_m":round(float(matching[original_index]),10),"tool_facet_normal_chest_outward":f(N),"tool_facet_normal_local_outward":f(B.T@N),
       "tool_barycentric":r['bary'],"tool_grip_center_intrinsic_m":r['grip_center_in_original_axis'],
       "pinned_cuff_loop_sizes":np.diff(prior[S+'_loop_offsets']).tolist(),
       "pinned_cuff_uv_rows":len(cuff_ids),"cuff_held_point_max_disagreement_m":0.,
       "web_geometry_role_boundary_edges":len(web_edges), "web_labels_are_not_material":True,
       "web_scope":"thumb.01↔index.01 dominant root weight >30% both vertices; not a full material/continuity authority",
       "prior_minimal_bearing_fixture_only":True,
       "prior_exact_retained_proximal_collision_pairs":len(prior[S+'_proximal_collision_ids']),
       "prior_full_forearm_tool_pairs":len(prior[S+'_forearm_collision_ids']),"cuts":{}}
 for label,y in [('palm',palm_y),('web',web_y)]:
  dd=local[:,1]-y; I,Q=section(hand_ids,dd,V)
  qloc=(Q-wrist)@B
  assert len(I) and np.max(abs(qloc[:,:,1]-y))<1e-10 and not coat[I].any()
  # Retained forearm marks, not undisclosed exclusion by dropping rows.
  own_forearm=(dom[F[I]]==f'forearm.{S}').any(1)
  boundary=(Q-face[0])@N
  side["cuts"][label]={"held_wrist_local_y_m":round(float(y),9),"original_arm_faces_evaluated":len(hand_ids),
          "section_source_segments":len(I),"retained_forearm_dominant_incident_segments":int(own_forearm.sum()),
          "coat_incidental_faces_in_selected_ids":0,
          "tool_facet_infinite_plane_endpoint_range_mm":f(np.array([boundary.min(),boundary.max()])*1000)}
  for k,z in [('faces',I),('segments',Q),('forearm_dominant_incident',own_forearm)]:data[S+'_'+label+'_'+k]=z
 for k,z in [('cuff_vertices',cuff_V),('cuff_source_edges',cuff_ids),('cuff_edge_t',cuff_t),('cuff_faces',prior[S+'_loop_source_faces']),
             ('cuff_uv',prior[S+'_loop_source_uv']),('cuff_loop_offsets',prior[S+'_loop_offsets']),
             ('web_role_edges',web_edges),('web_role_edges_held',V[web_edges]),('intact_tool_face',face),('wrist_basis',B),('wrist',wrist)]:
  data[S+'_'+k]=z
 out['sides'][S]=side
out["status"]="READ_ONLY_HELD_SOURCE_SECTION; NOT CLEARANCE OR A COMPLETE GLOVE"
out["limits"]="Section planes are sampled original shell slices; infinite plane signs are not tool penetration; full cuff/forearm/coat fit, mesh continuity of successors and motion untested."
d=paths[-1]
np.savez_compressed(d/'sections-private.npz',**data)
out['private_arrays_sha256']=sha(d/'sections-private.npz')
print(json.dumps(out,sort_keys=True,indent=2))
