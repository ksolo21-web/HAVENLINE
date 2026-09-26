#!/usr/bin/env python3
"""Restore exactly the already-pinned public reviewer. Cache misses are recoverable.
No credential, paid inference endpoint, game mutation or changed model selection.
"""
from __future__ import annotations
import concurrent.futures,hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path.home()/'.cache/havenline-t01-qwen35';ROOT.mkdir(parents=True,exist_ok=True)
REV='3885219b6810b007914f3a7950a8d1b469d598a5'
PUBLISHER='unsloth/Qwen3.5-9B-GGUF'
ITEMS=[{'filename':'Qwen3.5-9B-Q5_K_M.gguf','sha256':'dc2a39aef291f91a9116ad214058da0d86eb648743a124bd8c333787c4b9c91c','bytes':6577841376,'url':f'https://huggingface.co/{PUBLISHER}/resolve/{REV}/Qwen3.5-9B-Q5_K_M.gguf?download=true'},
{'filename':'mmproj-F16.gguf','sha256':'f70dc3509053962b0d0d3ee8a7eacebf5d60aa560cad78254ae8698516ae029f','bytes':918166080,'url':f'https://huggingface.co/{PUBLISHER}/resolve/{REV}/mmproj-F16.gguf?download=true'},
{'filename':'runtime.tar.gz','sha256':'5e34434ddc6d03cd1584f403201aff0d4bd1a5793a72ff7e286532dfd1e4b941','bytes':16734586,'url':'https://github.com/ggml-org/llama.cpp/releases/download/b10809/llama-b10809-bin-ubuntu-x64.tar.gz'}]
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4194304),b''):h.update(block)
    return h.hexdigest()
def restore(item):
    path=ROOT/item['filename']
    valid=path.is_file() and path.stat().st_size==item['bytes'] and digest(path)==item['sha256']
    if not valid:
        subprocess.run(['aria2c','--console-log-level=warn','--summary-interval=30','-x','12','-s','12','-k','4M','--file-allocation=none','--max-tries=3','--retry-wait=3','--connect-timeout=20','--timeout=90','--allow-overwrite=true','--auto-file-renaming=false','-d',str(ROOT),'-o',path.name,item['url']],check=True)
    assert path.stat().st_size==item['bytes'] and digest(path)==item['sha256'],'Reviewer download checksum mismatch'
    print('Verified',path.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(restore,ITEMS))
runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
with tarfile.open(ROOT/'runtime.tar.gz') as archive:archive.extractall(runtime,filter='data')
servers=list(runtime.rglob('llama-server'));assert len(servers)==1;servers[0].chmod(0o755)
manifest={'publisher':PUBLISHER,'revision':REV,'base_model':'Qwen/Qwen3.5-9B','model_file':ITEMS[0]['filename'],'projector_file':ITEMS[1]['filename'],'runtime_release':'b10809','files':ITEMS,'task':'T01','approval':False,'reason':'Restore exact earlier model after cache miss, not a new review model or desired-score selection.'}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Pinned reviewer ready; no image review or approval has occurred in this preparation step.')
