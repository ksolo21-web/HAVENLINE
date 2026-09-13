#!/usr/bin/env python3
"""Independent full-coverage T02 review via the publisher's public image demo.

The input adapter repairs a verified display-history serialization failure.
Earlier 9B reviews/conflicting observations are preserved unchanged. This is
not a request for a desired score or a new game revision. Both roles review all
45 actual frames, with exact recorded scene conditions, without prior scores.
No user credential, billing change, private reference chrome or APK upload.
"""
from __future__ import annotations
import hashlib,html,json,math,os,re,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from gradio_client import Client,handle_file

SOURCE='96f8d396a5015e136c590dc496214a689adb1e43'
SPACE='Qwen/Qwen3-VL-235B-A22B-Instruct-Demo'
SPACE_REV='eb7f245e2c0d3b573dd8ed6addca9b7f6af26847'
ROLE=os.environ['REVIEW_ROLE'];assert ROLE in ('reference-fidelity','visual-integrity')
ROOT=Path('evidence');OUT=Path('publisher-review');OUT.mkdir(exist_ok=True)
KEYS=['reference_fidelity','material_finish','geometry_contact','layout_readability','view_consistency']
GROUPS={
 'workfloor':['native4k/workfloor-gameplay.png','native4k/native-workfloor-overhead.png','gallery/bay-connection.png','native4k/native-overview.png','gallery/workfloor-gameplay.png','gallery/workfloor-overhead.png','native4k/terrain-only-floor-profile.png','gallery/terrain-only-floor-profile.png'],
 'shoreline':['gallery/lakeshore-gameplay.png','native4k/native-shore-detail.png','gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png','gallery/lakeshore-detail.png','native4k/terrain-only-bank-profile.png','gallery/terrain-only-bank-profile.png'],
 'snow-contact':['native4k/native-snow-join.png','gallery/approved-forest-contact.png','gallery/snow-workfloor-join.png'],
 'tree-visibility':['tree-clearance/clearance-baseline.png','tree-clearance/clearance-disabled.png','tree-clearance/clearance-enabled.png']+[f'tree-clearance/resource-clearance-{i:02d}.png' for i in range(6)]+['tree-clearance/resource-depleted.png','tree-clearance/resource-restored.png'],
 'camera-route-early':[f'gallery/route-camera-{i:02d}.png' for i in range(4)],
 'camera-route-late':[f'gallery/route-camera-{i:02d}.png' for i in range(4,8)],
 'water-sequence':[f'gallery/water-motion-{i:02d}.png' for i in range(6)],
 'night-overview':['gallery/lakeshore-night.png','gallery/terrain-overview.png']
}

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
pro=json.loads((ROOT/'provenance.json').read_text());assert pro['source']==SOURCE and pro['renderer']=='mobile'
assert set(pro['captures'])==set(x for names in GROUPS.values() for x in names)
assert len(pro['captures'])==45
for name,h in pro['captures'].items():assert sha(ROOT/name)==h,'Changed actual image '+name
ref=ROOT/'reference-ground.webp';assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
metadata={}
for folder in ('gallery','native4k'):
 for record in json.loads((ROOT/folder/'capture.json').read_text())['captures']:
  metadata[folder+'/'+record['name']+'.png']=record

info=json.load(urllib.request.urlopen('https://huggingface.co/api/spaces/'+SPACE,timeout=30))
assert info['sha']==SPACE_REV and info['private'] is False,'Publisher application changed; inspect before proceeding'
provenance={'task':'T02','source':SOURCE,'role':ROLE,'provider_space':SPACE,'provider_space_revision':SPACE_REV,'declared_model':'qwen3-vl-235b-a22b-instruct','weights_locally_checksum_verified':False,'public_runtime':info.get('runtime'),'code_sha256':sha(Path(__file__)),'evidence_provenance_sha256':sha(ROOT/'provenance.json'),'reference_sha256':sha(ref),'all45_frame_hashes_verified':True,'independent_model_execution':False,'prior_9B_raw_results_preserved':True,'reason':'Full independent review after demonstrated image/state misinterpretations in earlier reports, including snow called empty void and nighttime water compared with daytime coloration. No previous scores or desired grade supplied.','score_dimensions_unchanged':KEYS,'minimum_gate_unchanged':9,'task_approved':False,'physical4k60_verified':False,'user_account_credentials_used':False,'billing_settings_changed':False}
(OUT/'provider-provenance.json').write_text(json.dumps(provenance,indent=2))

