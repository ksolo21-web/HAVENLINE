import os
import json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent;A=np.load(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
v=A['rest'].astype(float);t=A['tri'];ee=A['E'];w=A['weights']
_,rep,ix=np.unique(np.rint(v/1e-6).astype(np.int64),axis=0,return_index=True,return_inverse=True)
I=json.loads((P/'mounts.json').read_text())['staged_islands']
clean=[a for a in I if a['disposition'].startswith('structural')]
hard=np.zeros(len(rep),bool);compliant=np.zeros(len(rep),bool);unknown=np.zeros(len(rep),bool)
assign=np.full(len(rep),-1)
for i,r in enumerate(I):
 k=r['observed_core_weld'];unknown[r['withheld_disconnected_welds']]=True
 if r not in clean: unknown[k]=True;continue
 assert np.all(assign[k]==-1)
 assign[k]=i;hard[k]=True;compliant[r['backing_weld']]=True
inters=int(sum(hard&compliant))
out={'hard_welded_count':int(hard.sum()),'candidate_leather_backing_welded_count':int(compliant.sum()),'hard_backing_overlap_welded':inters,'unknown_observed_welded_count':int(unknown.sum()),'unmapped_unknown_may_overlap':'left medial hidden topology has no complete coverage estimate','keys':{}}
for j,s in enumerate('LR'):
 eidx=A['edge'+s];E=ee[eidx];dn=np.linalg.norm(v[E[:,1]]-v[E[:,0]],axis=1)
 pure=(w[:,j*4+2:j*4+4].sum(1)>.99999)|(v[:,2]<=.075)
 pure[A['footprint'+s]]=True
 pure_w=np.zeros(len(rep),bool);pure_w[ix[pure]]=True
 X=ix[E]
 locks=(pure_w|hard)[X]
 none=~locks.any(1)
 res=[]
 for x in A['frames']:
  r=np.linalg.norm(x[E[:,1]]-x[E[:,0]],axis=1)/dn;f=(r<.5)|(r>2)
  AS=assign[X]
  same=(AS[:,0]>=0)&(AS[:,0]==AS[:,1]);different=(AS[:,0]>=0)&(AS[:,1]>=0)&(AS[:,0]!=AS[:,1])
  res.append(dict(guard_fail=int(sum(f)),frozen_sole_plus_connected_candidate_both_pinned=int(sum(f&locks.all(1))),same_hardware_island_bad=int(sum(f&same)),same_hardware_ids=eidx[f&same].tolist(),different_hardware_island_bad=int(sum(f&different)),known_unknown_endpoint_incidence=int(sum(f&unknown[X].any(1))),untouched_geometric_guarded=int(sum(f&none))))
 out['keys'][s]=res
(P/'coverage.json').write_text(json.dumps(out,indent=2));print(out)
