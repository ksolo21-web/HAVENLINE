"""Author owner 33035 gate/threshold posts, not a scene or collider edit."""
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import math
import numpy as np
import json

root=Path(__file__).resolve().parent
ref=root.parent/'hvn-owner-fence-33036-33035/33035.png'
assert sha256(ref.read_bytes()).hexdigest()=='bd17e02a2999294e032d78ee93b61228658fae060da77c241934bd3fad0a01a8'
for name,h in {'33039.png':'85712d3260ab7be14f40cd0371fa48703b74c99000e7cf25c3d3e30dd79e7548',
               '33040.png':'7e86d259cf4cf67d3a795ab0bb150d8ce67af7a03a23c240a8dd0e0cec137bdd'}.items():
    assert sha256(ref.with_name(name).read_bytes()).hexdigest()==h
intake=root.parent/'hvn-meshy-gate-33035-intake-v1'
assert sha256((intake/'SHA256SUMS').read_bytes()).hexdigest()=='abd120941854d0d3ad3f87d57c2f3750fc80bd7cc6ed91363a3f117016e1238f'
master=root.parent/'hvn-owner-fence-33036-33035/meshy-models/gate-front.glb'
assert sha256(master.read_bytes()).hexdigest()=='c5256ca7ac3956c91b19654076afa80b96fede20873be704136ab89edf4709b3'

out=root/'candidate';out.mkdir(exist_ok=True)
def v(x,y,z): return np.array((x,y,z),float)
def unit(x): return x/np.linalg.norm(x)
@dataclass
class Piece:
    name:str
    mat:str
    vertices:list
    tris:list
def signed(verts,tris):
    a,b,c=np.asarray(verts)[np.asarray(tris)].transpose(1,0,2)
    return float(np.sum(np.einsum('ij,ij->i',a,np.cross(b,c)))/6)
def solid(name,mat,rings,end0=True,end1=True):
    n=len(rings[0]); V=list(np.concatenate(rings));T=[]
    for i in range(len(rings)-1):
        for j in range(n):
            a=i*n+j; b=i*n+(j+1)%n; c=b+n; d=a+n
            T.extend([(a,b,c),(a,c,d)])
    if end0:T.extend([(0,j+1,j) for j in range(1,n-1)])
    p=(len(rings)-1)*n
    if end1:T.extend([(p,p+j,p+j+1) for j in range(1,n-1)])
    if signed(V,T)<0:T=[(a,c,b) for a,b,c in T]
    return Piece(name,mat,V,T)
def rounded_poly(w,h,r,steps=4):
    out=[]
    for a,cx,cy in [(0,w/2-r,h/2-r),(90,-w/2+r,h/2-r),(180,-w/2+r,-h/2+r),(270,w/2-r,-h/2+r)]:
        for k in range(steps+1):
            th=math.radians(a+90*k/steps)
            out.append((cx+r*math.cos(th),cy+r*math.sin(th)))
    return np.asarray(out,float)
def board(name,mat,x,y,w,h,z0,z1,r,angle=0):
    xy=rounded_poly(w,h,r); ca,sa=math.cos(angle),math.sin(angle)
    rings=[]; dz=min(.006,(z1-z0)/3)
    for z,scale in [(z0,.92),(z0+dz,1),(z1-dz,1),(z1,.92)]:
        rings.append([v(x+scale*(a*ca-b*sa),y+scale*(a*sa+b*ca),z) for a,b in xy])
    return solid(name,mat,rings)
def brace(name,a,b):
    a,b=np.array(a),np.array(b); c=(a+b)/2; d=b-a
    return board(name,'frame',*c,float(np.linalg.norm(d)),.112,.024,.061,.012,math.atan2(d[1],d[0]))
def turned(name,mat,center,profile,n=24):
    rings=[]
    for y,r in profile:
        rings.append([center+v(r*math.cos(i*math.tau/n),y,r*math.sin(i*math.tau/n)) for i in range(n)])
    return solid(name,mat,rings)
def tube(name,mat,center,mid_y,phase):
    n,m=48,10; R=.145; rad=.012
    rings=[]
    for i in range(n):
        t=i*math.tau/n
        yp=.007*math.sin(2*t+phase)
        rings.append([center+v((R+rad*math.cos(j*math.tau/m))*math.cos(t),mid_y+yp+rad*math.sin(j*math.tau/m),(R+rad*math.cos(j*math.tau/m))*math.sin(t)) for j in range(m)])
    V=list(np.concatenate(rings));T=[]
    for i in range(n):
        k=(i+1)%n
        for j in range(m):
            a=i*m+j;b=i*m+(j+1)%m;c=k*m+(j+1)%m;d=k*m+j
            T.extend([(a,b,c),(a,c,d)])
    if signed(V,T)<0:T=[(a,c,b) for a,b,c in T]
    return Piece(name,mat,V,T)
def crown():
    # Sheet 33039 oblique: rolled deep top, softly scalloped low skirt front AND rear.
    # Use existing center/end limits and identical station/ring count.
    rings=[];stations=39;sides=18
    for i in range(stations+1):
        t=i/stations;x=.073+1.084*t
        soften=min(1.,.59+min(t,1-t)*16)
        wave=.004*math.sin(math.tau*3.2*t)+.003*math.cos(math.tau*6.1*t)
        yc=1.273+wave*soften
        radius_z=.043+.013*min(1.,max(0.,(x-.19)/.07))
        drape=(.083+.018*math.sin(math.tau*4.0*t+.43)**2)*soften
        row=[]
        for j in range(sides):
            q=j*math.tau/sides
            cy,sz=math.cos(q),math.sin(q)
            rounded_rim=(1+.09*math.sin(math.tau*3.4*t+sz*.85)*max(0.,-cy))
            depth=(.048 if x<.19 else radius_z)*soften*rounded_rim
            yy=yc+(0.054*soften if cy>=0 else drape)*cy
            zz=.007+depth*sz
            # Protect the already-qualified old rear-most hardware envelope on the scarf.
            row.append(v(x,yy,max(-.054,min(.067,zz))))
        rings.append(row)
    return solid('soft_continuous_snow_ridge','snow',rings)
