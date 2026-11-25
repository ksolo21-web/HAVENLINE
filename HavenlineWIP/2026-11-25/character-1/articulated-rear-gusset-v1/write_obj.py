import os
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent
A=np.load(P/'gusset.npz')
v=A['v'];T=A['tri'];tags=A['labels'];uv=A['uv'];sel=np.flatnonzero(A['scope']|(tags=='unchanged sewing transition'))
u=np.unique(T[sel]); Rev={k:i+1 for i,k in enumerate(u)}
for kind,pts in [('neutral',v),('held_math_rejected',A['native0'])]:
 with (P/f'authored-regional-gusset-{kind}.obj').open('w') as f:
  f.write('# Candidate geometry only, existing specific PBR referenced in detached Blender source.\n')
  for q in pts[u]:f.write('v '+' '.join('%.10f'%z for z in q)+'\n')
  for qq in uv[sel].reshape(-1,2):f.write('vt '+' '.join('%.10f'%z for z in qq)+'\n')
  for group in ('shin','gusset','thigh','unchanged sewing transition'):
   f.write('g '+group.replace(' ','_')+'\n')
   for j in np.flatnonzero(tags[sel]==group):
    f.write('f '+' '.join(f'{Rev[z]}/{3*j+k+1}' for k,z in enumerate(T[sel[j]]))+'\n')
