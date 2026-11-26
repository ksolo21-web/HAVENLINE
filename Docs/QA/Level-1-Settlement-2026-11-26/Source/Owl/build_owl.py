"""Make the field owl from the selected Havenline eight-view board and author its flight wings."""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.measure import marching_cubes

H = .68
ANGLES = np.arange(8)*np.pi/4
class GLB:
    def __init__(self):
        self.binary=bytearray()
        self.doc=dict(asset=dict(version="2.0",generator="Havenline expedition owl sculpt and flight articulation"),scene=0,
                      scenes=[dict(nodes=[0])],nodes=[],meshes=[],materials=[],textures=[],images=[],buffers=[],bufferViews=[],accessors=[])
    def blob(self,data):
        start=len(self.binary)
        self.binary.extend(data)
        self.binary.extend(b'\0'*(-len(self.binary)%4))
        entries=self.doc["bufferViews"]
        entries.append(dict(buffer=0,byteOffset=start,byteLength=len(data)))
        return len(entries)-1
    def acc(self,data,typ,ctype):
        data=np.ascontiguousarray(data,dtype="<f4" if ctype==5126 else "<u4")
        entry=dict(bufferView=self.blob(data.tobytes()),componentType=ctype,count=len(data),type=typ)
        if typ=="VEC3":
            entry.update(min=data.min(0).tolist(),max=data.max(0).tolist())
        self.doc["accessors"].append(entry)
        return len(self.doc["accessors"])-1
    def mesh(self,name,vertices,faces,normals,uv):
        self.doc["meshes"].append(dict(name=name,primitives=[dict(attributes=dict(
               POSITION=self.acc(vertices,"VEC3",5126),NORMAL=self.acc(normals,"VEC3",5126),TEXCOORD_0=self.acc(uv,"VEC2",5126)),
               indices=self.acc(np.array(faces).reshape(-1),"SCALAR",5125),material=0)]))
        return len(self.doc["meshes"])-1
    def node(self,name,parent=None,xyz=None,mesh=None):
        nd=dict(name=name)
        if xyz is not None: nd["translation"]=list(xyz)
        if mesh is not None: nd["mesh"]=mesh
        index=len(self.doc["nodes"])
        self.doc["nodes"].append(nd)
        if parent is not None:self.doc["nodes"][parent].setdefault("children",[]).append(index)
        return index
    def save(self,path,atlas):
        im=io.BytesIO();atlas.save(im,format="JPEG",quality=96,subsampling=0)
        self.doc["images"]=[dict(name="OwlEightViewPlumage",bufferView=self.blob(im.getvalue()),mimeType="image/jpeg")]
        self.doc["textures"]=[dict(source=0)]
        self.doc["materials"]=[dict(name="Expedition plumage, eyes and leather",pbrMetallicRoughness=dict(baseColorTexture=dict(index=0),roughnessFactor=.9,metallicFactor=0),doubleSided=True)]
        self.doc["buffers"]=[dict(byteLength=len(self.binary))]
        meta=json.dumps(self.doc,separators=(',',':')).encode();meta+=b' '*(-len(meta)%4)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(meta)+len(self.binary))+struct.pack('<I4s',len(meta),b'JSON')+meta+struct.pack('<I4s',len(self.binary),b'BIN\0')+self.binary)

def views_from(sheet):
    views=[]
    for i in range(8):
        row,col=divmod(i,4); low,high=[(70,450),(495,882)][row]
        tile=sheet[low:high,384*col+10:384*(col+1)-10]
        bg=np.median(np.concatenate([tile[:,4:15],tile[:,-15:-4]],axis=1),axis=1)[:,None,:]
        dif=tile.astype(float)-bg
        mask=((dif[:,:,0]>14)|(dif[:,:,1]>22)|(dif[:,:,2]>35))&(np.linalg.norm(dif,axis=2)>29)
        mask[int(.84*len(mask)):,:] &= ((tile[:,:,0].astype(float)-tile[:,:,2])>-5)[int(.84*len(mask)):,:]
        labels,n=ndimage.label(ndimage.binary_closing(mask,iterations=2));sizes=np.bincount(labels.ravel());sizes[0]=0
        mask=ndimage.binary_fill_holes(labels==np.argmax(sizes))
        yy,xx=np.nonzero(mask);top,bottom=yy.min(),yy.max()
        # Anchor near the ankle, away from the trailing tail and the forward talon tips.
        head=xx[(yy>top+.15*(bottom-top))&(yy<top+.21*(bottom-top))]
        feet=xx[(yy>bottom-.045*(bottom-top))&(yy<bottom)]
        center=np.median(head)*.52+np.median(feet)*.48
        dist=ndimage.distance_transform_edt(mask)-ndimage.distance_transform_edt(~mask)
        _,nearest=ndimage.distance_transform_edt(~mask,return_indices=True)
        views.append(dict(pixels=(bottom-top)/H,center=center,bottom=bottom,dist=dist,
                          rgb=tile[nearest[0],nearest[1]],mask=mask,low=low,left=384*col+10))
    return views

