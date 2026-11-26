"""Build the Nov 25 canonical customer bench, using the selected detail plate as its paint.
python build_service_counter.py customer-counter-details.png canonical_counter.glb
The source is Docs/Design/StructureReferences/2026-11-25/selected at 26bb649e.
World coordinates are metres; +Z is the cashier side. The sockets are 1.080m high.
"""
import io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
sheet=Image.open(sys.argv[1]).convert('RGB')
out=Path(sys.argv[2])
def crop_quad(corners):
    # Corners in the calibrated 645px-wide inspection projection.
    order=[0,3,2,1]
    points=[v*sheet.width/645. for i in order for v in corners[i]]
    return sheet.transform((256,256),Image.Transform.QUAD,points,Image.Resampling.BICUBIC)
panels=[
 crop_quad([(13,55),(149,88),(149,98),(13,66)]),
 crop_quad([(17,117),(138,146),(138,157),(17,129)]),
 crop_quad([(88,305),(111,303),(111,377),(88,382)]),
 crop_quad([(79,245),(111,248),(113,258),(78,257)]),
 crop_quad([(189,92),(258,103),(236,130),(163,118)]),
 crop_quad([(202,57),(270,69),(261,101),(190,89)]),
]
tile=256
atlas=Image.new('RGB',(tile*len(panels),tile))
for i,panel in enumerate(panels):atlas.paste(panel,(i*tile,0))
verts=[]
def surf(pt,n,uv,k):
    return [*pt,*n,(k+.012+.976*uv[0])/len(panels),.012+.976*uv[1]]
def quad(pts,uv,n,k):
    for i in (0,1,2,0,2,3):verts.append(surf(pts[i],n[i] if len(np.shape(n))==2 else n,uv[i],k))
def rounded_box(pos,dim,r,mats):
    # Sampling the Minkowski bevel along all three axes makes genuinely
    # rounded silhouettes and interpolated normals rather than painted edges.
    half=np.array(dim)*.5
    for normal_axis in range(3):
        for sign in (-1,1):
            local_u=(normal_axis+1)%3;local_v=(normal_axis+2)%3
            if sign<0:local_u,local_v=local_v,local_u
            def steps(ax):
                h=half[ax];return [-h,-h+r*.38,-h+r,h-r,h-r*.38,h]
            U,V=steps(local_u),steps(local_v)
            for i in range(5):
                for j in range(5):
                    P=[];N=[];uv=[]
                    for a,b in ((U[i],V[j]),(U[i+1],V[j]),(U[i+1],V[j+1]),(U[i],V[j+1])):
                        q=np.zeros(3);q[normal_axis]=sign*half[normal_axis];q[local_u]=a;q[local_v]=b
                        inner=np.clip(q,-half+r,half-r)
                        n=q-inner;n/=np.linalg.norm(n)
                        P.append(np.array(pos)+inner+n*r);N.append(n)
                        uaxis,vaxis=((0,2) if normal_axis==1 else (0,1) if normal_axis==2 else (2,1))
                        u=.5+q[uaxis]/(2*half[uaxis]);v=.5+q[vaxis]/(2*half[vaxis])
                        uv.append((u,1-v))
                    quad(P,uv,N,mats[normal_axis])
# A pair of bolstered golden planks leaves a narrow actual seam through the
# transfer board. The two sockets stay directly above its measured timber.
for z in (-.2905,.2905):
    rounded_box((0,.978,z),(3.43,.204,.580),.049,[1,0,1])
for x in (-1.41,1.41):
    for z in (-.395,.395):
        rounded_box((x,.43,z),(.256,.87,.255),.032,[2,1,2])
    rounded_box((x,.358,0),(.171,.125,.80),.018,[2,1,2])
for z in (-.1445,.1445):
    rounded_box((0,.352,z),(2.84,.116,.285),.020,[1,0,1])
