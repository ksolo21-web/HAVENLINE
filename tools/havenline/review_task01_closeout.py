#!/usr/bin/env python3
"""Independent T01 review with single-image boards and blind comparison controls.
The previous comparison path invented differences between identical images.
This runner must pass same/different controls before grading. It neither changes
candidate pixels nor supplies desired scores. All failed reports are preserved.
"""
from __future__ import annotations
import base64,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw
E=Path('task01-evidence');O=Path('critic-results');O.mkdir(exist_ok=True)
ROLE=os.environ['REVIEW_ROLE'];GROUP=os.environ['REVIEW_GROUP']
GROUPS=('variant-1','variant-2','variant-3','forest','clearance','camera-motion')
KEYS=('silhouette','materials','reference_fidelity','integration','geometric_integrity')
assert ROLE in ('reference-fidelity','visual-integrity') and GROUP in GROUPS
CACHE=Path.home()/'.cache/havenline-t01-qwen35'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4194304),b''):h.update(block)
 return h.hexdigest()
pro=json.loads((E/'provenance.json').read_text());SOURCE=pro['source']
assert pro['task']=='T01' and pro['evidence_revision']==10
for name,h in pro['captures'].items():assert sha(E/name)==h,name
ref=E/'reference-detail.webp';assert sha(ref)=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'
m=json.loads((CACHE/'manifest.json').read_text())
assert m['base_model']=='Qwen/Qwen3.5-9B' and m['revision']=='3885219b6810b007914f3a7950a8d1b469d598a5'
for item in m['files']:assert sha(CACHE/item['filename'])==item['sha256']
server=next((CACHE/'runtime').rglob('llama-server'))
controls=[]
provenance={'task':'T01','source':SOURCE,'role':ROLE,'group':GROUP,'model':m['base_model'],'model_revision':m['revision'],'runtime_manifest':m,'capture_provenance':pro,'reviewer_sha256':sha(__file__),'independent_model_execution':False,'comparison_controls_passed':False,'old_failed_reviews_preserved':True,'task_approved':False,'physical_4k60_verified':False}

def cropped(rel,box=None):
 im=Image.open(E/rel).convert('RGB')
 if box:
  sx=im.width/1280;sy=im.height/720
  im=im.crop(tuple(round(value*(sx if i%2==0 else sy)) for i,value in enumerate(box)))
 return im

