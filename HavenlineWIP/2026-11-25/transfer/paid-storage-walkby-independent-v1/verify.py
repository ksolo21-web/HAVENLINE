from pathlib import Path
import re,json,math,hashlib,subprocess
p=Path(__file__).resolve().parent.parent/'hvn-l1-paid-storage-walkby-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='ac4a8d52a510abd6b657872fc6f73f45d043115152ce943576c365b0d4cccd80'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
log=(p/'native.log').read_text().splitlines()
def read(t):return [json.loads(l[len(t)+1:]) for l in log if l.startswith(t+' ')]
S,=read('WALK_SUM'); G=read('WALK_GEOM'); F=read('WALK_OBSTRUCTION')
def sep(a,b):
 return max(b[0]-a[2],b[1]-a[3],a[0]-b[2],a[1]-b[3])
def view(g):
 return all(all(sep(a,b)>0 for b in [g['skin_rect']]+g['carry_rects']) and all(g['viewport'][i]<=a[i] if i<2 else g['viewport'][i]>=a[i] for i in range(4)) for a in g['target_rects'])
assert len(G)==29 and all(view(g)==g['both_conservative_open'] for g in G)
def run(g):return g['animation'].endswith('/run') and g['anim_t']>0.00001 and math.hypot(g['motion'][0],g['motion'][2])>.65
arrival=next(g for g in G if g['tick']==1333)
assert view(arrival) and S['ticks']==146 and S['checks']==26 and S['failures']==1
byphase={}
for g in G:
 if run(g):
  vals=byphase.setdefault(g['phase'],[0,0]);vals[0]+=1;vals[1]+=view(g)
assert byphase['near_edge_approach']==[4,4] and byphase['along_west_departure']==[2,2]
assert all(sum(g['scene_rays_blocked'])==0 for g in G)
assert any('PASS unchanged native paid ledger/two carried pieces/gates; no delivery' in l for l in log)
assert any('PASS landed back at original South point' in l for l in log)
bytick={g['tick']:g for g in G}; known=[]
for f in F:
 tick=f['tick']; assert tick not in bytick and (tick-1 not in bytick or tick not in bytick)
 nbr=[max(t for t in bytick if t<tick),min(t for t in bytick if t>tick)]
 assert set(f)=={'fraction','grounded','phase','tick','unsafe','world'}
 known.append(dict(tick=tick,exact_guard_safe_fraction=f['fraction'],sum_proxy_endpoint_reports=f['unsafe'],adjacent_projection_sample_ticks=nbr))
assert [f['tick'] for f in known]==[1306,1353]
print(json.dumps(dict(observed_paid_path_completed=True,overall_assertion_HOLD=True,
 run_samples_total_then_clear=byphase,arrival_min_rect_margin_px=min(sep(a,b) for a in arrival['target_rects'] for b in [arrival['skin_rect']]+arrival['carry_rects']),
 sampled_scene_rays=sum(sum(g['scene_rays_total']) for g in G),silent_unproven_ticks=known,finite_actual_mesh_contact='undetermined; no timed endpoints or body identities'),indent=2))