rounded_box((0,.592,-.012),(2.80,.397,.115),.020,[1,0,1])
# Custom wedge hull joins a recessed keypad and angled display. The case
# itself has the five visible breaks and chamfered sides in the detail plate.
cx=1.13;zbase=-.32;ybase=1.065
profile=[(-.219,.015),(.227,.015),(.234,.083),(.220,.128),(.028,.204),(-.046,.387),(-.080,.411),(-.164,.410),(-.188,.390),(-.221,.135)]
rings=[]
for x,shrink in ((-.252,.024),(-.230,0),(.230,0),(.252,.024)):
    ring=[]
    for z,y in profile:
        ring.append(np.array([cx+x,ybase+y+( .2-y)*shrink/.22,zbase+z*(1-shrink/.24)]))
    rings.append(ring)
def planar(points,k,uv=((0,1),(1,1),(1,0),(0,0))):
    n=np.cross(points[1]-points[0],points[2]-points[0]);n/=np.linalg.norm(n);quad(points,uv,n,k)
for i in range(len(profile)):
    j=(i+1)%len(profile)
    for ri in range(3):
        p=[rings[ri][i],rings[ri+1][i],rings[ri+1][j],rings[ri][j]]
        planar(p,3)
for x,ring in [(-.252,rings[0]),(.252,rings[-1])]:
    center=np.array([cx+x,ybase+.174,zbase])
    for i in range(len(ring)):
        j=(i+1)%len(ring)
        a,b=(ring[j],ring[i]) if x>0 else (ring[i],ring[j])
        for pt,uv in [(center,(.5,.5)),(a,(.75,.25)),(b,(.75,.75))]:
            verts.append(surf(pt,[1 if x>0 else -1,0,0],uv,3))
def panel(za,ya,zb,yb,tex):
    half=.231
    pts=[np.array([cx-half,ybase+ya+.002,zbase+za]),np.array([cx+half,ybase+ya+.002,zbase+za]),np.array([cx+half,ybase+yb+.002,zbase+zb]),np.array([cx-half,ybase+yb+.002,zbase+zb])]
    planar(pts,tex)
panel(.220,.128,.028,.204,4)
panel(.028,.204,-.046,.387,5)
data=np.array(verts,np.float32);blob=bytearray();views=[];acc=[]
def store(bb,target=None):
    blob.extend(b'\0'*(-len(blob)%4));idx=len(views);views.append(dict(buffer=0,byteOffset=len(blob),byteLength=len(bb)))
    if target:views[-1]['target']=target
    blob.extend(bb);return idx
for arr,typ in ((data[:,:3],'VEC3'),(data[:,3:6],'VEC3'),(data[:,6:],'VEC2')):
    a=np.ascontiguousarray(arr,dtype='<f4');acc.append(dict(bufferView=store(a.tobytes(),34962),count=len(arr),componentType=5126,type=typ,min=arr.min(0).tolist(),max=arr.max(0).tolist()))
im=io.BytesIO();atlas.save(im,'JPEG',quality=94,subsampling=0)
vi=store(im.getvalue());m=dict(name='SourcePlateTimberAndRegister',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0),metallicFactor=.015,roughnessFactor=.60),emissiveTexture=dict(index=0),emissiveFactor=[.11,.105,.09])
doc=dict(asset=dict(version='2.0',generator='Havenline canonical counter reconstruction'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(name='CanonicalGoldenCounter',mesh=0)],meshes=[dict(primitives=[dict(attributes=dict(POSITION=0,NORMAL=1,TEXCOORD_0=2),material=0)])],materials=[m],images=[dict(name='CanonicalCounterPaint',bufferView=vi,mimeType='image/jpeg')],textures=[dict(source=0)],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=acc)
hdr=json.dumps(doc,separators=(',',':')).encode();hdr+=b' '*(-len(hdr)%4);blob.extend(b'\0'*(-len(blob)%4))
out.write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(hdr)+len(blob),len(hdr),b'JSON')+hdr+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
