import os
import numpy as np,json,hashlib
from pathlib import Path
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parent
S=Path(os.environ['C1_KNEE_DATA'])
A=np.load(S/'poses.npz'); rest=A['rest'].astype(float); E=A['E']; z=rest[:,2]
W=A['weights']; man=json.loads((P/'islands.json').read_text())
sources=Path(os.environ['C1_OWNER_VIEW_DIR'])
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
refs={name:h(sources/name) for name in ('32911.png','32913.png','c1-front-exact-input.png','c1-left90-exact-input.png','c1-right270-exact-input.png','c1-front45-exact-input.png')}
old=np.load(S/'rejected-material-arrays.npz')['xyz']
_, rep, weld=np.unique(np.rint(rest/1e-6).astype('int64'),axis=0,return_index=True,return_inverse=True)
core=np.zeros(len(rest),bool); uncertain=np.zeros(len(rest),bool)
kd=cKDTree(rest)
core_by=[]
for rec in man['observations']:
 if 'raw' not in rec:continue
 region=np.array(rec['raw_seam_aliases'],int)
 br=np.array(kd.query_ball_point(rec['xyz_175_m'],.0135),int)
 uncertain[region]=True;uncertain[br]=True
 if rec['candidate']=='relief-backed visible core':
  core[region]=True
  core_by.append(rec)
cu=np.zeros(len(rep),bool);cu[weld[uncertain]]=True;uncertain=cu[weld]
assert np.all(uncertain[core])
summary={}
for j,s in enumerate(('L','R')):
 ei=A['edge'+s]; ed=E[ei]
 den=np.linalg.norm(rest[ed[:,0]]-rest[ed[:,1]],axis=1)
 prior_broad=(z<=.075)|(W[:,4*j+2:4*j+4].sum(1)>.99999)
 prior_broad[A['footprint'+s]]=True
 policies={'original outsole and pure distal only':prior_broad,'plus observed relief core frozen':prior_broad|core,'plus measured nearby uncertain region frozen':prior_broad|uncertain}
 rows=[]
 for k,p in enumerate(A['frames']):
  ratio=np.linalg.norm(p[ed[:,0]]-p[ed[:,1]],axis=1)/den
  fail=(ratio<.5)|(ratio>2)
  prior=fail&((np.abs(p[ed]-old[k,ed]).max(2))<1e-9).all(1)
  row={}
  for name,B0 in policies.items():
   lock=np.zeros(len(rep),bool);lock[weld[B0]]=True;B=lock[weld]
   row[name]={'bad_edges_with_both_ends_locked':int(sum(fail&B[ed].all(1))),'prior_untouched_with_both_locked':int(sum(prior&B[ed].all(1))),'bad_edges_touching_any_lock':int(sum(fail&B[ed].any(1))),'exact_both_locked_edge_ids':ei[fail&B[ed].all(1)].tolist()}
  rows.append({'failed':int(sum(fail)),'prior_untouched':int(sum(prior)),'locks':row})
 summary[s]=rows
out={'identity_source_sha':refs,'observed_core_anchors':[{k:v for k,v in x.items() if k in ('side','view','side_view','label','face','xyz_175_m','normal')} for x in core_by],'core_raw_count':int(sum(core)),'uncertainty_raw_count':int(sum(uncertain)),'endpoint_counts':summary,'unknown':'Density patch is not an approved rigid-island extent, unknown buried geometry not silently tagged. Lace bridges not locked or authorized; verified attachment candidate cores independent of span. Full outsole policy remains separate.'}
(P/'impact.json').write_text(json.dumps(out,indent=2))
for s,rows in summary.items():
 for j,r in enumerate(rows): print(s,j,r['failed'],r['prior_untouched'],[(k,y['bad_edges_with_both_ends_locked'],y['bad_edges_touching_any_lock']) for k,y in r['locks'].items()])
