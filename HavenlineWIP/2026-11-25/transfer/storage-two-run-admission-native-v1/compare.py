from pathlib import Path
import hashlib,json,re,sys

def require(p,s):
 if not p: raise ValueError(s)
def rows(txt,label):
 return [l[len(label)+1:] for l in txt.splitlines() if l.startswith(label+' ')]
def obj(txt,label):
 r=rows(txt,label);require(len(r)==1,label)
 return json.loads(r[0])
def diag(t):
 require('Godot Engine v4.7.2' in t,'version')
 require(not any(x.startswith(('SCRIPT ERROR','ERROR:','WARNING:','FATAL:')) for x in t.splitlines()),'native diagnostics')
def phase_a(a):
 diag(a)
 x=obj(a,'PFX_A_STATUS')
 require({k:x.get(k) for k in ['end_tick','prefix','observer_valid','request_dispatched']}=={'end_tick':1423,'prefix':57,'observer_valid':True,'request_dispatched':False},'full A')
 require([r['tick'] for r in x['turn_records']]==[1306,1353] and all(r['ids'] and r['oriented_clearance']>.0001 for r in x['turn_records']),'A verified two original turns')
 old=obj(a,'WALK_SUM');require((old['checks'],old['failures'],old['ticks'],old['obstructed_ticks'])==(26,1,146,2),'preserve original result')
 aa=rows(a,'PFX_OBS')
 require(len(aa)==57 and all(re.fullmatch(f'{1277+i} [0-9a-f]{{64}}',r) for i,r in enumerate(aa)),'missing or malformed prefix A')
 return old
def phases(a,b):
 old=phase_a(a)
 diag(b)
 statuses=[obj(a,'PFX_A_STATUS'),obj(b,'PFX_B_STATUS')]
 require(statuses[1]=={'admission_prefix':True,'prefix':57,'native_tick_end':1333,'request_dispatched':False,'reason':'UNPROVEN_EXACT_LIVE_FLIGHT_OR_RECEIVER_VISUAL_DEPTH'},'B only live prefix')
 require(not rows(b,'WALK_SUM') and not rows(b,'TURN_ADMISSION') and len(rows(b,'WALK_OBSTRUCTION'))==1,'B has no post-near future proof')
 aa=rows(a,'PFX_OBS');bb=rows(b,'PFX_OBS')
 require(len(aa)==len(bb)==57 and all(re.fullmatch(f'{1277+i} [0-9a-f]{{64}}',r) for i,r in enumerate(aa)),'missing or malformed prefix')
 require(aa==bb,'live prefix drift')
 na=obj(a,'PFX_NEAR');nb=obj(b,'PFX_NEAR')
 require(na==nb and nb['stock']=={'wood':2} and nb['v']==[0,0,0] and nb['own_stable']==True and len(set(nb['held_paths']))==2 and nb['t']==1333,'live exact near and identities')
 return {'status':'EXAMINER ADMISSION OBSERVED; ACTION HELD','native_full_a':old,'native_fresh_b_prefix':statuses[1],
 'matched_tick_records':len(aa),'near':nb,'prefix_sha256':hashlib.sha256('\n'.join(aa).encode()).hexdigest(),
 'blocked_action_reason':'No exact live bounded flight clearance/marker depth-safe presentation; no request dispatched, no debit or credit, no display custody change.'}
if __name__=='__main__':
 try:
  if sys.argv[1]=='--require-a':
   phase_a(Path(sys.argv[2]).read_text())
  else:
   print(json.dumps(phases(*(Path(x).read_text() for x in sys.argv[1:3])),indent=2,sort_keys=True))
 except (ValueError,KeyError,TypeError) as e:
  print('HOLD: '+str(e),file=sys.stderr);sys.exit(15)
