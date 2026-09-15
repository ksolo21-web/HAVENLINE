#!/usr/bin/env python3
"""Read-only T01 review. New rendered revision; original failures are retained.
Uses two independent roles on one disclosed pinned Qwen3.5 model family.
No desired numeric score is supplied to inference. No game or evidence mutation.
"""
from __future__ import annotations
import base64,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('task01-evidence');OUT=Path('critic-results');OUT.mkdir(exist_ok=True)
ROLE=os.environ['REVIEW_ROLE'];SHARD=int(os.environ['REVIEW_SHARD'])
assert ROLE in ('reference-fidelity','visual-integrity') and SHARD in (0,1,2)
GROUPS={0:['variant-1','clearance'],1:['variant-2','forest'],2:['variant-3','camera-motion']}
KEYS=['silhouette','materials','reference_fidelity','integration','geometric_integrity']
CACHE=Path.home()/'.cache/havenline-t01-qwen35'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
p=json.loads((ROOT/'provenance.json').read_text());SOURCE=p['source']
for name,h in p['captures'].items():assert sha(ROOT/name)==h,name
manifest=json.loads((CACHE/'manifest.json').read_text())
assert manifest['base_model']=='Qwen/Qwen3.5-9B' and manifest['revision']=='3885219b6810b007914f3a7950a8d1b469d598a5'
for item in manifest['files']:assert sha(CACHE/item['filename'])==item['sha256']
server=next((CACHE/'runtime').rglob('llama-server'))
reference=ROOT/'reference-detail.webp';assert sha(reference)=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'
provenance={'task':'T01','source':SOURCE,'role':ROLE,'shard':SHARD,'model':manifest['base_model'],'model_revision':manifest['revision'],'runtime_manifest':manifest,'capture_provenance':p,'reference_sha256':sha(reference),'reviewer_sha256':sha(__file__),'independent_model_execution':False,'competency_passed':False,'task_approved':False,'physical_4k60_verified':False}

