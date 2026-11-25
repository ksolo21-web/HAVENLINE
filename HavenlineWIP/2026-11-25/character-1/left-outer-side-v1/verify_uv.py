import os
import numpy as np
from collections import Counter
from pathlib import Path
p=Path(__file__).parent
base=np.load(Path(os.environ['C1_ORDERED_COLLAR']))
cur=np.load(p/'editable_left_side.npz')
bf=base['combined_local_triangles'];bu=base['corner_uv'];f=cur['combined_tri'];uv=cur['corner_uv']
assert np.array_equal(f[:len(bf)],bf) and np.array_equal(uv[:len(bu)],bu)
def edges(F,U):
  index={};c=Counter()
  for f,u in zip(F,U):
    for i,j in ((0,1),(1,2),(2,0)):
      e=(int(f[i]),int(f[j]));c[e]+=1;index[e]=(u[i],u[j])
  return c,index
bc,bi=edges(bf,bu);cc,ci=edges(f,uv)
num=0
for seq in (cur['source_open_dorsal_path'],cur['source_open_web']):
  for i,j in zip(seq,seq[1:]):
    assert not bc[i,j] and bc[j,i]==cc[i,j]==cc[j,i]==1
    assert np.array_equal(ci[i,j][0],bi[j,i][1]) and np.array_equal(ci[i,j][1],bi[j,i][0])
    num+=1
assert num==5
print('5/5 directed sewn edges, 10/10 inherited seam-corner UVs, 105/105 inherited triangle UV rows unchanged.')
