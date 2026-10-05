#!/usr/bin/env python3
"""Two independent processes use one disclosed model family; never self-score.
Inputs: actual source-bound Mobile captures, actual cropped reference pixels.
Output preserves raw model results; no production or physical-FPS approval.
"""
from __future__ import annotations
import base64,hashlib,io,json,os,pathlib,subprocess,time,urllib.request
from PIL import Image,ImageDraw
ROLE=os.environ['REVIEW_ROLE']
assert ROLE in ('reference-fidelity','visual-integrity')
E=pathlib.Path('task01-evidence');O=pathlib.Path('critic-results-v2');O.mkdir(exist_ok=True)
source=json.loads((E/'provenance.json').read_text())
os.environ['EXPECTED_SOURCE']=source['source']
# Reuse only the checksum-bound runtime/model download bootstrap, not its old art prompt.
url='https://raw.githubusercontent.com/ksolo21-web/HAVENLINE/2254fa959bb3640c0d18a0638d9dddda86903b5b/tools/havenline/run_environment_vision_critic.py'
raw=urllib.request.urlopen(url,timeout=60).read()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='ae3ea8c72e42e2508e8d4129921ef3b566301a37'
bootstrap=raw.decode().split('# Wait for the exact revised source')[0].replace('releases/latest','releases/tags/b10809')
namespace={};exec(compile(bootstrap,'pinned-model-bootstrap','exec'),namespace)
WORK,server,MODEL_FILES=namespace['WORK'],namespace['server'],namespace['MODEL_FILES']
provenance=namespace['provenance'];provenance.update({'task':'T01','role':ROLE,'capture_provenance':source,'independent_model_execution':False,'production_approved':False,'bootstrap_git_blob':'ae3ea8c72e42e2508e8d4129921ef3b566301a37'})
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for rel,expected in source['captures'].items():
    p=E/rel;assert p.is_file() and digest(p)==expected,rel
reference=E/'reference-crops.webp'
assert digest(reference)=='0602b485dfd8ae9e06a9cb60f77fd902537b1b4cb9a84ab45ed57d7c54033b10'
def montage(names,path,columns,tile=(320,205)):
    w,h=tile;rows=(len(names)+columns-1)//columns
    canvas=Image.new('RGB',(columns*w,rows*h),(20,35,53));draw=ImageDraw.Draw(canvas)
    for i,name in enumerate(names):
        im=Image.open(E/'gallery'/name).convert('RGB');im.thumbnail((w,h-20))
        x=(i%columns)*w;y=(i//columns)*h
        canvas.paste(im,(x+(w-im.width)//2,y+20));draw.text((x+4,y+3),name,fill='white')
    canvas.save(path)
angles=[f'v{i:02d}-{a}.png' for i in (1,2,3) for a in ('front','rear','side','three-quarter')]
montage(angles,O/'all-variant-angles.png',4)
montage([f'orbit-{i:02d}.png' for i in range(24)],O/'orbit-sequence.png',6,(210,135))
inputs=[reference,O/'all-variant-angles.png',O/'orbit-sequence.png',E/'gallery/v01-three-quarter.png',E/'gallery/gameplay-integration.png']
content=[];records=[]
for p in inputs:
    im=Image.open(p).convert('RGB');original=im.size;im.thumbnail((1280,1280),Image.Resampling.LANCZOS)
    b=io.BytesIO();im.save(b,format='PNG');data=b.getvalue()
    records.append({'name':p.name,'source_sha256':digest(p),'original_size':original,'model_size':im.size,'input_sha256':hashlib.sha256(data).hexdigest()})
    content.append({'type':'text','text':'IMAGE: '+p.name})
    content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}})
