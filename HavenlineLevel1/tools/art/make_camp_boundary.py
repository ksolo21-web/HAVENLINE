"""Bake the paid camp boundary in metres.
The final art follows the fence and gate boards at art/structures-2026-11-25,
Docs/Design/StructureReferences/2026-11-25/selected, commit 26bb649e.
"""
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
        last_a=None
        distance=0.
        for i,pt in enumerate(pts):
            if i: distance+=np.linalg.norm(pt-pts[i-1])
            tangent=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
            tangent/=np.linalg.norm(tangent)
            ref=np.array([0.,1.,0.]) if abs(tangent[1])<.98 else np.array([0.,0.,1.])
            a=np.cross(tangent,ref) if last_a is None else last_a-np.dot(last_a,tangent)*tangent
            a/=np.linalg.norm(a)
            last_a=a
            b=np.cross(tangent,a)
            ring=[]
            for j in range(sides):
                # Rotate the clover cross-section as a whole to form three
                # continuous, rounded plies with shadowed grooves.
                angle=2*pi*j/sides
                r=radius*(.93+.13*cos(3*angle)) if twist else radius
                if twist: angle+=distance*2*pi/(radius*9.)
                ring.append(pt+(a*cos(angle)+b*sin(angle))*r)
            rings.append(ring)
        for i,(lo,hi) in enumerate(zip(rings,rings[1:])):
            for j in range(sides):
                k=(j+1)%sides
                self.face([lo[j],lo[k],hi[k],hi[j]],material,
                          [(j/sides,i*.18),(k/sides,i*.18),(k/sides,(i+1)*.18),(j/sides,(i+1)*.18)])
        for ring in (rings[0][::-1],rings[-1]):
            self.face(ring,material,[(.5,.5)]*sides)

    def button(self,x,y,z,rx,ry,rz,material):
        rings=[]
        for v in np.linspace(-pi*.495,pi*.495,8):
            rings.append([(x+rx*cos(v)*cos(2*pi*i/12),y+ry*sin(v),z+rz*cos(v)*sin(2*pi*i/12)) for i in range(12)])
        for lo,hi in zip(rings,rings[1:]):
            for i in range(12):
                j=(i+1)%12
                self.face([lo[j],lo[i],hi[i],hi[j]],material)

    def cap(self,x,z,r,h,phase, pointed=False):
        # The lip laps down the log in scallops. Its rounded outer shoulder
        # carries a little more powder on the windward face.
        rings=[]
        profile = [(h-.214,r*.98,.058),(h-.184,r*1.04,.052),
                                   (h-.121,r*1.066,.025),(h-.041,r*.93,.015),
                                   (h+.043,r*.71,.011),(h+.101,r*.38,.006),
                                   (h+.145,r*.085,.002),(h+.15,r*.009,0.)]
        if pointed:
            # A softly rounded point above a narrow, overhanging uneven lip.
            profile = [(h-.201,r*.96,.038),(h-.171,r*1.04,.039),
                       (h-.121,r*1.035,.025),(h-.050,r*.92,.013),
                       (h+.025,r*.71,.008),(h+.098,r*.47,.005),
                       (h+.162,r*.22,.002),(h+.193,r*.09,.001),
                       (h+.201,r*.009,0.)]
        for base,radius,ripple in profile:
            ring=[]
            for j in range(18):
                t=2*pi*j/18
                y=base+ripple*(sin(3*t+phase)+.45*cos(2*t-phase))
                ring.append((x+radius*cos(t)+.025*(1-radius/r),y,z+radius*sin(t)-.009*(1-radius/r)))
            rings.append(ring)
        for lo,hi in zip(rings,rings[1:]):
            for j in range(18):
                k=(j+1)%18
                self.face([lo[k],lo[j],hi[j],hi[k]],"snow")

    def rope_turns(self,x,z,r,y,turns=2):
        points=[]
        for j in range(64*turns+1):
            t=2*pi*j/64
            points.append((x+r*cos(t),y+.070*j/64,z+r*sin(t)))
        self.tube(points,.039,"rope",True,9)

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
                    key=(xyz,material) if material in ("snow","rope","timber","iron","brass","timber_dark") else (idx,material)
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
Image.fromarray(np.uint8(np.clip(np.array([199,121,55])+tone*np.array([1.2,1.02,.78]),0,255))).save(OUT/"golden_timber_grain.png")

panel=TimberKit("snowbound_palisade")
for i in range(8):
    x=-1.30+(i+.5)*.325
    r,h=.177,(1.18,1.127,1.16,1.203,1.144,1.18,1.213,1.151)[i]
    z=(.0,.003,-.005,.002)[i%4]
    panel.upright(x,z,[(-.02,r),(.13,r),(h-.23,r),(h-.159,r*.956),(h-.082,r*.77)],"timber",sides=12,turn=0)
    panel.cap(x,z,r,h,i*1.51,pointed=True)
