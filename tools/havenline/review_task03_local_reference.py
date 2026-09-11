#!/usr/bin/env python3
"""Checksum-pinned local public-model reference critic for Task 3.

This is a transport-resilient alternate reviewer, not a builder self-review. It
uses the exact final T03 evidence, a blind factual image prerequisite, the same
>=9 threshold, and never replaces a returned low score. Four shards cover all
11 evidence groups exactly once.
"""
from __future__ import annotations
import base64,copy,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

SOURCE='8dc19649160597f2926ad5bacbccc26ad01ab48f'
ROLE='reference-fidelity';SHARD=int(os.environ['REVIEW_SHARD']);assert SHARD in (0,1,2,3)
ROOT=Path('task03-evidence');OUT=Path('task03-local-reference');OUT.mkdir(exist_ok=True)
CACHE=Path.home()/'.cache/havenline-t01-qwen35'
KEYS=['reference_fidelity','boundary_finish','gate_readability','lane_legibility','river_preservation','view_consistency']
GROUPS={
0:['perimeter','north-gate','side-gates'],
1:['river-gates','south-fence','central-lane'],
2:['cross-shelter-lanes','bank-lane','detail-contact'],
3:['gameplay','conditions']}
FILES={
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
'conditions':['gallery/boundary-condition-day.png','gallery/boundary-condition-dusk.png','gallery/boundary-condition-night.png','gallery/boundary-condition-dawn.png','gallery/boundary-condition-blizzard-night.png','gallery/boundary-condition-day-return.png']}
EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4194304),b''):h.update(block)
 return h.hexdigest()

prov=json.loads((ROOT/'provenance.json').read_text());assert prov['source']==SOURCE and prov['task']=='T03-boundary-v1' and prov['all61_images_verified'] is True
for name,h in prov['captures'].items():assert digest(ROOT/name)==h,'Changed evidence '+name
reference=ROOT/'reference-ground.webp';assert reference.exists()
manifest=json.loads((CACHE/'manifest.json').read_text());assert manifest['publisher']=='unsloth/Qwen3.5-9B-GGUF' and manifest['base_model']=='Qwen/Qwen3.5-9B'
for item in manifest['files']:assert digest(CACHE/item['filename'])==item['sha256'],'Bad model/runtime bytes'
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0]

