"""Generate a bounded authored draft panel from exact R17 post component seats."""
import hashlib,json,math,sys
from collections import Counter
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
original=Path(sys.argv[1])
assert hashlib.sha256(original.read_bytes()).hexdigest()=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
v=np.array([[float(a) for a in l.split()[1:4]] for l in original.read_text().splitlines() if l.startswith('v ')])
assert len(v)==1920
WALL_DEPTH_SCALE=1.95
TAU=math.tau
matfaces={'timber':[],'snow':[],'rope':[]}
def add(token,a,b,c):
    a,b,c=map(np.asarray,(a,b,c))
    assert np.linalg.norm(np.cross(b-a,c-a))>1e-10
    matfaces[token].append((a,b,c))
def loft(token,rings,orient='y',cap_ends=True):
    n=len(rings[0])
    for a,b in zip(rings,rings[1:]):
        for j in range(n):
            k=(j+1)%n
            if orient=='y':
                add(token,a[j],b[j],a[k]); add(token,a[k],b[j],b[k])
            else:
                add(token,a[j],a[k],b[j]); add(token,a[k],b[k],b[j])
    if cap_ends:
        a,b=rings[0],rings[-1]
        ca,cb=np.mean(a,axis=0),np.mean(b,axis=0)
        for j in range(n):
            k=(j+1)%n
            add(token,ca,a[j],a[k]); add(token,cb,b[k],b[j])
def te(i,n):
    t=TAU*i/n
    return math.cos(t),math.sin(t)
def ovoid(cx,q,c,b):
    return [(cx+q[0]*x,q[1]+(c[i] if isinstance(c,list) else c),q[2]+b*z)
            for i,(x,z) in enumerate(te(j,12) for j in range(12))]
modules=[]
for post_num in range(10):
    source=v[post_num*192:(post_num+1)*192]
    lo,hi=source.min(0),source.max(0)
    cx=(lo[0]+hi[0])*.5
    z_mid=(lo[2]+hi[2])*.5
    yar=np.unique(source[:,1])
    roof_seat=yar[1]
    timber_top=yar[2]
    def timber_ring(y,xradius,zradius):
        # Broad faces with soft hewn corners. X and Z extents remain exact.
        wx,wz=.80,.65
        profile=[(1,0),(1,wz),(wx,1),(-wx,1),(-1,wz),(-1,-wz),
                 (-wx,-1),(wx,-1),(1,-wz)]
        return [(cx+xradius*x,y,zradius*z) for x,z in profile]
    # Two narrow working waists create room for round cross-lashings INSIDE
    # the original outer footprint; thick wood immediately above/below.
    belts=(.325,.735)
    profile=[(0,.1325,.070)]
    for y in belts:
        profile += [(y-.100,.1325,.070),(y-.069,.112,.039),
                    (y+.069,.112,.039),(y+.100,.1325,.070)]
    profile += [(timber_top,.1325,.070)]
    loft('timber',[timber_ring(*x) for x in profile])
    # Crown silhouette is a rounded asymmetric loft, not an engine primitive.
    # Its single full-width ring preserves original X and Z outer join envelope.
    rx=(hi[0]-lo[0])*.5; rz=(hi[2]-lo[2])*.5
    top=hi[1]
    skirts=[]
    for j in range(12):
        t=TAU*j/12
        wave=.010*math.sin(3*t+post_num*.8)+.006*math.cos(5*t-.7*post_num)
        skirts.append(.016+wave)
    snow=[
      ovoid(cx,(rx*.87,roof_seat,z_mid),skirts,rz*.85),
      ovoid(cx,(rx,roof_seat+.082,z_mid),0.,rz),
      ovoid(cx,(rx*.84,roof_seat+.157,z_mid+.002),0.,rz*.86),
      ovoid(cx+.008*math.sin(post_num),(rx*.53,roof_seat+.247,z_mid+.004),0.,rz*.60),
      ovoid(cx+.012*math.sin(post_num),(rx*.26,top-.050,z_mid+.003),0.,rz*.32),
      ovoid(cx+.014*math.sin(post_num),(rx*.067,top,z_mid+.003),0.,rz*.11)]
    loft('snow',snow)
    # Each crossing is two closed independent ropes. The same signed X slopes
    # cross on both elevations, and variable radius chooses an over/under layer
    # at the front/back center; each ring is computed in an actual 3D frame.
    for belt in belts:
        for strand in (-1,1):
            centers=[]
            for j in range(12):
                co,si=te(j,12)
                arch=abs(si)**7
                # At near-vertical crossings a thicker separation in Z keeps
                # separate tubes, while each path still wraps around the sides.
                cx_rope=.118*co
                z_rope=(.0547 + strand*.009*si*arch)*si
                centers.append(np.array((cx+cx_rope,belt+strand*.058*co,z_rope)))
            rings=[]
            for j,pt in enumerate(centers):
                tangent=centers[(j+1)%len(centers)]-centers[(j-1)%len(centers)]
                tangent/=np.linalg.norm(tangent)
                n=np.cross(tangent,[0.,1.,0.]); n/=np.linalg.norm(n)
                b=np.cross(tangent,n)
                ring=[]
                for k in range(5):
                    co,si=te(k,5)
                    ring.append(pt+.0069*(co*n+si*b))
                rings.append(ring)
            # Ring order n,b relative to the forward tubular axis.
            loft('rope',rings+[rings[0]],orient='axial',cap_ends=False)
            # Every individual rope must have supported contact, and exposed
            # contour must not be swallowed by the timber under its entire path.
            waist=np.array(timber_ring(belt,.112,.039))[:,[0,2]]
            contact=[]
            for rp in rings:
                d=[]
                for a in rp:
                    pt=a[[0,2]]
                    e=np.roll(waist,-1,axis=0)-waist
                    g=pt-waist
                    half=(e[:,0]*g[:,1]-e[:,1]*g[:,0])/np.linalg.norm(e,axis=1)
                    d.append(float(min(half)))
                if min(d)>=0.:
                    raise ValueError('hidden rope ring')
                if max(d)>=-.001:
                    contact.append(max(d))
            assert len(contact)>=2, (post_num,belt,strand,contact)
    modules.append({'post_index':post_num,'center_x_m':cx,'y_extent_m':[0.,top],
                    'two_belt_heights_m':list(belts),'two_closed_strands_per_belt':True})
