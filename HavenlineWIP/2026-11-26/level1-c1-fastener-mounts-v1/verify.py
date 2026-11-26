"""Test a private six-mount build without writing geometry or launching an engine."""
import json,struct,sys,hashlib,importlib.util
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from inspect_source import load,edges,weld
here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('archived_cavity_assess',here/'cavity-assess.py')
ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)

def nonadjacent(V,F,touched):
 # Scan whole rest shell around each replaced parent/candidate child, not
 # only the stitch rings. Count only strict interior plane crossing spans.
 _,alias=weld(V)
 Z=V[F].astype(float); low=Z.min(1); hi=Z.max(1); centers=(low+hi)/2
 r=np.linalg.norm(hi-centers,axis=1); max_r=r.max()
 kd=cKDTree(centers); seen=set(); hit=[]
 for i in sorted(map(int,touched)):
  j=np.array(kd.query_ball_point(centers[i],max_r+r[i]+2e-9),int)
  j=j[((hi[j]>=low[i]-2e-9)&(hi[i]>=low[j]-2e-9)).all(1)]
  j=j[~np.isin(alias[F[j]],alias[F[i]]).any(1)]
  for q in j:
   k=tuple(sorted((i,int(q))))
   if k not in seen:
    seen.add(k)
    s=ind.proper_span(Z[k[0]],Z[k[1]])
    if s is not None: hit.append([*k,s])
 return len(seen),hit

def glb_arrays(blob):
 n=struct.unpack_from('<I',blob,12)[0]; d=json.loads(blob[20:20+n]); raw=memoryview(blob)[28+n:]
 pr=d['meshes'][0]['primitives'][0]
 ret=[]
 for k in ('POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','indices'):
  a=d['accessors'][pr['indices'] if k=='indices' else pr['attributes'][k]]; view=d['bufferViews'][a['bufferView']]
  width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
  dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
  arr=np.frombuffer(raw,dtype=dtype,offset=view.get('byteOffset',0)+a.get('byteOffset',0),count=width*a['count'])
  ret.append(arr.reshape(-1,3 if k=='indices' else width))
 return d,raw,ret

