"""Check the film's native frame sequence and physical handoff receipts."""
from pathlib import Path
import hashlib,json,subprocess as sp,sys
r=Path(sys.argv[1])
result=Path(sys.argv[2])
rows=[json.loads(x) for x in (r/'observations.jsonl').read_text().splitlines()]
events=[json.loads(x) for x in (r/'events.jsonl').read_text().splitlines()]
seed=Path(__file__).parent/'earned-input.save.json'
def fingerprint(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def point(row):return [round(i,3) for i in row['pos']]
def phase(key): return next(i for i,row in enumerate(rows) if row['phase']==key)
def changes(key):
 return [(prev,row) for prev,row in zip(rows,rows[1:]) if row['settlement'][key]!=prev['settlement'][key]]
def shown(r):return dict(time=round(r['tick']/60,3),physics_tick=r['tick'],player_xyz=point(r),phase=r['phase'],inside=r['inside'],on_cooker_input=r['loading_cooker'],on_workshop_input=r['loading_timber_or_stone'],wood=r['settlement']['processed_wood'],stone=r['settlement']['processed_stone'],meals=r['settlement']['cooked'],in_hand=r['settlement']['held_meal'],served=r['settlement']['served'])
assert all(row['same_camera'] for row in rows)
assert events[-1]['event']=='complete'
first,last=rows[0],rows[-1]
assert first['carried']['wood']==9 and first['carried']['stone']==2 and first['carried']['meat']==2
assert first['settlement']['held_meal']==first['settlement']['cooked']==first['settlement']['processed_wood']==first['settlement']['processed_stone']==0
receipts={}
for kind,key in [('wood','processed_wood'),('stone','processed_stone'),('meat','cooked')]:
 hops=[(a,b) for a,b in zip(rows,rows[1:]) if b['settlement']['hoppers'][kind]>a['settlement']['hoppers'][kind]]
 manual=[b for a,b in hops if b['carried'][kind] < a['carried'][kind] and (b['loading_cooker'] if kind=='meat' else b['loading_timber_or_stone']==kind)]
 assert manual and all(b['inside'] for b in manual),kind
 manual_phase={'wood':('Load real carried timber at the connected saw','The input rack takes a small batch'),
               'stone':('Approach the stone input','Drop two raw stones'),
               'meat':('Load the cooker inlet','Release carried meat to the intake')}[kind]
 featured=next(b for b in manual if b['phase'] in manual_phase)
 product=changes(key)
 remote=[b for a,b in product if b['tick']>featured['tick'] and (not b['loading_cooker'] if kind=='meat' else b['loading_timber_or_stone']!=kind)]
 assert remote, (kind,[(p['tick'],p['phase']) for a,p in product])
 assert all(b['inside'] for a,b in product)
 receipts[kind]={'featured_player_load_with_raw_debit':shown(featured),'all_player_loads_with_raw_debit':[shown(b) for b in manual],'first_completion_after_departing_that_input':shown(remote[0]),'finished_units':last['settlement'][key],'hoppers_at_end':last['settlement']['hoppers'][kind]}
pickup_changes=changes('held_meal')
held=next(b for a,b in pickup_changes if b['settlement']['held_meal']>a['settlement']['held_meal'])
sale=next(b for a,b in changes('served') if b['settlement']['served']>a['settlement']['served'])
assert held['tick']>=phase('Walk to the distinct roast pickup position')+rows[0]['tick']-1
assert sale['tick']>held['tick'] and sale['settlement']['served']==1 and all(row['settlement']['served']==0 for row in rows if row['tick']<sale['tick'])
assert all(row['settlement']['held_meal']==0 for row in rows if row['tick']<held['tick'])
shipments=[]
for a,b in zip(rows,rows[1:]):
 kind=a['settlement'].get('worker_supply','')
 if kind and not b['settlement'].get('worker_supply','') and b['settlement']['hoppers'][kind]==a['settlement']['hoppers'][kind]+1 and b['worker_phase']=='supply_back':
  shipments.append({'kind':kind,'worker_xyz':[round(i,3) for i in b['worker_xyz']],'player':shown(b)})
assert any(item['player']['phase']=='The survivor loads a workshop from stock while the player stands aside' for item in shipments)
assert len([e for e in events if e['event']=='complete'])==len(json.loads((Path(__file__).parent/'production-route.json').read_text()))
report={'scene':first['scene'],'input':'Existing player-earned owl encounter, copied into a disposable profile. No inventory seeded by the capture driver.','input_checkpoint_sha256':fingerprint(seed),'input_source':'a0e83999064b666145a884eed767f68d4d127688','route_sha256':fingerprint(Path(__file__).parent/'production-route.json'),'native_physics_seconds':round(last['tick']/60,3),'output_receipts':receipts,'survivor_deliveries_witnessed':shipments,'roast_pickup':shown(held),'north_counter_sale':shown(sale),'gameplay_camera_at_every_tick':True,'sample_count':len(rows),'route_phases_completed':sum(e['event']=='complete' for e in events)}
result.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v['finished_units'] for k,v in receipts.items()}),len(rows),'physics samples;',report['route_phases_completed'],'completed route phases')
