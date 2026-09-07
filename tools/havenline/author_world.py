"""Reproducible authored mesh candidates; visual approval is explicitly separate.

Exports glTF meshes offline. The game never assembles built-in engine primitives.
Names and triangle counts are not evidence of production art quality.
"""
import json, math, struct
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parents[2] / 'HavenlineGodot/assets/world'
OUT.mkdir(parents=True, exist_ok=True)
MATERIALS = [
    ('snow', (0.74,0.86,0.96), 0.85, 0),
    ('pine', (0.035,0.20,0.19), 0.85, 0),
    ('timber', (0.30,0.13,0.065), 0.8, 0),
    ('cut_wood', (0.68,0.43,0.20), 0.8, 0),
    ('slate', (0.22,0.31,0.39), 0.9, 0),
    ('enamel', (0.07,0.29,0.37), 0.32, 0.45),
    ('brass', (0.68,0.38,0.14), 0.3, 0.7),
    ('dark_iron', (0.065,0.085,0.105), 0.48, 0.6),
    ('ember', (1,0.27,0.035), 0.8, 0),
    ('roof', (0.12,0.25,0.33), 0.65, 0.15),
    ('window', (1,0.62,0.22), 0.25, 0),
    ('bark_ridge', (0.20,0.075,0.035), 0.9, 0),
]

