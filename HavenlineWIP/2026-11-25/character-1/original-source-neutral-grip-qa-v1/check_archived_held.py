import json,sys
from pathlib import Path
import numpy as np
from qa import P,source,candidate
B,H,S,C,T=source(dict(zip(P,[Path(x) for x in sys.argv[1:]])))
# Negative controls only in memory. Adjacent source faces are chosen as witnesses to
# exercise the interface, not approved palm authority; the independent all-body scan
# does not consult these allowed witness IDs or the allowed edit mask.
A={'allowed_vertices':np.array([8595,416575])}
D={'posed':H['held'],'faces':H['faces'],'rest':B['P'],'weights':B['W'],'joint_names':B['names'],'tool_triangles':T}
for name,anchor in [('R',8595),('L',416575)]:
 A[name+'_palm_face_ids']=np.flatnonzero((B['F']==anchor).any(1))
 D[name+'_witness_ix']=0
out={'authentic_chest_held_negative':candidate(B,H,S,C,T,D,A)}
assert out['authentic_chest_held_negative']['strict_whole_pose_tool_surface_pairs']>0
v=D['posed'].copy();v[0,0]+=.001
assert candidate(B,H,S,C,T,{**D,'posed':v},A)['decision']=='HOLD_OUTSIDE_SCOPE_GEOMETRY_CHANGED'
assert candidate(B,H,S,C,T,{**D,'tool_triangles':T+[0,0,.001]},A)['decision']=='HOLD_AXE_OR_FRAME_CHANGED'
print(json.dumps(out,sort_keys=True,indent=2))
