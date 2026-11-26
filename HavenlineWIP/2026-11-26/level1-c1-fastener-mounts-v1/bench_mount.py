"""Isolate each authored mount with a tiny signed repeatable differential; not a gait."""
import json,sys
from pathlib import Path
import numpy as np
from inspect_source import load
from verify import nonadjacent

source,out=map(Path,sys.argv[1:])
_,v,n,u,j,w,t=load(source)
q=np.load(out/'mounts.LOCAL.npz',allow_pickle=False)
P,J,W,F,O=(q[k] for k in ('positions','joints','weights','faces','source_face_map'))
meta=json.loads((out/'build.json').read_text())
out_rows=[]
for name,region in meta['target'].items():
 s=int(name); metal=region['metal_faces']; patch=region['refined_cloth_faces']
 p=P[F[metal]].astype(float)
 # Normal of the actual exposed rigid source area, not a world-axis guess.
 cr=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]); ax=cr.sum(0); ax/=np.linalg.norm(ax)
 wat=np.where(J==s,W,0).sum(1).astype(float)
 affected=np.flatnonzero((wat[F]>0).any(1)); changed=np.flatnonzero(np.isin(O,patch+metal))
 assert set(affected)==set(changed) or set(affected)<set(changed), (s,len(affected),len(changed))
 assert (wat[F[metal]]==1).all()
 assert len(affected)>len(metal)
 ref=P[F[affected]].astype(float)
 rn=np.cross(ref[:,1]-ref[:,0],ref[:,2]-ref[:,0])
 states=[]
 for sign in (-1,1):
  # Physical 0.1 mm in original art coordinates, purely diagnostic.
  delta=ax*sign*.0001; Q=P.astype(float)+wat[:,None]*delta
  V=Q[F[affected]]; norms=np.cross(V[:,1]-V[:,0],V[:,2]-V[:,0])
  assert np.array_equal(Q[wat==0],P[wat==0])
  err=float(np.max(np.abs((Q-P)[F[metal]]-delta)))
  pairs,hits=nonadjacent(Q,F,affected)
  states.append(dict(signed_art_mm=sign*.1,rigid_translation_max_residual_art_m=err,
                     opposite_orientation_count=int(((norms*rn).sum(1)<=0).sum()),
                     finite_nonneighbor_pairs_checked=pairs,proper_intersections=hits))
 out_rows.append(dict(slot=s,metal_parent_faces=len(metal),surface_faces_moved=len(affected),rows=states))
print(json.dumps(dict(gate='single-channel micro-stroke diagnostic only; no actual mount motion authorization, animation, or gait certification',
  results=out_rows),indent=2))
