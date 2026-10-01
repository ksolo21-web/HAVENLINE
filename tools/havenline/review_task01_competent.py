#!/usr/bin/env python3
"""Alternate public-model critic with a blind factual prerequisite; never fabricate a pass.

Read-only game/evidence, unchanged >=9 task threshold. A different model is used
because previous raw reports confidently misidentified visible/hidden objects.
A single labelled comparison board avoids ambiguous multi-image association.
The probe has no art score and its answer key is never sent to the model.
"""
from __future__ import annotations
import ast,base64,copy,hashlib,io,json,math,os
from pathlib import Path
import subprocess,time,urllib.request
from PIL import Image,ImageDraw

SOURCE='8632c5b2c2a70ec1eb88db08bef8ca18b707e1a6'
ROLE=os.environ['REVIEW_ROLE'];SHARD=int(os.environ['REVIEW_SHARD'])
assert ROLE in ('reference-fidelity','visual-integrity') and SHARD in (0,1,2)
ROOT=Path('task01-evidence');OUT=Path('critic-results');OUT.mkdir(exist_ok=True)
CACHE=Path.home()/'.cache/havenline-t01-qwen35'
KEYS=['silhouette','materials','reference_fidelity','integration','geometric_integrity']
GROUPS={0:['variant-1','clearance'],1:['variant-2','forest'],2:['variant-3','camera-motion']}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4194304),b''):h.update(block)
    return h.hexdigest()

source=json.loads((ROOT/'provenance.json').read_text());assert source['source']==SOURCE and source['task']=='T01'
for name,h in source['captures'].items():assert digest(ROOT/name)==h,'Changed actual capture '+name
ref=ROOT/'reference-detail.webp';assert digest(ref)=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'
manifest=json.loads((CACHE/'manifest.json').read_text())
assert manifest['publisher']=='unsloth/Qwen3.5-9B-GGUF' and manifest['base_model']=='Qwen/Qwen3.5-9B'
for item in manifest['files']:assert digest(CACHE/item['filename'])==item['sha256'],'Bad model/runtime bytes'
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0]

# Reuse only the immutable original image-layout helpers, never the old model,
# prompt, response or execution. Crop provenance and all original PNGs remain.
raw=subprocess.check_output(['git','show',SOURCE+':tools/havenline/review_task01_cached.py'])
assert hashlib.sha256(raw).hexdigest()=='1a3945a788aa4826995e6728b02a7257e99df3eace8abf3e563a564b9f144677'
text=raw.decode();tree=ast.parse(text)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ('layout','prepare'):
        exec(compile(ast.Module(body=[node],type_ignores=[]),'immutable-capture-layout','exec'),globals())

