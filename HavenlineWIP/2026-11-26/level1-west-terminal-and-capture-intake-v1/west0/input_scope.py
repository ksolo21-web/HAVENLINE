from pathlib import Path
import hashlib,numpy as np,json
from collections import Counter
P=Path(__file__).resolve().parent;H=P.parent
prior=H/'hvn-l1-fence-33036-west0-joint-feasibility-v2'
assert hashlib.sha256((prior/'SHA256SUMS').read_bytes()).hexdigest()=='1ffa19a7eb699b95b045d02abbece86518fa873ccaa540a882c7a9716bd8bd85'
s=(prior/'audit.py').read_text();env={'__file__':str(prior/'audit.py')}
exec(s[:s.index('hits=contacts()')],env)
U,M,N=env['U'],env['SM'],env['N']
def audit(T):
 p=T.reshape(-1,3)
 ids=np.unique(np.around(p,9),axis=0,return_inverse=True)[1].reshape(-1,3)
 c=Counter(tuple(sorted((x,y))) for t in ids for x,y in zip(t,np.roll(t,-1)))
 return {'triangles':len(T),'bounds':[p.min(0).tolist(),p.max(0).tolist()],'edge_counts':dict(Counter(c.values()))}
if __name__=='__main__': print(json.dumps({'stock':{g:audit(U[M==g]) for g in set(M)},'owner':{g:audit(t) for g,t in N.items()}},indent=2))