# Blind factual prerequisite. Answer key is never placed in the request.
PROBE_EXPECTED={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
probe=Image.new('RGB',(720,780),(22,35,49));draw=ImageDraw.Draw(probe);probe_sources=[]
for i,(label,name,box) in enumerate([
 ('A','tree-clearance/clearance-enabled.png',(490,235,790,555)),
 ('B','gallery/perimeter-oblique.png',(0,0,640,720)),
 ('C','tree-clearance/clearance-disabled.png',(490,235,790,555)),
 ('D','tree-clearance/clearance-baseline.png',(490,235,790,555))]):
 p=ROOT/name;im=Image.open(p).convert('RGB').crop(box);im.thumbnail((350,350),Image.Resampling.LANCZOS)
 x=(i%2)*360;y=(i//2)*390;probe.paste(im,(x+(360-im.width)//2,y+28));draw.text((x+10,y+7),label,fill='white')
 probe_sources.append({'panel':label,'source':name,'sha256':digest(p),'crop_xyxy':box})
probe.save(OUT/'blind-competency.png');(OUT/'competency-source-provenance.json').write_text(json.dumps(probe_sources,indent=2))

PROMPT='''You are an independent visual reference critic. Judge ONLY Havenline Task T03: finished camp fences, intentional gate openings, and navigable packed work lanes. The reference strip at the top is extracted from the user's authoritative gameplay videos; candidate panels below are actual Godot Mobile renders from one source-bound build. Match the reference language: bright clean sculpted winter-survival forms, readable irregular timber fencing, purposeful entrances, compact clear routes, dense blue-white winter setting and warm work-zone contrast. Do not demand photorealism. Do not grade later-task station/camera/character work except where it makes the T03 evidence impossible to judge.
T03 requires six readable open gates: north main, west/east work gates, and three river-facing gates aligned to reserved future crossings. No bridge is required yet. Fence posts/panels must look grounded and connected, with no unexplained holes outside gates, floating/buried pieces, crude blockout repetition, or invisible collision implied by the visible evidence. Work lanes must read as intentional packed/worn ground integrated into the terrain, not floating planes or painted stripes. The accepted T02 meandering river and usable bank/crossing space must remain visually coherent. Day/night/weather may change lighting without changing geometry. Native-4K panels are resolution evidence, not physical FPS proof.
Score reference_fidelity, boundary_finish, gate_readability, lane_legibility, river_preservation, and view_consistency from 0 to 10. 10 means fully finished in this demonstrated T03 scope with no known defect. Give two or three specific visible observations and up to three mandatory defects naming actual panels/locations. Missing necessary pixels means coverage_complete=false. Return JSON only. Do not infer whole-game completion.'''
SCHEMA={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defects':{'type':'array','items':{'type':'string'},'maxItems':3},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
(OUT/'rubric.txt').write_text(PROMPT)

def board_for(group):
 ref=Image.open(reference).convert('RGB');ref.thumbnail((1560,430),Image.Resampling.LANCZOS)
 ims=[]
 for name in FILES[group]:
  im=Image.open(ROOT/name).convert('RGB');im.thumbnail((510,290),Image.Resampling.LANCZOS);ims.append((name,im))
 cols=3;rows=(len(ims)+cols-1)//cols;w=1600;h=500+rows*340
 b=Image.new('RGB',(w,h),(22,35,49));d=ImageDraw.Draw(b);b.paste(ref,((w-ref.width)//2,36));d.text((16,10),'USER VIDEO REFERENCE',fill='white');y0=500
 for i,(name,im) in enumerate(ims):
  c=i%cols;r=i//cols;x=c*530+(530-im.width)//2;y=y0+r*340+30
  d.text((c*530+12,y0+r*340+5),name,fill='white');b.paste(im,(x,y))
 path=OUT/(group+'-comparison.jpg');b.save(path,quality=93)
 return path

def query(image,prompt,schema,name,max_tokens=650):
 im=Image.open(image).convert('RGB');original=im.size;im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
 buf=io.BytesIO();im.save(buf,format='JPEG',quality=92);data=buf.getvalue()
 reqbody={'model':'T03-local-reference','messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':max_tokens,'temperature':.25,'top_p':.9,'seed':20260911+SHARD,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 (OUT/(name+'-request.json')).write_text(json.dumps({'model':reqbody['model'],'prompt':prompt,'schema':schema,'image_sha256':hashlib.sha256(data).hexdigest(),'original_size':original,'input_size':im.size},indent=2,default=list))
 start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(reqbody).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=900) as resp:result=json.load(resp)
 (OUT/(name+'-raw.json')).write_text(json.dumps(result,indent=2));choice=result['choices'][0];assert choice['finish_reason']=='stop','Truncated '+name
 content=choice['message']['content'];(OUT/(name+'-raw.txt')).write_text(content);return json.loads(content),round(time.monotonic()-start,3)

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','');log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--mmproj',str(CACHE/manifest['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','1024','--image-max-tokens','2048']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);rows=[];failure=None;competent=False
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('local reviewer runtime exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('local reviewer runtime not ready')
 ps={'type':'object','properties':{k:{'type':'string','enum':['human_character','snow_tree','other_or_unclear']} for k in ('A','B','C','D')},'required':['A','B','C','D'],'additionalProperties':False}
 answer,elapsed=query(OUT/'blind-competency.png','Four panels are labelled A, B, C and D. Identify the prominent subject nearest the centre of EACH panel: human_character, snow_tree, or other_or_unclear. Return only the JSON object.',ps,'competency',180)
 competent=answer==PROBE_EXPECTED;(OUT/'competency.json').write_text(json.dumps({'answers':answer,'expected':PROBE_EXPECTED,'passed':competent,'answer_key_not_in_request':True,'elapsed_seconds':elapsed},indent=2));assert competent,'Blind factual competency failed; do not grade art'
 for group in GROUPS[SHARD]:
  row={'task':'T03-boundary-v1','source':SOURCE,'role':ROLE,'group':group,'independent_execution':False,'passed':False}
  try:
   path=board_for(group);review,elapsed=query(path,PROMPT+'\nEvidence group: '+group+'. Assess every labelled candidate panel shown.',SCHEMA,group)
   scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
   row.update({'independent_execution':True,'review':review,'lowest_score':min(scores.values()),'elapsed_seconds':elapsed,'comparison_sha256':digest(path)})
   row['passed']=row['lowest_score']>=9 and review['defects']==[] and review['coverage_complete'] is True and review['confidence']!='low'
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:failure=str(exc)
finally:
 result={'task':'T03-boundary-v1','source':SOURCE,'role':ROLE,'shard':SHARD,'expected_groups':GROUPS[SHARD],'reviews':rows,'competency_passed':competent,'error':failure,'passed':competent and len(rows)==len(GROUPS[SHARD]) and all(r['passed'] for r in rows),'model':manifest['base_model'],'quantized_publisher':manifest['publisher'],'model_revision':manifest['revision'],'local_checksum_verified_runtime':True,'same_game_evidence':True,'task_approved':False,'physical4k60_verified':False}
 (OUT/'shard-review.json').write_text(json.dumps(result,indent=2));(OUT/'provenance.json').write_text(json.dumps({'source':SOURCE,'role':ROLE,'shard':SHARD,'model_manifest':manifest,'evidence_provenance_sha256':digest(ROOT/'provenance.json'),'reference_sha256':digest(reference),'script_sha256':digest(__file__)},indent=2));print(json.dumps(result),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
