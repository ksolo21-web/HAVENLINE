"""Bake the paid camp timber kit from the 18600/18607 asset plates. Units are metres."""
from pathlib import Path
from math import cos, sin, pi
from PIL import Image
import numpy as np

OUT = Path(__file__).resolve().parents[2] / "assets/field_camp"

class TimberKit:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.surfaces = {}

    def face(self, points, material, uv=None):
        if uv is None:
            uv = [(0,0),(0.95,0),(0.95,1),(0,1)]
        first = len(self.vertices) + 1
        for xyz, st in zip(points, uv):
            self.vertices.append((xyz,st))
        faces = self.surfaces.setdefault(material,[])
        for i in range(1,len(points)-1):
            faces.append((first, first+i, first+i+1))

    def upright(self, x,z, rings, material, sides=9, turn=0):
        for a,b in zip(rings,rings[1:]):
            for i in range(sides):
                t0,t1 = (turn+2*pi*j/sides for j in (i,i+1))
                def vertex(r,t):
                    return (x+r[1]*cos(t),r[0],z+r[1]*sin(t))
                self.face([vertex(a,t1),vertex(a,t0),vertex(b,t0),vertex(b,t1)],material,
                          [(i*.18,0),((i+1)*.18,0),((i+1)*.18,1),(i*.18,1)])

    def timber(self,a,b,width,depth,material):
        a,b = np.array(a),np.array(b)
        u=(b-a)/np.linalg.norm(b-a)
        normal=np.array([0.,0.,1.])
        v=np.cross(u,normal)
        cross=[(-1,-.72),(-.82,-1),(.82,-1),(1,-.72),(1,.72),(.82,1),(-.82,1),(-1,.72)]
        def ring(c):
            return [c+v*width*.5*x+normal*depth*.5*y for x,y in cross]
        lo,hi=ring(a),ring(b)
        for i,p in enumerate(lo):
            j=(i+1)%len(lo)
            self.face([p,hi[i],hi[j],lo[j]],material)
        self.face([lo[0],lo[3],lo[4],lo[7]],material)
        self.face([hi[7],hi[4],hi[3],hi[0]],material)

    def wrap(self,x,z,r,y,turns=2):
        # Raised spiral band is visible across both faces of the snowline.
        points=36*turns
        for i in range(points):
            def at(j,dy):
                a=2*pi*j/36
                return (x+(r+.009)*cos(a),y+j/36*.049+dy,z+(r+.009)*sin(a))
            self.face([at(i+1,-.020),at(i,-.020),at(i,.020),at(i+1,.020)],"rope")

    def tube(self, points, radius, material, twist=False, sides=9):
        pts=np.array(points,dtype=float)
        rings=[]
        for i,pt in enumerate(pts):
            tangent=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
            tangent/=np.linalg.norm(tangent)
            ref=np.array([0.,1.,0.]) if abs(tangent[1])<.98 else np.array([0.,0.,1.])
            a=np.cross(tangent,ref)
            a/=np.linalg.norm(a)
            b=np.cross(tangent,a)
            ring=[]
            for j in range(sides):
                angle=2*pi*j/sides
                r=radius*(.90+.16*cos(3*angle-i*.96)) if twist else radius
                ring.append(pt+(a*cos(angle)+b*sin(angle))*r)
            rings.append(ring)
        for i,(lo,hi) in enumerate(zip(rings,rings[1:])):
            for j in range(sides):
                k=(j+1)%sides
                self.face([lo[j],lo[k],hi[k],hi[j]],material,
                          [(j/sides,i*.18),(k/sides,i*.18),(k/sides,(i+1)*.18),(j/sides,(i+1)*.18)])
        for ring in (rings[0][::-1],rings[-1]):
            self.face(ring,material,[(.5,.5)]*sides)

    def cap(self,x,z,r,h,phase):
        # The lip laps down the log in scallops. Its rounded outer shoulder
        # carries a little more powder on the windward face.
        rings=[]
        for base,radius,ripple in [(h-.21,r*1.005,.041),(h-.178,r*1.055,.032),
                                   (h-.09,r*1.075,.014),(h-.017,r*.96,.009),
                                   (h+.03,r*.63,.006),(h+.045,r*.02,.001)]:
            ring=[]
            for j in range(12):
                t=2*pi*j/12
                y=base+ripple*(sin(3*t+phase)+.45*cos(2*t-phase))
                ring.append((x+radius*cos(t),y,z+radius*sin(t)))
            rings.append(ring)
        for lo,hi in zip(rings,rings[1:]):
            for j in range(12):
                k=(j+1)%12
                self.face([lo[k],lo[j],hi[j],hi[k]],"snow")

    def rope_turns(self,x,z,r,y,turns=2):
        points=[]
        for j in range(24*turns+1):
            t=2*pi*j/24
            points.append((x+r*cos(t),y+.062*j/24,z+r*sin(t)))
        self.tube(points,.037,"rope",True)

    def save(self):
        lines=["# Havenline golden timber perimeter","mtllib boundary_v2.mtl",f"o {self.name}","s off"]
        for xyz,_ in self.vertices:
            lines.append("v %.5f %.5f %.5f"%tuple(xyz))
        for _,uv in self.vertices:
            lines.append("vt %.5f %.5f"%tuple(uv))
        normals={}
        normal_keys={}
        for material,faces in self.surfaces.items():
            for tri in faces:
                a,b,c=[np.asarray(self.vertices[i-1][0]) for i in tri]
                n=np.cross(b-a,c-a)
                length=np.linalg.norm(n)
                if length < 1e-9:continue
                for idx in tri:
                    xyz=tuple(np.round(self.vertices[idx-1][0],5))
                    key=(xyz,material) if material in ("snow","rope","timber") else (idx,material)
                    normals[key]=normals.get(key,0.)+n/length
                    normal_keys[idx]=key
        for i in range(1,len(self.vertices)+1):
            n=normals.get(normal_keys.get(i),np.array([0.,1.,0.]))
            lines.append("vn %.5f %.5f %.5f"%tuple(n/max(np.linalg.norm(n),1e-6)))
        for material, faces in self.surfaces.items():
            lines.append("usemtl "+material)
            lines.extend("f "+" ".join(f"{n}/{n}/{n}" for n in face) for face in faces)
        (OUT/f"{self.name}.obj").write_text("\n".join(lines)+"\n")

