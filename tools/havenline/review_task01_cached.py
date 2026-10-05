#!/usr/bin/env python3
"""Independent T01 pixel reviews using pinned cached CPU weights, not builder scores.

Each role/shard is a separate execution. Shared model family is disclosed.
Failures/truncation remain failures and cannot advance a task. No paid endpoints.
"""
from __future__ import annotations
import base64, hashlib, io, json, math, os
from pathlib import Path
import subprocess, time, urllib.request
from PIL import Image, ImageDraw

ROLE = os.environ['REVIEW_ROLE']
SHARD = int(os.environ['REVIEW_SHARD'])
assert ROLE in ('reference-fidelity', 'visual-integrity') and SHARD in (0,1,2)
ROOT = Path('task01-evidence')
OUT = Path('critic-results'); OUT.mkdir(exist_ok=True)
CACHE = Path.home()/'.cache/havenline-t01-vision'
MODEL = 'Qwen3VL-8B-Instruct-Q4_K_M.gguf'
PROJECTOR = 'mmproj-Qwen3VL-8B-Instruct-F16.gguf'
EXPECTED = {MODEL:'67d1659bfe71b89d50b45a4ad1a9e5b997e5bb16ce5da66a6a6167abd569e9e2',
            PROJECTOR:'ca524100ebf825c9a870db1c580d03879e0da0ab2541697e2458e64891cf9d38',
            'runtime.tar.gz':'5e34434ddc6d03cd1584f403201aff0d4bd1a5793a72ff7e286532dfd1e4b941'}
