#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, hashlib, json, os, pathlib, shutil, subprocess, tarfile, urllib.request
from lib import DOCS, load_json

RUNTIME_SHA256="5e34434ddc6d03cd1584f403201aff0d4bd1a5793a72ff7e286532dfd1e4b941"
RUNTIME_URL="https://github.com/ggml-org/llama.cpp/releases/download/b10809/llama-b10809-bin-ubuntu-x64.tar.gz"

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def download(url:str,path:pathlib.Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    aria=shutil.which('aria2c')
    if aria:
        subprocess.run([aria,'--console-log-level=warn','--summary-interval=20','-x','12','-s','12','-k','4M','--file-allocation=none','--max-tries=3','--retry-wait=3','--connect-timeout=20','--timeout=60','--allow-overwrite=true','--auto-file-renaming=false','-d',str(path.parent),'-o',path.name,url],check=True)
    else:
        req=urllib.request.Request(url,headers={'User-Agent':'Havenline-independent-specialist-review'})
        with urllib.request.urlopen(req,timeout=120) as src,path.open('wb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)

def main():
    cfg=load_json(DOCS/'CRITIC_EXECUTION.json')['local_independent_runtime'];root=pathlib.Path(os.path.expanduser(cfg['cache_path']));root.mkdir(parents=True,exist_ok=True)
    repo=cfg['provider'];revision=cfg['model_revision'];api=f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true'
    req=urllib.request.Request(api,headers={'User-Agent':'Havenline-independent-specialist-review'})
    with urllib.request.urlopen(req,timeout=60) as r:info=json.load(r)
    if info.get('sha')!=revision:raise SystemExit(f'publisher revision mismatch: {info.get("sha")} != {revision}')
    siblings={r['rfilename']:r for r in info['siblings']};model='Qwen3.5-9B-Q5_K_M.gguf';projector='mmproj-F16.gguf' if 'mmproj-F16.gguf' in siblings else 'mmproj-BF16.gguf'
    records=[]
    for name in (model,projector):
        item=siblings.get(name);sha=(item or {}).get('lfs',{}).get('sha256')
        if not sha or len(sha)!=64:raise SystemExit('publisher SHA-256 missing at pinned revision: '+name)
        records.append({'filename':name,'sha256':sha,'url':f'https://huggingface.co/{repo}/resolve/{revision}/{name}?download=true'})
    records.append({'filename':'runtime.tar.gz','sha256':RUNTIME_SHA256,'url':RUNTIME_URL})
    def ensure(item):
        p=root/item['filename']
        if not p.is_file() or digest(p)!=item['sha256']:
            if p.exists():p.unlink()
            download(item['url'],p)
        actual=digest(p)
        if actual!=item['sha256']:raise SystemExit(f'hash mismatch {item["filename"]}: {actual}')
        item['bytes']=p.stat().st_size
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(ensure,records))
    runtime=root/'runtime';runtime.mkdir(exist_ok=True)
    with tarfile.open(root/'runtime.tar.gz') as t:t.extractall(runtime,filter='data')
    servers=list(runtime.rglob('llama-server'))
    if len(servers)!=1:raise SystemExit(f'expected one llama-server, found {len(servers)}')
    servers[0].chmod(0o755)
    manifest={'publisher':repo,'revision':revision,'base_model':cfg['base_model'],'model_file':model,'projector_file':projector,'runtime_release':'b10809','files':records,'purpose':'Havenline independent C1/C2/C3/C4/C5/C7/C8/C10/C11 review','paid_inference':False,'pinned_revision_enforced':True}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'passed':True,'cache':str(root),'publisher':repo,'revision':revision,'runtime':'b10809','files':[{'filename':x['filename'],'sha256':x['sha256'],'bytes':x['bytes']} for x in records]},indent=2))
if __name__=='__main__':main()
