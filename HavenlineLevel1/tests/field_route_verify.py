import sys,json,hashlib
from pathlib import Path
from collections import Counter
from itertools import pairwise
p=Path(sys.argv[1]); rr=[json.loads(s) for s in (p/'observations.jsonl').read_text().splitlines()]; ee=json.loads((p/'game-events.json').read_text())
counts=Counter(e['event'] for e in ee)
assert all(b['tick']==a['tick']+1 for a,b in pairwise(rr))
assert all(r['same_camera'] for r in rr)
assert all(not r['field']['save_blocked'] for r in rr)
assert rr[0]['field']['carried']=={'wood':0,'stone':0,'meat':0} and not rr[0]['camp_visible']
assert counts['impact_wood']>=6 and counts['deplete_wood']>=2
assert counts['impact_stone']>=3 and counts['deplete_stone']>=1
assert counts['hit']>=3 and counts['defeat']>=1 and counts['enemy_attack']>=1 and counts['player_hurt']>=1
assert max(r['field']['player_hp'] for r in rr)>min(r['field']['player_hp'] for r in rr)
assert counts['purchase']==2 and counts['build']==1 and counts['reveal']==1
for kind,n in [('wood',3),('stone',3),('meat',2)]:
 assert counts['deposit_'+kind]>=n
 assert counts['spend_'+kind]=={'wood':3,'stone':2,'meat':1}[kind]
assert max(min(r['field']['carried'].values()) for r in rr)>=2
busy=next(r for r in rr if r['stage']=='Read all three carried stacks')
floor=next(r for r in rr if r['stage']=='Three dedicated floor stacks')
items=busy['field']['vis_items']
sectors={}
for k in ['wood','stone','meat']:
 positions=items['carry/'+k]
 assert len(positions)>=2
 assert all(abs(positions[0][0]-v[0])<1e-5 and abs(positions[0][2]-v[2])<1e-5 for v in positions)
 sectors[k]=[positions[0][0],positions[0][2]]
assert len(set(tuple(x) for x in sectors.values()))==3
assert floor['field']['stored']['wood']>=3 and floor['field']['stored']['stone']>=3 and floor['field']['stored']['meat']>=2
assert not any(e['event']=='impact_wood' and abs(e['x'])<.01 and abs(e['z'])<.01 for e in ee)
for row in rr:
 st=row['field']
 quantities=Counter(st['collected'].values())
 for material in ('wood','stone','meat'):
  spent=sum(receipt.get(material,0) for receipt in st['paid'].values())
  assert quantities[material]==st['carried'][material]+st['stored'][material]+spent

crossings=[]
for gate,axis,ortho,line,coordinate in [('gate-south',2,0,4,0),('gate-east',0,2,5,0)]:
 legs=set()
 for a,b in pairwise(rr):
  if not a['camp_visible'] or not b['camp_visible']:continue
  start=a['pos'][axis]-line;end=b['pos'][axis]-line
  if (start>0)==(end>0):continue
  t=-start/(end-start)
  cross=a['pos'][ortho]+(b['pos'][ortho]-a['pos'][ortho])*t
  if abs(cross-coordinate)>1.0:continue
  assert next(g for g in b['gates'] if g['id']==gate)['open']
  d='outward' if end>start else 'inward'
  legs.add(d);crossings.append({'gate':gate,'direction':d,'physics_s':round((a['tick']+t)/60.,3),'opening_center_offset_m':round(cross-coordinate,3)})
 assert legs=={'outward','inward'},(gate,legs)
end=rr[-1]['field'];assert end['tool_count']==3 and end['stored']=={k:n-{'wood':0,'stone':2,'meat':1}[k] for k,n in floor['field']['stored'].items()} and end['carried']=={'wood':0,'stone':0,'meat':0} and end['paid']=={'center_hearth':{'wood':3},'orbit_upgrade':{'stone':2,'meat':1}}
from math import dist
wolf_metrics={}
for key in ['windup','lunge','recover']:
 ds=[dist(r['pos'],r['field']['wolf']['pos']) for r in rr if r['field']['wolf']['state']==key and r['stage'].startswith('Wolf encounter')]
 if ds: wolf_metrics[key]=round(min(ds),3)
assert wolf_metrics['lunge']>=1.18,wolf_metrics
receipt={'physics_ticks':len(rr),'physics_hz':60,'route_s':round(rr[-1]['tick']/60,3),'crossings':crossings,'world_event_counts':counts,'begin_carried':rr[0]['field']['carried'],'costs_paid':end['paid'],'carry_at_return':busy['field']['carried'],'pack_footprints_xz_m':sectors,'stocks_before_upgrade':floor['field']['stored'],'stocks_after_upgrade':end['stored'],'tools_before':rr[0]['field']['tool_count'],'tools_after':end['tool_count'],'wolf_player_min_separation_m':wolf_metrics,'player_hp_before':rr[0]['field']['player_hp'],'player_hp_min':min(r['field']['player_hp'] for r in rr),'begins_unbuilt':not rr[0]['camp_visible'],'ends_built':rr[-1]['camp_visible'],'max_pinch':max(r['zoom'] for r in rr),'persist_errors':0}
(p/'route-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PASS',crossings,receipt['wolf_player_min_separation_m'])