def project(p,v,i):
    return v['center']+v['pixels']*(p[:,0]*np.cos(ANGLES[i])-p[:,2]*np.sin(ANGLES[i])),v['bottom']-v['pixels']*p[:,1]

def body(g,v):
    pitch=.0074
    axes=[np.arange(-.35,.36,pitch),np.arange(-.028,.71,pitch),np.arange(-.45,.31,pitch)]
    grid=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1);p=grid.reshape(-1,3)
    fields=[]
    for i,view in enumerate(v):
        u,y=project(p,view,i)
        fields.append(ndimage.map_coordinates(view['dist'],[y,u],order=1,mode='constant',cval=-60).reshape(grid.shape[:-1])/view['pixels'])
    # Keep individual ear tufts and toe tips despite the small asymmetries between the drawings.
    ordered=np.sort(np.stack(fields),axis=0)
    sdf=ndimage.gaussian_filter(.58*ordered[0]+.32*ordered[1]+.10*ordered[2],.62)
    pts,faces,normals,_=marching_cubes(sdf,0,spacing=(pitch,)*3,gradient_direction='descent',allow_degenerate=False)
    pts+=np.array([a[0] for a in axes])
    faces=faces[:,::-1].copy()
    ctr=pts[faces].mean(axis=1)
    normals_at_face=normals[faces].mean(axis=1)
    radial=ctr[:,[0,2]].copy();radial[:,1]+=.028
    radial/=np.maximum(.001,np.linalg.norm(radial,axis=1,keepdims=True))
    dirs=np.stack([np.sin(ANGLES),np.cos(ANGLES)],axis=1)
    vote=(.69*radial+.31*normals_at_face[:,[0,2]])@dirs.T
    # The front camera best preserves the eye, brow and beak relationship.
    front=((ctr[:,1]>.49)&(ctr[:,2]>.019)&(abs(ctr[:,0])<.118))
    vote[front,0]+=.36
    which=np.argmax(vote,axis=1)
    # Horizontal board cameras have no top view. Explicit dorsal maps use the crown and
    # snow-dusted blue bedroll from the back drawing, preserving both from the gameplay camera.
    crown=(ctr[:,1]>.575)&(normals_at_face[:,1]>.72)&(ctr[:,2]>-.145)&((ctr[:,2]<.028)|(ctr[:,1]>.626))
    roll=(ctr[:,1]>.475)&(ctr[:,1]<.540)&(ctr[:,2]<-.105)&(normals_at_face[:,1]>.77)
    which[crown]=8
    which[roll]=9
    unique,remap=np.unique((faces*10+which[:,None]).ravel(),return_inverse=True)
    vi=unique//10;src=unique%10;uv=np.zeros((len(vi),2))
    for i,view in enumerate(v):
        mask=(src==i);u,y=project(pts[vi[mask]],view,i)
        uv[mask]=np.column_stack([(view['left']+u+.5)/1536,(view['low']+y+.5)/1024])
    for chart in [8,9]:
        mask=(src==chart);c=pts[vi[mask]];x,y,z=c.T
        if chart==8:
            u=181-x*345
            yy=65+z*165
            safe_width=np.clip((yy-34)*1.35+22,24,53)
            uv[mask,0]=(10+181+np.clip(u-181,-safe_width,safe_width))/1536
            uv[mask,1]=(495+np.clip(yy,40,88))/1024
        else:
            uv[mask,0]=(10+np.clip(182-x*496,86,277))/1536
            uv[mask,1]=(495+np.clip(114+(z+.165)*148,105,131))/1024
    mesh=g.mesh("Owl with blue bedroll, talons and harness",pts[vi],remap,normals[vi],uv)
    c=pts[vi];x,y,z=c.T
    # Local flight flexion brings the feathered shanks and talons up and aft.
    # Returning to zero on a dive re-extends the feet for the physical strike.
    weight=np.clip((.218-y)/.132,0,1)*np.clip((z+.168)/.11,0,1)
    weight=weight*weight*(3-2*weight)
    delta=np.zeros_like(c);delta[:,1]=weight*(.085+.08*np.maximum(0,z));delta[:,2]=-weight*.106
    g.doc['meshes'][mesh]['primitives'][0]['targets']=[dict(POSITION=g.acc(delta,"VEC3",5126))]
    g.doc['meshes'][mesh]['extras']={'targetNames':['FlightTalons']}
    g.doc['meshes'][mesh]['weights']=[0.]
    g.node("EightViewOwl",0,mesh=mesh)

