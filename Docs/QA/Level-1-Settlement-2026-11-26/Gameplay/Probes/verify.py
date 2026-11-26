import json,hashlib,sys,collections,pathlib,math
run=pathlib.Path(sys.argv[1]);journal=[]
def envelope(p):
 env=json.loads(p.read_text());assert hashlib.sha256(env['payload'].encode()).hexdigest()==env['sha256'];return json.loads(env['payload'])
def read_events():
 for line in (run/'events.jsonl').open():yield json.loads(line)
def accounting(x):
 c=collections.Counter(x['collected'].values());budget=collections.Counter(x['carried'])+collections.Counter(x['stored'])
 for row in x['paid'].values():budget.update(row)
 sj=x.get('settlement',{});budget['meat']+=sj.get('cooked',0)
 budget['wood']+=sj.get('survivor_wood',0)+sj.get('processed_wood',0);budget['stone']+=sj.get('processed_stone',0)
 assert +budget==+c, (budget,c,sj)
 return dict(c)
stops={}
for e in read_events():
 if e['event']=='earned_checkpoint':
  datum=e['data'];name=datum['name'];f=run/(name+'.save.json');st=envelope(f);tokens=accounting(st)
  assert hashlib.sha256(f.read_bytes()).hexdigest()==datum['file_sha256']
  stops[name]={'tick':e['tick'],'profile_sha256':datum['file_sha256'],'carried':st['carried'],'stored':st['stored'],'tokens':tokens,'build_order':st['build_order'],'settlement':st.get('settlement',{})}
 if e['event']=='continuation_tap':journal.append(e)
assert len(journal)==1
events=json.loads((run/'world-events-complete.json').read_text()); names=collections.Counter(r['event'] for r in events)
for name in ['owl_hit','process_wood','process_stone','process_done','survivor_rescued','worker_pickup','worker_delivery','cooker_start','meal_ready','meal_served','level_complete','next_level']:assert names[name]>=1,(name,names)
f=stops['post-completion'];a=stops['level-one-ready'];assert f['settlement']['level']==2 and a['settlement']['level']==1
assert len(f['build_order'])==8 and len(set(f['build_order']))==8
assert f['settlement']['served']==a['settlement']['served']==1 and f['settlement']['cooked']==a['settlement']['cooked']==1
for n in ['rescued','survivor_paid','survivor_wood','processed_wood','processed_stone','served','cooked']:assert f['settlement'][n]==a['settlement'][n],n
assert f['settlement']['survivor_paid'] and f['settlement']['survivor_wood']==2 and min(f['settlement'][k] for k in ('processed_wood','processed_stone','owl_hits'))>=1
# Autonomous foresters can finish an independently earned delivery between UI snapshots.
prior=a['settlement']['worker_receipts'];after=f['settlement']['worker_receipts'];assert after[:len(prior)]==prior
assert f['carried']==a['carried'] and all(f['tokens'].get(k,0)-a['tokens'].get(k,0)==(len(after)-len(prior) if k=='wood' else 0) for k in set(f['tokens'])|set(a['tokens']))
assert len(f['settlement']['worker_receipts'])==len(set(f['settlement']['worker_receipts']))==f['settlement']['worker_deliveries']
for e in journal:assert e['data']['settlement']['level']==1
with (run/'events.jsonl').open() as in_file:r=[json.loads(x) for x in in_file if '"event":"complete"' in x]
final=r[-1]['data']
out={'normal_entry':'res://field_opening.tscn','completed':True,'source_frames':'One 60 Hz physics observation per tick, ordinary screen touch/drag controls and genuine on-screen continuation press. No credits, teleports, direct purchases, time advances or forced completion.','full_route_seconds':r[-1]['t'],'full_route_physics_ticks':r[-1]['tick'],'initial_phase':r[0]['phase'],'checkpoints':stops,'native_events':dict(names),'settlement_events':[e for e in events if e['event'] in ('owl_hit','process_wood','process_stone','process_done','survivor_rescued','worker_pickup','worker_delivery','cooker_start','meal_ready','meal_served','level_complete','next_level')],'continuation_tap':journal,'final_rails':{'paid':f['build_order'],'worker_unique_receipts':f['settlement']['worker_receipts'],'paid_meals':f['settlement']['served'],'exact_credit_conservation':True},'warnings':[]}
previous=None;crossings=[]
with (run/'observations.jsonl').open() as records:
 for line in records:
  current=json.loads(line);f=current['field']
  if previous and previous['camp_visible'] and current['camp_visible'] and previous['field']['perimeter']==f['perimeter']:
   for gate,axis,other in [('gate-south',2,0),('gate-east',0,2)]:
    center=f['gate_centers'][gate];x0=previous['pos'][axis]-center[axis];x1=current['pos'][axis]-center[axis]
    if (x0>0)==(x1>0):continue
    frac=-x0/(x1-x0);offset=previous['pos'][other]+frac*(current['pos'][other]-previous['pos'][other])-center[other]
    if abs(offset)>1.1:continue
    assert next(g['open'] for g in current['gates'] if g['id']==gate)
    crossings.append(dict(stage=f['stage_number'],gate=gate,direction='out' if x1>x0 else 'in',s=round((current['tick']-1+frac)/60,3),offset_m=round(offset,3)))
  previous=current
expected={(s,g,d) for s in (1,2,3) for g in ('gate-south','gate-east') for d in ('in','out')}
assert {(c['stage'],c['gate'],c['direction']) for c in crossings}>=expected,crossings
out['open_gate_crossings']=crossings
(run/'completion-evidence.json').write_text(json.dumps(out,indent=2)+'\n');print(f['settlement'])