def horizontal_rod(name,x,y,z,profile,flatten=1.0):
    # Revolute hardware axis along wood plane's X, cap edges softly beveled.
    a=turned(name,'iron',v(0,0,0),profile,24)
    a.vertices=[v(x+ty,y-tx,z+flatten*tz) for tx,ty,tz in a.vertices]
    return a
def knob(name,x,y,z,direction):
    a=turned(name,'iron_soft',v(0,0,0),[(0,.024),(.003,.026),(.008,.023),(.017,.016),(.020,.009)],24)
    a.vertices=[v(x+tx,y-direction*tz,z+direction*ty) for tx,ty,tz in a.vertices]
    return a
def leaf(owner):
    p=[]
    # Chunky stiles and top/bottom rails, no rear diagonal brace.
    p.extend([board('outer_stile','frame',.084,.665,.154,1.174,-.016,.057,.020),
              board('center_stile','frame',1.098,.665,.160,1.174,-.028,.059,.018),
              board('top_rail','frame',.623,1.162,1.030,.177,-.016,.054,.018),
              board('base_rail','frame',.623,.190,1.030,.178,-.016,.054,.018)])
    for k in range(7):
        p.append(board('vertical_board_'+str(k),('wood_even','wood_amber','wood_soft')[k%3],.221+k*.130,.673,.126,.980,-.015 if k==0 else -.030,.030,.010))
    lines=[((.164,.267),(1.054,1.078)),((.173,1.083),(.553,.727)),((.660,.628),(1.055,.267))]
    p.extend(brace('front_x_'+str(k),a,b) for k,(a,b) in enumerate(lines))
    p.append(crown())
    for k,y in enumerate((.278,1.125)):
        p.append(board('hinge_plate_'+str(k),'iron',.099,y,.131,.089,.025,.062,.011))
        p.append(turned('barrel_hinge_'+str(k),'iron',v(.034,y,.049),[(-.071,.014),(-.062,.019),(.064,.019),(.072,.014)],20))
        p.append(turned('hinge_pin_top_'+str(k),'iron_soft',v(.034,y,.049),[(.070,.010),(.076,.012),(.080,.008)],20))
    # Owner-sheet front grouping and rear paired dots are distinct hardware,
    # not a bridge or an animation: front image-left leaf owns the handle.
    if owner:
        p.append(board('front_handle_rosette','iron_soft',1.056,.681,.078,.096,.044,.068,.020))
        p.append(horizontal_rod('front_handle_owned_bar',1.107,.681,.058,[(-.066,.014),(-.055,.020),(.055,.020),(.071,.014)],.49))
    else:
        p.append(board('front_receiver_keeper','iron',1.135,.681,.078,.080,.044,.069,.016))
    p.append(knob('rear_owned_knob_dot',1.138,.681,-.025,-1.))
    return p
def post():
    p=[]; c=v(0,0,0)
    p.append(turned('rounded_threshold_log','wood_amber',c,[(0,.124),(.018,.137),(.08,.142),(.565,.131),(1.155,.141),(1.480,.143),(1.52,.119)],36))
    # High volume dome skirt variations reference a rounded drape, not a white polygon strip.
    rings=[]; n=45
    for y,r,skirt in [(1.421,.138,1),(1.455,.155,.95),(1.504,.157,.6),(1.575,.138,.25),(1.674,.094,.12),(1.755,.044,.04),(1.776,.008,0)]:
        rings.append([v(r*math.cos(t),y+skirt*(.018*math.sin(5*t+.3)+.006*math.sin(7*t)),r*math.sin(t)) for t in (i*math.tau/n for i in range(n))])
    p.append(solid('rounded_draped_post_snow','snow',rings))
    for b,y in enumerate((.315,1.112)):
        for k,(offset,phase) in enumerate(((-.0185,0),(.0185,math.pi))):
            p.append(tube('post_wrap_%s_%s'%(b,k),'rope' if k==0 else 'rope_soft',c,y+offset,phase))
    for k,y in enumerate((.332,1.181)):
        # Static mate plates seat into the log at local x=.097 and stop before
        # the hinge plane; they are entirely on the positive-depth side.
        p.append(board('fixed_post_hinge_mate_'+str(k),'iron',.143,y,.092,.077,.040,.071,.010))
    return p
def write(P,name,side):
    q=out/name
    lines=['# owner 33035 detached study; no collision or gameplay edit','mtllib owner33035.mtl','o '+q.stem]
    st=1
    for a in P:
        lines+=['g '+a.name,'usemtl '+a.mat]
        lines += ['v %.7f %.7f %.7f'%(x*side,y,z) for x,y,z in a.vertices]
        lines += ['f %d %d %d'%(i+st,j+st,k+st) for i,j,k in (a.tris if side==1 else [(i,k,j) for i,j,k in a.tris])]
        st+=len(a.vertices)
    q.write_text('\n'.join(lines)+'\n')
    return dict(sha256=sha256(q.read_bytes()).hexdigest(),triangles=sum(len(a.tris) for a in P),closed_components=len(P))
P=leaf(True); R=leaf(False); Q=post()
print(json.dumps({'left':write(P,'GateLeaf.obj',1),'right':write(R,'GateLeaf_Right.obj',-1),'post_left':write(Q,'ThresholdPost.obj',1),'post_right':write(Q,'ThresholdPost_Right.obj',-1)},indent=2))
