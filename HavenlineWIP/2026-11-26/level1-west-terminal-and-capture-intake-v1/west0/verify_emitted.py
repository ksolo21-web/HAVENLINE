from pathlib import Path
from collections import Counter
import numpy as np,json
p=Path(__file__).parent
v=[]; groups={}
for line in (p/'West0_closed_terminal_detached_HOLD.obj').read_text().splitlines():
 a=line.split()
 if a[0]=='o':g=a[1];groups[g]=[]
 elif a[0]=='v':v.append(tuple(map(float,a[1:])))
 elif a[0]=='f':groups[g].append([int(i)-1 for i in a[1:]])
r=json.loads((p/'result.json').read_text())['new_components']
assert groups.keys()==r.keys()
for g,faces in groups.items():
 verts=np.array(v)[faces]
 assert len(verts)==r[g]['triangles']
 edge=Counter((a,b) for f in faces for a,b in [(v[x],v[y]) for x,y in zip(f,f[1:]+f[:1])])
 assert all(edge[(b,a)]==m==1 for (a,b),m in edge.items()),g
 ctr=verts.reshape(-1,3).mean(0);q=verts-ctr
 vol=np.einsum('ij,ij->',q[:,0],np.cross(q[:,1],q[:,2]))/6
 assert vol>0 and abs(vol-r[g]['outward_volume_m3'])<1e-10,g
print(f'verified emitted encoding: {len(groups)} outward closed components')
