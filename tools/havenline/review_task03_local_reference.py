#!/usr/bin/env python3
"""Checksum-pinned local public-model critic for Task 3.

This transport-resilient reviewer uses exact source-bound T03 evidence, a blind
factual image prerequisite, the unchanged >=9 threshold, and group-scoped
boards plus whole-camp context so a close-up is not penalized for objects that
are intentionally outside its camera. Four shards cover all 11 groups exactly
once per role. Returned low scores are never retried to improve a grade.
"""
from __future__ import annotations
import base64,hashlib,io,json,math,os,subprocess,time,urllib.request
from pathlib import Path
from PIL import Image,ImageDraw

SOURCE=os.environ['EXPECTED_SOURCE'];ROLE=os.environ['REVIEW_ROLE'];SHARD=int(os.environ['REVIEW_SHARD'])
assert len(SOURCE)==40 and ROLE in ('reference-fidelity','visual-integrity') and SHARD in (0,1,2,3)
ROOT=Path('task03-evidence');OUT=Path('task03-local-review');OUT.mkdir(exist_ok=True)
CACHE=Path.home()/'.cache/havenline-t01-qwen35'
KEYS=['reference_fidelity','boundary_finish','gate_readability','lane_legibility','river_preservation','view_consistency']
GROUPS={0:['perimeter','north-gate','side-gates'],1:['river-gates','south-fence','central-lane'],2:['cross-shelter-lanes','bank-lane','detail-contact'],3:['gameplay','conditions']}
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
NOTES={
'perimeter':'Judge the complete boundary, all six gate openings, overall packed-lane network and river/crossing relationship. This is the group where full-network gate presence is mandatory.',
'north-gate':'Judge ONLY the north-main gate, its two hinge/lantern thresholds, open leaves, fence contact and adjacent lane. Do not demand side or river gates inside these close-ups; use WHOLE-CAMP CONTEXT only for their overall presence.',
'side-gates':'Judge the west-work and east-work gates specifically: each must read as an intentional opening with grounded threshold posts/open leaves and a route through it. Do not demand the north or river gates inside the local close-ups.',
'river-gates':'Judge the three river-facing gate corridors specifically. They intentionally have NO bridges yet. Require readable opened leaves/posts, dry approach, preserved bank, and clear future crossing space.',
'south-fence':'Judge the continuous river-side fence sections and their joins around the three intentional river-gate gaps. A missing bridge or decorative latch is not required in T03.',
'central-lane':'Judge the central packed route from north entry through camp toward the river. Do not interpret fence sections outside the focus as floating merely because an orthographic crop excludes their ground context.',
'cross-shelter-lanes':'Judge packed cross-camp/shelter route continuity and its actual intersections. Gate openings need only be present in the whole-camp context unless a local frame is specifically centered on one.',
'bank-lane':'Judge the dry packed north-bank lane and its three reserved crossing connectors. North/side gates are intentionally outside these close-ups; their absence from a bank-lane frame is NOT a defect.',
'detail-contact':'Judge close fence-panel joins, ground/root contact, gate threshold posts and the two visibly opened leaves. Unrelated geometry clipped at an outer frame edge is not a defect unless it is actually disconnected in the whole-camp context.',
'gameplay':'Judge normal gameplay readability of the north/work/river approaches, not diagnostic completeness of every gate in every frame.',
'conditions':'Judge the same boundary/lane layout for geometry/material stability through day, dusk, night, dawn and blizzard. Darkness itself is not a defect.'}
EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11
CONTEXT=['gallery/perimeter-topdown.png','gallery/reserved-crossings-overhead.png']

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4194304),b''):h.update(block)
 return h.hexdigest()

prov=json.loads((ROOT/'provenance.json').read_text());assert prov['source']==SOURCE and prov['task']=='T03-boundary-v2' and prov['all61_images_verified'] is True
for name,h in prov['captures'].items():assert digest(ROOT/name)==h,'Changed evidence '+name
reference=ROOT/'reference-ground.webp';assert reference.exists()
manifest=json.loads((CACHE/'manifest.json').read_text());assert manifest['publisher']=='unsloth/Qwen3.5-9B-GGUF' and manifest['base_model']=='Qwen/Qwen3.5-9B'
for item in manifest['files']:assert digest(CACHE/item['filename'])==item['sha256'],'Bad model/runtime bytes'
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0]