def board(name,panels,cols=2,tile=(600,540),reference=True):
 w,h=tile;header=340 if reference else 0
 image=Image.new('RGB',(w*cols,header+math.ceil(len(panels)/cols)*h),(233,239,244));d=ImageDraw.Draw(image)
 if reference:
  image.paste(Image.open(ref).convert('RGB'),(6,10))
  d.text((460,35),'REFERENCE A / B at left. ACTUAL '+name+' below.',fill='black')
 origins=[]
 for i,(label,rel,box) in enumerate(panels):
  im=cropped(rel,box);im.thumbnail((w-10,h-27),Image.Resampling.LANCZOS)
  x=i%cols*w;y=header+i//cols*h
  d.text((x+6,y+5),label,fill='black');image.paste(im,(x+(w-im.width)//2,y+27))
  origins.append({'label':label,'file':rel,'source_sha256':sha(E/rel),'crop_in_1280x720_coordinates':box})
 path=O/(name+'.png');image.save(path);(O/(name+'-sources.json')).write_text(json.dumps(origins,indent=2));return path

r=Image.open(ref).convert('RGB').crop((0,0,220,300))
human=cropped('clearance/clearance-baseline.png',(490,235,790,555))
control_inputs=[]
for name,left,right,expected in [('same',r,r,True),('different',r,human,False)]:
 image=Image.new('RGB',(720,500),(235,238,241));d=ImageDraw.Draw(image)
 for i,(label,im) in enumerate([('LEFT',left),('RIGHT',right)]):
  im=im.copy();im.thumbnail((340,460),Image.Resampling.LANCZOS)
  image.paste(im,(i*360+(360-im.width)//2,34));d.text((i*360+10,10),label,fill='black')
 path=O/('control-'+name+'.png');image.save(path);control_inputs.append((name,path,expected))

PROMPT='''Independently review the actual labelled evidence for Task T01: snow-covered conifers and woodland framing. Reference crops from both supplied videos are at the top; the other panels are actual game renders. Compare the pictured content rather than assuming the builder matched it. The target is clean, sculpted, layered blue-white winter trees with narrow irregular branch notches and short warm trunks. Photorealistic bark, random surface noise and needle detail are not the reference style. Judge actual silhouette, authored materials, reference fidelity, integration and geometry integrity. Normal changes in directional light across camera angles are not by themselves broken materials. Do not invent unseen details or defects to fill a list.
Scope is trees and forest framing. The earlier cabin/workfloor layout, characters and wider game are locked later tasks: neither penalize their unfinished design as a tree defect nor approve them. The actual forest-edge view demonstrates density; the normal work clearing intentionally preserves existing routes. Diagnostic clearance OFF deliberately shows an occluding tree; ON tests whether the player is revealed. Depleted resources are supposed to disappear. Judge the actual fade, depletion and restored-tree frames, not whether every frame contains a complete tree.
Score each required dimension independently from 0 (absent/uncompleted) to 10 (fully finished within this demonstrated scope). Report concise observations and any genuine unresolved mandatory defect with exact panel/location. If no defect is visible use defect_count=0 and defect_details="none". Missing necessary evidence means coverage_complete=false. Give actual scores, not numbers the builder wants. A still image or camera-pose sheet does not certify physical frame rate, a full animation cycle or complete game release. Return only the required JSON. Reviewer role: '''+ROLE
PROMPT+='\n'+('Emphasize comparison of tree proportions, notch silhouettes and blue-white material language with BOTH real reference crops.' if ROLE=='reference-fidelity' else 'Emphasize joins, ground contact, shading continuity, all labelled camera views, and correct visibility/depletion behavior; independently assess reference fidelity too.')
SCHEMA={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defect_count':{'type':'integer','minimum':0,'maximum':3},'defect_details':{'type':'string'},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':list(KEYS),'additionalProperties':False}},'required':['observations','defect_count','defect_details','coverage_complete','confidence','scores'],'additionalProperties':False}
(O/'rubric.txt').write_text(PROMPT);(O/'schema.json').write_text(json.dumps(SCHEMA,indent=2))

def query(path,prompt,schema,name,tokens=420):
 image=Image.open(path).convert('RGB');image.thumbnail((1536,1536),Image.Resampling.LANCZOS)
 buf=io.BytesIO();image.save(buf,format='PNG');data=buf.getvalue()
 request={'model':'T01-independent-'+ROLE,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':tokens,'temperature':.15,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=800) as response:raw=json.load(response)
 (O/(name+'-raw.json')).write_text(json.dumps(raw,indent=2));provenance['independent_model_execution']=True
 choice=raw['choices'][0];assert choice['finish_reason']=='stop','Truncated '+name
 value=json.loads(choice['message']['content'])
 return value,{'file':path.name,'board_sha256':sha(path),'input_sha256':hashlib.sha256(data).hexdigest(),'input_size':list(image.size),'elapsed_seconds':time.monotonic()-start}

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(O/'inference.log').open('w');proc=subprocess.Popen([str(server),'-m',str(CACHE/m['model_file']),'--mmproj',str(CACHE/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','1024','--image-max-tokens','2048'],stdout=log,stderr=subprocess.STDOUT,env=env)
row={'task':'T01','source':SOURCE,'role':ROLE,'group':GROUP,'passed':False,'independent_execution':False,'comparison_controls_passed':False}
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('Reviewer process exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Reviewer startup failed')
 schema={'type':'object','properties':{'same_content':{'type':'boolean'},'left_subject':{'type':'string'},'right_subject':{'type':'string'},'visible_differences':{'type':'string'}},'required':['same_content','left_subject','right_subject','visible_differences'],'additionalProperties':False}
 control_prompt='Compare LEFT and RIGHT pictured content in this one board, ignoring the labels and borders. Is the pictured content identical? Identify the subject in each and state any real visible difference, or none. Do not invent differences. Return JSON only.'
 for name,path,expected in control_inputs:
  value,inputs=query(path,control_prompt,schema,'control-'+name,180)
  record={'name':name,'expected_not_in_request':expected,'response':value,'input':inputs,'passed':type(value['same_content']) is bool and value['same_content'] is expected}
  controls.append(record);(O/'comparison-controls.json').write_text(json.dumps(controls,indent=2));print(json.dumps(record),flush=True)
 assert len(controls)==2 and all(r['passed'] for r in controls),'Blind comparison controls failed; no task score is permitted'
 provenance['comparison_controls_passed']=True;row['comparison_controls_passed']=True
 if GROUP.startswith('variant-'):
  i=int(GROUP[-1]);path=board(GROUP,[(a,f'gallery/v{i:02d}-{a}.png',(340,70,930,705)) for a in ('front','rear','side','three-quarter')],2,(600,580))
  note='Four grounded views of the same tree variant; inspect each view and the reference crops above.'
 elif GROUP=='forest':
  path=board(GROUP,[('normal work clearing','gallery/gameplay-integration.png',None),('dense forest edge','gallery/forest-boundary-gameplay.png',None),('native 4K gameplay','native4k/native-scene.png',None),('ground/forest detail','gallery/forest-boundary-gameplay.png',(640,150,1200,705))],2,(720,490))
  note='The clear working area is preserved; judge the demonstrated dense perimeter, grounded tree instances and readable framing.'
 elif GROUP=='clearance':
  panels=[('control: added tree absent','clearance/clearance-baseline.png',(420,210,860,690)),('clearance OFF','clearance/clearance-disabled.png',(420,210,860,690)),('clearance ON','clearance/clearance-enabled.png',(420,210,860,690))]
  panels += [(f'fade {i}/5',f'clearance/resource-clearance-{i:02d}.png',(420,210,860,690)) for i in range(6)]
  panels += [('resource depleted','clearance/resource-depleted.png',(420,210,860,690)),('resource restored at original world position','clearance/resource-restored.png',None)]
  path=board(GROUP,panels,4,(390,370));note='The final restored-tree view uses a disclosed close-up and adjacent lead at the original resource location. It is the real restored mesh, not an image replacement. Inspect all fade states plus OFF/ON and depletion/restoration.'
 else:
  panels=[(f'orbit {i:02d}',f'gallery/orbit-{i:02d}.png',(360,70,940,705)) for i in range(24)]+[(f'gameplay camera {i:02d}',f'gallery/integration-{i:02d}.png',None) for i in range(12)]
  path=board(GROUP,panels,6,(320,220));note='All 24 ordered tree-orbit poses plus 12 gameplay camera poses are shown. Check structural and shading consistency; fine surface detail is covered separately by the full variant groups.'
 value,inputs=query(path,PROMPT+'\n'+note,SCHEMA,GROUP)
 row.update(review=value,inputs=[inputs],independent_execution=True)
 scores=value['scores'];assert set(scores)==set(KEYS) and all(type(s) in (int,float) and math.isfinite(s) and 0<=s<=10 for s in scores.values())
 assert type(value['defect_count']) is int and type(value['coverage_complete']) is bool
 row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9 and value['defect_count']==0 and value['coverage_complete'] and value['confidence'] in ('medium','high')
except Exception as exc:row['error']=str(exc)
finally:
 (O/'provenance.json').write_text(json.dumps(provenance,indent=2));(O/'task-review.json').write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
