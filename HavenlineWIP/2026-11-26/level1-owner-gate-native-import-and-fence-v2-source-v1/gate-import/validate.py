"""Verify detached Godot import evidence against exact OBJ triangle coordinates."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree

root=Path(__file__).resolve().parent
donors=root/'input/donors'
files=("GateLeaf.obj","GateLeaf_Right.obj","ThresholdPost.obj","ThresholdPost_Right.obj")
def filehash(p):return sha256(p.read_bytes()).hexdigest()
def parse(f):
    v=[]; rows=[]
    for line in f.read_text().splitlines():
        a=line.split()
        if not a:continue
        if a[0]=='g':
            assert len(a)==2
            rows.append({'group':a[1],'label':None,'faces':[]})
        if a[0]=='usemtl':
            assert len(a)==2 and rows[-1]['label'] is None
            rows[-1]['label']=a[1]
        if a[0]=='v':
            assert len(a)==4
            v.append(tuple(map(float,a[1:])))
        if a[0]=='f':
            assert len(a)==4
            fids=[int(k)-1 for k in a[1:]]
            assert all(0<=i<len(v) for i in fids)
            rows[-1]['faces'].append(fids)
    xyz=np.asarray(v)
    for r in rows:r['xyz']=xyz[np.asarray(r.pop('faces'))]
    return xyz,rows

def read_mtl():
    rgb={}
    for l in (donors/'owner33035.mtl').read_text().splitlines():
        a=l.split()
        if not a:continue
        if a[0]=='newmtl': key=a[1]
        if a[0]=='Kd': rgb[key]=[float(v) for v in a[1:]]+[1.]
        assert not a[0].startswith('map_')
    return rgb

def expected():
    rgb=read_mtl(); out={}; all_labels=set()
    for f in files:
        vs,rows=parse(donors/f)
        surfaces=[{'index':i,'source_group':r['group'],'label':r['label'],'triangles':len(r['xyz']),
                   'required_class':'StandardMaterial3D','primitive':3,'map_slots_bound':[]}
                  for i,r in enumerate(rows)]
        all_labels.update(r['label'] for r in surfaces)
        out[f]={"aabb":[vs.min(0).tolist(),vs.max(0).tolist()],
                "triangles":sum(r['triangles'] for r in surfaces),"surfaces":surfaces,
                "hash":filehash(donors/f),"resource":"res://donors/"+f}
    assert all_labels==set(rgb)
    for f,count,n in zip(files,(5056,4868,5278,5278),(24,23,8,8)):
        assert out[f]['triangles']==count and len(out[f]['surfaces'])==n
    return dict(files=out,mtl_rgb=rgb,mtl_sha256=filehash(donors/'owner33035.mtl'),surface_order_rule='source g/usemtl entry sequence, no collapse/repartition expected')

def cyclic(ids):
    u=tuple(map(int,ids))
    return min(u,u[1:]+u[:1],u[2:]+u[:2])

def validate(out):
    pins=expected()
    assert pins==json.loads((root/'expected.json').read_text())
    observed=[json.loads(s) for s in (out/'result.jsonl').read_text().splitlines()]
    assert [r['file'] for r in observed]==list(files)
    frames={};used=set()
    for row in observed:
        f=row['file']; want=pins['files'][f]
        assert row['mesh_resource']==want['resource']
        bounds=np.asarray(row['aabb'])
        assert bounds.shape==(2,3) and np.max(np.abs(bounds-want['aabb']))<1e-6
        assert len(row['surfaces'])==len(want['surfaces'])
        _,original=parse(donors/f);seen=[];global_wind=set()
        for got,e,source in zip(row['surfaces'],want['surfaces'],original):
            n=e['triangles']; i=e['index']
            assert got['index']==i and got['label']==e['label']
            assert got['material_class']==e['required_class'] and got['primitive']==e['primitive']
            assert got['map_slots_bound']==[] and got['triangles']==n
            assert (got['indices']==3*n and 3<=got['vertices']<=3*n) or (got['indices']==0 and got['vertices']==3*n)
            native=np.asarray(got['albedo_rgba']); rgba=np.asarray(pins['mtl_rgb'][got['label']])
            assert native.shape==(4,) and np.max(np.abs(native-rgba))<.002
            payload=Path(f).stem+".surface-"+str(i)+".xyzf32"
            assert payload==got['payload'] and payload not in used
            used.add(payload);path=out/payload
            assert path.stat().st_size==n*9*4
            native_xyz=np.fromfile(path,dtype='<f4').reshape(n,3,3).astype(float)
            exact,idx=np.unique(source['xyz'].reshape(-1,3),axis=0,return_inverse=True)
            sep,obj=cKDTree(exact).query(native_xyz.reshape(-1,3),k=1)
            assert np.max(sep)<4e-7
            old=idx.reshape(n,3); new=obj.reshape(n,3)
            assert Counter(tuple(sorted(t)) for t in old)==Counter(tuple(sorted(t)) for t in new)
            wanted_o=Counter(cyclic(t) for t in old)
            if wanted_o==Counter(cyclic(t) for t in new):
                sense='source_winding'
            elif wanted_o==Counter(cyclic(t[::-1]) for t in new):
                sense='consistent_reversal'
            else: raise AssertionError((f,i,'mixed imported winding'))
            global_wind.add(sense)
            seen.append(dict(got,source_group=e['source_group'],max_position_error=float(np.max(sep)),
                             geometry_payload_sha256=filehash(path),exact_triangle_coordinate_multiset=True,winding=sense))
        assert len(global_wind)==1
        frames[f]={"digest":want['hash'],"exact_mesh_resource":row['mesh_resource'],"aabb":row['aabb'],
            "triangles":sum(r['triangles'] for r in seen),"exact_ordered_surface_count":len(seen),"winding":global_wind.pop(),"surfaces":seen}
    assert used=={p.name for p in out.glob('*.xyzf32')}
    print(json.dumps({"native_import_read_only":True,"source_world_space_triangle_geometry_matches":True,
                      "digest_of_observed_jsonl":filehash(out/'result.jsonl'),"meshes":frames,
                      "not_render_assembly_footprint_or_runtime_approval":True},indent=2,sort_keys=True))
if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--source-only':
        print(json.dumps(expected(),indent=2,sort_keys=True))
    else:
        assert len(sys.argv)==2
        validate(Path(sys.argv[1]))
