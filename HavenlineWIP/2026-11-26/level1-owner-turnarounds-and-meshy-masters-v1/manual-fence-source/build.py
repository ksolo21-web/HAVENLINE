"""Fresh 33036 panel: authored solid mesh, no engine/source integrations."""
from collections import defaultdict
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
root=Path(__file__).resolve().parent
ref,env=map(Path,sys.argv[1:3])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ref)=='067b1e9f387882314094196dce1938f713875805f50902857499df6c376261e3'
assert sha(env)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
V=np.array([[float(x) for x in l.split()[1:4]] for l in env.read_text().splitlines() if l.startswith('v ')])
L,U=V.min(0),V.max(0)
assert np.allclose(L,[-1.47045,0,-.0806]) and np.allclose(U,[1.47045,1.465,.0706])
faces=defaultdict(list); groups=defaultdict(list)
def triangulated(label,part,a,b,c):
    assert np.linalg.norm(np.cross(b-a,c-a))>1e-10
    faces[label].append((a,b,c));groups[label].append(part)
def tube(label,part,R,axis_cyl='across',capped=True):
    n=len(R[0])
    def path(a,b,c):triangulated(label,part,a,b,c)
    for a,b in zip(R,R[1:]):
        for j in range(n):
            k=(j+1)%n
            if axis_cyl=='up':
                path(a[j],b[j],b[k]);path(a[j],b[k],a[k])
            else:
                path(a[j],a[k],b[k]);path(a[j],b[k],b[j])
    if capped:
        a,b=R[0],R[-1]
        ca,cb=a.mean(0),b.mean(0)
        for j in range(n):
            k=(j+1)%n
            if axis_cyl=='up':
                path(ca,a[j],a[k]);path(cb,b[k],b[j])
            else:
                path(ca,a[k],a[j]);path(cb,b[j],b[k])
def oval(c,t,r):return math.cos(t)*r[0],math.sin(t)*r[1]
W=2*U[0];pitch=W/8
centers=[-W*.5+pitch*(i+.5) for i in range(8)]
wood_rx=pitch*.486
wood_z=-.0235
wood_rz=.0448
rail_z=.0353
rail_ry=.056
rail_rz=.0280
role_y=[.191,.883]
ROPE_RAD_Y=.0175
ROPE_RAD_Z=.0064
parts=[]
def gxyz(cx,cy,cz,rx,rz,n,drip=0,seed=0,wood=False):
    ring=[]
    for j in range(n):
        t=math.tau*j/n; x,z=oval(cx,t,(rx,rz))
        # Subtle hand-cut timber form at twelve sides; no through-holes.
        y=cy+drip*(.57*math.cos(t*3+seed)+.28*math.sin(t*5-.37*seed)+.15*math.cos(t*2))
        if wood:
            x*=1+ .012*math.sin(j*4+seed)
            z*=1+.018*math.cos(j*2+seed)
        ring.append((cx+x,y,cz+z))
    return np.array(ring)
for i,x in enumerate(centers):
    label=f'post{i+1}'
    top=1.465-[.019,.006,0.,.019,.011,.003,.019,.012][i]
    root_rings=[gxyz(x,y,wood_z,wood_rx*r,wood_rz*d,12,seed=i*.93,wood=True)
            for y,r,d in [(0,.92,.95),(.032,.99,1),(.25,1,.98),(.52,1.007,1),(.85,.99,.98),(1.083,.98,.96),(1.142,.85,.83)]]
    tube('amber_logs',label,root_rings,'up')
    # Broad cap skirt fills the front gap with contact and stays below the
    # visible razor outline: in 33036 the log/snow borders nearly touch.
    Z=wood_z+.007
    skirt=top-.40
    caps=[gxyz(x,skirt,Z,pitch*.464,.0475,16,drip=.033,seed=i*1.3),
          gxyz(x,skirt+.073,Z,pitch*.488,.0620,16,drip=.011,seed=i*1.3),
          gxyz(x+.004*math.sin(i),top-.236,Z,pitch*.453,.056,16),
          gxyz(x+.004*math.sin(i),top-.115,Z,pitch*.302,.040,16),
          gxyz(x+.007*math.sin(i),top-.035,Z,pitch*.138,.022,16),
          gxyz(x+.007*math.sin(i),top,Z,pitch*.028,.006,16)]
    tube('soft_snow',label+'_icing',caps,'up')
    parts.append({'module':i+1,'log_x_center_m':x,'cap_apex_m':top})
def crossbar(y,z):
    r=[]
    for x,k in [(-W*.5+.007,.74),(-W*.5+.024,.98),(-W*.5+.046,1.),(W*.5-.046,1.),(W*.5-.024,.98),(W*.5-.007,.74)]:
        r.append(np.array([(x,y+rail_ry*k*math.cos(t),z+rail_rz*k*math.sin(t)) for t in [math.tau*j/16 for j in range(16)]]))
    return r
for i,y in enumerate(role_y):
    tube('front_rounded_rails',f'front_rail_{i+1}',crossbar(y,rail_z))