def verify(source,out,project):
 m,v,n,u,j,w,t=load(source)
 q=np.load(out/'mounts.LOCAL.npz',allow_pickle=False)
 b=json.loads((out/'build.json').read_text())
 def hashf(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 assert all(hashf(out/name)==h for name,h in b['artifact_sha256'].items())
 V,N,U,J,W,F=(q[k] for k in ('positions','normals','uv','joints','weights','faces'))
 new_meta, raw1,arr=glb_arrays((out/'Character1-detached-fastener-mounts.LOCAL.glb').read_bytes())
 old_meta, raw0,_=glb_arrays(source.read_bytes())
 assert bytes(raw1[:len(raw0)])==raw0
 assert all(np.array_equal(a,x) for a,x in zip(arr,(V,N,U,J,W,F)))
 assert all(new_meta[k]==old_meta[k] for k in ('materials','images','textures','skins','nodes','animations'))
 assert all(np.array_equal(x[:len(v)],y) for x,y in zip((V,N,U,J,W),(v,n,u,j,w)))
 changed=np.flatnonzero(np.any(F[:len(t)]!=t,axis=1)); origins=q['source_face_map']
 rigid={i for a in b['target'].values() for i in a['metal_faces']}
 assert len(rigid)==82 and not (rigid&set(changed))
 assert len(changed)==120 and set(changed)==set(origins[len(t):])
 assert not np.any(np.isin(j[t[changed]],(6,16)) & (w[t[changed]]>.01))
 assert not (v[t[changed],1].max()>.33)
 assert np.array_equal(V.min(0),v.min(0)) and np.array_equal(V.max(0),v.max(0))
 # Arc/outline: on each source triangle use exact barycentric lineage from
 # the original raw edge, then measure error after Float32 export.
 lineage={int(k):[int(a),int(b)] for _,a,b,k in q['raw_midpoint_indices']}
 proj_tol=0.; uv_tol=0.; rest_tol=0.; area_ratio=0.
 # At locked ortho camera, any affine position error projects at most its
 # 3D Euclidean length times uniform fit scale and pixel density.
 gd=(project/'previews/integrated_opening.gd').read_text()
 layout=json.loads((project/'layout.json').read_text())
 assert all(k in gd for k in ('camera.size = 13.0','Vector3(7, 11, 11)','Camera3D.PROJECTION_ORTHOGONAL'))
 assert 'window/size/viewport_height=720' in (project/'project.godot').read_text()
 pp=(float(layout['actor_height'])/float(np.ptp(v[:,1])))*720/13
 for i in changed:
  source_ids=t[i].tolist(); source_p=v[t[i]].astype(float); source_u=u[t[i]].astype(float)
  nc=np.cross(source_p[1]-source_p[0],source_p[2]-source_p[0]); normal=np.linalg.norm(nc)
  fr=F[np.flatnonzero(origins==i)]
  assert len(fr)==3
  total=0
  for face in fr:
   positions=V[face].astype(float); weights=[]
   for r in face:
    bary=np.zeros(3)
    if int(r) in source_ids:bary[source_ids.index(int(r))]=1
    else:
     for original in lineage[int(r)]:bary[source_ids.index(original)]=.5
    weights.append(bary)
   weights=np.array(weights)
   rest_tol=max(rest_tol,float(np.linalg.norm(positions-weights@source_p,axis=1).max()))
   uv_tol=max(uv_tol,float(np.max(np.abs(U[face]-weights@source_u))))
   n2=np.cross(positions[1]-positions[0], positions[2]-positions[0]); assert n2@nc>0
   total+=np.linalg.norm(n2)
  area_ratio=max(area_ratio,abs(total/normal-1))
 assert rest_tol<2e-8 and uv_tol<1e-7 and area_ratio<5e-5
 proj_tol=rest_tol*pp; assert proj_tol<1.
 # Verify opposite winding and exact welded two-sided local edge incidence;
 # outside unrelated topology is not repaired or reclassified.
 _,aliases=weld(V); FF=aliases[F]
 touched=np.flatnonzero(np.isin(origins,changed))
 patch={tuple(sorted(ee)) for f in touched for ee in edges(FF[f])}
 counts=Counter()
 for tri in FF:
  for a,b in edges(tri):
   if tuple(sorted((a,b))) in patch:counts[a,b]+=1
 assert all(counts[a,b]==counts[b,a]==1 for a,b in patch)
 for row in q['raw_midpoint_indices']:
  s,a,b,k=map(int,row)
  assert np.where(J[a]==s,W[a],0).sum()==1 and np.where(J[k]==s,W[k],0).sum()==0
  assert np.array_equal(J[k],j[b]) and np.array_equal(W[k],w[b])
 assert np.max(np.abs(W.sum(1)-1.))<1e-6
 # Catch a known interior intersection and no tangential/common-edge false count.
 a=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
 z=np.array([[.1,.3,-.5],[.1,.3,.5],[.45,.35,0.]])
 assert ind.proper_span(a,z)>.1 and ind.proper_span(a,a) is None
 tested0,hits0=nonadjacent(v,t,np.r_[changed,sorted(rigid)])
 tested,hits=nonadjacent(V,F,np.r_[touched,sorted(rigid)])
 assert not hits0 and not hits,(hits0,hits)
 return dict(exact_candidate_glb_sha256=hashf(out/'Character1-detached-fastener-mounts.LOCAL.glb'),
      original_num_unmodified_source_vertex_rows=len(v),original_rigid_faces=82,replaced_fabric_faces=len(changed),candidate_fabric_faces=len(touched),
      exact_opposed_incidence_edges=len(patch),max_export_affine_rest_error_art_m=rest_tol,max_hem_geometric_outline_error_at_stock_cam_px_bounded=proj_tol,
      max_relative_parent_area_error=area_ratio,max_uv_affine_error=uv_tol,baseline_strict_pairs_checked=tested0,
      detached_strict_pairs_checked=tested,strict_interior_crossing_pairs=hits,
      independent_mounts_style='original six separate joint channels, closed welded single exterior with flexible skirts, not separate closed fastener bodies',
      original_clips_unchanged_and_not_reviewed=True,gait_or_contact_approval=False,
      normal_view_raster_verified=False,installed=False)
if __name__=='__main__':
 print(json.dumps(verify(*(Path(x) for x in sys.argv[1:])),indent=2))