# The front rail on each level has its own interlocking X lacing.
# Both diagonal wraps continue round the far side of that same rail.
# Front cardinal render: the anchor rails cross the posts at 13% and
# 71% of crown height, leaving a longer section of clear wood between.
for level in (.164,.94):
    rail_z=.172
    panel.tube([(-1.30,level,rail_z),(1.30,level,rail_z)],.082,"timber_dark",sides=12)
    for i in range(8):
        center=-1.30+(i+.5)*.325
        for handed in (-1,1):
            path=[]
            # End both buried returns inside the solid stock. A smooth
            # three-ply profile only needs to continue across its visible arc.
            for j in range(17):
                angle=pi*(-.72+j*1.44/16)
                # The return arc sits against the face of its own stock.
                x=center+handed*.157*sin(angle)
                y=level+.099*sin(angle)
                # Offset one overpass so the two plies visibly interlock.
                z=rail_z+(.100+.025*(handed>0))*cos(angle)
                path.append((x,y,z))
            panel.tube(path,.024,"rope",True,9)
    # The reverse of the lashings follows the outside curve of each stock,
    # then dips into the narrowing at the seam before crossing the next.
    for i in range(8):
        center=-1.30+(i+.5)*.325
        path=[]
        for j in range(10):
            t=j/9
            dx=(t-.5)*.325
            z=-max(.097,(.177**2-dx**2)**.5)-.018
            path.append((center+dx,level+.010*cos(2*pi*t+i*.14),z))
        panel.tube(path,.024,"rope",True,6)
panel.save()

leaf=TimberKit("snowbound_gate_leaf")
for i in range(6):
    x=(i-2.5)*.183
    leaf.timber((x,.065,0),(x,1.31,0),.185,.165,"timber")
# Golden front frame and diagonals. The inner face shows the sawn boards.
for y in (.15,1.235):
    leaf.timber((-.559,y,.097),(.559,y,.097),.138,.067,"timber_dark")
for x in (-.49,.49):
    leaf.timber((x,.155,.093),(x,1.24,.093),.105,.063,"timber_dark")
leaf.timber((-.452,.205,.111),(.452,1.18,.111),.117,.071,"timber_dark")
leaf.timber((-.452,1.18,.127),(.452,.205,.127),.117,.066,"timber_dark")
# The rear elevation has a slim perimeter frame around plain vertical
# boards. The center rail on either leaf carries just one through-pin.
for x in (-.505,.505):
    leaf.timber((x,.076,-.105),(x,1.307,-.105),.096,.058,"timber_dark")
for y in (.123,1.264):
    leaf.timber((-.463,y,-.101),(.463,y,-.101),.090,.056,"timber_dark")
# Each leaf carries its own low, continuous drift. An elliptical profile
# rounds over both edges; a few broad undulations keep the rail nearly level.
rings=[]
for i in range(25):
    t=i/24
    x=(t-.5)*1.124
    end=min(1.,t*14.,(1.-t)*14.)
    center=1.320+.006*sin(2*pi*t+.2)+.006*cos(7*pi*t-.6)
    height=(.030+.008*cos(5*pi*t)+.004*sin(9*pi*t))*(.53+.47*end)
    width=(.107+.008*cos(6*pi*t+.3))*(.78+.22*end)
    ring=[]
    for j in range(14):
        angle=2*pi*j/14
        ring.append((x,center+height*cos(angle),width*sin(angle)))
    rings.append(ring)
for left,right in zip(rings,rings[1:]):
    for j in range(14):
        k=(j+1)%14
        leaf.face([left[j],left[k],right[k],right[j]],"snow")
for end in (rings[0][::-1],rings[-1]):
    leaf.face(end,"snow",[(.5,.5)]*len(end))
leaf.save()

post=TimberKit("snowbound_gate_post")
post.upright(0,0,[(-.02,.203),(.12,.211),(1.40,.202),(1.473,.18),(1.53,.141)],"timber",sides=12)
post.cap(0,0,.207,1.57,.85,pointed=True)
post.rope_turns(0,0,.211,.21)
post.rope_turns(0,0,.207,1.19)
post.save()

hinges=TimberKit("snowbound_hinges")
for y in (.30,1.049):
    hinges.timber((-.08,y,.127),(.087,y,.127),.071,.036,"iron")
    for x in (-.075,.078):
        hinges.button(x,y,.132,.046,.048,.025,"iron")
        hinges.button(x,y,.155,.020,.020,.012,"brass")
    for h in (-.052,.052):
        hinges.tube([(0,y+h-.026,.151),(0,y+h+.026,.151)],.037,"iron")
    hinges.tube([(0,y-.093,.151),(0,y+.093,.151)],.021,"brass")
    hinges.button(0,y+.089,.151,.031,.014,.031,"iron")
hinges.save()

keeper=TimberKit("snowbound_latch_keeper")
# The archived hinge/latch close-up shows a small round escutcheon
# under each terminal, one rear through-pin, and a plain horizontal bolt.
keeper.button(0,.714,.157,.034,.037,.015,"iron")
keeper.button(0,.714,-.139,.021,.023,.014,"iron")
path=[(0,.714+.027*cos(pi*j/12),.160+.049*sin(pi*j/12)) for j in range(13)]
keeper.tube(path,.010,"iron")
keeper.save()

bolt=TimberKit("snowbound_sliding_bolt")
# The moving bolt's pivot is 2 cm to the left of the closed gate seam.
bolt.tube([(-.054,.714,.193),(.094,.714,.193)],.0145,"iron")
for x in (-.054,.094):
    bolt.button(x,.714,.194,.020,.020,.017,"iron")
bolt.save()
