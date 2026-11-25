import os
import numpy as np,json,hashlib,struct
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P=Path(__file__).resolve().parent
H=Path(os.environ['C1_ISLAND_DIR'])
A=Path(os.environ['C1_KNEE_DATA'])
S=Path(os.environ['C1_EXACT_GLB'])
F=Path(os.environ['C1_EXACT_BLEND'])
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert h(H/'islands.json')=='737acd66bdc028d0bbe7e25afc3e9d42f1c67591d3939c218524664145ef44fb'
assert h(A/'poses.npz')=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert h(S)=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
assert h(F)=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
d=np.load(A/'poses.npz');R=d['rest'].astype(float);E=d['E']; T=d['tri'];X=d['frames'].astype(float);W=d['weights']
source=json.loads((H/'islands.json').read_text())['observations']
raw=S.read_bytes(); n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);k=28+n
uv_id=g['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
uv_a=g['accessors'][uv_id]; vw=g['bufferViews'][uv_a['bufferView']]
assert uv_a['type']=='VEC2' and uv_a['componentType']==5126
uv=np.ndarray((uv_a['count'],2),dtype='<f4',buffer=raw,offset=k+vw.get('byteOffset',0)+uv_a.get('byteOffset',0),strides=(vw.get('byteStride',8),4))
_,rep,ix=np.unique(np.rint(R/1e-6).astype(np.int64),axis=0,return_index=True,return_inverse=True)
M=R[rep]; wt=ix[T]
se=np.unique(np.sort(ix[E],axis=1),axis=0);se=se[se[:,0]!=se[:,1]]
Sgraph=coo_matrix((np.ones(len(se)),se.T),shape=(len(M),len(M))).tocsr();Sgraph=Sgraph+Sgraph.T
def components(nodes):
 nodes=np.asarray(sorted(set(nodes)),dtype=int)
 return nodes,connected_components(Sgraph[nodes][:,nodes],directed=False)[1]
def nbr(nodes):return set(Sgraph[np.asarray(sorted(nodes))].indices.tolist()) if nodes else set()
def proper(p,q):
 po=np.mean(p,axis=0);qo=np.mean(q,axis=0);P=p-po;Q=q-qo
 U,s,V=np.linalg.svd(P.T@Q); D=np.eye(3);D[-1,-1]=np.sign(np.linalg.det(U@V))
 rot=U@D@V; tr=qo-po@rot
 return rot,tr,s
def stats(v):return dict(max=float(v.max()*1000),rms=float(np.sqrt(np.mean(v**2))*1000))
results=[]
for j,o in enumerate(source):
 raw_ids=np.asarray(o['raw_seam_aliases'],int); seed=int(ix[o['raw'][0]])
 ids,lab=components(o['welded_ids'])
 assert seed in ids
 si=int(lab[np.where(ids==seed)[0][0]]); K=set(ids[lab==si].tolist()); unknown=sorted(set(ids)-K)
 # Candidate core islands use their seed-connected actual shell; nothing dropped
 # may be classified soft or attached, only unknown. Hard statuses remain provisional.
 assert set(ix[o['raw']]).issubset(K)
 f=np.flatnonzero(np.isin(wt,list(K)).all(1))
 adjacent=set(np.flatnonzero(np.isin(wt,list(K)).any(1)).tolist())
 af=sorted(adjacent-set(f))
 bb1=nbr(K)-K; bb2=nbr(bb1)-K-bb1
 # Explicit leather backing is outward from core skin border in same connected
 # source slot, near rest face-normal tangent, not a cut or owner-approved mount.
 normal=np.asarray(o['normal']);origin=np.asarray(o['xyz_175_m'])
 skin=[]
 for q1 in sorted(bb1|bb2):
  dd=M[q1]-origin
  if np.linalg.norm(dd)<.018 and -0.016<dd@normal<.004:
   skin.append(q1)
 skin=np.asarray(skin,int)
 core=np.asarray(sorted(K),int)
 aliases=np.flatnonzero(np.isin(ix,core))
 fcoords=uv[T[f]].astype(float)
 UVarea=np.abs((fcoords[:,1,0]-fcoords[:,0,0])*(fcoords[:,2,1]-fcoords[:,0,1])-(fcoords[:,1,1]-fcoords[:,0,1])*(fcoords[:,2,0]-fcoords[:,0,0]))*.5
 if len(f):
  Fuv=T[f]; fe=np.sort(Fuv[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
  ue,l=np.unique(fe,return_counts=True,axis=0)
  uv_boundary_edges=int(sum(l==1))
 else:uv_boundary_edges=0
 by={'index':j,'side':o['side'],'aspect':o['side_view'],'label':o['label'],'observed_relief_mm':o['relieffront_mm'],'pixel_seed_face':o['face'],'source_component_sizes':np.bincount(lab).tolist(),'observed_core_weld':core.tolist(),'core_raw_aliases':aliases.tolist(),'withheld_disconnected_welds':unknown,'withheld_disconnected_raw_aliases':np.flatnonzero(np.isin(ix,unknown)).tolist(),'core_faces':f.tolist(),'seam_incident_faces':af,'backing_weld':skin.tolist(),'backing_raw_aliases':np.flatnonzero(np.isin(ix,skin)).tolist(),'uv_nondegenerate_face_count':int(sum(UVarea>1e-12)),'uv_boundary_edges':uv_boundary_edges,'rest_bary_center_m':origin.tolist(),'observed_other_views':sum(int(k)!=o['view'] and rec['visible'] for k,rec in o['projected_witness'].items()),'held_shape_fits':[]}
 # Source local frame uses proper outward normal and gravity-referenced tangent;
 # allocate leather backing motion to a future constrained mount, not existing unrelated bone.
 up=np.array([0.,0.,1.])-normal*normal[2]; up/=np.linalg.norm(up)
 basis=np.stack((np.cross(up,normal),up,normal),axis=1)
 assert np.linalg.det(basis)>.999999
 by['rest_surface_frame_columns']=basis.tolist()
 if len(core)<4 or len(f)<2:by['disposition']='withheld triangular stud'
 elif not by['observed_other_views']:by['disposition']='withheld single-view port'
 elif len(skin)<6 or by['uv_nondegenerate_face_count']<len(f):by['disposition']='withheld insufficient connected backing/UV'
 else:by['disposition']='structural rest design admitted as candidate, not complete island'
 if len(skin)>=4:
  for posed in X:
   p=M[skin]; q=posed[rep[skin]]
   m,t,s=proper(p,q)
   Wcore=M[core]@m+t
   m2,t2,s2=proper(M[core],posed[rep[core]])
   by['held_shape_fits'].append({'proper_backing_fit':stats(np.linalg.norm(p@m+t-q,axis=1)),'held_core_residual_to_backing':stats(np.linalg.norm(Wcore-posed[rep[core]],axis=1)),'held_core_best_rigid_residual':stats(np.linalg.norm(M[core]@m2+t2-posed[rep[core]],axis=1)),'leather_rank_sigmas':s.tolist()})
 results.append(by)
out={'staged_islands':results,'withheld_other':['left medial/occluded','entire lace spans and hidden lace routes','unidentified collar band material and complete hardware peripheral extent','rigid island mounts not assigned to rig bones'],'role_contract':{'hardware':'proper rigid rest attachment root at annotated frame; capture leather seam rotation through local compliant annulus, no identity move at rest','lace':'hold localized port endpoint in backing frame with slip/length slack; permit spanning lace flex and no automatic transitive rigid mask','outsole':'original sole/forefoot source indices remain fixed with exact existing Foot/Toe driver','everything_else':'unknown until silhouette-preservation segmentation authority; define independently, not copy mirrored'} }
(P/'mounts.json').write_text(json.dumps(out,indent=2,default=lambda n:n.item()))
for a in results:print(a['index'],a['side'],a['label'],a['source_component_sizes'],len(a['backing_weld']),a['disposition'],[(round(p['held_core_residual_to_backing']['max'],3),round(p['held_core_best_rigid_residual']['max'],3)) for p in a['held_shape_fits']])
