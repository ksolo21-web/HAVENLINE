"""Reference-derived rounded timber primitives; source a4860b7544e05918369496152f070ce64acc77ae.

Bounded tessellation matches the reviewed boundary repair; dimensions stay frozen.
"""
from pathlib import Path
import math
import numpy as np
from task03_mesh_authoring import Model, rotation, TAU

def fit_visual_envelope(model,minimum,maximum):
    v=np.concatenate([p.vertices for p in model.parts]);lo=v.min(0);hi=v.max(0)
    minimum=np.asarray(minimum);maximum=np.asarray(maximum);scale=(maximum-minimum)/(hi-lo)
    for part in model.parts:
        part.vertices=(part.vertices-lo)*scale+minimum
        part.normals=part.normals/scale
        part.normals/=np.linalg.norm(part.normals,axis=1,keepdims=True)
    return model

def picket(m,name,x,height=1.40,radius=.108,depth=None,seed=0,ropes=True):
    if depth is None:depth=radius
    seg=8 if name=='threshold_post' else 6;rows=3 if name=='threshold_post' else 2;v=[];f=[];ys=np.linspace(0,height-.36,rows)
    for y in ys:
        for i in range(seg):
            a=TAU*i/seg;ripple=1+.030*math.cos(a*7+seed*.3)+.018*math.sin(a*3+y*3+seed)
            v.append([x+radius*math.cos(a)*ripple,y,depth*math.sin(a)*ripple])
    for j in range(rows-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=b+seg;d=a+seg;f.extend([[a,b,c],[a,c,d]])
    bottom=len(v);v.append([x,0,0]);tip=len(v);v.append([x,height+.035,0])
    for i in range(seg):
        j=(i+1)%seg;f.extend([[bottom,j,i],[(rows-1)*seg+i,(rows-1)*seg+j,tip]])
    p=m.add(name+'_carved_timber','wood_light',v,f,tint=(1.,.90,.78),smooth=True)
    vv=p.vertices;angles=np.arctan2(vv[:,2]/depth,(vv[:,0]-x)/radius)
    p.colors[:,:3]=1.0
    p.uv=np.column_stack([(angles+math.pi)/math.pi,vv[:,1]/height*2.5+seed*.173])
    rings=[(0.,1.12),(.18,.80),(.38,.12)] if name=='threshold_post' else [(0.,1.12),(.38,.12)]
    v=[];f=[];snow_base=height-.32
    for j,(yy,rr) in enumerate(rings):
        for i in range(seg):
            a=TAU*i/seg;scallop=.036*math.sin(5*a+seed*.47)+.018*math.sin(8*a+1.2);y=snow_base+yy
            if j==0:y+=scallop
            elif j==1:y+=scallop*.35
            v.append([x+radius*rr*1.09*math.cos(a),y,depth*rr*1.09*math.sin(a)])
    for j in range(len(rings)-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=b+seg;d=a+seg;f.extend([[a,b,c],[a,c,d]])
    btm=len(v);v.append([x,snow_base-.01,0]);top=len(v);v.append([x,snow_base+.403,0])
    for i in range(seg):
        j=(i+1)%seg;f.extend([[btm,j,i],[(len(rings)-1)*seg+i,(len(rings)-1)*seg+j,top]])
    m.add(name+'_snow_crown','snow',v,f)
    if ropes:
        for y in [.34,.90]:
            for wrap in range(2 if name=='threshold_post' else 1):
                t=np.linspace(0,TAU,7 if name=='threshold_post' else 4)
                path=[(x+(radius+.019+wrap*.006)*math.cos(a),y+(-1 if wrap else 1)*.050*math.cos(a),(depth+.019+wrap*.006)*math.sin(a)) for a in t]
                m.tube(name+'_rope_wrap','cream',path,.018,3,tint=(.84,.76,.61))

def fence_panel():
    m=Model('fence_panel');span=2.9409;radius=.118;pitch=(span-radius*2)/11
    for i in range(12):
        x=-span/2+radius+i*pitch
        picket(m,'picket_%02d'%i,x,height=1.382+.027*math.sin(i*2.1),radius=radius,depth=.080,seed=i,ropes=True)
    for y in [.33,.88]:m.bevel_box('rear_support','wood',(span-.035,.09,.08),(0,y,.073),.018)
    return fit_visual_envelope(m,(-1.47045,0.,-.0806),(1.47045,1.465,.0706))

def gate_post():
    m=Model('gate_post');picket(m,'threshold_post',0,height=1.535,radius=.150,depth=.150,seed=4,ropes=True)
    return fit_visual_envelope(m,(-.168,0.,-.1724),(.168,1.605,.168))

def export_obj(model,path):
    mapping={'wood':'timber_dark','wood_light':'timber','snow':'snow','cream':'rope','metal':'blue'}
    lines=['# HAVENLINE supplied-reference T03 sculpted visual candidate','mtllib boundary_v2.mtl','o '+model.name,'s 1'];base=1
    for p in model.parts:
        lines.append('usemtl '+mapping[p.material])
        for v,c in zip(p.vertices,p.colors):lines.append('v '+' '.join(f'{x:.8g}' for x in [*v,*c[:3]]))
        for uv in getattr(p,'uv',np.zeros((len(p.vertices),2))):lines.append('vt '+' '.join(f'{x:.8g}' for x in uv))
        for n in p.normals:lines.append('vn '+' '.join(f'{x:.8g}' for x in n))
        for f in p.faces:lines.append('f '+' '.join(f'{base+int(i)}/{base+int(i)}/{base+int(i)}' for i in f))
        base+=len(p.vertices)
    Path(path).write_text('\n'.join(lines)+'\n')

def topology_errors(v,f):
    v,inv=np.unique(np.round(v,8),axis=0,return_inverse=True);f=inv[f]
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ordered=np.sort(edges,axis=1)
    _,ix,count=np.unique(ordered,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));errors=[]
    if not np.all(count==2):errors.append('open/nonmanifold')
    if not np.all(balance==0):errors.append('inconsistent winding')
    p=v[f];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    if (np.linalg.norm(cross,axis=1)<1e-12).any():errors.append('degenerate')
    if np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6<=1e-12:errors.append('inward/zero volume')
    return errors
