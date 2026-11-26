"""Detached six-fastener sewn exterior mount, never a hidden closure or a game install."""
import argparse, json, hashlib, struct, itertools
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from inspect_source import load,edges,weld

SLOTS=(58,59,60,61,64,65)
COUNT=(4,14,18,12,10,24)
RIMS=(6,8,10,10,8,10)
ID05=(49688,49719,49721,49723)
CLOTH05=(49685,49689,49718,49720,49722,51160)
def h(a): return hashlib.sha256(a).hexdigest()
def author(path):
 d,V,N,U,J,W,T=load(path)
 _, alias=weld(V); TW=alias[T]
 edge_map=defaultdict(list)
 for f,tri in enumerate(TW):
  for a,b in edges(tri):edge_map[tuple(sorted((a,b)))].append((f,a,b))
 patch={}; report={}; X=[[],[],[],[],[]]; created={}
 for s,n,k in zip(SLOTS,COUNT,RIMS):
  assert d['nodes'][d['skins'][0]['joints'][s]]['name']==f'HemFastener_{s-53:02}'
  pure=np.where(J==s,W,0).sum(1)==1
  metal=np.flatnonzero(pure[T].all(1))
  es=Counter(tuple(sorted(e)) for f in metal for e in edges(TW[f]))
  rim_edges={e for e,c in es.items() if c==1}
  rb=Counter(itertools.chain.from_iterable(rim_edges))
  rim=set(rb)
  assert len(metal)==n and len(rim_edges)==k and len(rim)==k and set(rb.values())=={2}
  assert pure[np.isin(alias,list(rim))].all()
  neigh=set()
  for e in rim_edges:
   a,b=edge_map[e]
   assert a[1:]==b[1:][::-1] and sum(f in metal for f,_,_ in (a,b))==1
   neigh.update(f for f,_,_ in (a,b) if f not in metal)
  if s==58:
   assert tuple(metal)==ID05 and tuple(sorted(neigh))==CLOTH05
  cloth=np.setdiff1d(np.flatnonzero(np.isin(TW,list(rim)).any(1)),metal)
  assert not (set(cloth)&set(patch))
  rb_ack=set()
  def mid(i,o):
   # All new points were evaluated on genuine neighboring exterior triangles.
   # No hidden seat: retain the original rigid rim, stop mount influence at
   # the new middle row, and preserve the adjacent untouched cloth carriers.
   assert pure[i] and alias[i] in rim and alias[o] not in rim
   assert not any(np.where(J[o]==t,W[o],0).sum()==1 for t in SLOTS)
   assert np.where(J[o]==s,W[o],0).sum()==0
   key=(s,int(i),int(o))
   if key not in created:
    created[key]=len(V)+len(X[0])
    q=(V[i].astype(float)+V[o].astype(float))*.5
    normal=N[i].astype(float)+N[o].astype(float)
    assert np.linalg.norm(normal)>1e-7
    normal/=np.linalg.norm(normal)
    for x,val in zip(X,(q,normal,(U[i].astype(float)+U[o].astype(float))*.5,J[o],W[o])):x.append(val)
   rb_ack.add(tuple(sorted((int(alias[i]),int(alias[o])))))
   return created[key]
  for f in cloth:
   a,b,c=map(int,T[f]); flags=[alias[x] in rim for x in (a,b,c)]
   assert sum(flags) in (1,2)
   while flags[0]!=(sum(flags)==1) or flags[1:]==[True,False]:
    # Rotate to (rim,cloth,cloth) or (cloth,rim,rim).
    a,b,c=b,c,a; flags=flags[1:]+flags[:1]
   if sum(flags)==1:
    m,n=mid(a,b),mid(a,c)
    patch[int(f)]=[(a,m,n),(m,b,c),(m,c,n)]
   else:
    m,n=mid(b,a),mid(c,a)
    patch[int(f)]=[(a,m,n),(m,b,c),(m,c,n)]
  assert all(len(edge_map[e])==2 and all(f in patch for f,*_ in edge_map[e]) for e in rb_ack)
  report[s]={'metal_faces':metal.tolist(),'shared_rim_edge_count':len(rim_edges),'opposite_edge_cloth_faces':sorted(neigh),
             'refined_cloth_faces':cloth.tolist(),'flex_edge_count_welded':len(rb_ack)}
 A=[np.concatenate([prev,np.asarray(new,dtype=prev.dtype)]) for prev,new in zip((V,N,U,J,W),X)]
 # Preserve unrelated faces at their exact source indices; append only new child's two extras.
 F=T.copy(); extra=[]; origins=list(range(len(T)))
 for f,parts in sorted(patch.items()):
  F[f]=parts[0]; extra+=parts[1:]; origins.extend([f]*2)
 F=np.concatenate([F,np.asarray(extra,dtype=T.dtype)])
 return d,A,F,np.array(origins),report,created