PROBE_EXPECTED={'A':'human_character','B':'snow_tree','C':'snow_tree','D':'human_character'}
FACTS={'baseline_tree_blocks_central_player':False,'disabled_tree_blocks_central_player':True,'enabled_tree_blocks_central_player':False,'depleted_resource_tree_visible':False}
# Do not include the probe answer key or expected clearance facts in a request.
probe=Image.new('RGB',(720,780),(22,35,49));draw=ImageDraw.Draw(probe);probe_sources=[]
for i,(label,name,box) in enumerate([
 ('A','clearance/clearance-enabled.png',(490,235,790,555)),
 ('B','gallery/v01-three-quarter.png',(360,110,920,670)),
 ('C','clearance/clearance-disabled.png',(490,235,790,555)),
 ('D','clearance/clearance-baseline.png',(490,235,790,555))]):
    p=ROOT/name;im=Image.open(p).convert('RGB').crop(box);im.thumbnail((360,365))
    x=(i%2)*360;y=(i//2)*390;probe.paste(im,(x+(360-im.width)//2,y+25));draw.text((x+10,y+7),label,fill='white')
    probe_sources.append({'panel':label,'source':name,'sha256':digest(p),'crop_xyxy':box})
probe.save(OUT/'blind-competency.png')
(OUT/'competency-source-provenance.json').write_text(json.dumps(probe_sources,indent=2))

PROMPT='''You are an independent critic inspecting actual game images. Judge ONLY Task T01: the three snow conifers, forest framing, surface/geometry integrity, grounding and player visibility. The top-left reference panel contains actual tree crops from the user's two supplied gameplay videos. The larger labelled panels are actual Godot Mobile captures. Match the intended clean stylized blue-white three-layer snow crowns, narrow V-notched edges, short warm reddish trunks and dense forest. Realism, bark noise and extra polygons are not the target. Crude unfinished substitutes, wrong proportions/colors, broken joins or unexplained obstruction are defects. Do not invent problems to fill a list, and do not ignore real defects.
The surrounding terrain, cabins, characters and HUD belong to locked later tasks; do not score their unfinished features as tree defects or approve them. Isolated variant views intentionally have no ground plane: examine silhouette/surface integrity there; physical grounding is demonstrated in the separate forest images. For integration score evaluate the demonstrated role of the trees, not whether an isolated diagnostic contains unrelated scenery. In visibility/depletion tests intentional hiding is the expected behavior to assess, not automatically a missing asset. Evaluate the actual transition finish; dither quality is a legitimate concern if visible. Ordered camera-pose panels are real inspection samples, not a frame-rate benchmark. Missing necessary pixels must be disclosed with coverage_complete=false.
Independently score silhouette, materials, reference_fidelity, integration and geometric_integrity on 0 to 10. 0 means absent/uncompleted, 10 means fully finished within this demonstrated scope with no known defect. Give two specific visible observations and up to three mandatory defects naming actual panels/locations. Assess every labelled view in this evidence group. Return the requested JSON only; do not infer unseen full-game completion or device performance. There is no approval merely because the builder wants one.'''
PROMPT+='\nRole: '+ROLE+'. '+('Emphasize actual reference shape, palette, proportions, finish and forest density.' if ROLE=='reference-fidelity' else 'Emphasize actual joins, shading, contact, multi-angle consistency and visibility/depletion behavior, independently checking reference fidelity too.')
schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},'defects':{'type':'array','items':{'type':'string'},'maxItems':3},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
(OUT/'rubric.txt').write_text(PROMPT)
provenance={'task':'T01','source':SOURCE,'role':ROLE,'shard':SHARD,'model':manifest['base_model'],'quantized_publisher':manifest['publisher'],'model_revision':manifest['revision'],'runtime_manifest':manifest,'reference_sha256':digest(ref),'capture_provenance':source,'script_sha256':digest(__file__),'independent_model_execution':False,'competency_passed':False,'same_family_roles_disclosed':True,'prior_failed_reviews_preserved':True,'artwork_and_score_threshold_unchanged':True,'task_approved':False,'physical_4k60_verified':False}

