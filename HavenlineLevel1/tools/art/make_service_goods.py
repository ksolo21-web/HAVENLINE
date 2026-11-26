"""Rebuild hand-sized service props from the eight reviewed turnaround photographs.

Run with the cooked-game-meat sheet, money sheet, and output directory.
The eight calibrated silhouettes constrain one solid surface. Each face samples
the outside view facing its normal. No backdrop, contact shadow or sheet label
becomes part of the model.
"""
import argparse
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

CORNERS = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
TETRAHEDRA = [[0,5,1,6],[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6]]


def segment(sheet):
    rgb = np.asarray(Image.open(sheet).convert("RGB"))
    height,width = rgb.shape[:2]
    views = []
    for row in range(2):
        for col in range(4):
            top,bottom = ((.16,.41) if row == 0 else (.54,.80))
            crop = rgb[round(height*top):round(height*bottom),round(width*(col+.035)/4):round(width*(col+.965)/4)]
            r,g,b = crop.astype(float).transpose(2,0,1)
            mask = (np.maximum(r,g) > 1.10*b) & (np.maximum(r,g) > 40)
            ids,n = ndimage.label(mask)
            mask = ndimage.binary_fill_holes(ids == np.bincount(ids.ravel())[1:].argmax()+1)
            ys,xs = np.nonzero(mask)
            sl = np.s_[ys.min():ys.max()+1,xs.min():xs.max()+1]
            mask = np.pad(mask[sl],4)
            paint = np.pad(crop[sl],((4,4),(4,4),(0,0)),mode="edge")
            interior = ndimage.binary_erosion(mask,iterations=2)
            nearest = ndimage.distance_transform_edt(~interior,return_distances=False,return_indices=True)
            views.append((ndimage.distance_transform_edt(mask)-ndimage.distance_transform_edt(~mask),paint[tuple(nearest)]))
    return views


def surface(samples,grid,step):
    # March only cubes that straddle the zero-isosurface. Adjacent tetrahedra
    # use a common vertex where they cross the same grid edge.
    cells = [samples[x:x+samples.shape[0]-1,y:y+samples.shape[1]-1,z:z+samples.shape[2]-1] for x,y,z in CORNERS]
    active = np.argwhere((np.min(cells,axis=0)<0) & (np.max(cells,axis=0)>=0))
    vertices,triangles,edges = [],[],{}
    for start in active:
        pts = start + CORNERS
        vals = samples[tuple(pts.T)]
        indices = np.ravel_multi_index(pts.T,samples.shape)
        def cross(a,b):
            key=tuple(sorted((indices[a],indices[b])))
            if key not in edges:
                t=vals[a]/(vals[a]-vals[b])
                edges[key]=len(vertices)
                vertices.append(grid+step*(pts[a]+t*(pts[b]-pts[a])))
            return edges[key]
        for ids in TETRAHEDRA:
            on = [v for v in ids if vals[v]>=0]
            off = [v for v in ids if vals[v]<0]
            if not on or not off:
                continue
            points = [cross(a,b) for a in on for b in off]
            if len(points)==4:
                triangles.extend([[points[0],points[1],points[3]],[points[0],points[3],points[2]]])
            else:
                triangles.append(points)
    p=np.array(vertices)
    # Orient outward using the gradient of the fitted signed distance field.
    f=np.array(triangles)
    gradient=np.gradient(samples)
    coords=((p-grid)/step).T
    n=-np.stack([ndimage.map_coordinates(c,coords,order=1,mode="nearest") for c in gradient],axis=1)
    n/=np.maximum(1e-10,np.linalg.norm(n,axis=1,keepdims=True))
    sign=np.einsum("ij,ij->i",np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),n[f[:,0]])
    f[sign<0]=f[sign<0][:,[0,2,1]]
    return p,n,f


