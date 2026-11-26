from pathlib import Path
from collections import defaultdict, Counter
import hashlib,json,sys,contextlib,io
p=Path(__file__).resolve().parent
src=p.parent/'hvn-l1-fence-33036-emboss-bounded-shards-v1'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(src/'SHA256SUMS')=='190f5ddf47e0d1ff363a229047b5b67d1b1f64b084078d467c0ea0dd561ffe58'
for row in (src/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(maxsplit=1);assert sha(src/n)==h
pack=src/'pack.py'; d={'__file__':str(pack)}
with contextlib.redirect_stdout(io.StringIO()):
 exec(pack.read_text().split('if len(sys.argv)==2:')[0],d)
V,runs=d['V'],d['runs']
# Positions are evaluated both with and without UV splits. Authored OBJ gives no
# normative rule telling a consuming smooth normal generator which of these to use.
def gather(uv):
 keys=defaultdict(set)
 for i,((obj,s,mat),faces) in enumerate(runs):
  for f in faces:
   for v,u in f:
    key=(obj,s,mat,V[0][v-1],V[1][u-1] if uv else None)
    keys[key].add(i)
 return keys
def graph(keys):
 adj=defaultdict(set)
 for rs in keys.values():
  for i in rs:adj[i].update(rs-{i})
 comps={}; ranks=[]
 for i in range(len(runs)):
  if i in comps:continue
  span={i};stack=[i]
  while stack:
   j=stack.pop()
   for k in adj[j]-span:span.add(k);stack.append(k)
  ranks.append(span)
  for j in span:comps[j]=span
 return comps,ranks
rc={}
for key,uv in [('same_obj_material_smooth_position',False),('same_obj_material_smooth_position_uv',True)]:
 keys=gather(uv); cc,ranks=graph(keys)
 split=[(k,a) for k,a in keys.items() if len({i//24 for i in a})>1]
 direct=Counter(len(a) for _,a in split)
 closure=Counter(len(cc[min(a)]) for _,a in split)
 rc[key]={ 'keys_split_by_shards':len(split),'direct_incident_run_hist':dict(direct),'whole_exact_incidence_component_hist':dict(Counter(len(q) for q in ranks)),
           'split_key_full_connected_closure_run_hist':dict(closure),'closure_examples':[{'key':list(k),'first_last_runs_1based':[min(cc[min(a)])+1,max(cc[min(a)])+1], 'size':len(cc[min(a)])} for k,a in sorted(split,key=lambda ka:-len(cc[min(ka[1])]))[:2]]}
res={'status':'HOLD until explicit source-corner normal authority or actual importer semantics prove equal implicit smoothing',
     'transport_identity_verified':{'faces':sum(len(fs) for _,fs in runs),'source_bytes_pin':sha(d['p']),'via_verified_literal_roundtrip':True},
     'scope':'direct incident runs may be finite per key, connected normal authority must keep every affected key exact across complete surface order; cannot assume implicit native strategy from OBJ',
     'candidate_scope_models':rc}
(p/'result.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