# Blind controls; answer key is not included in any request.
probe=Image.new('RGB',(720,780),(24,37,52));d=ImageDraw.Draw(probe)
for i,name in enumerate(['clearance-enabled','clearance-disabled','clearance-disabled','clearance-baseline']):
 im=Image.open(ROOT/'tree-clearance'/f'{name}.png').convert('RGB').crop((490,235,790,555));im.thumbnail((360,360));x=i%2*360;y=i//2*390
 probe.paste(im,(x+(360-im.width)//2,y+26));d.text((x+9,y+7),'ABCD'[i],fill='white')
probe.save(OUT/'blind-control.png')
expected={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}

# Use the same observable task scope as the existing independent review.
PROMPT='''Independently inspect the actual reference and candidate image board. Review ONLY Task 2: terrain, snow, warm cleared work floor, connected lakeside work area, lake bank/water, ground contact and ground-route readability. The top-left source-video crops establish clean stylized blue-white snow, warm peach/brown working ground and turquoise daytime water. Candidate panels are unretouched Godot Mobile renders. Match that observable language, not gritty photorealism. Intentionally smooth floors/snow are legitimate; unfinished-looking surfaces, wrong material palette, obvious geometric seams, floating contacts or obstructed ground routes are defects. Do not invent defects or overlook real ones.
Existing cabins, machinery, NPCs, fences and final camera behavior belong to later locked tasks. Do not score their incompleteness as ground defects or approve them. Approved tree geometry is unchanged; inspect its contact and visibility where demonstrated. Enlarged overhead and terrain-only profile cameras are disclosed diagnostics. They do not replace normal views. Motion panels are ordered sampled camera/water/fade states, not proof of 60FPS or arbitrary in-between motion. Judge all labelled frames in the group; unreadable essential evidence requires incomplete coverage rather than invented certainty.
Recorded conditions below describe the actual capture, not a grade or a verdict. Judge physical integrity under each shown condition; compare the underlying palette to the reference in corresponding daytime normal/close views, not by requiring a night scene to have daytime brightness. A distant fogged overview is a layout diagnostic, not a material swatch. A terrain-only diagnostic hides unrelated meshes after setting the camera; it does not delete any terrain. Distinguish cast shadows, material transitions and genuine voids from actual pixels; report uncertainty rather than confidently inventing geometry.
Give two or three concrete observations and any unresolved mandatory defects, each identifying candidate filename, region and issue. Independently score reference_fidelity, material_finish, geometry_contact, layout_readability and view_consistency on 0 to 10, decimals allowed. Zero is absent/uncompleted; ten means finished within the shown scope with no known mandatory defect. Desired scores are not supplied and must not influence your judgment. If a dimension is below 9, describe the specific deficiency so the developer can address it; this does NOT mean you should raise the score or invent a defect. Use an empty defects array only when no mandatory visible defect is found. Coverage must be complete only if you actually inspected all listed panels. Never claim full-game approval or hardware frame rate.
Return ONE complete JSON object only: {"observations":["..."],"defects":[{"view":"candidate path","region":"...","issue":"..."}],"scores":{"reference_fidelity":0,"material_finish":0,"geometry_contact":0,"layout_readability":0,"view_consistency":0},"coverage_complete":true,"confidence":"low|medium|high"}. Replace example numbers/values with your own judgment.'''
PROMPT+='\nIndependent role: '+ROLE+'. '+('Emphasize actual reference palette, clean surface finish, workfloor and shoreline spatial language.' if ROLE=='reference-fidelity' else 'Emphasize actual ground/shore joins, contact, shape continuity and view consistency, independently checking reference fidelity too.')
(OUT/'rubric.txt').write_text(PROMPT)

# One normal public session per request. Uploaded image is held in the app's
# own gr.State; display-only history is empty to avoid local/remote path errors.
def request(image:Path,prompt:str,label:str):
 client=Client(SPACE,hf_token=False,download_files=False,verbose=False)
 api=client.view_api(return_format='dict',print_info=False)
 for name,params in {'/add_file':['history','file'],'/add_text':['history','text'],'/predict':['_chatbot']}.items():
  assert [v['parameter_name'] for v in api['named_endpoints'][name]['parameters']]==params
 (OUT/(label+'-request.json')).write_text(json.dumps({'space':SPACE,'space_revision':SPACE_REV,'image_filename':image.name,'image_sha256':sha(image),'prompt':prompt,'session_scope':'fresh independent public demo session; no previous grades/answers'},indent=2))
 began=time.monotonic()
 client.predict(history=[],file=handle_file(str(image)),api_name='/add_file')
 history=client.predict(history=[],text=prompt,api_name='/add_text')
 response=client.submit(_chatbot=history,api_name='/predict').result(timeout=180)
 elapsed=time.monotonic()-began
 (OUT/(label+'-raw.json')).write_text(json.dumps(response,indent=2,default=str))
 text=response[-1][1];assert isinstance(text,str)
 (OUT/(label+'-raw.txt')).write_text(text)
 clean=html.unescape(re.sub(r'<[^>]+>','\n',text));start=clean.find('{');assert start>=0,'No complete JSON response'
 parsed,end=json.JSONDecoder().raw_decode(clean[start:])
 provenance['independent_model_execution']=True
 # Service returns a completed public job, not a token-level finish_reason.
 return parsed,{'elapsed_seconds':elapsed,'service_job_completed':True,'token_finish_reason_exposed':False,'image_sha256':sha(image),'raw_sha256':sha(OUT/(label+'-raw.json'))}

rows=[];error=None
try:
 answer,control=request(OUT/'blind-control.png','Four panels are labelled A, B, C and D. For EACH panel identify the prominent subject nearest the centre: human_character, snow_tree, or other_or_unclear. Judge the actual pixels. Return ONLY a JSON object with keys A, B, C and D. This is an image-recognition check, not an art grade.','control')
 (OUT/'control.json').write_text(json.dumps({'answers':answer,'expected_not_sent':expected,'passed':answer==expected,'execution':control},indent=2))
 assert answer==expected,'Blind factual control failed; cannot accept subsequent grades'
 for group,names in GROUPS.items():
  w=800;h=480;cols=2;board=Image.new('RGB',(w*cols,260+((len(names)+1)//2)*h),(24,37,52));draw=ImageDraw.Draw(board)
  rim=Image.open(ref).convert('RGB');board.paste(rim,(8,22));draw.text((8,4),'ACTUAL REFERENCE CROPS A / B (DAYTIME)',fill='white');draw.text((520,35),'TASK 2 ACTUAL CANDIDATE: '+group,fill='white')
  records=[]
  for i,name in enumerate(names):
   image=Image.open(ROOT/name).convert('RGB');original=image.size;image.thumbnail((w,h-30),Image.Resampling.LANCZOS);x=(i%2)*w;y=260+(i//2)*h
   board.paste(image,(x+(w-image.width)//2,y+30));draw.text((x+6,y+6),name,fill='white')
   state=metadata.get(name,{})
   records.append({'filename':name,'sha256':sha(ROOT/name),'original_size':original,'shown_size':image.size,'recorded_capture_state':state})
  path=OUT/(group+'-input.png');board.save(path)
  note='\nGroup: '+group+'; every candidate frame: '+', '.join(names)+'.\n'
  for r in records:
   st=r['recorded_capture_state']
   if st:
    note+=r['filename']+': simulation_seconds='+str(st.get('simulation_seconds'))+', camera_position='+str(st.get('camera_position'))+', orthographic_size='+str(st.get('camera_size'))+', terrain_only_diagnostic='+str(st.get('terrain_only_diagnostic',False))+'.\n'
  if group=='night-overview':note+='The lakeshore-night frame is simulated night (630 seconds, hour22.6); terrain-overview is simulated daytime (0seconds, hour10) at a distant diagnostic camera. Night integrity must still pass; intentional night illumination is not a request to waive defects.\n'
  if group=='tree-visibility':note+='The first three images are baseline, clearance-disabled and clearance-enabled; the following six are successive fade states, then distinct depleted and restored resource states. Inspect the actual ground and subject visibility, not labels alone.\n'
  print('Reviewing',ROLE,group,flush=True)
  row={'task':'T02','source':SOURCE,'role':ROLE,'group':group,'passed':False,'independent_execution':False,'control_passed':True,'inputs':records}
  try:
   review,execution=request(path,PROMPT+note,group);row.update(review=review,execution=execution,independent_execution=True)
   scores=review['scores'];assert set(scores)==set(KEYS) and all(type(x) in (int,float) and math.isfinite(x) and 0<=x<=10 for x in scores.values())
   assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high')
   for defect in review['defects']:assert isinstance(defect,dict) and set(defect)=={'view','region','issue'}
   row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9 and not review['defects'] and review['coverage_complete'] and review['confidence']!='low'
  except Exception as exc:
   row['error']=str(exc);error=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2),flush=True)
  if row.get('error'):break # Do not evade a service refusal, timeout or rate limit.
  time.sleep(2)
finally:
 (OUT/'provider-provenance.json').write_text(json.dumps(provenance,indent=2))
 report={'task':'T02','source':SOURCE,'role':ROLE,'reviews':rows,'error':error,'groups_required':list(GROUPS),'groups_completed':len(rows),'all_required_groups_passed':len(rows)==8 and all(r['passed'] for r in rows),'lowest_score':min((r.get('lowest_score',0) for r in rows),default=None),'model_as_declared_by_publisher':'qwen3-vl-235b-a22b-instruct','public_space_revision':SPACE_REV,'weights_locally_verified':False,'task_approved':False,'previous_reviews_preserved':True,'physical_phone_tablet4k60_verified':False,'task3_started':False}
 (OUT/'role-summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
