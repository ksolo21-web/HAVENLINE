#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,time,urllib.request
from lib import DOCS,load_json

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    cfg=load_json(DOCS/'CRITIC_EXECUTION.json')['local_independent_runtime'];cache=pathlib.Path(os.path.expanduser(cfg['cache_path']));m=json.loads((cache/'manifest.json').read_text())
    assert m['publisher']==cfg['provider'] and m['base_model']==cfg['base_model']
    for item in m['files']:assert digest(cache/item['filename'])==item['sha256']
    servers=list((cache/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0];env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
    log=open('specialist-runtime-smoke.log','w');cmd=[str(server),'-m',str(cache/m['model_file']),'--mmproj',str(cache/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','2048','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja']
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    try:
        for _ in range(150):
            if proc.poll() is not None:raise RuntimeError('runtime exited')
            try:
                if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
            except Exception:pass
            time.sleep(2)
        else:raise RuntimeError('runtime not ready')
        schema={'type':'object','properties':{'runtime_ready':{'type':'boolean'},'token':{'type':'string','enum':['havenline-specialist-v1']}},'required':['runtime_ready','token'],'additionalProperties':False}
        body={'model':'havenline-specialist-smoke','messages':[{'role':'user','content':'Return JSON only with runtime_ready=true and token=havenline-specialist-v1.'}],'max_tokens':80,'temperature':0,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema}}
        req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=300) as r:raw=json.load(r)
        parsed=json.loads(raw['choices'][0]['message']['content']);assert raw['choices'][0]['finish_reason']=='stop' and parsed=={'runtime_ready':True,'token':'havenline-specialist-v1'}
        result={'passed':True,'provider':m['publisher'],'base_model':m['base_model'],'publisher_revision':m.get('revision'),'runtime_release':m.get('runtime_release'),'all_cached_files_hash_verified':True,'response':parsed}
        pathlib.Path('specialist-runtime-smoke.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    finally:
        proc.terminate()
        try:proc.wait(timeout=10)
        except Exception:proc.kill()
        log.close()
if __name__=='__main__':main()