prompt='''You are a separately executing critic, not the builder. Review ONLY Task T01: snow conifers and woodland framing. First image contains actual resized crops from the two user reference recordings, A left and B right. The reference is clean stylized blue-white snow crowns, warm trunks, scalloped/notched layered silhouettes; do not reward unrelated realistic bark/noise. The other images are actual Godot Mobile outputs: twelve labelled views of three candidate trees, ordered camera orbit frames, a larger three-quarter view, and actual existing gameplay integration. Asset diagnostics intentionally hide unrelated objects; the gameplay image includes unfinished cabins and terrain that belong to LOCKED later tasks, so do not score them as T01 defects or approve them. Assess whether the NEW TREES are genuinely finished, reference-faithful and not primitive-looking, grounded, cleanly shaded, readable and free of joins/seams/camera-angle defects. Existing unfinished gameplay is NOT passed by this scoped review. There are only small reference crops; disclose inability to verify fine details. Orbit panels are sampled actual camera poses, not an FPS or complete movement benchmark. Do not infer physical-device performance. Inspect every labelled required view, identify concrete visible defects and their view/location. Do not invent defects; do not inflate or repeatedly round scores. This is one model family, not a human expert panel. Score 0-10 each: silhouette, materials, reference_fidelity, integration, geometric_integrity. Passing intermediate task score is >=9 per dimension AND no unresolved mandatory defect, but give your independent score, not the desired number. Aim is 10. If evidence is insufficient mark coverage_complete false and explain. Give at most four concise defects. Output JSON only. Reviewer role: '''+ROLE
if ROLE=='reference-fidelity':prompt+=' Focus particularly on crown proportions, blue-white material language, notches, tree shape/scale and density compared with the actual reference pixels.'
else:prompt+=' Focus particularly on view-to-view shape/shading integrity, roots/contact, visible seams, overlapping crowns and foreground integration; independently also score reference fidelity.'
content.append({'type':'text','text':prompt})
(O/'instructions.txt').write_text(prompt);(O/'model-inputs.json').write_text(json.dumps(records,indent=2))
keys=['silhouette','materials','reference_fidelity','integration','geometric_integrity']
schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'}},'defects':{'type':'array','items':{'type':'string'}},'coverage_complete':{'type':'boolean'},'limitations':{'type':'array','items':{'type':'string'}},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in keys},'required':keys,'additionalProperties':False}},'required':['observations','defects','coverage_complete','limitations','confidence','scores'],'additionalProperties':False}
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(O/'inference-server.log').open('w')
cmd=[str(server),'-m',str(WORK/MODEL_FILES[0]),'--mmproj',str(WORK/MODEL_FILES[1]),'--host','127.0.0.1','--port','8080','-c','12288','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-max-tokens','1024']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
report={'task':'T01','source':source['source'],'role':ROLE,'independent_execution':False,'passed':False,'production_approved':False,'physical_4k60_verified':False}
try:
    for _ in range(180):
        if proc.poll() is not None:raise RuntimeError('Vision server stopped')
        try:
            if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError('Vision server not ready')
    request={'model':'independent-T01-'+ROLE,'messages':[{'role':'user','content':content}],'max_tokens':850,'temperature':.1,'seed':20260908 if ROLE=='reference-fidelity' else 20260909,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
    http=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'},method='POST')
    start=time.monotonic()
    with urllib.request.urlopen(http,timeout=1000) as response:result=json.load(response)
    (O/'raw-response.json').write_text(json.dumps(result,indent=2))
    report['independent_execution']=True;report['elapsed_seconds']=time.monotonic()-start
    provenance['independent_model_execution']=True
    assert result['choices'][0]['finish_reason']=='stop','Truncated review'
    text=result['choices'][0]['message']['content'];(O/'raw-response.txt').write_text(text)
    parsed=json.loads(text);assert set(parsed['scores'])==set(keys)
    assert all(type(v) in (float,int) and 0<=v<=10 for v in parsed['scores'].values())
    assert isinstance(parsed['defects'],list) and type(parsed['coverage_complete']) is bool
    assert parsed['confidence'] in ('low','medium','high')
    report['review']=parsed;report['lowest_score']=min(parsed['scores'].values())
    report['passed']=report['lowest_score']>=9 and not parsed['defects'] and parsed['coverage_complete'] and parsed['confidence']!='low'
except Exception as exc:
    report['error']=str(exc)
finally:
    (O/'provenance.json').write_text(json.dumps(provenance,indent=2))
    (O/'task-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
    proc.terminate()
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:proc.kill()
    log.close()
# Execution success is not a task pass. The independent aggregate controls progression.
