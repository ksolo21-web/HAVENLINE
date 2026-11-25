import os
import numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parent
a=np.load((Path(os.environ['C1_COLLAR_DATA'])/'exact-assembled-surface.npz'));b=np.load(P/'new-rear-panel.npz')
# Analytical section extrema of mesh intersections with height planes.
# 0.35mm sampled height gate, no image synthesis. Separate front and side.
def edges(T):
 s=T[:,((0,1),(1,2),(2,0))].reshape(-1,2);return np.unique(np.sort(s,axis=1),axis=0)
fs=np.linspace(.356,.501,416)
def spans(v,t):
 E=edges(t);s=v[E];lo=s[:,:,2].min(1);hi=s[:,:,2].max(1)
 out=[]
 for z in fs:
  a=s[(lo<=z)&(hi>=z)&(hi>lo)]
  w=(z-a[:,0,2])/(a[:,1,2]-a[:,0,2])
  x=a[:,0,:2]+w[:,None]*(a[:,1,:2]-a[:,0,:2])
  out.append(np.r_[x.min(0),x.max(0)])
 return np.asarray(out)
q=spans(a['v'],a['tri']);r=spans(b['v'],b['tri'])
v=abs(q-r).max(0)*1000
z={'height_samples':len(fs),'extent_max_delta_mm_minX_minY_maxX_maxY':v.tolist(),'gate':bool(v.max()<.07)}
(P/'silhouette.json').write_text(json.dumps(z,indent=2));print(z)
