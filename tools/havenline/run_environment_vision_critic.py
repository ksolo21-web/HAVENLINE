"""Independent CPU vision review of actual Havenline captures; never auto-approve production.
Only public model/runtime downloads and loopback inference are used. No paid inference
endpoint, account secret, game-source mutation or physical performance claim.
"""
from __future__ import annotations
import base64,concurrent.futures,hashlib,io,json,os,pathlib,shutil,subprocess,tarfile,time,urllib.request,zipfile
from PIL import Image
OUT=pathlib.Path('critic-results-v2');OUT.mkdir(exist_ok=True)
WORK=pathlib.Path(os.environ['RUNNER_TEMP'])/'havenline-vision-runtime';WORK.mkdir(exist_ok=True)
EXPECTED_SOURCE=os.environ['EXPECTED_SOURCE']
MODEL_ID='Qwen/Qwen3-VL-8B-Instruct-GGUF'
MODEL_FILES=['Qwen3VL-8B-Instruct-Q4_K_M.gguf','mmproj-Qwen3VL-8B-Instruct-F16.gguf']
def get_json(url,timeout=60):
    request=urllib.request.Request(url,headers={'User-Agent':'Havenline-visual-review'})
    with urllib.request.urlopen(request,timeout=timeout) as response:return json.load(response)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def download(url,path,expected=None):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=180) as response,path.open('wb') as f:shutil.copyfileobj(response,f,4*1024*1024)
            actual=digest(path)
            if expected and actual!=expected:raise ValueError('Download digest mismatch: '+path.name)
            return {'file':path.name,'sha256':actual,'bytes':path.stat().st_size}
        except Exception:
            if attempt==2:raise
            time.sleep(3*(attempt+1))
release=get_json('https://api.github.com/repos/ggml-org/llama.cpp/releases/latest')
assets=[a for a in release['assets'] if ('bin-ubuntu-x64' in a['name'] or 'bin-linux-x64' in a['name']) and not any(x in a['name'].lower() for x in ('cuda','vulkan','rocm','sycl')) and a['name'].endswith(('.tar.gz','.zip'))]
if len(assets)!=1:raise RuntimeError('CPU release asset not uniquely identified: '+str([a['name'] for a in assets]))
a=assets[0];archive=WORK/a['name'];expected=a.get('digest','').removeprefix('sha256:') or None
runtime=download(a['browser_download_url'],archive,expected)
binroot=WORK/'runtime';binroot.mkdir(exist_ok=True)
if archive.name.endswith('.zip'):
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            assert not pathlib.PurePosixPath(member.filename).is_absolute() and '..' not in pathlib.PurePosixPath(member.filename).parts
        z.extractall(binroot)
else:
    with tarfile.open(archive) as t:t.extractall(binroot,filter='data')
servers=list(binroot.rglob('llama-server'));assert len(servers)==1
server=servers[0];server.chmod(0o755)
info=get_json('https://huggingface.co/api/models/'+MODEL_ID+'?blobs=true');revision=info['sha']
siblings={f['rfilename']:f for f in info['siblings']}
def get_model(filename):
    expected=siblings[filename].get('lfs',{}).get('sha256')
    assert expected,'Model publisher SHA256 missing'
    return download('https://huggingface.co/'+MODEL_ID+'/resolve/'+revision+'/'+filename,WORK/filename,expected)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:weights=list(pool.map(get_model,MODEL_FILES))
provenance={'runner':'separate GitHub Actions CPU process','model':MODEL_ID,'model_revision':revision,'weight_files':weights,'runtime_release':release['tag_name'],'runtime_asset':runtime,'expected_source':EXPECTED_SOURCE,'independent_model_execution':False,'production_approved':False,'physical_4k60_verified':False}
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Verified public runtime and model weights.',flush=True)
# Wait for the exact revised source to finish its own actual rendering workflow.
capture_path='Docs/Art/EnvironmentReview/captures'
for attempt in range(45):
    subprocess.run(['git','fetch','--quiet','--depth=1','origin','codex/havenline-environment-review'],check=True)
    result=subprocess.run(['git','show','FETCH_HEAD:'+capture_path+'/provenance.json'],capture_output=True,text=True)
    if result.returncode==0:
        cp=json.loads(result.stdout)
        if cp['source']==EXPECTED_SOURCE:break
    time.sleep(20)
else:raise RuntimeError('Fresh capture provenance never matched expected source')
source_root=WORK/'captures';source_root.mkdir(exist_ok=True)
for record in cp['captures']:
    name=record['view'];folder=source_root/name;folder.mkdir(exist_ok=True)
    for filename in ('native-scene.png','render-evidence.json'):
        data=subprocess.check_output(['git','show','FETCH_HEAD:'+capture_path+'/'+name+'/'+filename]);(folder/filename).write_bytes(data)
    assert digest(folder/'native-scene.png')==record['sha256']
