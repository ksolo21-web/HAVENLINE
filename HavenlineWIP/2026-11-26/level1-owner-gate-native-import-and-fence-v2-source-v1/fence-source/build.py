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
def sample_track(y,hand):
    front=[];rear=[]
    # Phase alternates smoothly at shared post boundaries. Each log interval
    # has a single X from two distinct full strands, not paired V decals.
    for k in range(81):
        s=k/10.0
        x=-W/2+W*k/80
        base=np.cos(math.pi*s)
        offset=hand*.038*base
        crossover=(1-base*base)**11
        face=rail_z+rail_rz*math.sqrt(max(.06,1-(offset/rail_ry)**2))
        # Two flattened contact shoulders inside the unchanged relative depth.
        # Negative hand stays at rail surface; positive hand lays across it.
        center_z=face-.0028+crossover*(.0021 if hand<0 else .0048)
        x=max(-W/2+.027,min(W/2-.027,x))
        front.append((np.array([x,y+offset,center_z]),.0057*(1-crossover)+.0016*crossover,.0156))
    for k in range(80,-1,-1):
        s=k/10.
        x=-W/2+W*k/80
        f=s%1.
        z=wood_z-wood_rz-.0035+.010*(.5+.5*math.cos(math.tau*f))
        x=max(-W/2+.027,min(W/2-.027,x))
        rear.append((np.array([x,y+hand*.012+.003*math.cos(math.tau*f),z]),.0064,.0108))
    def carry(a,b,sgn):
        a,b=a[0],b[0]; mid=(a+b)*.5
        return [(np.array([sgn*(W/2-.027+.014*math.sin(t)),mid[1]+(a[1]-mid[1])*math.cos(t),
                            mid[2]+(a[2]-mid[2])*math.cos(t)]),.0044,.0093)
                for t in [math.pi*j/10 for j in range(1,10)]]
    return front+carry(front[-1],rear[0],1)+rear+carry(rear[-1],front[0],-1),front,rear
tracks=[]
for i,y in enumerate(role_y):
    for hand in (-1,1):
        P,front,rear=sample_track(y,hand)
        rings=[]
        for k,(c,radius_z,radius_y) in enumerate(P):
            tangent=P[(k+1)%len(P)][0]-P[(k-1)%len(P)][0];tangent/=np.linalg.norm(tangent)
            radial=np.cross(tangent,np.array([0.,1.,0.]));radial/=np.linalg.norm(radial)
            up=np.cross(tangent,radial)
            ring=[]
            corner = min(k,len(P)-k,abs(k-80),abs(k-90),abs(k-170))
            taper=.53+.47*min(corner/4,1)
            for q in range(6):
                a=math.tau*q/6
                relief=1+.022*math.cos(a*3-k*.47)
                ring.append(c+taper*relief*(radial*radius_z*math.cos(a)+up*radius_y*math.sin(a)))
            rings.append(np.array(ring))
        label='ivory_hemp_warm' if hand<0 else 'ivory_hemp_cream'
        tube(label,f'front_X_distinct_return_{i+1}_{hand}',rings+[rings[0]],capped=False)
        tracks.append({'track_level':i+1,'handed_course':hand,'front_run_samples':len(front),'rear_run_samples':len(rear),
                       'front_vertical_centerline_m':float(np.ptp(np.array([r[0] for r in front])[:,1])),
                       'rear_vertical_centerline_m':float(np.ptp(np.array([r[0] for r in rear])[:,1])),
                       'returns_only_at_actual_isolated_module_ends':True})
C=root/'candidate';C.mkdir(exist_ok=True)
out=C/'FenceOwner33036V2.obj'
lines=['# Fresh reference reconstruction from owner 33036; no game import or approval','mtllib FenceOwner33036V2.mtl','o FenceOwner33036V2','s 1']
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
assert (mx[2]-mn[2])*1.95 <= .28448356346880777+1e-8,(mn,mx)
lines+=['v '+' '.join(f'{x:.9f}' for x in t) for t in verts]
lines+=['vn '+' '.join(f'{x:.9f}' for x in t) for t in normals]
for label,x,n in material_groups:
    lines.append('usemtl '+label)
    for i in range(x,x+3*n,3):lines.append('f '+' '.join(f'{j}//{j}' for j in range(i,i+3)))
out.write_text('\n'.join(lines)+'\n')
mtl=C/'FenceOwner33036V2.mtl'
mtl.write_text('newmtl amber_logs\nKd 0.81 0.43 0.17\nPr 0.83\nnewmtl soft_snow\nKd 0.94 0.956 0.99\nPr 0.79\nnewmtl front_rounded_rails\nKd 0.69 0.34 0.15\nPr 0.85\nnewmtl ivory_hemp_warm\nKd 0.91 0.73 0.46\nPr 0.87\nnewmtl ivory_hemp_cream\nKd 0.97 0.83 0.56\nPr 0.87\n')
res=dict(reference_sha=sha(ref),collision_envelope_source_sha=sha(env),obj_sha=sha(out),mtl_sha=sha(mtl),geometry_min_max=[mn.tolist(),mx.tolist()],
    old_art_envelope_min_max=[L.tolist(),U.tolist()],world_depth_if_using_protected_1_95_scale=float((mx[2]-mn[2])*1.95),
    section_counts={k:len(x) for k,x in faces.items()},log_count=8,rounded_rail_count=2,tracks=tracks,modules=parts,
    relative_rail_heights_over_panel=[y/1.465 for y in role_y],no_runtime_engine_or_route_changes=True)
(root/'build-result.json').write_text(json.dumps(res,indent=2)+'\n')
