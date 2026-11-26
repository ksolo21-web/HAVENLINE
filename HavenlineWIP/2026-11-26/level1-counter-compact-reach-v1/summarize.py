import sys, re, json, hashlib
from pathlib import Path
p=Path(sys.argv[1])
log=(p/'route.log').read_text()
prov=(p/'provenance.txt').read_text().splitlines()
assert prov==['11c14a1c41971067c7dc97db69375f720a408f68','d764a05246cbff96983aa27af17e2e919a946ae0','21683d4ff9492e7c4cb987610d2e885c791ad17978fc4da486a6d3eb1d5d957d  reach_probe.gd','4.7.2.stable.official.ed1daf0bf']
assert not re.search(r'(?im)^(?:ERROR|WARNING|SCRIPT ERROR|FAIL)[ :]|Parse Error|Failed (?:loading|to load)',log)
assert (p/'godot-status.txt').read_text()=='0\n'
assert all((p/k).read_text()=='' for k in ('save-artifacts.txt','import.errors','materialized.after'))
assert (p/'donor.before').read_bytes()==(p/'donor.after').read_bytes()
result=re.findall(r'^DOCKED_CENTER_ROUTE_RESULT checks=(\d+) failures=0 no_image_stages=(\d+)$',log,re.M)
assert len(result)==1
checks,skipped=map(int,result[0])
assert len(re.findall(r'^PASS .* tick=\d+$',log,re.M))==checks
rows=[json.loads(r) for r in re.findall(r'^COMPACT_COUNTER_REACH (.+)$',log,re.M)]
assert [d['side'] for d in rows]==['inside','outside']
for row in rows:
 assert len(row['measurements'])==12
 assert 0<=row['heading_error_deg']<=5
 assert row['actor_foot'][2]*row['unchanged_marker'][2]>0
 for k,v in row['measurements'].items():
  assert v['straight_pivot_distance_m']>0 and v['tested_triangles']>0
  h=v['first_donor_distance_m']
  assert h is None or 0<=h<v['straight_pivot_distance_m']
  assert v['earlier_than_endpoint_by_1cm']==(h is not None and h<v['straight_pivot_distance_m']-.01)
controls={k:len(re.findall('^'+k+' ',log,re.M)) for k in ('STOP_GUARD','SHOULDER_ROUTE','CPU_SURFACE','CPU_STANCE')}
assert controls=={'STOP_GUARD':6,'SHOULDER_ROUTE':4,'CPU_SURFACE':2,'CPU_STANCE':10}
print(json.dumps(dict(disposition='HOLD: no authored customer/service reach contract or rendered proof',pinned_source=prov[0],pinned_tree=prov[1],engine=prov[3],headless=True,checks_passed=checks,checks_failed=0,explicitly_skipped_image_stages=skipped,observed_original_marker_rows=rows,retained_controls=controls,save_writes=False,route_sha256=hashlib.sha256(log.encode()).hexdigest()),indent=2,sort_keys=True))
