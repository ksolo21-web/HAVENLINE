import json,struct,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
root=P.parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel):
 p=root/rel;b=p.read_bytes()
 assert b[:4]==b'glTF'
 n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a
 g=json.loads(b[20:20+n]);return p,g,b,28+n
def get(data,i):
 p,g,b,k=data
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
 typ={5126:'<f4',5125:'<u4',5123:'<u2',5121:'<u1'}[a['componentType']]
 cols={'VEC3':3,'SCALAR':1,'VEC4':4}[a['type']]; n=a['count']
 offset=k+v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((n,cols),dtype=typ,buffer=b,offset=offset,strides=(v.get('byteStride',cols*np.dtype(typ).itemsize),np.dtype(typ).itemsize))
sources={}
paths={'active_stock':'hvn-stock-pose-run.cy7Qk9/project/assets/characters/Character1.glb','newer_direct_owner_visual':'c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb','earlier_owner_v2_draft':'c1-nov24-owner-v2/c1-meshy-draft.glb','retopo_v1_rejected':'c1-ultra-rig-witness-v1/c1-ultra-retopo-rig-witness-v1.glb','retopo_v2_rejected_likeness':'c1-ultra-rig-witness-repair-v2/c1-ultra-retopo-rig-witness-repair-v2.glb'}
rest_archive=root/'hvn-l1-hero-walk-boot-v7/scratch/geometry.npz'
assert h(rest_archive)=='9fac2349626d9719636961f20b92da3c8bfbb4f4098855886f4775cfdad1f9aa'
stock=np.load(rest_archive); st=(stock['rest']-stock['center'])*stock['scale']
for key,rel in paths.items():
 data=read(rel); p,g,b,k=data
 I=[a for m in g['meshes'] for a in m['primitives']]
 assert all(a.get('mode',4)==4 for a in I)
 nodes=[x.get('name','') for x in g.get('nodes',[])]; skins=g.get('skins',[])
 e={'sha':h(p),'bytes':len(b),'rows':sum(g['accessors'][a['attributes']['POSITION']]['count'] for a in I),'triangles':sum(g['accessors'][a['indices']]['count']//3 for a in I),'skins':[len(x['joints']) for x in skins],'animation':[(a.get('name'),len(a['channels'])) for a in g.get('animations',[])],'materials':len(g.get('materials',[])),'textures':len(g.get('textures',[])),'explicit_digit_joint_labels':[nodes[j] for s in skins for j in s['joints'] if any(t in nodes[j].lower() for t in ('index','thumb','middle','ring','pinky','little','finger'))]}
 if key=='active_stock': V=st.copy()
 else:
  # Raw geometry estimates for identity-mapped master and candidate exports only.
  V=np.vstack([get(data,a['attributes']['POSITION']) for a in I]).astype(float)
  V=V[:,[0,2,1]]*np.array([1.,-1,1.])
  e['nonidentity_mesh_node_trs']=any(any(c in node for c in ('matrix','rotation','scale','translation')) and not np.array_equal(np.array(node.get('matrix',[]) ).reshape(-1),np.eye(4).ravel()) for node in g.get('nodes',[]) if 'mesh' in node)
  mi,ma=V.min(0),V.max(0); e['source_extent_xyz']=np.round(ma-mi,7).tolist()
  V=(V-np.array([(mi[0]+ma[0])/2,(mi[1]+ma[1])/2,mi[2]]))*(1.75/(ma[2]-mi[2]))
 if key=='active_stock' or not e['nonidentity_mesh_node_trs']:
  # Direct same selector in height-normalized rest coordinates. No surface correspondence asserted.
  v={}
  for s,j in [('L',1),('R',-1)]:
   vv=V[(V[:,2]<.05)&(j*V[:,0]>.025)]
   mi=vv.min(0);ma=vv.max(0)
   v[s]={'raw_rows':len(vv),'width_maxspan_mm':round(1000*(ma[0]-mi[0]),3),'depth_maxspan_mm':round(1000*(ma[1]-mi[1]),3),'inner_edge_mm':round(1000*np.min(j*vv[:,0]),3),'frontmost_mm':round(-1000*mi[1],3),'rear_most_mm':round(1000*ma[1],3)}
  e['fixed_low_50mm_compare']=v
 sources[key]=e
glbs=sources
assert glbs['active_stock']['sha']=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
assert glbs['newer_direct_owner_visual']['sha']=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
bpath=root/'c1-full-detail-rig-witness-repair-v2/c1-full-detail-rig-weight-repair-v2.blend'
assert h(bpath)=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
owner_sources={x.name:h(x) for x in (root/'c1-nov24-owner-v2').glob('3291*.png')}
out={'candidate_glb':glbs, 'owner_turnaround_sha':owner_sources,'detached_52_rig_sha':h(bpath),'basis_note':'Normalized rest geometry, not deformation or correspondence; stock data from exact prior Blender import; static identity raw GLB uses (X,-Z,Y); height 1.75m for comparative geometric slices and existing in-game actor measurement, no scale edit.'}
(P/'result.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
