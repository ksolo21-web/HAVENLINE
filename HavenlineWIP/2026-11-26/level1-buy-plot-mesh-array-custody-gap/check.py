from pathlib import Path
import struct, hashlib, json
root=Path('..'); stage=root/'hvn-buy-plot-c1-stencil-native-preflight'
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
pos=[]
for n,x in (('characters/Character1.glb','95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'),('studio/wood_bundle_v3.glb','1004ea2f41751bf79ad10ab0165c60a05e5ee581d35095913a0794f16931abd9')):
 p=stage/'staged/project/assets'/n
 assert sha(p)==x
 b=p.read_bytes(); L=struct.unpack_from('<I',b,12)[0]; j=json.loads(b[20:20+L]); a=j['accessors']
 for node in j['nodes']:
  if 'mesh' not in node:continue
  pos.append((node['name'],[[a[q['attributes']['POSITION']]['count'],a[q['indices']]['count'],a[q['attributes']['WEIGHTS_0']]['count']*4 if 'WEIGHTS_0' in q['attributes'] else 0] for q in j['meshes'][node['mesh']]['primitives']]))
obs={}
for n,x in (('funded-approach-moving','cbcf2616fb77dcac0a835b6ff40035f5efaeef8b25fd45250552f730840c5a3e'),('funded-near-moving','6f2e7258515795f76018fa06bc59667511466f6d9fd25f74f840dc7cb53010e0')):
 f=stage/'graphics-evidence.mawe8Hs6/enabled'/(n+'.pose.json')
 assert sha(f)==x
 j=json.loads(f.read_text())
 a={s['relative'].rsplit('/',1)[-1]:[[r['vertices'],r['indices'],r['weights']] for r in s['surfaces']] for s in j['surfaces']}
 assert dict(pos)==a
 obs[n]={'hash':x,'tick':j['tick'],'meshes':len(a),'primitive_count':sum(map(len,a.values()))}
print(json.dumps({'count_identity_only':pos,'poses':obs,'exact_runtime_array_values_or_hash_captured':False,
 'offline_stencil_or_phone_claim':False},indent=2))
