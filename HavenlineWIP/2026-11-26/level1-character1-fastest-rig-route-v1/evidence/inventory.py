from pathlib import Path
from collections import defaultdict
import struct,json,sys,hashlib
root=Path(sys.argv[1]); found=defaultdict(list);failed=[]
for f in root.rglob('*.glb'):
 if f.is_symlink() or any(k in f.parts for k in ('.git','.godot','node_modules','tmp')):continue
 try:
  with f.open('rb') as fd:
   h=fd.read(20)
   if h.startswith(b'version https://git'): continue
   if h[:4]!=b'glTF':continue
   n,t=struct.unpack_from('<II',h,12)
   if n>16_000_000 or t!=0x4e4f534a:continue
   o=json.loads(fd.read(n))
   sku=[x.get('name','') for x in o.get('animations',[])]; nodes=[x.get('name','') for x in o.get('nodes',[])]
   if not sku or not o.get('skins'):continue
   key=(hashlib.sha256(h+json.dumps(o,sort_keys=True).encode()).hexdigest(),tuple(sku),tuple(len(x['joints']) for x in o['skins']))
   if not found[key]:
    fd.seek(0); digest=hashlib.file_digest(fd,'sha256').hexdigest()
   else: digest=found[key][0][1]
   found[key].append((str(f),digest))
 except (OSError,struct.error,ValueError) as e:failed.append(f.name)
print(json.dumps({'distinct_document_groups':len(found),'groups':[dict(json_class_sha=k[0],clip_names=k[1],skin_joint_counts=k[2],first_payload_sha=v[0][1],first_local_example=v[0][0],matching_documents=len(v)) for k,v in sorted(found.items())],'decode_errors':failed},indent=2))
