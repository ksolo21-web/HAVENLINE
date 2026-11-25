import os
import numpy as np
from pathlib import Path
p=Path(__file__).parent
z=np.load(p/'editable_left_coarse.npz')
u=np.load(Path(os.environ['C1_INTRINSIC_PANELS']))
Q=u['L_0_indices'];UV=u['L_0_uv']; n=len(u['L_0_open'])//2
k={}
for f,uv in zip(Q,UV):
 for i,j in ((0,1),(1,2),(2,0)):
  if f[i]>=n and f[j]>=n:
   k[(f[i]-n,f[j]-n)]=(uv[i],uv[j])
ff=z['sewn_dorsal_faces'];cc=z['proximal_source_split_uv'];src=z['proximal_exact_source_rows']
seen=set()
for f,uv in zip(ff,cc):
 for i,j in ((0,1),(1,2),(2,0)):
  if f[i] == f[j]+1 and f[i]<len(src):
   v,w=k[src[f[j]],src[f[i]]]
   assert np.array_equal(uv[i],w) and np.array_equal(uv[j],v)
   seen.add(int(f[j]))
assert seen==set(range(76))
print('76/76 directed near-arc edges opposite, 152/152 seam corner UV samples identical')
