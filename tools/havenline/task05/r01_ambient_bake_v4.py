"""Deterministic R01 vertex-occlusion authoring; NumPy only, no runtime shader.
Twenty-four cosine-weighted rays per vertex intersect the complete closed mesh.
Short-range contact shading is geometry-bound, with flames kept unoccluded.
This is asset preparation, not a visual approval or a physical FPS measurement.
"""
from __future__ import annotations
import hashlib,math
import numpy as np

GEOMETRY_SHA256='7c2ca939d271e1cbe5666757d76582f417f6c763d8ed1998264b08a92b82e1a0'
VERTEX_COUNT=14486
RAY_COUNT=24
MAX_DISTANCE=.24
SURFACE_BIAS=.003
OCCLUSION_STRENGTH=.40


def geometry_digest(model):
    h=hashlib.sha256()
    for part in model.parts:
        h.update(part.name.encode()+b'\0')
        h.update(np.asarray(part.vertices,dtype='<f4').tobytes())
        h.update(np.asarray(part.faces,dtype='<i4').tobytes())
    return h.hexdigest()


def bake_values(model):
    vertices=np.concatenate([p.vertices for p in model.parts])
    normals=np.concatenate([p.normals for p in model.parts])
    triangles=np.concatenate([p.vertices[p.faces] for p in model.parts])
    low=triangles.min(axis=1);high=triangles.max(axis=1);centres=(low+high)*.5
    nodes=[]
    def make_node(ids):
        index=len(nodes);nodes.append(None)
        lo=low[ids].min(0);hi=high[ids].max(0)
        if len(ids)<=10:
            nodes[index]=(lo,hi,-1,-1,ids)
        else:
            axis=int(np.argmax(np.ptp(centres[ids],axis=0)))
            ids=ids[np.argsort(centres[ids,axis],kind='stable')];mid=len(ids)//2
            left=make_node(ids[:mid]);right=make_node(ids[mid:])
            nodes[index]=(lo,hi,left,right,None)
        return index
    make_node(np.arange(len(triangles)))
    helper=np.zeros_like(normals);helper[:,1]=1.
    helper[np.abs(normals[:,1])>.9]=[1.,0.,0.]
    tangent=np.cross(helper,normals)
    tangent/=np.linalg.norm(tangent,axis=1,keepdims=True)
    bitangent=np.cross(normals,tangent)
    j=np.arange(RAY_COUNT,dtype=float);u=(j+.5)/RAY_COUNT;angle=j*2.399963229728653
    hemisphere=np.stack((np.cos(angle)*np.sqrt(u),np.sin(angle)*np.sqrt(u),np.sqrt(1.-u)),axis=1)
    directions=(tangent[:,None,:]*hemisphere[None,:,0,None]+
                bitangent[:,None,:]*hemisphere[None,:,1,None]+
                normals[:,None,:]*hemisphere[None,:,2,None]).reshape(-1,3)
    origins=np.repeat(vertices+normals*SURFACE_BIAS,RAY_COUNT,axis=0)
    parallel=np.abs(directions)<1e-12
    inverse=np.divide(1.,directions,out=np.zeros_like(directions),where=~parallel)
    occluded=np.zeros(len(origins),dtype=bool)
    p0=triangles[:,0];e1=triangles[:,1]-p0;e2=triangles[:,2]-p0
    stack=[(0,np.arange(len(origins)))]
    while stack:
        node,ids=stack.pop()
        ids=ids[~occluded[ids]]
        if not len(ids):continue
        lo,hi,left,right,face_ids=nodes[node]
        o=origins[ids];inv=inverse[ids];par=parallel[ids]
        near=(lo-o)*inv;far=(hi-o)*inv
        tmin=np.where(par,-np.inf,np.minimum(near,far)).max(1)
        tmax=np.where(par,np.inf,np.maximum(near,far)).min(1)
        outside=(par & ((o<lo)|(o>hi))).any(1)
        ids=ids[(~outside)&(np.maximum(tmin,0.)<=np.minimum(tmax,MAX_DISTANCE))]
        if not len(ids):continue
        if left>=0:
            stack.append((left,ids));stack.append((right,ids));continue
        # Keep intermediate allocations bounded, even for a broad coplanar leaf.
        for start in range(0,len(ids),2048):
            chunk=ids[start:start+2048];d=directions[chunk,None,:];o=origins[chunk,None,:]
            a=e1[face_ids][None,:,:];b=e2[face_ids][None,:,:]
            h=np.cross(d,b);det=np.sum(a*h,axis=2)
            valid=np.abs(det)>=1e-11
            invdet=np.divide(1.,det,out=np.zeros_like(det),where=valid)
            s=o-p0[face_ids][None,:,:];uv=np.sum(s*h,axis=2)*invdet
            q=np.cross(s,a);vv=np.sum(d*q,axis=2)*invdet
            distance=np.sum(b*q,axis=2)*invdet
            hits=valid&(uv>=0.)&(uv<=1.)&(vv>=0.)&(uv+vv<=1.)&(distance>.0002)&(distance<MAX_DISTANCE)
            occluded[chunk]=hits.any(1)
    values=1.-OCCLUSION_STRENGTH*occluded.reshape(len(vertices),RAY_COUNT).mean(1)
    offset=0
    for part in model.parts:
        if 'flame' in part.name or 'ember_coal' in part.name:
            values[offset:offset+len(part.vertices)]=1.
        offset+=len(part.vertices)
    return np.rint(values*255).astype(np.uint8)


def apply_baked_occlusion(model):
    if geometry_digest(model)!=GEOMETRY_SHA256:
        raise ValueError('R01 occlusion bake is not bound to current geometry')
    values=bake_values(model)
    if len(values)!=VERTEX_COUNT or values.min()<153:
        raise ValueError('Invalid R01 occlusion bake')
    offset=0
    for part in model.parts:
        count=len(part.vertices)
        part.colors[:,:3]*=values[offset:offset+count,None]/255.0
        offset+=count
    assert offset==len(values)