def blended_tile(p,n,faces,view,observations):
    # Reproject each atlas texel into all eight views. Weighting by its surface
    # normal avoids abrupt color seams along the corners of the bills and roast.
    _,project,source = observations[view]
    v,u=project(p)
    h,w=source.shape[:2]
    uv=np.column_stack((.5+u/(w-1)*255,.5+v/(h-1)*255))
    world=np.zeros((256,256,3)); normal=np.zeros_like(world); filled=np.zeros((256,256),bool)
    for face in faces:
        a,b,c=uv[face]
        x0,y0=np.maximum(0,np.floor(np.minimum(np.minimum(a,b),c)).astype(int))
        x1,y1=np.minimum(255,np.ceil(np.maximum(np.maximum(a,b),c)).astype(int))
        ab=b-a;ac=c-a;den=ab[0]*ac[1]-ab[1]*ac[0]
        if abs(den)<1e-7:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
        dx=xx+.5-a[0];dy=yy+.5-a[1]
        wb=(dx*ac[1]-dy*ac[0])/den;wc=(ab[0]*dy-ab[1]*dx)/den;wa=1-wb-wc
        inside=(wa>=0)&(wb>=0)&(wc>=0)
        ys,xs=yy[inside],xx[inside]
        weights=np.column_stack((wa[inside],wb[inside],wc[inside]))
        world[ys,xs]=weights@p[face];normal[ys,xs]=weights@n[face];filled[ys,xs]=True
    xyz=world[filled];normals=normal[filled]
    if len(xyz)==0:return Image.fromarray(source).resize((256,256),Image.Resampling.LANCZOS)
    normals/=np.maximum(1e-8,np.linalg.norm(normals,axis=1,keepdims=True))
    colors=np.zeros_like(xyz);weights=np.zeros(len(xyz))
    for cam,mapper,paint in observations:
        coords=mapper(xyz);weight=np.maximum(.015,normals@cam)**8
        rgb=np.stack([ndimage.map_coordinates(paint[:,:,c].astype(float),coords,order=1,mode="nearest") for c in range(3)],axis=1)
        colors+=rgb*weight[:,None];weights+=weight
    tile=np.zeros((256,256,3),np.uint8);tile[filled]=(colors/weights[:,None]).clip(0,255).astype(np.uint8)
    nearest=ndimage.distance_transform_edt(~filled,return_distances=False,return_indices=True)
    return Image.fromarray(tile[tuple(nearest)])


