#!/usr/bin/env python3
"""Read-only independent T02 lake review. Never copies earlier passing scores.
Two separately executed roles use the same publisher-declared model; no claim
of locally verified remote weights. No credentials, paid API or APK upload.
"""
from pathlib import Path
import hashlib,html,json,math,os,re,time,urllib.request
from PIL import Image,ImageDraw
from gradio_client import Client,handle_file
SOURCE=os.environ['EXPECTED_SOURCE'];ROLE=os.environ['REVIEW_ROLE']
assert len(SOURCE)==40 and ROLE in ('reference-fidelity','visual-integrity')
SPACE='Qwen/Qwen3-VL-235B-A22B-Instruct-Demo';REV='eb7f245e2c0d3b573dd8ed6addca9b7f6af26847'
ROOT=Path('lake-evidence');OUT=Path('lake-review');OUT.mkdir(exist_ok=True)
KEYS=['reference_fidelity','material_finish','geometry_contact','layout_readability','view_consistency']
GROUPS={
 'workfloor':['native4k/workfloor-gameplay.png','native4k/native-workfloor-overhead.png','gallery/bay-connection.png','native4k/native-overview.png','gallery/workfloor-gameplay.png','gallery/workfloor-overhead.png','native4k/terrain-only-floor-profile.png','gallery/terrain-only-floor-profile.png'],
 'shoreline':['gallery/lakeshore-gameplay.png','native4k/native-shore-detail.png','gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png','gallery/lakeshore-detail.png','native4k/terrain-only-bank-profile.png','gallery/terrain-only-bank-profile.png'],
 'snow-contact':['native4k/native-snow-join.png','gallery/approved-forest-contact.png','gallery/snow-workfloor-join.png'],
 'tree-visibility':['tree-clearance/clearance-baseline.png','tree-clearance/clearance-disabled.png','tree-clearance/clearance-enabled.png']+[f'tree-clearance/resource-clearance-{i:02d}.png' for i in range(6)]+['tree-clearance/resource-depleted.png','tree-clearance/resource-restored.png'],
 'camera-route-early':[f'gallery/route-camera-{i:02d}.png' for i in range(4)],
 'camera-route-late':[f'gallery/route-camera-{i:02d}.png' for i in range(4,8)],
 'water-sequence':[f'gallery/water-motion-{i:02d}.png' for i in range(6)],
 'night-overview':['gallery/lakeshore-night.png','gallery/terrain-overview.png']+['lake4k/lake-condition-'+n+'.png' for n in ('day','dusk','night','dawn','blizzard-night','day-return')],
 'east-west-extent':['lake4k/'+n+'.png' for n in ('long-lake-gameplay-west','long-lake-gameplay-centre','long-lake-gameplay-east','lake-entire-east-west','lake-top-down-extent','lake-west-bank','lake-east-bank','lake-rear-shore')]
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pro=json.loads((ROOT/'provenance.json').read_text())
assert pro['source']==SOURCE and pro['renderer']=='mobile'
assert set(pro['captures'])=={p for rows in GROUPS.values() for p in rows} and len(pro['captures'])==59
for name,h in pro['captures'].items():assert sha(ROOT/name)==h,'Changed image '+name
ref=ROOT/'reference-ground.webp';assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
metadata={}
for folder in ('gallery','native4k','lake4k'):
 for row in json.loads((ROOT/folder/'capture.json').read_text())['captures']:metadata[folder+'/'+row['name']+'.png']=row
info=json.load(urllib.request.urlopen('https://huggingface.co/api/spaces/'+SPACE,timeout=40))
assert info['sha']==REV and info['private'] is False,'Publisher application changed; inspect before using'
provider={'task':'T02-lake-correction','source':SOURCE,'role':ROLE,'provider_space':SPACE,'provider_space_revision':REV,'declared_model':'qwen3-vl-235b-a22b-instruct','weights_locally_checksum_verified':False,'same_published_model_for_both_roles':True,'code_sha256':sha(Path(__file__)),'evidence_provenance_sha256':sha(ROOT/'provenance.json'),'all59_frame_hashes_verified':True,'independent_model_execution':False,'minimum_gate':9,'task_approved':False,'physical4k60_verified':False,'credentials_used':False,'billing_changed':False}
(OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2))
probe=Image.new('RGB',(720,780),(24,37,52));d=ImageDraw.Draw(probe)
for i,name in enumerate(['clearance-enabled','clearance-disabled','clearance-disabled','clearance-baseline']):
 im=Image.open(ROOT/'tree-clearance'/f'{name}.png').convert('RGB').crop((490,235,790,555));im.thumbnail((360,360));x=i%2*360;y=i//2*390
 probe.paste(im,(x+(360-im.width)//2,y+26));d.text((x+9,y+7),'ABCD'[i],fill='white')
probe.save(OUT/'blind-control.png');expected={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
PROMPT='''Independently inspect the actual source-reference and candidate image board. Review ONLY Task 2 terrain/snow/workfloor/lakeshore, including the user's newest correction: the lake must be much longer, from end to end EAST TO WEST. The candidate spans the full playable map's west-to-east extent. The latest requested length supersedes the old shorter basin. Judge the actual pixels, not a desired score. Source-video crops establish the clean stylized blue-white snow, warm peach/brown working ground and turquoise DAYTIME water. Do not demand gritty realism, and do not penalize the deliberately requested long lake for differing in length from a limited source-video crop. Clean smooth surfaces are intended; unfinished joins, seams, floating water, flooded trees, obstructed routes or wrong palettes are defects.
Candidate panels are unretouched Godot Mobile captures with labelled normal views and disclosed QA angles. Existing stations, characters, fences and final camera behavior belong to later tasks and are not approved here; do not score their incompleteness as lake defects. Approved trees are unchanged, but inspect their contact and visibility where shown. Terrain-only profile cameras hide unrelated models solely to reveal ground geometry; normal views remain included. Motion panels are ordered sampled states, not proof of hardware FPS.
Judge physical integrity under the recorded scene lighting. Night water is intentionally darker; compare the underlying palette in corresponding DAYTIME views rather than requiring night to look like day. Fogged distant overview is a layout view, not a material color swatch. Distinguish actual snow, fog and shadows from missing terrain. Give specific observations and mandatory visible defects naming filenames/regions. Inspect ALL listed frames; unreadable required evidence means coverage_complete false. Independently score reference_fidelity, material_finish, geometry_contact, layout_readability and view_consistency on 0-10, decimals allowed. Zero means absent; ten means fully finished within the demonstrated task scope. A below-nine dimension must identify its actionable deficiency, not be silently rounded up. Do not invent defects to justify a number or omit real defects. Return ONLY one complete JSON object: {"observations":["..."],"defects":[{"view":"candidate filename","region":"...","issue":"..."}],"scores":{"reference_fidelity":0,"material_finish":0,"geometry_contact":0,"layout_readability":0,"view_consistency":0},"coverage_complete":true,"confidence":"low|medium|high"}. Replace example values with your independent judgment; never infer whole-game or physical-device performance approval.'''
PROMPT+='\nRole: '+ROLE+'. '+('Emphasize reference palette, clean finish and the requested much longer east-west lake.' if ROLE=='reference-fidelity' else 'Emphasize bank/ground joins, water boundaries, tree contact, route readability and multi-view consistency.')
(OUT/'rubric.txt').write_text(PROMPT)
def request(image,prompt,label):
 client=Client(SPACE,hf_token=False,download_files=False,verbose=False)
 api=client.view_api(return_format='dict',print_info=False)
 for name,params in {'/add_file':['history','file'],'/add_text':['history','text'],'/predict':['_chatbot']}.items():assert [v['parameter_name'] for v in api['named_endpoints'][name]['parameters']]==params
 (OUT/(label+'-request.json')).write_text(json.dumps({'image_sha256':sha(image),'prompt':prompt,'space':SPACE,'revision':REV,'fresh_session_no_prior_grades':True},indent=2))
 start=time.monotonic();client.predict(history=[],file=handle_file(str(image)),api_name='/add_file');history=client.predict(history=[],text=prompt,api_name='/add_text')
 raw=client.submit(_chatbot=history,api_name='/predict').result(timeout=200)
 (OUT/(label+'-raw.json')).write_text(json.dumps(raw,indent=2,default=str));text=raw[-1][1];assert isinstance(text,str)
 (OUT/(label+'-raw.txt')).write_text(text);clean=html.unescape(re.sub(r'<[^>]+>','\n',text));start_json=clean.find('{');assert start_json>=0,'No complete JSON response'
 result,_=json.JSONDecoder().raw_decode(clean[start_json:]);provider['independent_model_execution']=True
 return result,{'completed_public_job':True,'token_finish_reason_exposed':False,'elapsed_seconds':time.monotonic()-start,'image_sha256':sha(image),'raw_sha256':sha(OUT/(label+'-raw.json'))}
rows=[];error=None
try:
 answer,execution=request(OUT/'blind-control.png','Identify the prominent centre subject in each labelled panel A,B,C,D: human_character, snow_tree, or other_or_unclear. Inspect actual pixels. Return only JSON with keys A,B,C,D. No grades are requested.','control')
 (OUT/'control.json').write_text(json.dumps({'answers':answer,'expected_not_sent':expected,'passed':answer==expected,'execution':execution},indent=2));assert answer==expected,'Blind image-recognition control failed'
 for group,names in GROUPS.items():
  board=Image.new('RGB',(1600,260+((len(names)+1)//2)*480),(24,37,52));d=ImageDraw.Draw(board)
  board.paste(Image.open(ref).convert('RGB'),(8,22));d.text((8,4),'ACTUAL REFERENCE CROPS (DAYTIME)',fill='white');d.text((520,35),'ACTUAL LAKE CORRECTION: '+group,fill='white')
  inputs=[]
  for i,name in enumerate(names):
   image=Image.open(ROOT/name).convert('RGB');original=image.size;image.thumbnail((800,450),Image.Resampling.LANCZOS);x=i%2*800;y=260+(i//2)*480
   board.paste(image,(x+(800-image.width)//2,y+30));d.text((x+5,y+5),name,fill='white')
   inputs.append({'filename':name,'sha256':sha(ROOT/name),'original_size':original,'shown_size':image.size,'recorded_state':metadata.get(name,{})})
  path=OUT/(group+'-input.png');board.save(path)
  note='\nGroup '+group+'. Every required panel: '+', '.join(names)+'.\n'
  for r in inputs:
   s=r['recorded_state']
   if s:note+=r['filename']+': simulation_seconds='+str(s.get('simulation_seconds'))+', hour='+str(s.get('hour','not separately recorded'))+', terrain_only_diagnostic='+str(s.get('terrain_only_diagnostic',False))+'.\n'
  if group=='east-west-extent':note+='The orthographic north-up top-down diagnostic has world west on the left and east on the right; the lake should visibly be a single very long horizontal body with rounded ends, not the former short off-centre pond. Near gameplay views may show only part of the whole lake. Include extent_observation as a string describing what is actually visible; do not infer dimensions from filenames alone.'
  print('Reviewing',ROLE,group,flush=True)
  row={'task':'T02-lake-correction','source':SOURCE,'role':ROLE,'group':group,'inputs':inputs,'passed':False,'independent_execution':False,'control_passed':True}
  try:
   review,execution=request(path,PROMPT+note,group);row.update(review=review,execution=execution,independent_execution=True)
   scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
   assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high')
   row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9 and review['defects']==[] and review['coverage_complete'] and review['confidence']!='low'
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:error=str(exc)
finally:
 (OUT/'provider-provenance.json').write_text(json.dumps(provider,indent=2))
 result={'task':'T02-lake-correction','source':SOURCE,'role':ROLE,'reviews':rows,'error':error,'passed':len(rows)==9 and all(r['passed'] for r in rows),'lowest_score':min((r.get('lowest_score',0) for r in rows),default=None),'task_approved':False,'physical4k60_verified':False}
 (OUT/'role-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
