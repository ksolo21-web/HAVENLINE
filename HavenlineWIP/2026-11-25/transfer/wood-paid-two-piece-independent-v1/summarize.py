from pathlib import Path
import json,re
s=Path('native-sanitized.log').read_text(); assert not re.search(r'(?im)^(?:ERROR|SCRIPT ERROR|WARNING|FAIL)',s)
m=re.search(r'^PROBE_COUNT (\d+) failures 0 grounded (\d+)',s,re.M); assert m and tuple(map(int,m.groups()))==(31,1347)
r=[json.loads(x[13:]) for x in s.splitlines() if x.startswith('CROWN_SAMPLE ')]; assert len(r)==7
ph=[d for d in r if d['label'].startswith('ordinary_run_phase_')]; assert len(ph)==4
assert all(d['anim'].endswith('/run') and d['actor_speed']>3.9 and d['mesh_count']==1 for d in ph)
assert all(d['actor_back_separating_plane_gap_m']>0 and d['capsule_back_plane_gap_m']>0 and d['pair_plan_z_separation_m']>.001 for d in r)
print(json.dumps(dict(checks=int(m[1]),grounded=int(m[2]),ordinary_run_seconds=[d['anim_t'] for d in ph],min_skin_plane_mm=min(d['actor_back_separating_plane_gap_m'] for d in r)*1000,min_capsule_plane_mm=min(d['capsule_back_plane_gap_m'] for d in r)*1000,min_crown_pair_plane_mm=min(d['pair_plan_z_separation_m'] for d in r)*1000,graphics=False,continuous_claim=False),indent=2))
