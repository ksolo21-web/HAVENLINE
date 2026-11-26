"""Compare every animated skinned vertex at 120 Hz, independent of image changes."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def digest(data):
    return hashlib.sha256(data).hexdigest()

class Model:
    def __init__(self, path):
        data = path.read_bytes()
        length = struct.unpack_from('<I', data, 12)[0]
        self.hash = digest(data)
        self.g = json.loads(data[20:20 + length])
        self.blob = data[28 + length:]
        self.nodes = self.g['nodes']
        self.parents = {c:i for i,n in enumerate(self.nodes) for c in n.get('children', [])}
        mesh_node, = [n for n in self.nodes if 'skin' in n and 'mesh' in n]
        skin = self.g['skins'][mesh_node['skin']]
        self.bones = skin['joints']
        self.bind = self.read(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
        self.surface, = self.g['meshes'][mesh_node['mesh']]['primitives']
        self.attrs = {k:self.read(v) for k,v in self.surface['attributes'].items()}
        self.verts = np.pad(self.attrs['POSITION'], ((0,0),(0,1)), constant_values=1)
        self.idx = self.attrs['JOINTS_0']
        self.weights = self.attrs['WEIGHTS_0']

    def read(self, index):
        a = self.g['accessors'][index]
        assert 'sparse' not in a
        v = self.g['bufferViews'][a['bufferView']]
        typ = np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1',5122:'<i2',5120:'i1'}[a['componentType']])
        n = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        data = np.ndarray((a['count'],n), dtype=typ,buffer=self.blob,
                          offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(v.get('byteStride',typ.itemsize*n),typ.itemsize))
        if a.get('normalized') and typ.kind in 'iu':
            return np.maximum(-1, data.astype(float)/np.iinfo(typ).max)
        return data

    def clip(self, anim):
        duration = max(self.read(s['input']).max() for s in anim['samplers'])
        times = np.r_[np.arange(0,float(duration),1/120), float(duration)]
        defaults = {'rotation':[0,0,0,1], 'translation':[0,0,0], 'scale':[1,1,1]}
        trs = {k:np.tile(np.array([n.get(k,v) for n in self.nodes],float),
                         (len(times),1,1)) for k,v in defaults.items()}
        for ch in anim['channels']:
            sampler=anim['samplers'][ch['sampler']]
            keys=self.read(sampler['input']).ravel()
            out=self.read(sampler['output'])
            target=ch['target']
            t=np.clip(times,keys[0],keys[-1])
            mode=sampler.get('interpolation','LINEAR')
            if len(keys)==1:
                value=np.repeat(out[:1],len(t),axis=0)
            elif mode=='LINEAR' and target['path']=='rotation':
                value=Slerp(keys,Rotation.from_quat(out))(t).as_quat()
            elif mode=='LINEAR':
                value=np.stack([np.interp(t,keys,col) for col in out.T],axis=1)
            elif mode=='STEP':
                value=out[np.maximum(0,np.searchsorted(keys,t,side='right')-1)]
            else:
                raise ValueError(mode)
            trs[target['path']][:,target['node']]=value
        n=len(self.nodes)
        local=np.zeros((len(times),n,4,4))
        local[:,:,:,3]=np.pad(trs['translation'],((0,0),(0,0),(0,1)),constant_values=1)
        local[:,:,:3,:3]=Rotation.from_quat(trs['rotation'].reshape(-1,4)).as_matrix().reshape(
            len(times),n,3,3)*trs['scale'][:,:,None,:]
        for i, node in enumerate(self.nodes):
            if 'matrix' in node:
                local[:,i]=np.asarray(node['matrix']).reshape(4,4).T
        glob={}
        def get(i):
            if i not in glob:
                glob[i] = get(self.parents[i]) @ local[:,i] if i in self.parents else local[:,i]
            return glob[i]
        joints=np.stack([get(i) for i in self.bones],axis=1)
        return times, joints, (joints @ self.bind).astype(np.float32)

    def skinned_positions(self, mats):
        xyz=np.zeros((len(self.verts),3),np.float32)
        for slot in range(self.idx.shape[1]):
            transformed=np.einsum('nij,nj->ni',mats[self.idx[:,slot],:3,:],self.verts)
            xyz+=transformed*self.weights[:,slot,None]
        return xyz

def main(before,after,output):
    a,b=Model(before),Model(after)
    data = dict(baseline_sha256=a.hash, candidate_sha256=b.hash,
                bone_count=len(b.bones), vertices=len(b.verts),
                checks={}, clips={})
    checks=data['checks']
    for key in ('nodes','skins','animations','meshes','scenes'):
        checks[key+'_definition_identical']=a.g[key]==b.g[key]
    checks['same_bone_names']=[a.nodes[i]['name'] for i in a.bones]==[b.nodes[i]['name'] for i in b.bones]
    for name in sorted(set(a.attrs)|set(b.attrs)):
        checks[name+'_identical']=name in a.attrs and name in b.attrs and np.array_equal(a.attrs[name],b.attrs[name])
    checks['triangle_indices_identical']=np.array_equal(a.read(a.surface['indices']),b.read(b.surface['indices']))
    checks['inverse_binds_identical']=np.array_equal(a.bind,b.bind)
    for aa,bb in zip(a.g['animations'],b.g['animations'],strict=True):
        ta,ja,sa=a.clip(aa)
        tb,jb,sb=b.clip(bb)
        assert np.array_equal(ta,tb) and aa['name']==bb['name']
        drift=0.0; h1=hashlib.sha256();h2=hashlib.sha256()
        for ma,mb in zip(sa,sb,strict=True):
            va=a.skinned_positions(ma); vb=b.skinned_positions(mb)
            drift=max(drift, float(np.abs(va-vb).max()))
            h1.update(va.tobytes());h2.update(vb.tobytes())
        data['clips'][aa['name']] = dict(seconds=float(ta[-1]),poses=len(ta),
             joint_matrix_max_component_difference=float(np.abs(ja-jb).max()),
             max_skinned_vertex_component_difference_m=drift,
             baseline_skinned_vertices_sha256=h1.hexdigest(),candidate_skinned_vertices_sha256=h2.hexdigest())
    data['passed']=all(checks.values()) and all(
        r['max_skinned_vertex_component_difference_m']==0 and r['joint_matrix_max_component_difference']==0
        for r in data['clips'].values())
    output.write_text(json.dumps(data,indent=2)+'\n')
    if not data['passed']:raise SystemExit(1)

if __name__=='__main__':
    main(*(Path(v) for v in sys.argv[1:]))
