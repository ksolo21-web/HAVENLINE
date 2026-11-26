from components import *
from closed import loops
for g in sorted(set(M)):
 ia=np.flatnonzero(M==g)
 for ids in components(U[M==g]):
  T=U[ia[ids]]
  if T[:,:,2].max()<4.465:continue
  print(g,len(T),ia[ids],json.dumps([s.tolist() for s in loops(T)]))