def query(image:Path,prompt:str,response_schema:dict,name:str,max_tokens=550):
    im=Image.open(image).convert('RGB');original=im.size;im.thumbnail((1536,1536),Image.Resampling.LANCZOS)
    buffer=io.BytesIO();im.save(buffer,format='PNG');data=buffer.getvalue()
    request={'model':'T01-independent-'+ROLE,'messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':prompt}]}],'max_tokens':max_tokens,'temperature':.3,'top_p':.9,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':response_schema},'cache_prompt':False}
    start=time.monotonic();req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=900) as response:result=json.load(response)
    (OUT/(name+'-raw.json')).write_text(json.dumps(result,indent=2))
    provenance['independent_model_execution']=True
    choice=result['choices'][0];assert choice['finish_reason']=='stop','Truncated '+name
    content=choice['message']['content'];(OUT/(name+'-raw.txt')).write_text(content)
    parsed=json.loads(content)
    return parsed,{'filename':image.name,'source_sha256':digest(image),'original_size':original,'input_size':list(im.size),'input_sha256':hashlib.sha256(data).hexdigest(),'elapsed_seconds':round(time.monotonic()-start,3)}

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--mmproj',str(CACHE/manifest['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','1024','--image-max-tokens','2048']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
rows=[];failure=None
try:
    for _ in range(150):
        if proc.poll() is not None:raise RuntimeError('Alternate inference runtime exited')
        try:
            if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError('Alternate inference runtime not ready')
    probe_schema={'type':'object','properties':{k:{'type':'string','enum':['human_character','snow_tree','other_or_unclear']} for k in ('A','B','C','D')},'required':['A','B','C','D'],'additionalProperties':False}
    answer,probe_input=query(OUT/'blind-competency.png','Four panels are labelled A, B, C and D. Identify the prominent subject nearest the centre of EACH panel from the actual pixels: human_character, snow_tree, or other_or_unclear. Return only the JSON object. No grading or desired answers are supplied.',probe_schema,'competency',180)
    competent=answer==PROBE_EXPECTED
    (OUT/'competency.json').write_text(json.dumps({'answers':answer,'expected':PROBE_EXPECTED,'input':probe_input,'passed':competent,'answer_key_was_not_in_request':True,'not_an_art_score':True},indent=2))
    assert competent,'Alternate reviewer failed blind factual image recognition; art scores must not be produced'
    provenance['competency_passed']=True
    for group in GROUPS[SHARD]:
        row={'task':'T01','source':SOURCE,'role':ROLE,'group':group,'passed':False,'independent_execution':False,'competency_passed':True}
        try:
            panels,note=prepare(group)
            source_images=[Image.open(p).convert('RGB') for p in panels]
            # One image, explicit reference/candidate separation, no source retouch.
            width=max(1280,max(im.width for im in source_images));height=350+sum(im.height+28 for im in source_images)
            board=Image.new('RGB',(width,height),(22,35,49));d=ImageDraw.Draw(board)
            rim=Image.open(ref).convert('RGB');board.paste(rim,(8,24));d.text((8,5),'REFERENCE CROPS A / B',fill='white')
            d.text((470,40),'CANDIDATE: '+group,fill='white');y=350
            for p,im in zip(panels,source_images):
                d.text((8,y+4),p.name,fill='white');board.paste(im,((width-im.width)//2,y+28));y+=im.height+28
            path=OUT/(group+'-comparison.png');board.save(path)
            response_schema=copy.deepcopy(schema)
            if group=='clearance':
                response_schema['properties']['evidence_facts']={'type':'object','properties':{k:{'type':'boolean'} for k in FACTS},'required':list(FACTS),'additionalProperties':False};response_schema['required'].append('evidence_facts')
                note+=' Also report factual booleans by inspecting the labelled baseline, disabled, enabled and depleted panels: does a tree block the central player in each of the first three, and is the depleted resource tree visible? Do not infer these from labels alone.'
            print('Reviewing',ROLE,group,flush=True)
            review,input_record=query(path,PROMPT+'\nGroup: '+group+'. '+note,response_schema,group)
            row['independent_execution']=True;row['inputs']=[input_record]
            s=review['scores'];assert set(s)==set(KEYS) and all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=10 for v in s.values())
            assert isinstance(review['defects'],list) and type(review['coverage_complete']) is bool and review['confidence'] in ('low','medium','high')
            row['review']=review;row['lowest_score']=min(s.values())
            if group=='clearance':
                row['factual_image_recognition_passed']=review.get('evidence_facts')==FACTS
                assert row['factual_image_recognition_passed'],'Incorrect recognition of actual clearance states'
            row['passed']=row['lowest_score']>=9 and not review['defects'] and review['coverage_complete'] and review['confidence']!='low'
        except Exception as exc:row['error']=str(exc)
        rows.append(row);(OUT/(group+'-review.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2),flush=True)
except Exception as exc:failure=str(exc)
finally:
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))
    result={'task':'T01','source':SOURCE,'role':ROLE,'shard':SHARD,'expected_groups':GROUPS[SHARD],'reviews':rows,'competency_passed':provenance['competency_passed'],'error':failure,'passed':len(rows)==2 and all(r['passed'] for r in rows),'task_approved':False,'full_game_approved':False,'physical_4k60_verified':False}
    (OUT/'shard-review.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
    proc.terminate()
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:proc.kill()
    log.close()