assert len(cp['captures'])==14
provenance['capture_provenance']=cp
provenance['capture_commit']=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],text=True).strip()
(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference-server.log').open('w')
command=[str(server),'-m',str(WORK/MODEL_FILES[0]),'--mmproj',str(WORK/MODEL_FILES[1]),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-max-tokens','1024']
proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
GUIDE=('You are an independent environment-art critic. Inspect this actual game screenshot closely. '
       'The agreed target is a finished premium stylized 3D winter-survival game: crafted timber buildings, '
       'branching snow-laden evergreens, shaped snow terrain, refined surfaces, clean geometry and readable lighting. '
       'Stylization is intentional; photorealism is not the target. Evaluate environment artwork only, not people, UI or unseen areas. '
       'First give two specific visible observations. Then identify at most three real visible defects, naming the object and image location; '
       'an empty defects list is allowed only when no defect is visible. Do not invent a problem to fill a slot. '
       'Independently score craft, materials, lighting, camera composition and geometry integrity from0 to10, decimals allowed. '
       '0 is absent/uncompleted and10 is perfectly finished with no known visible defect. Do not inflate scores to please the builder. '
       'A score is an evidence-based opinion, not proof of frame rate or complete-game functionality. Keep each observation/defect under20words. '
       'Return only the required JSON object.')
schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':2},'defects':{'type':'array','items':{'type':'string'},'maxItems':3},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in ('craft','materials','lighting','camera','geometry')},'required':['craft','materials','lighting','camera','geometry'],'additionalProperties':False},'confidence':{'type':'string','enum':['low','medium','high']}},'required':['observations','defects','scores','confidence'],'additionalProperties':False}
(OUT/'instructions.txt').write_text(GUIDE+'\n');(OUT/'review-schema.json').write_text(json.dumps(schema,indent=2))
records=[]
try:
    for i in range(120):
        if proc.poll() is not None:raise RuntimeError('Vision server exited during startup')
        try:
            if get_json('http://127.0.0.1:8080/health',5).get('status')=='ok':break
        except Exception:pass
        time.sleep(2)
    else:raise RuntimeError('Vision server did not become ready')
    order=['mobile-render','outpost-tree-detail','outpost-shelter-detail','outpost-shelter-detail-rear','outpost-furnace-detail','outpost-night','mobile-three-quarter','mobile-rear','mobile-left','mobile-side','outpost-blizzard','outpost-warmth4','outpost-gather','outpost-native-4k']
    for index,name in enumerate(order):
        p=source_root/name/'native-scene.png';image=Image.open(p).convert('RGB');original_size=list(image.size)
        image.thumbnail((1024,1024),Image.Resampling.LANCZOS);buffer=io.BytesIO();image.save(buffer,format='PNG')
        data=buffer.getvalue();record={'view':name,'source_sha256':digest(p),'original_size':original_size,'model_input_size':list(image.size),'model_input_sha256':hashlib.sha256(data).hexdigest(),'response':None,'passed':False}
        content=[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(data).decode()}},{'type':'text','text':'Evidence filename: '+name+'/native-scene.png. '+GUIDE}]
        request={'model':'environment-critic','messages':[{'role':'user','content':content}],'max_tokens':320,'temperature':0.15,'seed':20260907,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
        begin=time.time();print('Reviewing',index+1,'of14:',name,flush=True)
        http=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(http,timeout=240) as response:result=json.load(response)
        record['response']=result;record['elapsed_seconds']=round(time.time()-begin,2)
        raw=result['choices'][0]['message']['content'];record['raw_response']=raw
        try:
            assert result['choices'][0]['finish_reason']=='stop','Truncated review'
            parsed=json.loads(raw);scores=parsed['scores']
            assert set(scores)==set(schema['properties']['scores']['required'])
            assert all(type(v) in (float,int) and 0<=v<=10 for v in scores.values())
            assert isinstance(parsed['defects'],list) and len(parsed['observations'])==2
            record['parsed']=parsed;record['lowest_score']=min(scores.values())
            record['passed']=record['lowest_score']>9 and not parsed['defects']
        except Exception as e:record['validation_error']=str(e)
        records.append(record);(OUT/f'view-{index+1:02d}-{name}.json').write_text(json.dumps(record,indent=2)+'\n')
        print(raw,flush=True)
    provenance['independent_model_execution']=True
    summary={'independent_model_execution':True,'views_reviewed':len(records),'passed':len(records)==14 and all(r['passed'] for r in records),'lowest_valid_score':min((r['lowest_score'] for r in records if 'lowest_score' in r),default=None),'invalid_review_count':sum('validation_error' in r for r in records),'production_approved':False,'limitations':['Quantized8B vision model is advisory; verify its claims against original images.','Images resized to at most1024pixels on the longest side; source hashes and dimensions retained.','No temporal gameplay review, physical-device performance or whole-game certification.']}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
finally:
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    proc.terminate()
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:proc.kill()
    log.close()
