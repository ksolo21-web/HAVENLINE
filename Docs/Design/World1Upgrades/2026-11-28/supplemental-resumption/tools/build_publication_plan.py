#!/usr/bin/env python3
"""Build exact overlay entries for a new Git tree. Does not perform remote writes."""
from pathlib import Path
import argparse
import hashlib
import json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--parent',required=True)
    p.add_argument('--base-tree',required=True)
    p.add_argument('--branch',required=True)
    a=p.parse_args()
    package=a.package.resolve(); out=a.output.resolve()
    if out.is_relative_to(package):
        raise ValueError('Output must be outside the package to avoid recursive manifests')
    out.mkdir(parents=True,exist_ok=True)
    entries=[]; files=[]
    for source in sorted(package.rglob('*')):
        if not source.is_file(): continue
        if source.is_symlink(): raise ValueError('Refusing symlink: '+str(source))
        data=source.read_bytes()
        relative=source.relative_to(package).as_posix()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        binary=source.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.pdf','.zip'}
        item={'path':relative,'mode':'100644','type':'blob'}
        if binary: item['sha']=blob
        else: item['content']=data.decode('utf-8')
        entries.append(item)
        files.append({'path':relative,'source':str(source),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':blob,'binary':binary})
    batches=[]; batch=[]; size=2
    for item in entries:
        length=len(json.dumps(item,ensure_ascii=False,separators=(',',':')).encode())+1
        if batch and size+length>250000:
            batches.append(batch);batch=[];size=2
        batch.append(item);size+=length
    if batch:batches.append(batch)
    saved=[]
    for i,batch in enumerate(batches):
        target=out/f'batch-{i:03}.json'
        target.write_text(json.dumps(batch,ensure_ascii=False,separators=(',',':')))
        saved.append({'path':str(target),'entries':len(batch),'bytes':target.stat().st_size})
    manifest={'repository':'ksolo21-web/HAVENLINE','parent_sha':a.parent,'base_tree_sha':a.base_tree,'branch':a.branch,'overlay_policy':'Add/replace only listed paths on the exact supplied base tree; no deletions or native activation inferred.','package':str(package),'file_count':len(files),'unique_binary_blobs':len({x['git_blob_sha1'] for x in files if x['binary']}),'files':files,'batches':saved}
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))
if __name__=='__main__':
    main()