PROBE_EXPECTED={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
probe=Image.new('RGB',(720,780),(22,35,49));draw=ImageDraw.Draw(probe);probe_sources=[]
for i,(label,name,box) in enumerate([('A','tree-clearance/clearance-enabled.png',(490,235,790,555)),('B','gallery/perimeter-oblique.png',(0,0,640,720)),('C','tree-clearance/clearance-disabled.png',(490,235,790,555)),('D','tree-clearance/clearance-baseline.png',(490,235,790,555))]):
 p=ROOT/name;im=Image.open(p).convert('RGB').crop(box);im.thumbnail((350,350),Image.Resampling.LANCZOS)
 x=(i%2)*360;y=(i//2)*390;probe.paste(im,(x+(360-im.width)//2,y+28));draw.text((x+10,y+7),label,fill='white');probe_sources.append({'panel':label,'source':name,'sha256':digest(p),'crop_xyxy':box})
probe.save(OUT/'blind-competency.png');(OUT/'competency-source-provenance.json').write_text(json.dumps(probe_sources,indent=2))

PROMPT='''You are an independent visual critic inspecting actual source-bound Havenline renders. Judge ONLY Task T03: finished camp fences, six intentional gate openings, and navigable packed work lanes. The USER VIDEO REFERENCE strip comes from the authoritative gameplay videos. Match its bright clean sculpted winter-survival language: readable irregular timber boundary, purposeful entrances/routes, dense blue-white winter setting and warm work-zone contrast. Do not demand photorealism or later-task machinery/customers/bridges.
The candidate board contains GROUP-SCOPED DETAIL panels plus two clearly labelled WHOLE-CAMP CONTEXT panels. Strictly separate those purposes. A local close-up is NOT required to show unrelated gates that are outside its camera. Use whole-camp context to confirm the full six-gate network and river relationship; cite a local defect only when visible in the group-scoped panels or corroborated by context. Do not call an object floating/disconnected solely because the orthographic crop cuts off surrounding ground or another fence segment.
T03 requires six gates overall: north main, west/east work, and three river-facing future-crossing corridors. No bridge is required. Open timber leaves/threshold lantern posts should make the intended gaps readable. Fence roots/panels should look grounded and joined, with no genuine unexplained gaps outside gates. Packed lanes must read as worn/compressed material in the SAME terrain surface, not floating path planes or painted stripes. The accepted T02 river and crossing reserves must remain coherent. Day/night/weather may alter illumination without altering geometry.
Score reference_fidelity, boundary_finish, gate_readability, lane_legibility, river_preservation, and view_consistency from 0 to 10. Every score below 9 MUST cite an actionable defect actually visible in the supplied pixels. 10 means fully finished within the demonstrated T03 scope with no known defect. If you find NO actionable defect, the defects array MUST be [] exactly; never put phrases such as "none", "none observed", praise, or scope commentary in defects. Return JSON only. Do not infer whole-game completion or physical-device performance.'''
PROMPT+='\nRole: '+ROLE+'. '+('Prioritize fit to the supplied video visual language, gate hierarchy, lane readability and coherent camp composition.' if ROLE=='reference-fidelity' else 'Prioritize actual joins/contact, intentional gaps versus defects, route continuity, river-bank integrity and cross-view consistency.')
SCHEMA={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defects':{'type':'array','items':{'type':'string'},'maxItems':3},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
(OUT/'rubric.txt').write_text(PROMPT)

def board_for(group):
 ref=Image.open(reference).convert('RGB');ref.thumbnail((1540,370),Image.Resampling.LANCZOS)
 context=[]
 for name in CONTEXT:
  im=Image.open(ROOT/name).convert('RGB');im.thumbnail((760,425),Image.Resampling.LANCZOS);context.append((name,im))
 ims=[]
 for name in FILES[group]:
  im=Image.open(ROOT/name).convert('RGB');im.thumbnail((510,290),Image.Resampling.LANCZOS);ims.append((name,im))
 cols=3;rows=(len(ims)+cols-1)//cols;w=1600;context_h=470;group_y=420+context_h;h=group_y+70+rows*340
 b=Image.new('RGB',(w,h),(22,35,49));d=ImageDraw.Draw(b);b.paste(ref,((w-ref.width)//2,35));d.text((16,10),'USER VIDEO REFERENCE',fill='white')
 d.text((16,410),'WHOLE-CAMP CONTEXT — for overall network/river presence, not local defect invention',fill='white')
 for i,(name,im) in enumerate(context):
  x=i*800+(800-im.width)//2;y=445;b.paste(im,(x,y));d.text((i*800+12,430),name,fill='white')
 d.text((16,group_y+5),'GROUP-SCOPED DETAIL: '+group,fill='white');y0=group_y+45
 for i,(name,im) in enumerate(ims):
  c=i%cols;r=i//cols;x=c*530+(530-im.width)//2;y=y0+r*340+30
  d.text((c*530+12,y0+r*340+5),name,fill='white');b.paste(im,(x,y))
 path=OUT/(group+'-comparison.jpg');b.save(path,quality=93);return path

def query(image,prompt,schema,name,max_tokens=650):
 im=Image.open(image).convert('RGB');original=im.size;im.thumbnail((1664,1664),Image.Resampling.LANCZOS)
 buf=io.BytesIO();im.save(buf,format='JPEG',quality=92);data=buf.getvalue()
 reqbody={'model':'T03-local-'+ROLE,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':max_tokens,'temperature':.25,'top_p':.9,'seed':20260911+SHARD+(0 if ROLE=='reference-fidelity' else 100),'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 (OUT/(name+'-request.json')).write_text(json.dumps({'model':reqbody['model'],'prompt':prompt,'schema':schema,'image_sha256':hashlib.sha256(data).hexdigest(),'original_size':original,'input_size':im.size},indent=2,default=list))
 start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(reqbody).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=1200) as resp:result=json.load(resp)
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
  row={'task':'T03-boundary-v2','source':SOURCE,'role':ROLE,'group':group,'independent_execution':False,'passed':False}
  try:
   path=board_for(group);review,elapsed=query(path,PROMPT+'\nCurrent evidence group: '+group+'. '+NOTES[group]+' Assess every labelled GROUP-SCOPED DETAIL panel.',SCHEMA,group)
   scores=review['scores'];assert set(scores)==set(KEYS) and all(type(v) in (int,float) and math.isfinite(v) and 0<=v<=10 for v in scores.values())
   assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high')
   row.update({'independent_execution':True,'review':review,'lowest_score':min(scores.values()),'elapsed_seconds':elapsed,'comparison_sha256':digest(path)})
   row['passed']=row['lowest_score']>=9 and review['defects']==[] and review['coverage_complete'] is True and review['confidence']!='low'
  except Exception as exc:row['error']=str(exc)
  rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
except Exception as exc:failure=str(exc)
finally:
 result={'task':'T03-boundary-v2','source':SOURCE,'role':ROLE,'shard':SHARD,'expected_groups':GROUPS[SHARD],'reviews':rows,'competency_passed':competent,'error':failure,'passed':competent and len(rows)==len(GROUPS[SHARD]) and all(r['passed'] for r in rows),'model':manifest['base_model'],'quantized_publisher':manifest['publisher'],'model_revision':manifest['revision'],'local_checksum_verified_runtime':True,'same_model_family_roles_disclosed':True,'same_game_evidence':True,'task_approved':False,'physical4k60_verified':False}
 (OUT/'shard-review.json').write_text(json.dumps(result,indent=2));(OUT/'provenance.json').write_text(json.dumps({'source':SOURCE,'role':ROLE,'shard':SHARD,'model_manifest':manifest,'evidence_provenance_sha256':digest(ROOT/'provenance.json'),'reference_sha256':digest(reference),'script_sha256':digest(__file__),'group_scoped_rubric':True,'whole_camp_context_in_every_board':True},indent=2));print(json.dumps(result),flush=True)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
