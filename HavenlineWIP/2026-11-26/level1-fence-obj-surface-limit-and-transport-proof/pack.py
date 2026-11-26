from pathlib import Path
from collections import defaultdict
import hashlib,json,sys
R=Path(__file__).resolve().parent
P=R.parent/'hvn-l1-fence-33036-rooted-emboss-module-v1'
p=P/'RootedEmbossedFence_SourceOnly.obj'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(p.read_bytes())=='cca517cdb235c81d7286af74fa02d1ba1d38142a4686a8a88ff11ce24a79554c'
def parse(text):
 vals=[[],[]]; chunks=[]; st=['','','']; current=[]
 for row in text.splitlines():
  if not row or row.startswith('#'):continue
  key,b=row.split(maxsplit=1)
  if key in ('v','vt'):vals[('v','vt').index(key)].append(b)
  elif key in ('o','s','usemtl'):
   i=('o','s','usemtl').index(key)
   if st[i]!=b and current:chunks.append((tuple(st),current));current=[]
   st[i]=b
  elif key=='f':
   f=[tuple(map(int,x.split('/'))) for x in b.split()]
   assert len(f)==3 and all(len(x)==2 and min(x)>0 for x in f)
   current.append(f)
  else:assert key=='mtllib'
 if current:chunks.append((tuple(st),current))
 return vals,chunks
V,runs=parse(p.read_text())
assert len(runs)==324 and {k[1] for k,_ in runs}=={'1'}
pos=defaultdict(set); uv=defaultdict(set)
for i,(k,fs) in enumerate(runs):
 for f in fs:
  for v,u in f:
   pos[(k,V[0][v-1])].add(i)
   uv[(k,V[0][v-1],V[1][u-1])].add(i)
def exact(V,runs):
 return [(k,[[[V[0][v-1],V[1][u-1]] for v,u in f] for f in fs]) for k,fs in runs]
out=[]; aggregate=[]
for i in range(0,len(runs),24):
 picks=runs[i:i+24]; rows=['# Detached exact source transport','mtllib RootedFence.mtl']; lookup=[{},{}]
 for k,fs in picks:
  for f in fs:
   for c in f:
    for j,idx in enumerate(c):
     if idx not in lookup[j]:
      lookup[j][idx]=len(lookup[j])+1;rows.append(('v','vt')[j]+' '+V[j][idx-1])
 state=['','','']
 for k,fs in picks:
  for j,tag in enumerate(('o','s','usemtl')):
   if k[j]!=state[j]:rows.append(tag+' '+k[j]); state[j]=k[j]
  for f in fs:rows.append('f '+' '.join(f'{lookup[0][v]}/{lookup[1][u]}' for v,u in f))
 blob='\n'.join(rows)+'\n'; ov,oo=parse(blob)
 assert exact(V,picks)==exact(ov,oo)
 iv=[{t:s for s,t in a.items()} for a in lookup]
 restored=[(k,[[(iv[0][v],iv[1][u]) for v,u in f] for f in fs]) for k,fs in oo]
 assert restored==picks
 aggregate+=restored
 out.append((blob,dict(name=f'shard_{i//24:02}.obj',runs=len(picks),first_run=i+1,triangles=sum(len(fs) for _,fs in picks),sha256=sha(blob.encode()))))
assert aggregate==runs
if len(sys.argv)==2:
 dest=Path(sys.argv[1]).resolve()
 assert dest.is_relative_to(R) and not dest.exists()
 dest.mkdir()
 for b,row in out:(dest/row['name']).write_text(b)
assert len(sys.argv)<=2
print(json.dumps(dict(state='source transport exact; native import and shading HOLD',runs=len(runs),faces=sum(len(fs) for _,fs in runs),objects=list(dict.fromkeys(k[0] for k,_ in runs)),smoothing_labels=['1'],distinct_object_smoothing_material=len(set(k for k,_ in runs)),shared_same_partition_pos_cross_run=sum(len(a)>1 for a in pos.values()),shared_same_partition_posuv_cross_run=sum(len(a)>1 for a in uv.values()),declared_normals=0,shards=[row for _,row in out]),indent=2))