KEYS = ['silhouette','materials','reference_fidelity','integration','geometric_integrity']
GROUPS = {0:['variant-1','clearance'],1:['variant-2','forest'],2:['variant-3','camera-motion']}

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def layout(names:list[str], output:Path, columns:int, tile:tuple[int,int], crop=None)->dict:
    """Labelled, geometrically unaltered inspection samples; original pixels retained."""
    w,h=tile; c=Image.new('RGB',(columns*w,math.ceil(len(names)/columns)*h),(22,35,49))
    draw=ImageDraw.Draw(c); record=[]
    for index,name in enumerate(names):
        p=ROOT/name; im=Image.open(p).convert('RGB');size=im.size
        if crop is not None:im=im.crop(crop)
        im.thumbnail((w,h-22),Image.Resampling.LANCZOS)
        x=(index%columns)*w;y=(index//columns)*h
        c.paste(im,(x+(w-im.width)//2,y+22));draw.text((x+5,y+4),Path(name).stem,fill='white')
        record.append({'path':name,'source_sha256':digest(p),'original_size':size,'crop_xyxy':crop,'tile_size':list(im.size)})
    c.save(output)
    return {'path':output.name,'sha256':digest(output),'source_frames':record,'operation':'label/crop/resample only; no retouch or synthesis'}

source=json.loads((ROOT/'provenance.json').read_text())
assert source['task']=='T01' and len(source['source'])==40
for name,h in source['captures'].items():
    assert digest(ROOT/name)==h,'Changed capture '+name
for name,h in EXPECTED.items():
    assert digest(CACHE/name)==h,'Missing/mismatched pinned runtime '+name
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1
server=servers[0];server.chmod(0o755)
ref=ROOT/'reference-detail.webp'
assert digest(ref)=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'

provenance={'task':'T01','source':source['source'],'role':ROLE,'shard':SHARD,
 'runner':'separate GitHub Actions CPU inference process','model':'Qwen/Qwen3-VL-8B-Instruct-GGUF',
 'model_revision':'f982a07559d4a2f6c8744d840bf6fccab30eea96','runtime_release':'b10809',
 'verified_runtime_hashes':EXPECTED,'reference_sha256':digest(ref),'capture_provenance':source,
 'independent_model_execution':False,'task_approved':False,'physical_4k60_verified':False}
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))

PROMPT='''Act as an independent art/technical critic, not the builder. Task T01 is ONLY the three reference snow conifers and woodland framing, their ground contact, visual integrity and player-visibility cutaway. Image 1 contains actual tree crops from the user's two gameplay recordings: A at 00:05 left and B at 00:02 right. It is the visual target. Other images are actual Godot Mobile runtime captures of the candidate; filenames label each view. Judge pixels rather than filenames or the builder's desired score. Both references intentionally have clean blue-white layered conical snow crowns with small V-cut edges, short reddish-brown trunks and dense repeated forest. Do not reward photorealistic bark/noise or penalize intentional clean stylization. Conversely primitive-looking, uncrafted substitutes, incorrect profiles/palette, ugly seams, broken contact or poor visibility are real defects. Assess the candidate against what is actually visible in the references; do not infer unavailable exact geometry.
The task is frozen to trees. Existing cabins/terrain/characters/UI belong to locked later tasks: their completion is NOT requested or approved by this scoped review. Do not use their defects to lower the tree score; do assess how the trees themselves integrate and frame the current world. Isolated asset views intentionally hide unrelated scenery. Diagnostic test fixtures are disclosed, not production placements. Ordered camera frames are actual rendered pose samples, NOT 60 FPS evidence. Review every labelled view in this evidence group; provide specific visible observations and at most three concrete mandatory defects with filename/location. An empty defects list is appropriate only when no mandatory issue is visible. Scores are your opinion: 0 means absent, 10 means fully finished for the demonstrated scope. A minimum of 9 per required dimension and no mandatory defect is needed for internal task progression, but never inflate scores to force a pass. Missing evidence means coverage_complete=false. Low confidence blocks approval. Do not claim completion of other groups, unseen fine detail, complete gameplay or physical-device performance. Give scores for silhouette, materials, reference_fidelity, integration and geometric_integrity for the trees shown in this group. Output only the requested JSON object. Keep total response concise.'''
PROMPT += '\nReviewer role: '+ROLE+'. '+('Emphasize shape proportions, material palette, intended stylization and density versus the actual reference pixels.' if ROLE=='reference-fidelity' else 'Emphasize angle consistency, smooth shading, surface joins, contact, visibility transitions and integration; also independently score fidelity.')
(OUT/'rubric.txt').write_text(PROMPT)
schema={'type':'object','properties':{
 'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':3},
 'defects':{'type':'array','items':{'type':'string'},'maxItems':3},
 'coverage_complete':{'type':'boolean'},
 'confidence':{'type':'string','enum':['low','medium','high']},
 'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in KEYS},'required':KEYS,'additionalProperties':False}},
 'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
(OUT/'response-schema.json').write_text(json.dumps(schema,indent=2))

def prepare(group):
    plans=[];paths=[]
    if group.startswith('variant-'):
        i=int(group[-1]);names=[f'gallery/v{i:02d}-{a}.png' for a in ('front','rear','side','three-quarter')]
        p=OUT/(group+'.png');plans.append(layout(names,p,2,(410,470),crop=(360,110,920,670)));paths.append(p)
        note=f'Four exact views of variant {i}. The crop retains the complete crown and trunk; original full frames are preserved. Check every angle.'
    elif group=='forest':
        names=['gallery/gameplay-integration.png','gallery/forest-boundary-gameplay.png']
        p=OUT/'forest-integration.png';plans.append(layout(names,p,1,(1120,652)));paths.append(p)
        names=['gallery/forest-boundary-gameplay.png'];p=OUT/'forest-contact.png';plans.append(layout(names,p,1,(980,650),crop=(500,100,1240,630)));paths.append(p)
        note='Normal gameplay and a reachable boundary diagnostic (player at 12.4,0), plus its contact crop. Judge tree framing and contact; the underlying terrain/buildings remain later tasks. The forest is intentionally outside unchanged playable routes.'
    elif group=='clearance':
        names=[f'clearance/clearance-{x}.png' for x in ('baseline','disabled','enabled')]
        p=OUT/'player-clearance.png';plans.append(layout(names,p,3,(300,330),crop=(490,235,790,555)));paths.append(p)
        names=[f'clearance/resource-clearance-{i:02d}.png' for i in range(6)]+['clearance/resource-depleted.png','clearance/resource-restored.png']
        p=OUT/'resource-clearance.png';plans.append(layout(names,p,4,(250,290),crop=(490,235,790,555)));paths.append(p)
        note='Actual diagnostic: one instanced tree in the player sightline, baseline hidden / clearance disabled / actual clearance enabled. Remaining panels show real resource-tree cutaway 0,.2,.4,.6,.8,1, depletion and restoration. Dither fading is intentional to retain sightline. Do not confuse restoration to original position with a missing resource.'
    else:
        names=[f'gallery/orbit-{i:02d}.png' for i in range(24)]
        p=OUT/'tree-orbit.png';plans.append(layout(names,p,6,(210,238),crop=(360,110,920,670)));paths.append(p)
        names=[f'gallery/integration-{i:02d}.png' for i in range(12)]
        p=OUT/'world-orbit.png';plans.append(layout(names,p,4,(350,220)));paths.append(p)
        note='Ordered 24-pose full tree orbit and 12-pose world-camera integration sequence. Check view consistency and tree obstruction throughout all labelled samples. These sampled images do not certify real-time animation or FPS.'
    (OUT/(group+'-input-transform.json')).write_text(json.dumps(plans,indent=2))
    return paths,note

env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/MODEL),'--mmproj',str(CACHE/PROJECTOR),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-max-tokens','1024']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
reviews=[]
try:
    for _ in range(120):
        if proc.poll() is not None:raise RuntimeError('Vision process exited')
        try:
            if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError('Vision runtime not ready')
    for group in GROUPS[SHARD]:
        record={'task':'T01','group':group,'source':source['source'],'role':ROLE,'passed':False,'independent_execution':False}
        try:
            paths,note=prepare(group);content=[];inputs=[]
            for p in [ref]+paths:
                im=Image.open(p).convert('RGB');original=im.size
                im.thumbnail((1280,1280),Image.Resampling.LANCZOS)
                b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
                inputs.append({'filename':p.name,'original_size':original,'input_size':im.size,'source_sha256':digest(p),'input_sha256':hashlib.sha256(data).hexdigest()})
                content.extend([{'type':'text','text':'Evidence: '+p.name},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}}])
            content.append({'type':'text','text':PROMPT+'\nEvidence group '+group+': '+note})
            record['inputs']=inputs
            request={'model':'T01-independent-'+ROLE,'messages':[{'role':'user','content':content}],'max_tokens':550,'temperature':.1,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
            req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'},method='POST')
            print('Reviewing',ROLE,group,flush=True);start=time.monotonic()
            with urllib.request.urlopen(req,timeout=1100) as r:result=json.load(r)
            (OUT/(group+'-raw.json')).write_text(json.dumps(result,indent=2))
            record.update(independent_execution=True,elapsed_seconds=round(time.monotonic()-start,3))
            provenance['independent_model_execution']=True
            assert result['choices'][0]['finish_reason']=='stop','Truncated output'
            raw=result['choices'][0]['message']['content'];(OUT/(group+'-raw.txt')).write_text(raw)
            parsed=json.loads(raw)
            assert set(parsed['scores'])==set(KEYS)
            assert all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=10 for v in parsed['scores'].values())
            assert isinstance(parsed['defects'],list) and type(parsed['coverage_complete']) is bool
            assert parsed['confidence'] in ('low','medium','high') and 2<=len(parsed['observations'])<=3
            record['review']=parsed;record['lowest_score']=min(parsed['scores'].values())
            record['passed']=record['lowest_score']>=9 and not parsed['defects'] and parsed['coverage_complete'] and parsed['confidence']!='low'
        except Exception as exc:record['error']=str(exc)
        reviews.append(record);(OUT/(group+'-review.json')).write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
finally:
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))
    report={'task':'T01','source':source['source'],'role':ROLE,'shard':SHARD,'expected_groups':GROUPS[SHARD],'reviews':reviews,'passed':len(reviews)==len(GROUPS[SHARD]) and all(r['passed'] for r in reviews),'production_approved':False,'physical_4k60_verified':False}
    (OUT/'shard-review.json').write_text(json.dumps(report,indent=2))
    proc.terminate()
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:proc.kill()
    log.close()
# Review execution completing is not equivalent to PASS. The gate reads records.