def mantle(g,parent,side,name,length,sweep):
    p=[];uv=[];fi=[]
    for row in range(9):
        t=row/8
        for col in range(9):
            w=col/8
            x=length*t
            z=.061-.147*w + sweep*t
            y=.012+.023*np.sin(w*np.pi)-.012*w*w+.003*t
            p.append([side*x,y,z])
            # One coherent band of shoulder plumage across each panel.
            u=171+52*t+24*w
            yy=225+65*w+13*t
            uv.append([(780+u)/1536,(58+yy)/1024])
    for row in range(8):
        for col in range(8):
            a=row*9+col
            fi.extend([[a,a+9,a+1],[a+1,a+9,a+10]])
    p=np.array(p);fi=np.array(fi)
    if np.cross(p[fi[0,1]]-p[fi[0,0]],p[fi[0,2]]-p[fi[0,0]])[1]<0:fi=fi[:,::-1]
    n=np.zeros_like(p);fn=np.cross(p[fi[:,1]]-p[fi[:,0]],p[fi[:,2]]-p[fi[:,0]])
    for i in range(3):np.add.at(n,fi[:,i],fn)
    n/=np.maximum(1e-12,np.linalg.norm(n,axis=1,keepdims=True))
    g.node(name,parent,mesh=g.mesh(name,p,fi,n,uv))

def ear_tuft(g,side):
    vertices=[];faces=[];uv=[]
    for i,offset in enumerate([-.020,.0,.017]):
        base=np.array([side*(.088+offset),.606,-.027+offset*.42])
        tip=np.array([side*(.150+offset*.70),[.673,.692,.683][i],-.050+offset*.58])
        # Layer three pointed feathers around the folded crown. The upper inner vane
        # uses the dark tip and buff outside border painted on the exact front ear.
        for j,t in enumerate([0.,.23,.49,.74,1.]):
            point=base*(1-t)+tip*t
            w=(1-t)**.71*.020+0.0002
            for k in range(10):
                a=2*np.pi*k/10
                vertices.append(point+[side*w*np.cos(a),0,w*.64*np.sin(a)])
                u=180+(1 if side>0 else -1)*(44+17*t+7*np.cos(a)*(1-t))
                yy=47-29*t+3*np.sin(a)
                uv.append([(10+u)/1536,(70+yy)/1024])
            if j:
                lo=i*50+(j-1)*10
                for k in range(10):
                    n=(k+1)%10
                    faces.extend([[lo+k,lo+10+k,lo+n],[lo+n,lo+10+k,lo+10+n]])
    p=np.array(vertices);f=np.array(faces)
    if side<0:f=f[:,::-1]
    n=np.zeros_like(p);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    for j in range(3):np.add.at(n,f[:,j],fn)
    n/=np.maximum(1e-12,np.linalg.norm(n,axis=1,keepdims=True))
    g.node("CrownEar"+("R" if side>0 else "L"),0,mesh=g.mesh("Layered ear tuft",p,f,n,uv))

