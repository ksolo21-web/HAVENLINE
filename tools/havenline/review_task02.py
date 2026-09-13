#!/usr/bin/env python3
"""Read-only independent T02 visual review. No score injection or source mutation.
One pinned model family, separate reference-fidelity and visual-integrity roles.
Preserve raw results and input hashes. Neither this review nor screenshots certify FPS.
"""
from __future__ import annotations
import base64,copy,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path('task02-evidence');OUT=Path('task02-review');OUT.mkdir(exist_ok=True)
ROLE=os.environ['REVIEW_ROLE'];GROUP=os.environ['REVIEW_GROUP']
assert ROLE in ('reference-fidelity','visual-integrity')
GROUPS={
 'workfloor':['gallery/workfloor-gameplay.png','gallery/workfloor-overhead.png','gallery/bay-connection.png','native4k/native-overview.png'],
 'shoreline':['gallery/lakeshore-gameplay.png','gallery/lakeshore-detail.png','gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png'],
 'snow-contact':['gallery/snow-workfloor-join.png','gallery/approved-forest-contact.png','tree-clearance/clearance-baseline.png','tree-clearance/clearance-disabled.png','tree-clearance/clearance-enabled.png','tree-clearance/resource-depleted.png','tree-clearance/resource-restored.png'],
 'motion-light':[f'gallery/route-camera-{i:02d}.png' for i in range(8)]+[f'gallery/water-motion-{i:02d}.png' for i in range(6)]+['gallery/lakeshore-night.png','gallery/terrain-overview.png']
}
assert GROUP in GROUPS
KEYS=['reference_fidelity','material_finish','geometry_contact','layout_readability','view_consistency']
CACHE=Path.home()/'.cache/havenline-t01-qwen35'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()

p=json.loads((ROOT/'provenance.json').read_text());source=p['source']
assert p['task']=='T02' and len(source)==40 and p['renderer']=='mobile'
for name,h in p['captures'].items():assert sha(ROOT/name)==h,'Changed capture '+name
ref=Path('Docs/Production/T02/reference-ground.webp')
assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
manifest=json.loads((CACHE/'manifest.json').read_text())
assert manifest['base_model']=='Qwen/Qwen3.5-9B' and manifest['revision']=='3885219b6810b007914f3a7950a8d1b469d598a5'
for row in manifest['files']:assert sha(CACHE/row['filename'])==row['sha256'],'Unverified model bytes'
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0]
provenance={'task':'T02','source':source,'role':ROLE,'group':GROUP,'model':manifest['base_model'],'model_revision':manifest['revision'],'runtime_manifest':manifest,'reference_sha256':sha(ref),'script_sha256':sha(__file__),'capture_provenance_sha256':sha(ROOT/'provenance.json'),'independent_model_execution':False,'physical_4k60_verified':False,'same_model_family_roles_disclosed':True}

