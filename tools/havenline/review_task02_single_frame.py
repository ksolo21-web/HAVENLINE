#!/usr/bin/env python3
"""Review the three unresolved groups one actual full frame at a time.
The prior montage reviews contradicted visible ground pixels. Neither scores nor
original captures are altered. Single-image controls must pass before grading;
Gemma's previously failed montage control is retained and grants no approval.
"""
from pathlib import Path
import base64,hashlib,io,json,math,os,subprocess,time,urllib.request
from PIL import Image
S='586604eb8ab6404fc8084b6853fd03cfa842d3af'
ROLE=os.environ['REVIEW_ROLE'];GROUP=os.environ['REVIEW_GROUP'];INDEX=int(os.environ['REVIEW_INDEX'])
E=Path('task02-evidence');O=Path('single-review');O.mkdir(exist_ok=True)
C=Path.home()/'.cache/havenline-t01-gemma'
GROUPS={'workfloor':['native4k/workfloor-gameplay.png','native4k/native-workfloor-overhead.png','gallery/bay-connection.png','native4k/native-overview.png'],'tree-visibility':['tree-clearance/clearance-baseline.png','tree-clearance/clearance-disabled.png','tree-clearance/clearance-enabled.png','tree-clearance/resource-depleted.png','tree-clearance/resource-restored.png']}
assert ROLE in ('reference-fidelity','visual-integrity') and GROUP in GROUPS
assert GROUP!='workfloor' or ROLE=='reference-fidelity'
NAME=GROUPS[GROUP][INDEX]
K=['reference_fidelity','material_finish','geometry_contact','layout_readability','view_consistency']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
p=json.loads((E/'provenance.json').read_text());assert p['source']==S and p['renderer']=='mobile'
for n,h in p['captures'].items():assert sha(E/n)==h,n
m=json.loads((C/'manifest.json').read_text())
assert m['base_model']=='google/gemma-3-12b-it' and m['revision']=='05c2df468ad7a0bb1284b3d6fe2bdf495a885567'
for f in m['files']:assert sha(C/f['filename'])==f['sha256']
server=list((C/'runtime').rglob('llama-server'));assert len(server)==1;server=server[0]
ref=E/'reference-ground.webp';assert sha(ref)=='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
pro={'task':'T02','source':S,'role':ROLE,'group':GROUP,'index':INDEX,'candidate':NAME,'model':m['base_model'],'model_revision':m['revision'],'runtime_manifest':m,'script_sha256':sha(__file__),'independent_model_execution':False,'source_images_unchanged':True,'previous_failed_reviews_retained':True,'single_frame_grounding_required':True,'task_approved':False,'physical_4k60_verified':False}
report={'task':'T02','source':S,'role':ROLE,'group':GROUP,'index':INDEX,'candidate':NAME,'passed':False,'independent_execution':False,'control_passed':False,'task_approved':False,'physical_4k60_verified':False}

