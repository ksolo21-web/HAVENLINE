#!/usr/bin/env python3
"""Independent second-family T01 review with readable batches, not score selection.
Preserve prior Qwen responses. No desired numeric score/old verdict is sent to this
model. Every role reviews the complete frozen scope using the same exact renders.
"""
from __future__ import annotations
import ast,base64,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('task01-evidence');OUT=Path('critic-results');OUT.mkdir(exist_ok=True)
ROLE=os.environ['REVIEW_ROLE'];GROUP=os.environ['REVIEW_GROUP']
GROUPS=['variant-1','variant-2','variant-3','forest','clearance','camera-motion']
assert ROLE in ('reference-fidelity','visual-integrity') and GROUP in GROUPS
SOURCE='41f5446b2ecc4e29ad63ae814ad8491cc2763674'
KEYS=['silhouette','materials','reference_fidelity','integration','geometric_integrity']
CACHE=Path.home()/'.cache/havenline-t01-gemma'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
pro=json.loads((ROOT/'provenance.json').read_text());assert pro['source']==SOURCE and pro['revision']==6
for name,h in pro['captures'].items():assert sha(ROOT/name)==h,name
manifest=json.loads((CACHE/'manifest.json').read_text())
assert manifest['publisher']=='ggml-org/gemma-3-12b-it-qat-GGUF' and manifest['base_model']=='google/gemma-3-12b-it'
for item in manifest['files']:assert sha(CACHE/item['filename'])==item['sha256']
server=next((CACHE/'runtime').rglob('llama-server'))
reference=ROOT/'reference-detail.webp';assert sha(reference)=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'
raw=Path('tools/havenline/review_task01_revision4.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8c4dea512acf674bab5fa800b760588c582325a5767fb77f10fcf65f5ce59de6'
for n in ast.parse(raw.decode()).body:
 if isinstance(n,ast.FunctionDef) and n.name=='board':exec(compile(ast.Module(body=[n],type_ignores=[]),'preserved-board-helper','exec'),globals())
EXPECTED={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
probe=board('competency',[('A','clearance/clearance-enabled.png',(490,235,790,555)),('B','gallery/v01-three-quarter.png',(420,100,860,680)),('C','clearance/clearance-disabled.png',(490,235,790,555)),('D','clearance/clearance-baseline.png',(490,235,790,555))],2,(360,390),False)
provenance={'task':'T01','source':SOURCE,'role':ROLE,'group':GROUP,'model':manifest['base_model'],'model_revision':manifest['revision'],'runtime_manifest':manifest,'capture_provenance':pro,'reference_sha256':sha(reference),'reviewer_sha256':sha(__file__),'independent_model_execution':False,'competency_passed':False,'old_Qwen_reports_preserved':True,'different_model_family':True,'reason':'Resolve factual contradictions with source-bound readable evidence; not repeated unchanged scoring by the same critic','task_approved':False,'physical_4k60_verified':False}
SCHEMA={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defect_count':{'type':'integer','minimum':0,'maximum':3},'defect_details':{'type':'string'},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},'required':['observations','defect_count','defect_details','coverage_complete','confidence','scores'],'additionalProperties':False}
PROMPT='''Independently inspect Task T01: authored snow-covered conifers and their forest framing. The first image contains real reference crops from two supplied gameplay recordings. Other labelled images are actual Godot Mobile output of the candidate. Compare the visible silhouette, blue-white palette, layered notch shape, material finish, grounding, shading and geometry with the intended clean stylized reference. Judge against this reference style, not photorealism or an imagined asset. The trees must be finished, not crude stand-ins. Natural shaded faces differ from sunlit faces. Evaluate actual demonstrated defects, not the engine class name or polygon count.
This is a scoped tree task: redesign of the cabins, terrain layout, camera or characters belongs to separate locked tasks. Neither score those unrelated features as tree defects nor certify them. The forest group includes the actual dense perimeter; the moving-camera sequence circles the preserved work clearing. An intentionally clear working area is distinct from missing perimeter trees. Depletion and camera-clearance panels intentionally show states with a tree hidden; evaluate whether the transitions correctly reveal the player rather than treating intended hiding as an absent asset. Disclosure of intended state is not proof it works: inspect the pixels.
Score silhouette, materials, reference_fidelity, integration and geometric_integrity from 0 (absent/uncompleted) through 10 (fully finished within this demonstrated scope). Give two concise visible observations. Report real unresolved mandatory defects with panel/position details; defect_count=0 and defect_details="none" only when none is visible. If necessary evidence is missing, coverage_complete=false. No performance, full-game or unseen-content claims. Return only the requested JSON. Reviewer role: '''+ROLE
(OUT/'rubric.txt').write_text(PROMPT)

def query(paths,prompt,schema,name,max_tokens=500):
 content=[];inputs=[]
 for path in paths:
  im=Image.open(path).convert('RGB');im.thumbnail((1536,1536),Image.Resampling.LANCZOS)
  b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
  inputs.append({'file':str(path),'board_sha256':sha(path),'input_sha256':hashlib.sha256(data).hexdigest(),'input_size':list(im.size)})
  content += [{'type':'text','text':'IMAGE: '+path.name},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}}]
 content.append({'type':'text','text':prompt})
 request={'model':'independent-T01-'+ROLE,'messages':[{'role':'user','content':content}],'max_tokens':max_tokens,'temperature':.15,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 start=time.monotonic();http=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(http,timeout=1200) as response:result=json.load(response)
 (OUT/(name+'-raw.json')).write_text(json.dumps(result,indent=2));provenance['independent_model_execution']=True
 choice=result['choices'][0];assert choice['finish_reason']=='stop','Truncated '+name
 parsed=json.loads(choice['message']['content'])
 return parsed,inputs,time.monotonic()-start

def panels():
 note=''
 if GROUP.startswith('variant-'):
  i=int(GROUP[-1]);paths=[board(GROUP,[(a,f'gallery/v{i:02d}-{a}.png',(370,70,930,705)) for a in ('front','rear','side','three-quarter')],2,(600,610),False)]
  note='Four grounded views of this same tree variant. Inspect silhouette and materials across all four sides; no studio background substitution.'
 elif GROUP=='forest':
  paths=[board('forest-context',[('normal gameplay','gallery/gameplay-integration.png',None),('reachable forest edge','gallery/forest-boundary-gameplay.png',None)],1,(1280,745),False),board('forest-detail',[('native scene','native4k/native-scene.png',None),('edge detail','gallery/forest-boundary-gameplay.png',(640,150,1200,705))],2,(720,720),False)]
  note='Both the preserved working clearing and dense surrounding forest are shown. Ground contact and shading detail are included. No terrain/cabin redesign is part of this tree task.'
 elif GROUP=='clearance':
  ps=[('control: added tree absent','clearance/clearance-baseline.png',(420,210,860,690)),('clearance OFF','clearance/clearance-disabled.png',(420,210,860,690)),('clearance ON','clearance/clearance-enabled.png',(420,210,860,690)),('resource depleted','clearance/resource-depleted.png',(420,210,860,690))]
  paths=[board('clearance-states',ps,2,(500,525),False),board('clearance-transition',[(f'fade {i}/5',f'clearance/resource-clearance-{i:02d}.png',(420,210,860,690)) for i in range(6)],3,(400,470),False),board('resource-return',[('resource restored','clearance/resource-restored.png',None)],1,(1280,745),False)]
  note='The control omits the extra foreground tree; OFF/ON compare that same tree. Inspect all six fade states and depletion/restoration, including the dither finish. A hidden tree may still cast a contextual shadow.'
 else:
  paths=[]
  for batch in range(3):
   paths.append(board(f'orbit-batch-{batch}',[(f'orbit {i:02d}',f'gallery/orbit-{i:02d}.png',(420,90,860,690)) for i in range(batch*8,batch*8+8)],4,(290,420),False))
  for batch in range(3):
   paths.append(board(f'gameplay-batch-{batch}',[(f'gameplay {i:02d}',f'gallery/integration-{i:02d}.png',None) for i in range(batch*4,batch*4+4)],2,(640,385),False))
  note='All 24 actual camera-orbit poses followed by all 12 gameplay camera poses are split into readable batches instead of one reduced 36-frame sheet. Check consistency of actual depth, layering, shading and visibility. These are sampled camera poses, not an FPS benchmark.'
 return [reference]+paths,note

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--mmproj',str(CACHE/manifest['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
row={'task':'T01','source':SOURCE,'role':ROLE,'group':GROUP,'passed':False,'independent_execution':False,'competency_passed':False}
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('Gemma runtime exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Gemma startup timeout')
 schema={'type':'object','properties':{k:{'type':'string','enum':['human_character','snow_tree','other_or_unclear']} for k in EXPECTED},'required':list(EXPECTED),'additionalProperties':False}
 answer,inputs,elapsed=query([probe],'Identify the prominent subject nearest the centre of each labelled panel A,B,C,D: human_character, snow_tree or other_or_unclear. Return JSON only.',schema,'competency',110)
 (OUT/'competency.json').write_text(json.dumps({'answers':answer,'expected':EXPECTED,'passed':answer==EXPECTED,'answer_key_not_in_request':True,'inputs':inputs,'elapsed_seconds':elapsed},indent=2))
 assert answer==EXPECTED,'Blind factual recognition failed; no art score'
 provenance['competency_passed']=True;row['competency_passed']=True
 paths,note=panels();review,inputs,elapsed=query(paths,PROMPT+'\n'+note,SCHEMA,GROUP)
 row.update(independent_execution=True,review=review,inputs=inputs,elapsed_seconds=elapsed)
 scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
 assert type(review['defect_count']) is int and type(review['coverage_complete']) is bool
 row['lowest_score']=min(scores.values());row['passed']=row['lowest_score']>=9 and review['defect_count']==0 and review['coverage_complete'] and review['confidence'] in ('medium','high')
except Exception as exc:row['error']=str(exc)
finally:
 (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))
 (OUT/'task-review.json').write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
