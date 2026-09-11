#!/usr/bin/env python3
"""Independent source-bound T03 visual review.
Two roles execute separately through the same disclosed public publisher model.
A complete returned verdict is never retried to obtain a higher score. Only a
transport/malformed response with no complete verdict may retry, and each failed
attempt remains in the artifact. This reviewer cannot certify physical FPS.
"""
from pathlib import Path
import hashlib,html,json,math,os,re,time,urllib.request,shutil
from PIL import Image,ImageDraw
from gradio_client import Client,handle_file
SOURCE=os.environ['EXPECTED_SOURCE'];ROLE=os.environ['REVIEW_ROLE']
assert len(SOURCE)==40 and ROLE in ('reference-fidelity','visual-integrity')
SPACE='Qwen/Qwen3-VL-235B-A22B-Instruct-Demo';REV='eb7f245e2c0d3b573dd8ed6addca9b7f6af26847'
ROOT=Path('task03-evidence');OUT=Path('task03-review');OUT.mkdir(exist_ok=True)
KEYS=['reference_fidelity','boundary_finish','gate_readability','lane_legibility','river_preservation','view_consistency']
GROUPS={
 'perimeter':['gallery/perimeter-topdown.png','gallery/perimeter-oblique.png','gallery/camp-lanes-overhead.png','gallery/camp-lanes-oblique.png','native4k/native-perimeter.png','native4k/native-camp-oblique.png'],
 'north-gate':['gallery/north-gate-front.png','gallery/north-gate-rear.png','native4k/native-north-gate.png'],
 'side-gates':['gallery/west-work-gate.png','gallery/east-work-gate.png','native4k/native-side-gate-west.png','native4k/native-side-gate-east.png'],
 'river-gates':['gallery/river-gate-west.png','gallery/river-gate-centre.png','gallery/river-gate-east.png','native4k/native-river-gate-west.png','native4k/native-river-gate-centre.png','native4k/native-river-gate-east.png'],
 'south-fence':['gallery/south-fence-west.png','gallery/south-fence-centre.png','gallery/south-fence-east.png','native4k/native-south-fence.png'],
 'central-lane':['gallery/central-spine-north.png','gallery/central-spine-centre.png','gallery/central-spine-river.png','native4k/native-lane-network.png'],
 'cross-shelter-lanes':['gallery/cross-lane-west.png','gallery/cross-lane-centre.png','gallery/cross-lane-east.png','gallery/shelter-branch-west.png','gallery/shelter-branch-east.png','native4k/native-lane-network.png'],
 'bank-lane':['gallery/bank-lane-west.png','gallery/bank-lane-centre.png','gallery/bank-lane-east.png','gallery/reserved-crossings-overhead.png','native4k/native-lane-network.png'],
 'detail-contact':['gallery/fence-panel-detail.png','gallery/gate-post-detail.png','gallery/open-gate-leaves-detail.png','native4k/native-fence-detail.png'],
 'gameplay':['gallery/gameplay-north-gate.png','gallery/gameplay-west-gate.png','gallery/gameplay-east-gate.png','gallery/gameplay-river-gate-centre.png'],
 'conditions':['gallery/boundary-condition-day.png','gallery/boundary-condition-dusk.png','gallery/boundary-condition-night.png','gallery/boundary-condition-dawn.png','gallery/boundary-condition-blizzard-night.png','gallery/boundary-condition-day-return.png']
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pro=json.loads((ROOT/'provenance.json').read_text());assert pro['source']==SOURCE and pro['renderer']=='mobile'
required={p for rows in GROUPS.values() for p in rows};assert required.issubset(set(pro['captures']))
for name,h in pro['captures'].items():assert sha(ROOT/name)==h,'Changed image '+name
ref=ROOT/'reference-ground.webp';assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
metadata={}
for folder in ('gallery','native4k'):
 for row in json.loads((ROOT/folder/'capture.json').read_text())['captures']:metadata[folder+'/'+row['name']+'.png']=row
info=json.load(urllib.request.urlopen('https://huggingface.co/api/spaces/'+SPACE,timeout=40));assert info['sha']==REV and info['private'] is False
provider={'task':'T03-boundary-v1','source':SOURCE,'role':ROLE,'provider_space':SPACE,'provider_space_revision':REV,'declared_model':'qwen3-vl-235b-a22b-instruct','weights_locally_checksum_verified':False,'same_published_model_for_both_roles':True,'code_sha256':sha(Path(__file__)),'evidence_provenance_sha256':sha(ROOT/'provenance.json'),'all_frame_hashes_verified':True,'independent_model_execution':False,'minimum_gate':9.0,'task_approved':False,'physical4k60_verified':False,'credentials_used':False,'billing_changed':False}
(OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2))
# Blind factual control is unrelated to the requested score.
probe=Image.new('RGB',(720,780),(24,37,52));d=ImageDraw.Draw(probe)
for i,name in enumerate(['clearance-enabled','clearance-disabled','clearance-disabled','clearance-baseline']):
 im=Image.open(ROOT/'tree-clearance'/f'{name}.png').convert('RGB').crop((490,235,790,555));im.thumbnail((360,360));x=i%2*360;y=i//2*390
 probe.paste(im,(x+(360-im.width)//2,y+26));d.text((x+9,y+7),'ABCD'[i],fill='white')
probe.save(OUT/'blind-control.png');expected={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
PROMPT='''Independently inspect the supplied actual-reference crop and EVERY labelled Havenline candidate panel. Review ONLY Task 3: finished camp FENCES, six readable GATE openings, and NAVIGABLE PACKED WORK LANES. The accepted T02 map-spanning river and T01 blue-white forest are prerequisites that must remain visually coherent.
The authoritative source videos establish a bright clean sculpted winter-survival language: dense blue-white conifers, a warm peach/brown working camp, readable fenced boundaries and routes, saturated accents, compact oblique gameplay readability. Havenline adapts that language to its persistent river. Do NOT demand photorealistic bark, gritty materials, a bridge, customers, machinery, or later-task content.
The Task 3 design intentionally has six open gates: north main, west/east work gates, and three SOUTH/RIVER-facing gates aligned to reserved future bridge corridors. Those three river gates are OPEN CORRIDORS; missing bridges are not defects in T03. Fencing uses the authored irregular timber barricade kit plus lantern-post gate thresholds; open timber leaves should read as intentionally opened, not broken fence gaps. The south fence follows the north river bank outside its protected setback. Work lanes are packed/worn material in the same terrain surface, not floating path planes.
Judge actual pixels. Visible defects include crude repetition, disconnected/floating fence pieces, buried or hovering posts, accidental fence gaps outside gates, gates that cannot be read, lane markings that vanish or become noisy/painted stripes, paths running visibly through solid fence/water, river-bank clipping, obstructed future crossing corridors, primitive/blockout appearance, inconsistent geometry across views, or broken lighting/materials. Do not invent a defect merely to lower a score.
Top-down frames are disclosed QA views; gameplay frames show the normal camera relationship. Native frames are unretouched 3840x2160 render-scale-1 Mobile-renderer captures and prove pixel output only, NOT physical phone/tablet FPS or thermals. Condition frames share one camera and hold unrelated animation players only for controlled comparison.
Score EXACTLY these dimensions 0-10: reference_fidelity (fit to supplied source-video visual language), boundary_finish (fence/post/ground contact and authored-art polish), gate_readability (six deliberate readable openings with coherent posts/leaves), lane_legibility (clear, natural packed routes integrated into terrain), river_preservation (Task2 river/banks/crossing-space remain visually coherent), view_consistency (same finished layout/material holds across views/states). Any score below 9 MUST identify an actionable visible deficiency. Return ONLY one complete JSON object: {"observations":["..."],"defects":[{"view":"filename","region":"...","issue":"..."}],"scores":{"reference_fidelity":0,"boundary_finish":0,"gate_readability":0,"lane_legibility":0,"river_preservation":0,"view_consistency":0},"coverage_complete":true,"confidence":"low|medium|high"}. This is scoped Task 3 review only; do not infer whole-game or device-performance approval.'''
PROMPT+='\nRole: '+ROLE+'. '+('Prioritize the reference-video visual language, protected-camp composition, intentional gate hierarchy and naturally readable work lanes.' if ROLE=='reference-fidelity' else 'Prioritize mesh/contact integrity, visible/collision-consistent boundary logic, open gates/corridors, lane continuity, river preservation and multi-view/state consistency.')
(OUT/'rubric.txt').write_text(PROMPT)
def request_once(image,prompt,label):
 client=Client(SPACE,hf_token=False,download_files=False,verbose=False);api=client.view_api(return_format='dict',print_info=False)
 for name,params in {'/add_file':['history','file'],'/add_text':['history','text'],'/predict':['_chatbot']}.items():assert [v['parameter_name'] for v in api['named_endpoints'][name]['parameters']]==params
 (OUT/(label+'-request.json')).write_text(json.dumps({'image_sha256':sha(image),'prompt':prompt,'space':SPACE,'revision':REV,'fresh_session_no_prior_grades':True},indent=2))
 started=time.monotonic();client.predict(history=[],file=handle_file(str(image)),api_name='/add_file');history=client.predict(history=[],text=prompt,api_name='/add_text');raw=client.submit(_chatbot=history,api_name='/predict').result(timeout=220)
 (OUT/(label+'-raw.json')).write_text(json.dumps(raw,indent=2,default=str));text=raw[-1][1];assert isinstance(text,str);(OUT/(label+'-raw.txt')).write_text(text)
 clean=html.unescape(re.sub(r'<[^>]+>','\n',text));start=clean.find('{');assert start>=0,'No complete JSON response';result,_=json.JSONDecoder().raw_decode(clean[start:])
 return result,{'completed_public_job':True,'elapsed_seconds':time.monotonic()-started,'image_sha256':sha(image),'raw_sha256':sha(OUT/(label+'-raw.json'))}
def request(image,prompt,label):
 for attempt in range(3):
  try:return request_once(image,prompt,label)
  except Exception as exc:
   failed=OUT/'incomplete-attempts'/f'{label}-{attempt+1}';failed.mkdir(parents=True,exist_ok=True);(failed/'error.txt').write_text(type(exc).__name__+': '+str(exc))
   for suffix in ('-raw.json','-raw.txt','-request.json'):
    p=OUT/(label+suffix)
    if p.exists():shutil.move(str(p),str(failed/p.name))
   if attempt==2:raise
   time.sleep(5*(attempt+1))
rows=[];error=None
try:
 answer,execution=request(OUT/'blind-control.png','Identify the prominent centre subject in each labelled panel A,B,C,D: human_character, snow_tree, or other_or_unclear. Inspect actual pixels. Return only JSON with keys A,B,C,D. No grades are requested.','control')
 (OUT/'control.json').write_text(json.dumps({'answers':answer,'expected_not_sent':expected,'passed':answer==expected,'execution':execution},indent=2));assert answer==expected,'Blind image-recognition control failed'
 for group,names in GROUPS.items():
  rows_count=(len(names)+1)//2;board=Image.new('RGB',(1600,260+rows_count*480),(24,37,52));draw=ImageDraw.Draw(board);reference=Image.open(ref).convert('RGB');reference.thumbnail((500,230));board.paste(reference,(8,25));draw.text((8,5),'ACTUAL REFERENCE VIDEO CROPS',fill='white');draw.text((530,40),'ACTUAL TASK 3: '+group,fill='white')
  inputs=[]
  for i,name in enumerate(names):
   image=Image.open(ROOT/name).convert('RGB');original=image.size;image.thumbnail((800,450),Image.Resampling.LANCZOS);x=i%2*800;y=260+(i//2)*480;board.paste(image,(x+(800-image.width)//2,y+30));draw.text((x+5,y+5),name,fill='white');inputs.append({'filename':name,'sha256':sha(ROOT/name),'original_size':original,'shown_size':image.size,'recorded_state':metadata.get(name,{})})
  path=OUT/(group+'-input.jpg');board.save(path,quality=91)
  note='\nCurrent evidence group: '+group+'. Required panels: '+', '.join(names)+'.\n'
  if group=='river-gates':note+='All three river-facing gaps intentionally reserve later crossing/bridge corridors. Judge their readability and clear space; do not require bridges in Task 3.'
  if group=='bank-lane':note+='The river-bank lane must remain visibly dry and the three reserved crossing zones open. A future crossing is intentionally absent.'
  if group=='conditions':note+='These share one camera. Judge geometry/material stability across conditions; do not force daytime brightness at night.'
  print('Reviewing',ROLE,group,flush=True);row={'task':'T03-boundary-v1','source':SOURCE,'role':ROLE,'group':group,'inputs':inputs,'passed':False,'independent_execution':False}
  try:
   review,execution=request(path,PROMPT+note,group);row.update(review=review,execution=execution,independent_execution=True);scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<=10 for v in scores.values());assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high');row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9.0 and review['defects']==[] and review['coverage_complete'] and review['confidence']!='low'
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:error=str(exc)
finally:
 provider['independent_model_execution']=any(r.get('independent_execution') for r in rows);(OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2));summary={'task':'T03-boundary-v1','source':SOURCE,'role':ROLE,'reviews':rows,'error':error,'passed':len(rows)==len(GROUPS) and all(r['passed'] for r in rows),'lowest_score':min((r.get('lowest_score',0) for r in rows),default=None),'task_approved':False,'physical4k60_verified':False};(OUT/'role-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