out=root/'candidate'
out.mkdir(exist_ok=True)
lines=['# Reference-led details, detached rest mesh; no import or approval',
       'mtllib reference_detail.mtl','o FenceReferenceDetail']
vertices=[]; normals=[]; authorities=[]
for mat,faces in matfaces.items():
    authorities.append((mat,len(vertices)+1,len(faces)))
    smooth={}
    if mat in ('snow','rope'):
        for a,b,c in faces:
            n=np.cross(b-a,c-a)
            for x in (a,b,c):
                k=tuple(x)
                smooth[k]=smooth.get(k,np.zeros(3))+n
    for a,b,c in faces:
        face=np.array((a,b,c))
        normal=np.cross(b-a,c-a); normal/=np.linalg.norm(normal)
        vertices.extend(face)
        if smooth:
            normals.extend([smooth[tuple(x)]/np.linalg.norm(smooth[tuple(x)]) for x in face])
        else:
            normals.extend([normal]*3)
vertices=np.array(vertices); normals=np.array(normals)
lower,upper=vertices.min(0),vertices.max(0)
assert np.allclose(lower,v.min(0),rtol=0,atol=1e-9) and np.allclose(upper,v.max(0),rtol=0,atol=1e-9)
lines += [f'v {a:.9f} {b:.9f} {c:.9f}' for a,b,c in vertices]
lines += [f'vn {a:.9f} {b:.9f} {c:.9f}' for a,b,c in normals]
for mat,first,count in authorities:
    lines.append('usemtl '+mat)
    for off in range(0,count*3,3):
        lines.append('f '+' '.join(f'{i}//{i}' for i in range(first+off,first+off+3)))
mesh=out/'fence_reference_detail.obj'
mesh.write_text('\n'.join(lines)+'\n')
# MTL fallback uses fixed source palette, no texture/global light; repaired R17
# shader experiment may independently override it only at explicit adoption.
(out/'reference_detail.mtl').write_text('newmtl timber\nKd .76 .53 .40\nnewmtl snow\nKd .95 .985 1.0\nnewmtl rope\nKd .63 .455 .284\n')
receipt={'title':'Detached authored detail only; no native import, shading or appearance claim',
 'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
 'candidate_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),
 'stock_local_aabb_m': [lower.tolist(),upper.tolist()],
 'world_depth_after_exact_r17_scale_m':(upper[2]-lower[2])*WALL_DEPTH_SCALE,
 'overall_height_m':float(upper[1]-lower[1]),
 'panel_triangle_budget':{k:len(f) for k,f in matfaces.items()},
 'whole_camp_triangles_if_12_instances':sum(map(len,matfaces.values()))*12,
 'module_count':len(modules),'rope_strands':40,'lash_locations_per_panel':20,
 'curved_snow_crowns':10,'no_gate_floor_path_light_shader_collision_or_scene_edits':True,'modules':modules}
(root/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
