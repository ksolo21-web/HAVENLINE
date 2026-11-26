from inputs import *
import numpy as np,json
from collections import Counter,defaultdict
from scipy.spatial import cKDTree
from pathlib import Path
# Actual heavily foot-driven preexisting sole/heel/ball rows remain on the
# lower retained shell. Split by directed original topology edge vertices only.
Rfoot=(V[:,0]<-.04)&(V[:,1]<.3)
strong=Rfoot&((f.weight('RHeel')>=.96)|(f.weight('RBall')>=.96))
strong_top=float(V[strong,1].max())
alow=strong_top+0.000001
cuff=Rfoot&(f.weight('RCollarFlex')>.01)
ahigh=float(V[cuff,1].max())+.000001
print('lower upper',alow,ahigh)
lower=(V[F,0]<-.04).all(1)&(V[F,1]<=alow).all(1)
replace=(V[F,0]<-.04).all(1)&(~lower)&(V[F,1]<ahigh).any(1)
top=~(lower|replace)
print('lower upper faces',lower.sum(),replace.sum(), 'max span',V[F[replace],1].max(),'strong inside',np.isin(np.unique(F[lower]),np.flatnonzero(strong)).sum(),strong.sum(),'all support?',not (set(f.bounds['R']['faces'].ravel())-set(F[lower].ravel())))
def border(a,b):
 es=[(k,[(i,j,l) for i,j,l in g if a[i]],[(i,j,l) for i,j,l in g if b[i]]) for k,g in edge_face.items() if len(g)==2 and (a[g[0][0]]!=a[g[1][0]]) and (a[g[0][0]] and b[g[1][0]] or a[g[1][0]] and b[g[0][0]])]
 cnt=Counter(i for k,_,_ in es for i in k);print('edges',len(es),'degree',Counter(cnt.values()))
 g=defaultdict(list)
 for (i,j),_,_ in es:g[i].append(j);g[j].append(i)
 seen=set(g)
 comps=[]
 while seen:
  first=min(seen);todo={first};s=set(todo)
  while todo:
   todo=set(y for i in todo for y in g[i])-s;s|=todo
  seen-=s;comps.append(s)
 print('comps',[len(s) for s in comps])
 return es,g,comps
el,gl,cl=border(lower,replace);eu,gu,cu=border(top,replace)