def sample_track(y):
    front=[];rear=[]
    # One unbroken baked front zigzag per crossbar; rear is a nearly
    # level progression with only shallow scallop between adjacent logs.
    # Bridge around actual closed ends on left/right, not duplicated silhouettes.
    for i,x in enumerate(centers):
        for j in range(9):
            if i>0 and j==0:continue
            f=j/8
            dx=pitch*(f-.5)
            frac=f
            off=.042*math.cos(2*math.pi*frac)-.003*math.sin(2*math.pi*frac)
            localz=rail_z+rail_rz*math.sqrt(max(.06,1-(off/rail_ry)**2))-.0028
            px=x+dx
            px=max(-W/2+.024,min(W/2-.024,px))
            front.append(np.array([px,y+off,localz]))
    for i,x in reversed(list(enumerate(centers))):
        for j in range(8,-1,-1):
            if i<7 and j==8:continue
            f=j/8
            zz=wood_z-wood_rz-.004+.012*(.5+.5*math.cos(2*math.pi*f))
            px=max(-W/2+.024,min(W/2-.024,x+pitch*(f-.5)))
            rear.append(np.array([px,y+.004*math.cos(2*math.pi*f),zz]))
    def carry(a,b,sgn):
        m=(a+b)*.5
        # A half-ellipse tangent to both longitudinal rope runs, not a corner.
        return [np.array([sgn*(W/2-.024+.015*math.sin(t)),m[1]+(a[1]-m[1])*math.cos(t),
                          m[2]+(a[2]-m[2])*math.cos(t)])
                for t in [math.pi*j/8 for j in range(1,8)]]
    return front+carry(front[-1],rear[0],1)+rear+carry(rear[-1],front[0],-1),front,rear
tracks=[]
for i,y in enumerate(role_y):
    P,front,rear=sample_track(y)
    rings=[]
    for k,c in enumerate(P):
        tangent=P[(k+1)%len(P)]-P[(k-1)%len(P)];tangent/=np.linalg.norm(tangent)
        radial=np.cross(tangent,np.array([0.,1.,0.]));radial/=np.linalg.norm(radial)
        binormal=np.cross(tangent,radial)
        rr=[]
        corners={0:.48,1:.64,2:.84,62:.84,63:.64,64:.48,65:.50,66:.65,67:.81,
                 70:.80,71:.75,72:.72,135:.84,136:.70,137:.69,138:.74,141:.72,142:.55,143:.48}
        taper=corners.get(k,1.0)
        for j in range(8):
            a=math.tau*j/8
            # 3D closed rope with actual cross sections and mild twist relief.
            ripple=1+.035*math.cos(a*3-k*.73)
            rr.append(c+taper*ripple*(radial*ROPE_RAD_Z*math.cos(a)+binormal*ROPE_RAD_Y*math.sin(a)))
        rings.append(np.array(rr))
    tube('ivory_hemp',f'continuous_front_zigzag_rear_level_{i+1}',rings+[rings[0]],capped=False)
    tracks.append({'track':i+1,'front_run_samples':len(front),'rear_run_samples':len(rear),
                   'front_vertical_centerline_m':float(np.ptp(np.array(front)[:,1])),
                   'rear_vertical_centerline_m':float(np.ptp(np.array(rear)[:,1])),
                   'continuous_around_both_visible_end_profiles':True})
C=root/'candidate';C.mkdir(exist_ok=True)
out=C/'FenceOwner33036.obj'
lines=['# Fresh reference reconstruction from owner 33036; no game import or approval','mtllib FenceOwner33036.mtl','o FenceOwner33036','s 1']
normals=[];verts=[];material_groups=[]
for label,fa in faces.items():
    # Smooth measured wood/snow curves, retain distinct subassemblies.
    acc={}
    material_groups.append((label,len(verts)+1,len(fa)))
    for (a,b,c),part in zip(fa,groups[label]):
        n=np.cross(b-a,c-a)
        for q in (a,b,c):
            key=(part,*q);acc[key]=acc.get(key,np.zeros(3))+n
    for f,part in zip(fa,groups[label]):
        for q in f:
            n=acc[(part,*q)]
            verts.append(q);normals.append(n/np.linalg.norm(n))
verts=np.array(verts);normals=np.array(normals)
assert np.isfinite(normals).all()
mn,mx=verts.min(0),verts.max(0)
assert np.all(mn>=L-1e-9) and np.all(mx<=U+1e-9),(mn,mx,L,U)
lines+=['v '+' '.join(f'{x:.9f}' for x in t) for t in verts]
lines+=['vn '+' '.join(f'{x:.9f}' for x in t) for t in normals]
for label,x,n in material_groups:
    lines.append('usemtl '+label)
    for i in range(x,x+3*n,3):lines.append('f '+' '.join(f'{j}//{j}' for j in range(i,i+3)))
out.write_text('\n'.join(lines)+'\n')
mtl=C/'FenceOwner33036.mtl'
mtl.write_text('newmtl amber_logs\nKd 0.81 0.43 0.17\nPr 0.83\nnewmtl soft_snow\nKd 0.94 0.956 0.99\nPr 0.79\nnewmtl front_rounded_rails\nKd 0.69 0.34 0.15\nPr 0.85\nnewmtl ivory_hemp\nKd 0.94 0.78 0.51\nPr 0.87\n')
res=dict(reference_sha=sha(ref),collision_envelope_source_sha=sha(env),obj_sha=sha(out),mtl_sha=sha(mtl),geometry_min_max=[mn.tolist(),mx.tolist()],
    old_art_envelope_min_max=[L.tolist(),U.tolist()],world_depth_if_using_protected_1_95_scale=float((mx[2]-mn[2])*1.95),
    section_counts={k:len(x) for k,x in faces.items()},log_count=8,rounded_rail_count=2,tracks=tracks,modules=parts,
    relative_rail_heights_over_panel=[y/1.465 for y in role_y],no_runtime_engine_or_route_changes=True)
(root/'build-result.json').write_text(json.dumps(res,indent=2)+'\n')