def export_glb(src,path,meta,arrays,F):
 original=src.read_bytes(); jlen=struct.unpack_from('<I',original,12)[0]
 blen=struct.unpack_from('<I',original,20+jlen)[0]
 body=bytearray(original[28+jlen:28+jlen+blen]); source_prefix=len(body)
 pr=meta['meshes'][0]['primitives'][0]
 for key,A in zip(('POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0','indices'),[*arrays,F]):
  idx=pr['indices'] if key=='indices' else pr['attributes'][key]
  base=meta['accessors'][idx]
  while len(body)%4: body+=b'\0'
  v=len(meta['bufferViews'])
  meta['bufferViews'].append({'buffer':0,'byteOffset':len(body),'byteLength':A.nbytes,'target':34963 if key=='indices' else 34962})
  assert not base.get('normalized',False)
  rowlen=1 if key=='indices' else A.shape[-1]
  flat=A.reshape(-1,rowlen)
  a={**base,'bufferView':v,'byteOffset':0,'count':len(flat)}
  if key in ('POSITION','indices') or 'min' in a or 'max' in a:
   a.update(min=flat.min(0).tolist(),max=flat.max(0).tolist())
  new=len(meta['accessors']); meta['accessors'].append(a)
  if key=='indices': pr['indices']=new
  else:pr['attributes'][key]=new
  body+=A.tobytes()
 while len(body)%4:body+=b'\0'
 meta['buffers'][0]['byteLength']=len(body)
 j=json.dumps(meta,separators=(',',':'),ensure_ascii=True).encode()
 j+=b' '*((-len(j))%4)
 blob=struct.pack('<4sII',b'glTF',2,28+len(j)+len(body))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(body),b'BIN\0')+body
 assert blob[28+len(j):28+len(j)+source_prefix]==original[28+jlen:28+jlen+blen]
 path.write_bytes(blob)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('out',type=Path)
 a=p.parse_args(); a.out.mkdir()
 d,A,F,origins,report,created=author(a.source)
 np.savez_compressed(a.out/'mounts.LOCAL.npz',positions=A[0],normals=A[1],uv=A[2],joints=A[3],weights=A[4],faces=F,source_face_map=origins,
  raw_midpoint_indices=np.array([(*k,v) for k,v in sorted(created.items())],int))
 export_glb(a.source,a.out/'Character1-detached-fastener-mounts.LOCAL.glb',d,A,F)
 out={'source_sha256':h(a.source.read_bytes()),'target':report,'changed_cloth_faces':sum(len(x['refined_cloth_faces']) for x in report.values()),
      'new_raw_midpoints':len(created),'original_vertex_count':len(A[0])-len(created),'original_face_count':96001,'new_faces':len(F)-96001,
      'artifact_sha256':{p.name:h(p.read_bytes()) for p in a.out.iterdir()},'installed':False}
 (a.out/'build.json').write_text(json.dumps(out,indent=2)+'\n')
