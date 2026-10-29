#!/usr/bin/env python3
"""T05 R38: watertight, source-image textured MULTI-VIEW geometry proof.

Photocarving + original-pixel UV projection from 3 real renders. No AI invented
texture, no manually assembled model and NO assertion of source-fidelity/approval.
The geometry remains fused; unobserved side fails, hence non-shipping only.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from skimage.measure import marching_cubes
from PIL import Image
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial

LOCKED={
 "32451.jpg":"70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4",
 "32450.jpg":"5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719",
 "32441.png":"0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510"}
VIEWS={'front':('32451.jpg',30.,15.,175),
       'right':('32450.jpg',90.,7.,160),
       'rear':('32441.png',180.,7.,137)}
def run(refs,out):
    refs=Path(refs);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cameras={}
    for name,(filename,az,el,cut) in VIEWS.items():
        original=refs/filename
        sha=hashlib.sha256(original.read_bytes()).hexdigest()
        assert sha==LOCKED[filename],f'Wrong owner source: {filename}'
        rgb=np.asarray(Image.open(original).convert('RGB'))
        H,W=rgb.shape[:2]
        fg=rgb.max(axis=2)>28;fg[:cut]=False # no animated smoke geometry
        labels,_=ndi.label(fg)
        counts=np.bincount(labels.ravel());counts[0]=0
        fg=ndi.binary_fill_holes(ndi.binary_closing(labels==counts.argmax(),iterations=3))
        y,x=np.nonzero(fg)
        assert len(x)>30000,(name,len(x))
        bounds=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))
        theta=np.deg2rad(az);phi=np.deg2rad(el)
        look=np.array([np.sin(theta)*np.cos(phi),np.sin(phi),np.cos(theta)*np.cos(phi)])
        right=np.cross([0,1,0],look);right/=np.linalg.norm(right)
        up=np.cross(look,right);up/=np.linalg.norm(up)
        centers=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
        scales=((bounds[2]-bounds[0])/(4.1 if name!='right' else 3.0),(bounds[3]-bounds[1])/3.05)
        cameras[name]=dict(mask=fg,rgb=rgb,width=W,height=H,bounds=bounds,look=look,right=right,up=up,center=centers,scale=scales)
        Image.fromarray(fg.astype('uint8')*255).save(out/(name+'_source_mask.png'))
    xs=np.linspace(-2.2,2.2,175,dtype=np.float32)
    ys=np.linspace(0,3.1,130,dtype=np.float32)
    zs=np.linspace(-1.6,1.6,120,dtype=np.float32)
    X,Y,Z=np.meshgrid(xs,ys,zs,indexing='ij')
    hull=np.ones(X.shape,bool)
    for name,c in cameras.items():
        right,up=c['right'],c['up']
        px=X*right[0]+(Y-1.55)*right[1]+Z*right[2]
        py=X*up[0]+(Y-1.55)*up[1]+Z*up[2]
        u=np.rint(c['center'][0]+px*c['scale'][0]).astype(np.int32)
        v=np.rint(c['center'][1]-py*c['scale'][1]).astype(np.int32)
        valid=(u>=0)&(u<c['width'])&(v>=0)&(v<c['height'])
        observed=np.zeros(hull.shape,bool);observed[valid]=c['mask'][v[valid],u[valid]]
        hull&=observed
    assert hull.sum()>1000,'Original views cannot be carved with these uncalibrated camera assumptions'
    scalar=np.pad(ndi.gaussian_filter(hull.astype('float32'),.7),2)
    pitch=(xs[1]-xs[0],ys[1]-ys[0],zs[1]-zs[0])
    verts,faces,_,_=marching_cubes(scalar,.48,spacing=pitch)
    verts+=np.array([xs[0]-2*pitch[0],ys[0]-2*pitch[1],zs[0]-2*pitch[2]])
    raw=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
    raw.fix_normals()
    assert raw.is_watertight
    strengths=np.column_stack([np.maximum(0,raw.face_normals@c['look']) for c in cameras.values()])
    which=np.argmax(strengths,axis=1)
    scene=trimesh.Scene()
    for idx,(name,c) in enumerate(cameras.items()):
        original=raw.faces[np.where(which==idx)[0]]
        vertex_ids,remapped=np.unique(original.ravel(),return_inverse=True)
        xyz=raw.vertices[vertex_ids]
        px=(xyz-np.array([0,1.55,0]))@c['right']
        py=(xyz-np.array([0,1.55,0]))@c['up']
        u=(c['center'][0]+px*c['scale'][0])/(c['width']-1)
        v=1-(c['center'][1]-py*c['scale'][1])/(c['height']-1)
        uv=np.clip(np.column_stack((u,v)),0,1)
        texture=Image.fromarray(c['rgb'])
        mat=PBRMaterial(name='OWNER_SOURCE_'+name,baseColorTexture=texture,metallicFactor=0,roughnessFactor=1,doubleSided=True)
        part=trimesh.Trimesh(vertices=xyz,faces=remapped.reshape(-1,3),process=False,
            visual=TextureVisuals(uv=uv,material=mat))
        scene.add_geometry(part,node_name=name+'_owner_source',geom_name=name+'_owner_image_projection')
    glb=out/'T05_R38_SOURCE_PROJECTED_UNAPPROVED.glb'
    glb.write_bytes(scene.export(file_type='glb'))
    audit={'status':'ACTUAL_THREE_OWNER_IMAGES_PROJECTED_TO_WATERTIGHT_3D__ART_CRITIC_FAIL',
        'owner_original_sha256':LOCKED,'model_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
        'triangles':len(raw.faces),'watertight':True,
        'material_original_image_count':3,'camera_poses_calibrated':False,
        'geometry_has_separate_saw_meat_wood_snow_components':False,
        'hidden_left_reference_exists':False,'source_video_motion_complete':False,
        'art_critic_passed':False,'owner_approved':False,'shipping_asset_modified':False,
        'warning':'Source view appearance can resemble originals, but orbit reveals missing volume, seams, and undefined hidden surfaces. NEVER ship as the actual finished cooker.'}
    (out/'STATUS.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))
    return glb
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-dir',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.source_dir,a.out)
