#!/usr/bin/env python3
"""Independent read-only visual review for T02 river_v1_mapspan.
Two roles execute separately through one disclosed public publisher model. A
returned scored verdict is never retried to chase a higher number; only a
transport/malformed response that yields no complete verdict may retry, with
all failed attempts retained. This script cannot approve physical-device FPS.
"""
from pathlib import Path
import hashlib,html,json,math,os,re,time,urllib.request,shutil
from PIL import Image,ImageDraw
from gradio_client import Client,handle_file
SOURCE=os.environ['EXPECTED_SOURCE'];ROLE=os.environ['REVIEW_ROLE']
assert len(SOURCE)==40 and ROLE in ('reference-fidelity','visual-integrity')
SPACE='Qwen/Qwen3-VL-235B-A22B-Instruct-Demo';REV='eb7f245e2c0d3b573dd8ed6addca9b7f6af26847'
ROOT=Path('river-evidence');OUT=Path('river-review');OUT.mkdir(exist_ok=True)
KEYS=['reference_fidelity','river_form','bank_finish','expansion_readiness','view_consistency']
GROUPS={
 'map-span':['gallery/river-plan-topdown.png','gallery/river-plan-oblique.png','native4k/native-river-plan.png'],
 'current-layout':['gallery/river-current-topdown.png','gallery/river-current-oblique.png','gallery/camp-river-overhead.png','gallery/camp-river-oblique.png','native4k/native-current-map.png','native4k/native-camp-river-overhead.png'],
 'endpoints':['gallery/river-west-entry.png','gallery/river-east-exit.png','native4k/native-west-entry.png','native4k/native-east-exit.png'],
 'meanders-west':[f'gallery/river-bend-{i:02d}.png' for i in range(4)]+['native4k/native-bend-m10.png','native4k/native-bend-m3.png'],
 'meanders-east':[f'gallery/river-bend-{i:02d}.png' for i in range(4,8)]+['native4k/native-bend-4.png','native4k/native-bend-11.png'],
 'bank-contact':['gallery/north-bank-contact.png','gallery/south-bank-contact.png','native4k/native-north-bank-contact.png','native4k/native-south-bank-contact.png'],
 'gameplay-banks':['gallery/river-gameplay-'+n+'.png' for n in ('north-west','north-centre','north-east','south-west','south-centre','south-east')],
 'crossing-reserves':[f'gallery/crossing-reserve-{i:02d}.png' for i in range(3)],
 'flow-sequence':[f'gallery/river-flow-{i:02d}.png' for i in range(6)],
 'conditions':['gallery/river-condition-'+n+'.png' for n in ('day','dusk','night','dawn','blizzard-night','day-return')]
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pro=json.loads((ROOT/'provenance.json').read_text());assert pro['source']==SOURCE and pro['renderer']=='mobile'
required={p for rows in GROUPS.values() for p in rows}
assert required.issubset(set(pro['captures'])) and len(pro['captures'])==61
for name,h in pro['captures'].items():assert sha(ROOT/name)==h,'Changed image '+name
ref=ROOT/'reference-ground.webp';assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
metadata={}
for folder in ('gallery','native4k'):
 for row in json.loads((ROOT/folder/'capture.json').read_text())['captures']:metadata[folder+'/'+row['name']+'.png']=row
info=json.load(urllib.request.urlopen('https://huggingface.co/api/spaces/'+SPACE,timeout=40));assert info['sha']==REV and info['private'] is False
provider={'task':'T02-river-v1-mapspan','source':SOURCE,'role':ROLE,'provider_space':SPACE,'provider_space_revision':REV,'declared_model':'qwen3-vl-235b-a22b-instruct','weights_locally_checksum_verified':False,'same_published_model_for_both_roles':True,'code_sha256':sha(Path(__file__)),'evidence_provenance_sha256':sha(ROOT/'provenance.json'),'all61_frame_hashes_verified':True,'independent_model_execution':False,'minimum_gate':9.0,'task_approved':False,'physical4k60_verified':False,'credentials_used':False,'billing_changed':False}
(OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2))
# Blind factual control is intentionally unrelated to the desired river score.
probe=Image.new('RGB',(720,780),(24,37,52));d=ImageDraw.Draw(probe)
for i,name in enumerate(['clearance-enabled','clearance-disabled','clearance-disabled','clearance-baseline']):
 im=Image.open(ROOT/'tree-clearance'/f'{name}.png').convert('RGB').crop((490,235,790,555));im.thumbnail((360,360));x=i%2*360;y=i//2*390
 probe.paste(im,(x+(360-im.width)//2,y+26));d.text((x+9,y+7),'ABCD'[i],fill='white')
probe.save(OUT/'blind-control.png');expected={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
PROMPT='''Independently inspect the actual source-reference crop and every labelled Havenline candidate panel. Review ONLY reopened Task 2: terrain, snow, warm work area and the new persistent MAP-SPANNING RIVER. The user's locked requirement supersedes the former lake: the river is one continuous west-to-east world backbone across the full authored terrain, with smooth natural meanders, usable dry land on both sides, main camp on the north bank, and future crossing corridors intentionally left open. No bridges/fences are required in Task 2; those are later tasks. Future expansion should reveal more of this same river rather than a separate water body.
The source-video crop establishes the clean sculpted blue-white winter styling, warm peach/brown cleared ground and saturated turquoise water language; it does NOT prescribe the new river's exact spline. Judge the candidate pixels rather than demanding gritty realism or a lake shape. Smooth stylized surfaces are intended. Visible stretched-lake geometry, abrupt zigzags, sharp spline kinks, flooded trees, floating bank pieces, water/terrain seams, clipping, ugly repetition, implausibly pinched/wide reaches, unusable bank strips, obstructed reserved crossings, broken flow appearance, or inconsistent state views are defects.
Top-down and oblique plan frames are disclosed QA cameras used to prove the full authored map and future expansion. Gameplay-bank frames are normal camera states. Native frames are unretouched 3840x2160 render-scale-1 captures on the software Mobile renderer and prove pixel output only, NOT phone/tablet FPS or thermals. Night water may be darker than day; compare finish across the provided conditions rather than forcing a daytime palette at night.
Inspect ALL panels in the current group. Give specific observations tied to actual filenames/regions. Score exactly these dimensions 0-10: reference_fidelity (stylistic fit to supplied reference), river_form (continuous natural readable river form), bank_finish (snow/water/ground contact and polish), expansion_readiness (visually usable banks and unobstructed growth/crossing space), view_consistency (same geometry/materials hold across angles/states). A score below 9 must name the actionable deficiency. Do not invent a defect merely to justify a lower number, and do not omit a real visible defect. Return ONLY one complete JSON object: {"observations":["..."],"defects":[{"view":"filename","region":"...","issue":"..."}],"scores":{"reference_fidelity":0,"river_form":0,"bank_finish":0,"expansion_readiness":0,"view_consistency":0},"coverage_complete":true,"confidence":"low|medium|high"}. This is scoped Task 2 review only; never infer whole-game or physical-device approval.'''
PROMPT+='\nRole: '+ROLE+'. '+('Prioritize the reference visual language, natural readable river silhouette and coherent camp/river composition.' if ROLE=='reference-fidelity' else 'Prioritize geometry integrity, bank contacts, no flooded/hovering content, open crossing corridors, flow/state continuity and multi-view consistency.')
(OUT/'rubric.txt').write_text(PROMPT)
def request_once(image,prompt,label):
 client=Client(SPACE,hf_token=False,download_files=False,verbose=False);api=client.view_api(return_format='dict',print_info=False)
 for name,params in {'/add_file':['history','file'],'/add_text':['history','text'],'/predict':['_chatbot']}.items():assert [v['parameter_name'] for v in api['named_endpoints'][name]['parameters']]==params
 (OUT/(label+'-request.json')).write_text(json.dumps({'image_sha256':sha(image),'prompt':prompt,'space':SPACE,'revision':REV,'fresh_session_no_prior_grades':True},indent=2))
 start=time.monotonic();client.predict(history=[],file=handle_file(str(image)),api_name='/add_file');history=client.predict(history=[],text=prompt,api_name='/add_text');raw=client.submit(_chatbot=history,api_name='/predict').result(timeout=220)
 (OUT/(label+'-raw.json')).write_text(json.dumps(raw,indent=2,default=str));text=raw[-1][1];assert isinstance(text,str);(OUT/(label+'-raw.txt')).write_text(text)
 clean=html.unescape(re.sub(r'<[^>]+>','\n',text));start_json=clean.find('{');assert start_json>=0,'No complete JSON response';result,_=json.JSONDecoder().raw_decode(clean[start_json:])
 return result,{'completed_public_job':True,'elapsed_seconds':time.monotonic()-start,'image_sha256':sha(image),'raw_sha256':sha(OUT/(label+'-raw.json'))}
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
  board=Image.new('RGB',(1600,260+((len(names)+1)//2)*480),(24,37,52));d=ImageDraw.Draw(board);reference=Image.open(ref).convert('RGB');reference.thumbnail((500,230));board.paste(reference,(8,25));d.text((8,5),'ACTUAL REFERENCE VIDEO CROPS',fill='white');d.text((530,40),'ACTUAL TASK 2 RIVER: '+group,fill='white')
  inputs=[]
  for i,name in enumerate(names):
   image=Image.open(ROOT/name).convert('RGB');original=image.size;image.thumbnail((800,450),Image.Resampling.LANCZOS);x=i%2*800;y=260+(i//2)*480;board.paste(image,(x+(800-image.width)//2,y+30));d.text((x+5,y+5),name,fill='white');inputs.append({'filename':name,'sha256':sha(ROOT/name),'original_size':original,'shown_size':image.size,'recorded_state':metadata.get(name,{})})
  path=OUT/(group+'-input.jpg');board.save(path,quality=91)
  note='\nCurrent evidence group: '+group+'. Required panels: '+', '.join(names)+'.\n'
  if group=='map-span':note+='The top-down plan is the decisive visual for whether one continuous river spans the FULL 62-unit authored terrain; current movement unlocks only its central portion. Do not mistake future locked terrain outside the current play rectangle for missing river.'
  if group=='crossing-reserves':note+='These are RESERVED OPEN corridors, not unfinished missing bridges. Judge whether the banks remain visually usable/open; do not require a bridge in Task 2.'
  if group=='flow-sequence':note+='These are ordered sampled simulation states, not a frame-rate test. Judge continuity and whether the water reads as a subtle west-to-east current without obvious discontinuities.'
  print('Reviewing',ROLE,group,flush=True);row={'task':'T02-river-v1-mapspan','source':SOURCE,'role':ROLE,'group':group,'inputs':inputs,'passed':False,'independent_execution':False}
  try:
   review,execution=request(path,PROMPT+note,group);row.update(review=review,execution=execution,independent_execution=True);scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<=10 for v in scores.values());assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high');row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9.0 and review['defects']==[] and review['coverage_complete'] and review['confidence']!='low'
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:error=str(exc)
finally:
 provider['independent_model_execution']=any(r.get('independent_execution') for r in rows);(OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2));summary={'task':'T02-river-v1-mapspan','source':SOURCE,'role':ROLE,'reviews':rows,'error':error,'passed':len(rows)==len(GROUPS) and all(r['passed'] for r in rows),'lowest_score':min((r.get('lowest_score',0) for r in rows),default=None),'task_approved':False,'physical4k60_verified':False};(OUT/'role-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