def query(files,prompt,schema,name,tokens):
 content=[];inputs=[]
 for path in files:
  im=Image.open(path).convert('RGB');original=list(im.size);im.thumbnail((1280,1280),Image.Resampling.LANCZOS)
  buf=io.BytesIO();im.save(buf,format='PNG');b=buf.getvalue()
  saved=O/(name+'-input-'+str(len(inputs))+'.png');saved.write_bytes(b)
  inputs.append({'file':str(path.relative_to(E)),'original_sha256':sha(path),'original_size':original,'input_file':saved.name,'input_sha256':sha(saved),'input_size':list(im.size)})
  content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(b).decode()}})
 content.append({'type':'text','text':prompt})
 body={'model':'independent-single-frame-'+ROLE,'messages':[{'role':'user','content':content}],'max_tokens':tokens,'temperature':.15,'top_p':.9,'seed':20260910 if ROLE=='reference-fidelity' else 20260911,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 (O/(name+'-prompt.txt')).write_text(prompt);(O/(name+'-inputs.json')).write_text(json.dumps(inputs,indent=2))
 req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
 start=time.monotonic()
 with urllib.request.urlopen(req,timeout=1200) as response:raw=json.load(response)
 (O/(name+'-raw.json')).write_text(json.dumps(raw,indent=2));pro['independent_model_execution']=True
 choice=raw['choices'][0];assert choice['finish_reason']=='stop','Truncated '+name
 result=json.loads(choice['message']['content'])
 return result,inputs,time.monotonic()-start

log=(O/'inference.log').open('w');env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
cmd=[str(server),'-m',str(C/m['model_file']),'--mmproj',str(C/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
try:
 for _ in range(160):
  if proc.poll() is not None:raise RuntimeError('Model server exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Model server not ready')
 # Both positive and negative actual-image controls, one image per request.
 # The answer keys are only used after response and are never supplied in prompts.
 control_schema={'type':'object','properties':{'visible_water':{'type':'boolean'},'visible_orange_brown_ground':{'type':'boolean'}},'required':['visible_water','visible_orange_brown_ground'],'additionalProperties':False}
 controls=[]
 for i,(name,wanted) in enumerate([('gallery/lakeshore-detail.png',{'visible_water':True,'visible_orange_brown_ground':True}),('tree-clearance/clearance-enabled.png',{'visible_water':False,'visible_orange_brown_ground':True})]):
  result,inputs,elapsed=query([E/name],'Inspect this single game screenshot. Is water visible? Is an orange or brown ground surface visible? Answer from the actual image only.',control_schema,'control-'+str(i),100)
  controls.append({'answer':result,'expected':wanted,'passed':result==wanted,'inputs':inputs,'seconds':elapsed})
 (O/'controls.json').write_text(json.dumps(controls,indent=2))
 assert all(c['passed'] for c in controls),'Failed direct actual-image grounding; do not produce an art grade'
 report['control_passed']=True
 context=''
 if GROUP=='tree-visibility':
  context=' This is the ground-contact/camera-cutaway diagnostic '+NAME+'. The baseline and enabled states intentionally do not show the obstructing tree; disabled intentionally shows it, depleted intentionally removes the resource tree, restored uses the resource-closeup camera. Grade terrain continuity and ground contact in this state, not the intentional presence/absence of a tree. The ground remains both white snow and warm cleared surface; these are distinct intended materials.'
 prompt='Image 1 is the supplied reference-game ground palette. Image 2 is ONE actual candidate frame, '+NAME+'. You are the independent '+ROLE+' critic. Review Task 2 only: the finished terrain, clean snow, warm cleared work surface, shore where visible, material joins, grounding and readable ground layout. Match the clean sculpted reference style; photorealism or gritty texture is not required. Cabins, character art, fences, machinery and shipping-camera redesign belong to other locked tasks and are not graded here. Give two concrete observations and any real visible terrain defects with image location. Do not invent defects. Score reference_fidelity, material_finish, geometry_contact, layout_readability and view_consistency from 0 to 10; 10 means finished for this scoped view with no known defect. View consistency here means coherent materials/geometry within this view and fidelity to the reference; the task gate also checks all remaining required views separately. Mark coverage_complete false if this supplied frame is unreadable. Do not infer FPS or whole-game approval.'+context
 schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defects':{'type':'array','items':{'type':'object','properties':{'view':{'type':'string'},'region':{'type':'string'},'issue':{'type':'string'}},'required':['view','region','issue'],'additionalProperties':False},'maxItems':3},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in K},'required':K,'additionalProperties':False},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']}},'required':['observations','defects','scores','coverage_complete','confidence'],'additionalProperties':False}
 result,inputs,elapsed=query([ref,E/NAME],prompt,schema,'review',550)
 report['independent_execution']=True;report['review']=result;report['inputs']=inputs;report['elapsed_seconds']=elapsed
 scores=result['scores'];assert set(scores)==set(K) and all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
 report['lowest_score']=min(scores.values())
 report['passed']=report['lowest_score']>=9 and result['defects']==[] and result['coverage_complete'] is True and result['confidence'] in ('medium','high')
except Exception as exc:report['error']=str(exc)
finally:
 (O/'provenance.json').write_text(json.dumps(pro,indent=2));(O/'review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