def make_feathers(g,parent,side,name,designs):
    vert=[];uv=[];faces=[]
    # Curved feather vanes have two real faces, a raised rachis, a rounded shoulder and a pointed tip.
    sections=[.0,.11,.23,.40,.60,.78,.91,1.]
    for i,(base,tip,width) in enumerate(designs):
        start=len(vert);base=np.asarray(base);tip=np.asarray(tip)
        direction=tip-base
        cross=np.array([-direction[2],0,direction[0]]);cross/=np.linalg.norm(cross)
        cx,cy=[(196,239),(225,249),(241,282),(213,264),(271,288)][i%5]
        for t in sections:
            width_here=width*(.08+.92*np.sin(np.pi*(t**.85))**.66)
            center=base+t*direction+np.array([0,.018*np.sin(t*np.pi),0])
            for across in [-1.,0.,1.]:
                pos=center+cross*across*width_here
                pos[1]+=.008*(1.-abs(across))*np.sin(t*np.pi)
                pos[0]*=side
                vert.append(pos.tolist())
                u=(780+cx+(t-.50)*40+(across*(width_here/width))*10)/1536
                vv=(58+cy+(t-.50)*58-(across*(width_here/width))*5)/1024
                uv.append([u,vv])
        for j in range(len(sections)-1):
            for k in range(2):
                a=start+j*3+k;b=a+3
                faces.extend([[a,b,a+1],[a+1,b,b+1]])
    p=np.array(vert);f=np.array(faces)
    if np.cross(p[f[0,1]]-p[f[0,0]],p[f[0,2]]-p[f[0,0]])[1]<0:f=f[:,::-1]
    n=np.zeros_like(p)
    fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    for j in range(3):np.add.at(n,f[:,j],fn)
    n/=np.maximum(1e-12,np.linalg.norm(n,axis=1,keepdims=True))
    g.node(name,parent,mesh=g.mesh(name,p,f,n,uv))

def add_wing(g,side):
    suffix="R" if side>0 else "L"
    shoulder=g.node("Shoulder"+suffix,0,(side*.133,.385,-.020))
    elbow=g.node("Elbow"+suffix,shoulder,(side*.197,.01,-.025))
    wrist=g.node("Wrist"+suffix,elbow,(side*.194,0,.055))
    # Secondaries overlap broad coverts and taper into the separated outer flight feathers.
    for idx,(parent,dest,samples) in enumerate([(shoulder,.215,7),(elbow,.202,7),(wrist,.09,7)]):
        ds=[]
        for j in range(samples):
            t=j/(samples-1);x=.0+dest*t
            trail=.135+.083*np.sin((idx+t+.6)*.93)
            if idx==2:
                end=(x+.12+.10*t,-.040-t*.020,-.245+.195*t)
            else:
                end=(x+.03+.078*t,-.030-t*.006,-trail)
            ds.append(((x-.025,.003+j*.0008,.042+t*.012),end,.034 if idx==2 else .038))
        for j in range(samples):
            t=j/(samples-1);x=dest*t
            tip=(x+.075+.045*t,-.005,-.096+.021*t) if idx!=2 else (x+.100+.05*t,-.021,-.142+.103*t)
            ds.append(((x-.038,.021+j*.0007,.065),tip,.037))
        if idx<2:mantle(g,parent,side,"Mantle"+suffix+str(idx),dest+.010,-.02 if idx==0 else .028)
        make_feathers(g,parent,side,("Secondaries","GreaterCoverts","Primaries")[idx]+suffix,ds)

def build(ref,path):
    sheet=np.array(Image.open(ref).convert('RGB'))
    git=hashlib.sha1(b'blob '+str(ref.stat().st_size).encode()+b'\0'+ref.read_bytes()).hexdigest()
    if git!='db465610eb61d155a7ae0876b624fa625361a19f':raise ValueError(git)
    views=views_from(sheet)
    for v in views:
        h,w,_=v['rgb'].shape
        sheet[v['low']:v['low']+h,v['left']:v['left']+w]=v['rgb']
    g=GLB();g.node('ExpeditionOwl');body(g,views)
    for side in [-1,1]:
        add_wing(g,side)
        ear_tuft(g,side)
    g.save(path,Image.fromarray(sheet))
    print(path,path.stat().st_size)
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("selected_board",type=Path);ap.add_argument("output",type=Path)
    args=ap.parse_args();build(args.selected_board,args.output)