# Grade the inherited reference grain into the golden timber palette of the
# latest gate/construction boards while retaining its actual grain pattern.
wood=np.asarray(Image.open(OUT/"opening_wood_grain.png").convert("RGB"),np.float32)
tone=(wood[:,:,0]-wood[:,:,0].mean())[:,:,None]
Image.fromarray(np.uint8(np.clip(np.array([202,141,75])+tone*np.array([.55,.46,.40]),0,255))).save(OUT/"golden_timber_grain.png")

panel=TimberKit("snowbound_palisade")
for i in range(8):
    x=-1.30+(i+.5)*.325
    r,h=.177,(1.19,1.155,1.18,1.17,1.148,1.18,1.205,1.17)[i]
    z=(.0,.003,-.005,.002)[i%4]
    panel.upright(x,z,[(-.02,r),(.13,r),(h-.2,r),(h-.035,r*.96)],"timber",sides=12,turn=0)
    panel.cap(x,z,r,h,i*1.51)
for z in (-.167,.167):
    for y in (.35,.82):
        panel.tube([(-1.299,y,z),(1.299,y,z)],.071,"timber_dark")
# Exterior crossing lashes bind both rounded rails, repeated across the run.
for i in range(4):
    x=-.975+i*.65
    for direction in (-1,1):
        a=np.array([x-.248,.585-direction*.23,.225])
        b=np.array([x+.248,.585+direction*.23,.225])
        path=[a+(b-a)*j/15+np.array([0,0,.01*sin(pi*j/15)]) for j in range(16)]
        panel.tube(path,.029,"rope",True)
    for x2 in (x-.248,x+.248):
        panel.tube([(x2,.336,-.231),(x2,.836,-.231)],.023,"rope")
panel.save()

leaf=TimberKit("snowbound_gate_leaf")
for i in range(6):
    x=(i-2.5)*.183
    leaf.timber((x,.065,0),(x,1.31,0),.185,.165,"timber")
    leaf.timber((x,1.302,0),(x,1.334+sin(i*1.7)*.008,0),.184,.165,"snow")
# Golden front frame and diagonals. The inner face shows the sawn boards.
for y in (.15,1.235):
    leaf.timber((-.559,y,.097),(.559,y,.097),.138,.067,"timber_dark")
for x in (-.49,.49):
    leaf.timber((x,.155,.093),(x,1.24,.093),.105,.063,"timber_dark")
leaf.timber((-.452,.205,.111),(.452,1.18,.111),.117,.071,"timber_dark")
leaf.timber((-.452,1.18,.127),(.452,.205,.127),.117,.066,"timber_dark")
# A gently irregular ridge continues across both rectangular leaves.
leaf.timber((-.562,1.326,0),(.562,1.326,0),.078,.225,"snow")
leaf.save()

post=TimberKit("snowbound_gate_post")
post.upright(0,0,[(-.02,.203),(.12,.211),(1.47,.202),(1.56,.189)],"timber",sides=12)
post.cap(0,0,.207,1.62,.85)
post.rope_turns(0,0,.211,.21)
post.rope_turns(0,0,.207,1.19)
post.save()

hinges=TimberKit("snowbound_hinges")
for y in (.30,1.049):
    hinges.timber((-.09,y,.127),(.11,y,.127),.097,.048,"iron")
    hinges.tube([(0,y-.082,.143),(0,y+.082,.143)],.048,"iron")
    for x in (-.075,.082):
        hinges.timber((x,y-.016,.158),(x,y+.016,.158),.032,.021,"brass")
hinges.save()

keeper=TimberKit("snowbound_latch_keeper")
keeper.timber((0,.622,.161),(0,.807,.161),.099,.073,"iron")
keeper.timber((0,.674,.202),(0,.751,.202),.126,.074,"iron")
keeper.timber((0,.615,-.092),(0,.785,-.092),.054,.039,"iron")
keeper.save()

bolt=TimberKit("snowbound_sliding_bolt")
bolt.timber((-.22,.714,.249),(.22,.714,.249),.062,.068,"iron")
bolt.timber((-.161,.694,.269),(-.161,.797,.269),.039,.049,"iron")
bolt.save()
