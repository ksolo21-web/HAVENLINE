from pathlib import Path
import json,collections,math
P=Path(__file__).resolve().parent
d=json.loads((P/'sections-and-motion.json').read_text())
faces=d['approved_posterior_faces']; assert len(set(x['id'] for x in faces))==147
assert [x['id'] for x in faces if x['critical_overrun']]==list(range(42528,42534))
assert sum(not x['protected_from_bounded_cut'] for x in faces)==34
assert len(d['approved_boundary_vertices'])==41 and len(d['collar_boundary_edge_vertex_ids'])==162
assert d['anterior_source_native_rows']==[13484,13613,14018,14078]
assert d['motion']['times_ms']==[0,75,150]
for name,s in d['states'].items():
 v=s['exact_rear_and_collar_vertices']
 assert all(str(i) in v for f in faces for i in f['vertex_ids'])
 assert all(str(i) in v for edge in d['collar_boundary_edge_vertex_ids'] for i in edge)
 assert len(s['outline_guard_samples'])==7 and len(s['sole_guard_samples'])==3
 for z in s['outline_guard_samples']:
  for _,fi,p in z['sampled_extrema']:
   assert abs(p[2]-z['z_m'])<1e-9
 assert any(sq['segments'] for sq in s['sagittal_x_stations'])
for n in d['previous_exact_rail_source']:assert len(d['previous_exact_rail_source'][n])==21
objects=collections.defaultdict(collections.Counter);pts=0
for q in (P/'posterior-neutral-and-bent.obj').read_text().splitlines():
 a,*x=q.split()
 if a=='o':name=x[0]
 if a=='v':
  pts+=1; assert all(math.isfinite(float(y)) for y in x)
 if a in ('f','l'):
  objects[name][a]+=1;assert all(1<=int(i)<=pts for i in x)
for n in d['states']:
 assert objects[n+'_critical_rear_source_faces_42528_to_42533']['f']==6
 assert objects[n+'_approved_rear_other_source_faces']['f']==141
 assert objects[n+'_protected_collar_perimeter']['l']==162
 assert sum(k.startswith(n+'_REJECTED_overlay_occupancy') for k in objects)==3
print('PASS package structure and rest/held guide consistency; not garment feasibility')
