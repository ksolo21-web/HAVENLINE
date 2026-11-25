import os
import json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent
x=json.loads((P/'islands.json').read_text()); y=json.loads((P/'impact.json').read_text())
a=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'));E=a['E']
sites=[]
for rec in x['observations']:
 if 'normal' not in rec:continue
 n=np.asarray(rec['normal'],float)
 up=np.array([0,0,1.])-n*n[2]
 if np.linalg.norm(up)<1e-8:continue
 up/=np.linalg.norm(up)
 fx=np.cross(up,n)
 basis=np.stack((fx,up,n),axis=1)
 assert abs(np.linalg.det(basis)-1)<1e-7
 alias=np.array(rec['raw_seam_aliases'])
 sites.append({'side':rec['side'],'view':rec['view'],'aspect':rec['side_view'],'label':rec['label'],'face':rec['face'],'rest_xyz_m':rec['xyz_175_m'],'rest_basis_columns':basis.tolist(),'aliases':alias.tolist(),'assigned_bone':None,'confidence':'observed geometric center; acceptable as rigid attachment core candidate, not as exact full island/material stiffness'})
impact={}
for s,rows in y['endpoint_counts'].items():
 impact[s]=[]
 for row in rows:
  ids=row['locks']['plus observed relief core frozen']['exact_both_locked_edge_ids']
  e=E[ids]
  owner=[]
  for id,ed in zip(ids,e):
   found=[b for b,r in enumerate(sites) if all(int(t) in r['aliases'] for t in ed)]
   owner.append({'edge_id':id,'both_endpoints_same_core_observation':found})
  impact[s].append(owner)
q={'local_rigid_frame_rest_candidates':sites,'core_both_locked_edge_same_core_result':impact,'scope':'Mathematical local attach frame centered on geometric map; no bone parent/follow policy yet. Unknown shapes not forced rigid.'}
(P/'anchors.json').write_text(json.dumps(q,indent=2))
print([(s,[sum(bool(r['both_endpoints_same_core_observation']) for r in rr) for rr in rows]) for s,rows in impact.items()])
