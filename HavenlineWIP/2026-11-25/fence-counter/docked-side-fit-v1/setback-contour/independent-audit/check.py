"""Exact offline readback: frozen geometry and separate proposed service-ray diagnostics."""
import json,sys,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
p=Path(sys.argv[1]);L=Path(sys.argv[2])
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert H(p/'SHA256SUMS')=='9869ade56e63866dd780f0b125b496f2c303cc87ed918a0d133343c0ba8c6b6d'
for x in (p/'SHA256SUMS').read_text().splitlines():
 digest,n=x.split(maxsplit=1);assert H(p/n)==digest
assert H(L)=='3fd21560d24d14a22cd5d8485cd638cdb4ab85c7078889413547bfe5a515205c'
R=json.loads((p/'result.json').read_bytes());raw=p/'native'
log=(p/'native-route.log').read_text().splitlines()
assert sum(x.startswith('PASS ') for x in log)==119 and not any(x.startswith('FAIL ') for x in log)
assert sum('original stance occupancy excluded by temporary test prism without moving original marker' in x for x in log)==2
assert 'DOCKED_CENTER_ROUTE_RESULT checks=119 failures=0 no_image_stages=12' in log and not (raw/'save-artifacts.txt').read_bytes()
P={j['id']:j for j in [json.loads(x.removeprefix('PRISM_CPU ')) for x in log if x.startswith('PRISM_CPU ')]};assert len(P)==R['native_pose_count']==16
assert all(v['actual_unbound_markers']==R['all_six_immutable_surface_references'] for v in P.values())
code=L.read_text();sys.argv=[sys.argv[0],str(p)]
m={'__name__':'read_only_fixture_library'}
first=code.split("f=raw/'counter.json';")[0].replace("(p/'native-v3-geometry.json')","(p/'result.json')")
exec(compile(first,str(L),'exec'),m)
m['raw']=raw;f=raw/'counter.json';assert H(f)==R['same_donor_sha256'];D=m['tr'](f)
m['D']=D;DN,nd=m['vectors'](D);m.update(DN=DN,nD=nd,DL=D.min(1),DH=D.max(1))
exec(compile('def key(lo,hi):'+code.split('def key(lo,hi):',1)[1].split('state={}')[0],str(L),'exec'),m)
surfaces=json.loads(f.read_text());snum=np.ravel(np.concatenate([np.full(len(x['triangles'])//3,x['surface']) for x in surfaces]))
tid=np.ravel(np.concatenate([np.arange(len(x['triangles'])//3) for x in surfaces]));assert len(snum)==len(D)
# Identify exact board components (not full tray/props).
work=[]
for g in (2,3):
 U=np.flatnonzero(snum==g);T=D[U]
 _,w=np.unique(np.round(T.reshape(-1,3),5),return_inverse=True,axis=0);w=w.reshape(-1,3)
 _,C=connected_components(coo_matrix((np.ones(len(w)*3,dtype=bool),(w.ravel(),w[:,[1,2,0]].ravel()))),directed=False)
 for c in np.unique(C):
    ids=np.flatnonzero(C[w[:,0]]==c)
    if len(ids)!=528: continue
    a,b=T[ids].min((0,1)),T[ids].max((0,1))
    if np.allclose([a[0],b[0],a[1],b[1]],[-1.58,1.58,.915,1.085],atol=.00008,rtol=0):work+=U[ids].tolist()
assert len(work)==2640
def raycast(A,B,idx):
 X=np.asarray(A,float); Q=np.asarray(B,float); V=Q-X;lam=np.linalg.norm(V);U=V/lam
 T=D[idx];N=DN[idx];d=N@U;okay=np.abs(d)>1e-12
 t=np.einsum('ij,ij->i',T[:,0]-X,N)/np.where(okay,d,1.)
 P=X+t[:,None]*U
 for i in range(3):
    cross=np.cross(T[:,(i+1)%3]-T[:,i],P-T[:,i]); okay &= np.einsum('ij,ij->i',cross,N)>=-1e-10
 z=np.flatnonzero(okay&(t>1e-5)&(t<lam+5e-6)); assert len(z)!=0
 j=z[np.argmin(t[z])]; g=idx[j];return int(snum[g]), int(tid[g]), P[j],float(t[j]),float(lam)
T={}
for k in ('Stock','Payment'):
 x,_,z=R['all_six_immutable_surface_references'][k+'RestWitness'];s,i,Y,t,l=raycast([x,1.19,z],[x,.86,z],np.array(sorted(work)))
 a=R['exact_actual_worktop_endpoints'][k];assert s==a['surface'] and i==a['triangle'] and np.linalg.norm(Y-a['point'])<1e-9
 T[k]=Y
phase={}
for tag,S in R['sites'].items():
 f=raw/(tag+'.json'); assert H(f)==S['real_readback_sha256']
 A=m['tr'](f); assert len(A)==96001
 c,_=m['run'](A); assert c==S['entire_donor_pairs']==0,tag
 assert S['native_pose']==P[tag]
 mark={'strict_full_donor_count':c,'native_foot':P[tag]['foot']}
 if 'donor_only_segment_lines_to_actual_stock_payment_surfaces' in S:
    Y={}
    for k,key in S['donor_only_segment_lines_to_actual_stock_payment_surfaces'].items():
      W={}
      for b,j in key.items():
        X=P[tag]['foot'] if b=='foot' else P[tag]['anatomy'][b]
        i,r,Q,t,l=raycast(X,T[k],np.arange(len(D)))
        orig=j['nearest_actual_donor_intersection'];assert (i,r)==(orig['surface'],orig['triangle'])
        assert abs(t-orig['distance_m'])<1e-9 and abs(l-j['straight_line_to_real_worktop_m'])<1e-9
        assert l-t>.0005 and not j['clear_segment_to_target_before_endpoint']
        W[b]={'length_to_exact_board_m':l,'blocked_before_endpoint_by_m':l-t,'first_donor_surface':i,'first_donor_triangle':r}
      Y[k]=W
    mark['line_pivot_collision_diagnostic']=Y
 phase[tag]=mark
 print(tag,c,file=sys.stderr)
rays=[v for s in phase.values() for x in s.get('line_pivot_collision_diagnostic',{}).values() for v in x.values()]
assert len(rays)==48
print(json.dumps({'run':'exact archived captures, no native process or live change','native_steps_passed':119,'rendered_images':0,'original_occupations_denied':2,'distinct_hypothetical_occupations':6,'actual_worktops':{k:v.tolist() for k,v in T.items()},'direct_donor_only_pivot_lines_early_blocked':len(rays),'least_distance_short_of_endpoint_m':min(r['blocked_before_endpoint_by_m'] for r in rays),'sites':phase},indent=2))