def make(sheet,width,dimensions,elevation,power,out):
    views=segment(sheet)
    depth,height=dimensions
    base=np.array([-.57,-.10,-depth*.62])
    step=.037
    shape=np.ceil((np.array([.57,height+.10,depth*.62])-base)/step).astype(int)
    grid=np.stack(np.meshgrid(*[base[i]+np.arange(shape[i])*step for i in range(3)],indexing="ij"),axis=-1)
    # Calibrate each photograph independently to the common known object width.
    # Use the projected envelope of a rounded rectangular stack or a roast.
    xyz=np.linspace(-1,1,101)
    x,z=np.meshgrid(xyz,xyz)
    inside=abs(x)**power+abs(z)**power<=1.0001
    bound=np.column_stack((x[inside]*.5,np.zeros(inside.sum()),z[inside]*depth*.5))
    shapes=[bound.copy(),bound.copy()]
    shapes[1][:,1]=height
    corners=np.concatenate(shapes)
    calibrated=[]
    distances=[]
    phi=np.radians(elevation)
    for i,(sdf,paint) in enumerate(views):
        a=i*np.pi/4
        side=np.array([np.cos(a),0,-np.sin(a)])
        up=np.array([-np.sin(a)*np.sin(phi),np.cos(phi),-np.cos(a)*np.sin(phi)])
        cam=np.cross(side,up)
        xlim=corners@side; ylim=corners@up
        def mapper(points,side=side,up=up,xlim=xlim,ylim=ylim,w=sdf.shape[1],h=sdf.shape[0]):
            u=4+(points@side-xlim.min())/(xlim.max()-xlim.min())*(w-9)
            v=4+(ylim.max()-points@up)/(ylim.max()-ylim.min())*(h-9)
            return np.stack((v,u))
        distances.append(ndimage.map_coordinates(sdf,mapper(grid),order=1,mode="constant",cval=-20))
        calibrated.append((cam,mapper,paint))
    field=ndimage.gaussian_filter(np.min(distances,axis=0),.54)
    p,n,f=surface(field,base,step)
    # Project the actual photographs onto the fitted surface. At each triangle,
    # use the facing observation so artwork on the top, ends and back survives.
    cameras=np.stack([cam for cam,_,_ in calibrated])
    camera_index=np.argmax(np.mean(n[f],axis=1)@cameras.T,axis=1)
    atlas=Image.new("RGB",(1024,512))
    ps,ns,uvs,faces=[],[],[],[]
    for i,(_,project,paint) in enumerate(calibrated):
        xy=(i%4*256,i//4*256)
        part=f[camera_index==i]
        atlas.paste(blended_tile(p,n,part,i,calibrated),xy)
        if not len(part): continue
        used,remap=np.unique(part.ravel(),return_inverse=True)
        v,u=project(p[used]); h,w=paint.shape[:2]
        uv=np.column_stack(((xy[0]+.5+u/(w-1)*255)/1024,(xy[1]+.5+v/(h-1)*255)/512))
        faces.append(remap.reshape(-1,3)+sum(len(points) for points in ps))
        ps.append(p[used]);ns.append(n[used]);uvs.append(uv)
    p=np.concatenate(ps); p[:,1]-=p[:,1].min();p*=width/np.ptp(p[:,0])
    export(out,p,np.concatenate(ns),np.concatenate(faces),np.concatenate(uvs),atlas)


def export(path,p,n,f,uv,atlas):
    arrays=[p.astype('<f4'),n.astype('<f4'),uv.astype('<f4'),f.astype('<u2').ravel()]
    access=[];views=[];binary=bytearray()
    for i,arr in enumerate(arrays):
        start=len(binary);data=arr.tobytes(); binary.extend(data);binary.extend(bytes((-len(binary))%4))
        views.append(dict(buffer=0,byteOffset=start,byteLength=len(data),target=(34963 if i==3 else 34962)))
        ac=dict(bufferView=i,componentType=[5126,5126,5126,5123][i],count=len(arr),type=['VEC3','VEC3','VEC2','SCALAR'][i])
        if i==0: ac.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
        access.append(ac)
    buff=io.BytesIO();atlas.save(buff,format='JPEG',quality=92,subsampling=0);data=buff.getvalue()
    views.append(dict(buffer=0,byteOffset=len(binary),byteLength=len(data)));binary.extend(data);binary.extend(bytes((-len(binary))%4))
    obj=dict(asset=dict(version="2.0",generator="Havenline service turnaround reconstruction"),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0,name=path.stem)],meshes=[dict(primitives=[dict(attributes=dict(POSITION=0,NORMAL=1,TEXCOORD_0=2),indices=3,material=0)])],materials=[dict(name="Painted "+path.stem,pbrMetallicRoughness=dict(metallicFactor=0,roughnessFactor=.77,baseColorTexture=dict(index=0)))],images=[dict(name=path.stem+"_paint",bufferView=4,mimeType="image/jpeg")],textures=[dict(source=0)],accessors=access,bufferViews=views,buffers=[dict(byteLength=len(binary))])
    data=json.dumps(obj,separators=(',',':')).encode(); data+=b' '*((-len(data))%4)
    (path.parent/(path.stem+"_"+path.stem+"_paint.jpg")).write_bytes(buff.getvalue())
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(data)+len(binary))+struct.pack('<I4s',len(data),b'JSON')+data+struct.pack('<I4s',len(binary),b'BIN\0')+binary)
    print(path,len(p),len(f))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("roast");parser.add_argument("money");parser.add_argument("out",type=Path)
    args=parser.parse_args()
    make(args.roast,.44,(.55,.52),13,2,args.out/'cooked_game_meat.glb')
    make(args.money,.35,(.49,.30),23,7,args.out/'banded_notes.glb')