class Model:
    def __init__(self): self.parts=[]
    def surface(self, name, grid, mat, flip=False):
        grid=np.array(grid,dtype=np.float32); u,v,_=grid.shape
        indices=[]
        for i in range(u-1):
            for j in range(v-1):
                a=i*v+j;b=a+v
                indices += [(a,b,a+1),(a+1,b,b+1)]
        f=np.array(indices,dtype=np.uint32)
        if flip:f=f[:,::-1]
        self.mesh(name,grid.reshape((-1,3)),f,mat)
    def mesh(self,name,verts,faces,mat):
        v=np.asarray(verts,dtype=np.float32);f=np.asarray(faces,dtype=np.uint32)
        normal=np.zeros_like(v)
        cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
        for k in range(3):np.add.at(normal,f[:,k],cross)
        normal/=np.maximum(1e-9,np.linalg.norm(normal,axis=1,keepdims=True))
        self.parts.append((name,v,normal,f,mat))
    def lathe(self,name,profile,mat,center=(0,0,0),segments=32,lobes=0,phase=0):
        grid=[]
        for y,radius in profile:
            row=[]
            for j in range(segments+1):
                a=j/segments*math.tau
                r=radius*(1+lobes*math.sin(a*7+phase)+lobes*.4*math.sin(a*11-phase))
                row.append((center[0]+r*math.cos(a),center[1]+y,center[2]+r*math.sin(a)))
            grid.append(row)
        self.surface(name,grid,mat)
    def tube(self,name,path,radii,mat,sides=12):
        p=np.array(path);grid=[]
        for i,point in enumerate(p):
            tangent=p[min(i+1,len(p)-1)]-p[max(i-1,0)];tangent/=np.linalg.norm(tangent)
            axis=np.cross(tangent,[0,1,0] if abs(tangent[1])<.9 else [1,0,0]);axis/=np.linalg.norm(axis)
            other=np.cross(tangent,axis)
            grid.append([point+radii[i]*(math.cos(a)*axis+math.sin(a)*other) for a in np.linspace(0,math.tau,sides+1)])
        self.surface(name,grid,mat,flip=True)
    def rock(self,name,c,s,mat,seed=1):
        grid=[]
        for a in np.linspace(0.005,math.pi-.005,13):
            row=[]
            for b in np.linspace(0,math.tau,25):
                w=1+.075*math.sin(b*3+a*4+seed)+.04*math.sin(b*7-a*3)
                row.append((c[0]+s[0]*math.sin(a)*math.cos(b)*w,c[1]+s[1]*math.cos(a)*w,c[2]+s[2]*math.sin(a)*math.sin(b)*w))
            grid.append(row)
        self.surface(name,grid,mat,flip=True)
    def plank(self,name,c,size,mat,angle=0):
        # Rounded superellipse cross section, softly cambered along its length.
        w,h,d=size;grid=[]
        for t in np.linspace(-1,1,9):
            end=max(.01,min(1,(1-abs(t))*20))
            row=[]
            for a in np.linspace(0,math.tau,25):
                co,si=math.cos(a),math.sin(a)
                x=w*.5*math.copysign(abs(co)**.16,co)*end
                y=h*.5*math.copysign(abs(si)**.16,si)*end
                z=t*d*.5
                row.append((c[0]+x*math.cos(angle)-y*math.sin(angle),c[1]+x*math.sin(angle)+y*math.cos(angle),c[2]+z))
            grid.append(row)
        self.surface(name,grid,mat,flip=True)
    def save(self,name):
        binary=bytearray(); views=[];accessors=[];meshes=[];nodes=[]
        def accessor(a,typ,component):
            a=np.ascontiguousarray(a);offset=len(binary);binary.extend(a.tobytes());binary.extend(b'\0'*((-len(binary))%4))
            views.append({'buffer':0,'byteOffset':offset,'byteLength':a.nbytes})
            item={'bufferView':len(views)-1,'componentType':component,'count':len(a),'type':typ}
            if typ=='VEC3':item.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
            accessors.append(item);return len(accessors)-1
        for label,v,n,f,mat in self.parts:
            pv=accessor(v,'VEC3',5126);pn=accessor(n,'VEC3',5126);pi=accessor(f.reshape(-1),'SCALAR',5125)
            meshes.append({'name':label,'primitives':[{'attributes':{'POSITION':pv,'NORMAL':pn},'indices':pi,'material':mat}]})
            nodes.append({'name':label,'mesh':len(meshes)-1})
        materials=[]
        for label,color,rough,metal in MATERIALS:
            m={'name':label,'pbrMetallicRoughness':{'baseColorFactor':[*color,1],'roughnessFactor':rough,'metallicFactor':metal}}
            if label in ['ember','window']:m['emissiveFactor']=[x*.85 for x in color]
            materials.append(m)
        doc={'asset':{'version':'2.0','generator':'HAVENLINE offline mesh authoring — unapproved art candidate'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':materials,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
        js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
        content=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
        (OUT/(name+'.glb')).write_bytes(content)
        print(name,len(content),'bytes',sum(len(p[3]) for p in self.parts),'triangles')

def pine(seed):
    m=Model();m.lathe('sculpted_trunk',[(0,.22),(.05,.26),(.4,.18),(1.8,.09),(3.9,.015)],2,lobes=.10,phase=seed)
    for tier in range(5):
        h=.6+tier*.6;r=1.16-tier*.19
        m.lathe('branch_crown_'+str(tier),[(h-.09,.12),(h,r*.78),(h+.12,r),(h+.29,r*.84),(h+.53,r*.52),(h+.88,.02)],1,lobes=.12,phase=seed+tier)
        m.lathe('snow_mantle_'+str(tier),[(h+.19,r*.87),(h+.24,r*.94),(h+.33,r*.85),(h+.57,r*.50),(h+.90,.015)],0,lobes=.10,phase=seed+tier)
    m.save('pine_'+str(seed))

def furnace():
    m=Model()
    for i in range(12):
        a=i/12*math.tau;m.rock('foundation_'+str(i),(math.cos(a)*.78,.15,math.sin(a)*.78),(.30,.24,.29),4,i)
    m.lathe('cast_body',[(.15,.67),(.23,.78),(.34,.80),(1.22,.78),(1.42,.67),(1.55,.48),(1.58,.28)],5)
    for h in [.35,1.2]:m.lathe('brass_seam',[(h-.025,.80),(h,.83),(h+.035,.80)],6)
    m.lathe('smoke_flue',[(1.48,.24),(2.27,.24),(2.32,.32),(2.40,.34),(2.47,.24),(2.48,.01)],7)
    m.plank('firebox_frame',(0,.72,.79),(.83,.72,.14),7)
    m.plank('firebox_glow',(0,.72,.875),(.60,.50,.045),8)
    for x in [-.24,-.12,0,.12,.24]:m.plank('firebox_grate',(x,.70,.91),(.035,.59,.04),7)
    for i in range(16):
        a=i/16*math.tau
        for h in [.40,1.15]:m.rock('rivet',(math.cos(a)*.81,h,math.sin(a)*.81),(.034,.034,.034),6)
    m.tube('side_pipe',[(-.70,.40,0),(-1.0,.48,0),(-1.01,.86,0),(-.7,1.1,0)],[.10]*4,6)
    m.save('furnace')

def cabin():
    m=Model()
    for x in np.linspace(-1.2,1.2,8):m.plank('floor_board',(x,.10,0),(.33,.16,2.0),2)
    for y in np.linspace(.30,1.5,7):
        m.plank('rear_timber',(0,y,-.92),(2.45,.20,.20),2)
        m.plank('front_left',(-.88,y,.92),(.73,.20,.20),2)
        m.plank('front_right',(.88,y,.92),(.73,.20,.20),2)
    for x in [-1.13,1.13]:
        for z in np.linspace(-.85,.85,8):m.plank('side_board',(x,.91,z),(.18,1.49,.215),2)
    for x in [-1.2,1.2]:m.plank('corner_post',(x,.95,.97),(.22,1.8,.22),3)
    for x in [-.7,.7]:
        m.plank('roof_panel',(x,2.00,0),(1.68,.18,2.50),9,angle=-math.copysign(.45,x))
        m.plank('snow_blanket',(x,2.10,0),(1.71,.22,2.54),0,angle=-math.copysign(.45,x))
    m.plank('ridge_cap',(0,2.41,0),(.22,.22,2.63),0)
    m.plank('door', (0,.80,.94),(.80,1.40,.10),9)
    m.plank('door_glazing',(0,1.1,1.005),(.47,.43,.035),10)
    for x in [-.26,.26]:m.plank('window_frame',(x,1.1,1.04),(.04,.51,.045),6)
    m.plank('lintel',(0,1.64,.97),(1.1,.15,.25),3)
    m.plank('step',(0,.13,1.25),(1.0,.22,.48),4)
    m.lathe('chimney',[(1.8,.16),(2.75,.16),(2.8,.24),(2.9,.25)],7,center=(.82,0,-.40))
    m.save('shelter')

def resources():
    for name,mat in [('stone',4),('metal',7),('fuel',11)]:
        m=Model()
        for i in range(5):
            a=i*2.4;m.rock(name+'_'+str(i),(math.cos(a)*.37,.29+i*.035,math.sin(a)*.37),(.47,.37,.40),mat,i+2)
        for i in range(3):
            a=i*2.4;m.rock('snow_cap',(math.cos(a)*.32,.53,math.sin(a)*.32),(.36,.1,.28),0,i)
        m.save(name)
    m=Model();m.lathe('log_bark',[(-.32,.001),(-.31,.125),(.31,.12),(.32,.001)],2,lobes=.04)
    m.lathe('end_grain',[(.312,.113),(.322,.112)],3)
    m.save('log')
    m=Model()
    for x in np.linspace(-1.3,1.3,9):m.lathe('palisade_post',[(0,.12),(1.1,.12),(1.38,.025)],2,center=(x,0,0),segments=12)
    for y in [.30,.8]:m.plank('cross_timber',(0,y,.10),(3,.12,.12),3)
    m.save('barricade')
    m=Model()
    for z in [-.50,.50]:m.plank('rack_frame',(0,.16,z),(1.8,.22,.22),2)
    for x in [-.70,.70]:m.plank('rack_upright',(x,.65,0),(.16,1.25,1.1),5)
    for row in range(3):
        for col in range(4-row):
            m.tube('stacked_log',[(-.5+col*.32+row*.15,.33+row*.27,-.6),(-.5+col*.32+row*.15,.33+row*.27,.6)],[.15,.15],2)
    m.save('storage')

def terrain():
    m=Model();grid=[]
    for z in np.linspace(-20,20,101):
        row=[]
        for x in np.linspace(-19,19,97):
            edge=max(0,(max(abs(x)/15,abs(z)/17)-.72))
            y=-.04+edge*(.28+math.sin(x*.72)*.11+math.cos(z*.47)*.19)
            row.append((x,y,z))
        grid.append(row)
    m.surface('snowfield',grid,0,flip=False);m.save('terrain')

if __name__=='__main__':
    pine(1);pine(2);pine(3);furnace();cabin();resources();terrain()