# Single-board, blind same/different image controls. Expected answers are NOT sent.
probe=Image.new('RGB',(960,560),(24,37,52));draw=ImageDraw.Draw(probe)
probe_files=[ref,ref,ROOT/'gallery/lakeshore-detail.png',ROOT/'gallery/workfloor-overhead.png']
for i,path in enumerate(probe_files):
 im=Image.open(path).convert('RGB');im.thumbnail((480,250));x=(i%2)*480;y=(i//2)*280
 probe.paste(im,(x+(480-im.width)//2,y+25));draw.text((x+10,y+7),'ABCD'[i],fill='white')
probe.save(OUT/'blind-control.png')
probe_expected={'A_B_same_scene':True,'C_D_same_scene':False}

names=GROUPS[GROUP];columns=2 if len(names)<=4 else (3 if len(names)<=9 else 4)
tile_w=1440//columns;tile_h=int(tile_w*9/16)+24
rows=(len(names)+columns-1)//columns
board=Image.new('RGB',(1440,260+rows*tile_h),(24,37,52));d=ImageDraw.Draw(board)
rim=Image.open(ref).convert('RGB');board.paste(rim,(8,22));d.text((8,4),'ACTUAL REFERENCE CROPS: A / B',fill='white')
d.text((520,35),'TASK 2 ACTUAL CANDIDATE: '+GROUP,fill='white')
inputs=[]
for i,name in enumerate(names):
 im=Image.open(ROOT/name).convert('RGB');original=list(im.size);im.thumbnail((tile_w,tile_h-24))
 x=(i%columns)*tile_w;y=260+(i//columns)*tile_h
 board.paste(im,(x+(tile_w-im.width)//2,y+24));d.text((x+5,y+6),name,fill='white')
 inputs.append({'file':name,'original_size':original,'original_sha256':sha(ROOT/name)})
board.save(OUT/'comparison.png')

PROMPT='''Independently inspect this labelled reference/candidate comparison. Review ONLY Task2: terrain, snow, warm cleared work floor, connected lakeside work area, lake bank/water, ground contact and ground-route readability. The actual source-video crops at top left show the intended clean stylized blue-white snow, warm peach/brown working ground and turquoise water. The candidate panels are unretouched Godot Mobile renders. Match that observable visual language; the reference is not gritty photorealism. Intentionally smooth floors/snow are legitimate, but unfinished-looking surfaces, wrong palette, obvious geometric seams, floating contacts or obstructed ground routes are defects. Do not invent defects merely to fill a list; do not overlook real ones.
The existing cabins, machinery, NPCs, fences and final camera behavior belong to later locked tasks. Do not score their incompleteness as ground defects or approve those tasks. Approved trees are preserved; inspect their contact and visibility only where shown. Ground/water routes must look coherent in the actual layouts. Enlarged diagnostic and overhead cameras are disclosed inspection views, not changed shipping cameras. In clearance tests the labels denote baseline, cutaway disabled, cutaway enabled, depleted and restored tree states: intentional tree disappearance is not automatically missing artwork. Judge what is visible rather than assuming labels prove behavior. Motion panels are ordered sampled camera/water states; do not claim they prove animation smoothness at 60FPS, hardware performance or complete-game functionality.
Give two or three specific visible observations, up to four concrete mandatory defects with panel and location, and independent 0-10 scores for reference_fidelity, material_finish, geometry_contact, layout_readability and view_consistency. Zero means absent/uncompleted and ten means finished within the demonstrated scope with no known mandatory defect. A stated desired score must not influence your scores. Mark coverage_complete false or confidence low if the necessary pixels are unreadable or evidence is inadequate. Output only the requested JSON. No full-game, frame-rate or later-task approval.'''
PROMPT+='\nRole: '+ROLE+'. '+('Emphasize the actual reference palette, clean surface finish, workfloor and shoreline spatial language.' if ROLE=='reference-fidelity' else 'Emphasize actual ground/shore joins, contact, shape continuity and view consistency, independently checking reference fidelity too.')
PROMPT+='\nGroup: '+GROUP+'; candidate views: '+', '.join(names)
(OUT/'instructions.txt').write_text(PROMPT);(OUT/'source-inputs.json').write_text(json.dumps(inputs,indent=2))
schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defects':{'type':'array','items':{'type':'string'},'maxItems':4},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']}},'required':['observations','defects','scores','coverage_complete','confidence'],'additionalProperties':False}
(OUT/'schema.json').write_text(json.dumps(schema,indent=2))

def query(image,prompt,shape,label,tokens):
 im=Image.open(image).convert('RGB');original=list(im.size);im.thumbnail((1536,1536),Image.Resampling.LANCZOS)
 b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
 body={'model':'T02-'+ROLE,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':tokens,'temperature':.15,'top_p':.9,'seed':20260910 if ROLE=='reference-fidelity' else 20260911,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':shape},'cache_prompt':False}
 req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
 begin=time.monotonic()
 with urllib.request.urlopen(req,timeout=900) as response:raw=json.load(response)
 (OUT/(label+'-raw.json')).write_text(json.dumps(raw,indent=2));provenance['independent_model_execution']=True
 choice=raw['choices'][0];assert choice['finish_reason']=='stop','Truncated '+label
 text=choice['message']['content'];(OUT/(label+'-raw.txt')).write_text(text)
 result=json.loads(text)
 meta={'original_size':original,'model_size':list(im.size),'original_sha256':sha(image),'model_input_sha256':hashlib.sha256(data).hexdigest(),'elapsed_seconds':time.monotonic()-begin}
 (OUT/(label+'-input.png')).write_bytes(data)
 return result,meta

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--mmproj',str(CACHE/manifest['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','1024','--image-max-tokens','2048']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
report={'task':'T02','source':source,'role':ROLE,'group':GROUP,'passed':False,'independent_execution':False,'control_passed':False,'task_approved':False,'physical_4k60_verified':False}
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('Pinned vision runtime exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Vision runtime startup timed out')
 ps={'type':'object','properties':{k:{'type':'boolean'} for k in probe_expected},'required':list(probe_expected),'additionalProperties':False}
 answer,control=query(OUT/'blind-control.png','Inspect labelled panels A, B, C and D. Do A and B show the same scene image? Do C and D show the same scene image? Ignore panel labels when comparing. Return only A_B_same_scene and C_D_same_scene booleans from the pixels.',ps,'control',120)
 report['control_passed']=answer==probe_expected
 (OUT/'control.json').write_text(json.dumps({'answers':answer,'expected':probe_expected,'passed':report['control_passed'],'answer_key_not_sent':True,'input':control},indent=2))
 assert report['control_passed'],'Blind same/different image control failed; no art score accepted'
 review,meta=query(OUT/'comparison.png',PROMPT,schema,'review',600)
 report['independent_execution']=True;report['review']=review;report['model_input']=meta
 scores=review['scores'];assert set(scores)==set(KEYS) and all(type(x) in (int,float) and math.isfinite(x) and 0<=x<=10 for x in scores.values())
 assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high')
 report['lowest_score']=min(scores.values())
 report['passed']=report['lowest_score']>=9 and not review['defects'] and review['coverage_complete'] and review['confidence']!='low'
except Exception as exc:report['error']=str(exc)
finally:
 (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))
 (OUT/'review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
# A completed review job is not a pass; the raw review and task evidence decide.