def board(name,panels,cols=2,tile=(600,450),ref=True):
 w,h=tile;header=340 if ref else 0
 im=Image.new('RGB',(w*cols,header+math.ceil(len(panels)/cols)*h),(230,236,240));d=ImageDraw.Draw(im)
 if ref:
  r=Image.open(reference).convert('RGB');im.paste(r,(8,8));d.text((460,35),'TASK T01 / '+name,fill='black');d.text((460,55),'REFERENCE A + B (left); ACTUAL CANDIDATE below',fill='black')
 records=[]
 for i,(label,rel,crop) in enumerate(panels):
  path=ROOT/rel;image=Image.open(path).convert('RGB')
  if crop:image=image.crop(crop)
  original=list(image.size);image.thumbnail((w-8,h-25),Image.Resampling.LANCZOS)
  x=i%cols*w;y=header+i//cols*h
  d.text((x+8,y+5),label,fill='black');im.paste(image,(x+(w-image.width)//2,y+25))
  records.append({'label':label,'file':rel,'source_sha256':sha(path),'crop':crop,'crop_size':original})
 path=OUT/(name+'.png');im.save(path)
 (OUT/(name+'-sources.json')).write_text(json.dumps(records,indent=2));return path

EXPECTED={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
probe=board('competency',[('A','clearance/clearance-enabled.png',(490,235,790,555)),('B','gallery/v01-three-quarter.png',(420,100,860,680)),('C','clearance/clearance-disabled.png',(490,235,790,555)),('D','clearance/clearance-baseline.png',(490,235,790,555))],2,(360,390),False)
SCHEMA={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':2},'defect_count':{'type':'integer','minimum':0,'maximum':3},'defect_details':{'type':'string'},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},'required':['observations','defect_count','defect_details','coverage_complete','confidence','scores'],'additionalProperties':False}
PROMPT='''Independently review Task T01: three snow-conifer variants and forest framing in a stylized game. The reference panel contains actual crops from two supplied gameplay recordings. Candidate panels are real new renders. Inspect every labelled panel. Score silhouette, materials, reference_fidelity, integration, geometric_integrity from 0 (absent) to 10 (fully finished within demonstrated scope). Give two specific observations, a count of actual unresolved defects, and concise panel/location details. If no actual defect is seen, defect_count=0 and defect_details="none". Expected behavior and absent unrelated features are not defects. Do not invent findings or infer performance. Missing necessary evidence means coverage_complete=false. The clean simplified blue-white reference style is intentional, not a request for photorealism. Assess real visible geometry/shading faults, not normal directional shadows. Other scenery, characters and terrain redesign are outside this frozen tree task and are not approved here. Reviewer role: '''+ROLE
(OUT/'rubric.txt').write_text(PROMPT)

def query(path,prompt,schema,name,tokens=330):
 im=Image.open(path).convert('RGB');im.thumbnail((1536,1536),Image.Resampling.LANCZOS)
 b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
 req={'model':'independent-T01-'+ROLE,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':tokens,'temperature':.2,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 start=time.monotonic();http=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(req).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(http,timeout=800) as response:r=json.load(response)
 (OUT/(name+'-raw.json')).write_text(json.dumps(r,indent=2));provenance['independent_model_execution']=True
 c=r['choices'][0];assert c['finish_reason']=='stop','Truncated review '+name
 value=json.loads(c['message']['content'])
 return value,{'board_sha256':sha(path),'input_sha256':hashlib.sha256(data).hexdigest(),'input_size':list(im.size),'elapsed_seconds':time.monotonic()-start}

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w');cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--mmproj',str(CACHE/manifest['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','1024','--image-max-tokens','2048']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);rows=[];error=None
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('Inference server stopped')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Inference startup timed out')
 schema={'type':'object','properties':{k:{'type':'string','enum':['human_character','snow_tree','other_or_unclear']} for k in EXPECTED},'required':list(EXPECTED),'additionalProperties':False}
 value,metadata=query(probe,'Identify the prominent subject at the centre of each panel A,B,C,D: human_character, snow_tree, or other_or_unclear. Return JSON only.',schema,'competency',100)
 (OUT/'competency.json').write_text(json.dumps({'answers':value,'expected':EXPECTED,'passed':value==EXPECTED,'answer_key_not_in_request':True,'input':metadata},indent=2))
 assert value==EXPECTED,'Blind factual recognition failed; no art score'
 provenance['competency_passed']=True
 for group in GROUPS[SHARD]:
  row={'task':'T01','source':SOURCE,'role':ROLE,'group':group,'passed':False,'independent_execution':False,'competency_passed':True}
  try:
   note=''
   if group.startswith('variant-'):
    i=int(group[-1]);panels=[(a,f'gallery/v{i:02d}-{a}.png',(370,70,930,705)) for a in ('front','rear','side','three-quarter')]
    path=board(group,panels);note='All four views show this same variant on the actual snowfield. Judge tree contact and its surfaces; natural lit/shaded sides differ.'
   elif group=='forest':
    path=board(group,[('normal gameplay','gallery/gameplay-integration.png',None),('reachable forest edge','gallery/forest-boundary-gameplay.png',None),('native 4K gameplay','native4k/native-scene.png',None),('tree-ground detail','gallery/forest-boundary-gameplay.png',(640,150,1200,705))],2,(720,450));note='Trees are outside the preserved playable lanes. Clear work space and approach routes are intentional. Evaluate dense framing, tree contact and rendering coherence.'
   elif group=='camera-motion':
    panels=[(f'orbit {i:02d}',f'gallery/orbit-{i:02d}.png',(420,90,860,690)) for i in range(24)]+[(f'gameplay {i:02d}',f'gallery/integration-{i:02d}.png',None) for i in range(12)]
    path=board(group,panels,6,(240,190));note='Ordered 24-pose full orbit followed by 12 gameplay camera poses. Look for view-dependent geometry faults, popping or unexplained obstruction, not normal light direction. Detailed surfaces are separately captured in the variant groups.'
   else:
    panels=[('A: control without added foreground tree','clearance/clearance-baseline.png',(420,210,860,690)),('B: foreground tree, clearance OFF','clearance/clearance-disabled.png',(420,210,860,690)),('C: same tree, clearance ON','clearance/clearance-enabled.png',(420,210,860,690)),('D: depleted resource','clearance/resource-depleted.png',(420,210,860,690))]
    panels += [(f'fade {i}/5',f'clearance/resource-clearance-{i:02d}.png',(420,210,860,690)) for i in range(6)]
    panels += [('resource restored','clearance/resource-restored.png',None)]
    path=board(group,panels,4,(360,360));note='Visibility regression: reference is the full-tree appearance, not the expected depleted state. Control omits an extra obstructing tree; OFF/ON compare the same added tree. Six ordered fade steps and actual depletion/restoration are shown. Assess whether the player is revealed and the transition has a genuine visible defect. Intentional absence is not itself a missing-asset defect.'
   value,metadata=query(path,PROMPT+'\n'+note,SCHEMA,group)
   row.update(independent_execution=True,review=value,inputs=[metadata]);scores=value['scores']
   assert set(scores)==set(KEYS) and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
   assert type(value['defect_count']) is int and type(value['coverage_complete']) is bool
   row['lowest_score']=min(scores.values())
   row['passed']=row['lowest_score']>=9 and value['defect_count']==0 and value['coverage_complete'] and value['confidence'] in ('medium','high')
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:error=str(exc)
finally:
 (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))
 (OUT/'shard-review.json').write_text(json.dumps({'task':'T01','source':SOURCE,'role':ROLE,'shard':SHARD,'reviews':rows,'competency_passed':provenance['competency_passed'],'error':error,'passed':len(rows)==2 and all(r['passed'] for r in rows),'task_approved':False},indent=2))
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
