"""Provenance-bound four-face dart UV continuation onto the owner's exact fleece chart."""
import hashlib, io, json, struct
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize
from scipy.sparse.csgraph import connected_components
from PIL import Image, ImageDraw

here=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
source=here.parent/'c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb'
B=source.read_bytes()
assert sha(B)=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
d=here.parent/'hvn-l1-c1-cuff-relief-reroute-v1'; m=d/'SHA256SUMS'
assert sha(m.read_bytes())=='650ce1bd4399f51c6821e58a2ac6d33c5ae993add963859ba827957bd7944142'
for line in m.read_text().splitlines():
    h,f=line.split(maxsplit=1); assert sha((d/f).read_bytes())==h,f
q=np.load(d/'editable_cuff_relief.npz'); P=q['bind']; OP=q['open']
F={int(i):list(map(int,f)) for i,f in zip(q['original_face_ids'],q['triangles'])}
UV={int(i):u.copy() for i,u in zip(q['original_face_ids'],q['corner_uv'])}
locked=set(map(int,q['verified_existing_L0_face_rows']))
dart=[122,123,124,125]
assert not locked & set(dart) and 72 in locked and 88 not in dart
assert [F[i] for i in dart]==[[77,0,104],[77,103,81],[0,103,104],[103,77,104]]
n=struct.unpack_from('<I',B,12)[0]; gltf=json.loads(B[20:20+n]); start=20+n+8
def view(i):
    v=gltf['bufferViews'][i]; off=start+v.get('byteOffset',0)
    return memoryview(B)[off:off+v['byteLength']]
def accessor(i):
    a=gltf['accessors'][i]; t={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]; dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
    return np.frombuffer(view(a['bufferView']),dtype=dt,offset=a.get('byteOffset',0),count=a['count']*t).reshape(-1,t)
prim=gltf['meshes'][0]['primitives'][0]
srcp=accessor(prim['attributes']['POSITION'])
st=accessor(prim['attributes']['TEXCOORD_0']).copy(); st[:,1]=1.-st[:,1]
sf=accessor(prim['indices']).reshape(-1,3)
un=(sf[:,[0,1,2]].ravel(),sf[:,[1,2,0]].ravel())
_, labels=connected_components(sp.coo_matrix((np.ones(len(un[0]),np.uint8),un),shape=(len(srcp),len(srcp))).tocsr(),directed=False)
srcfaces=labels[sf[:,0]]
assert (labels[sf]==srcfaces[:,None]).all()
maps=gltf['materials'][0]
channels={'base_color':maps['pbrMetallicRoughness']['baseColorTexture'],
          'metal_rough':maps['pbrMetallicRoughness']['metallicRoughnessTexture'],'normal':maps['normalTexture']}
assert prim['material']==0 and all(c.get('texCoord',0)==0 and not c.get('extensions') for c in channels.values())
raw={k:view(gltf['images'][gltf['textures'][v['index']]['source']]['bufferView']) for k,v in channels.items()}
img={k:Image.open(io.BytesIO(b)).convert('RGB') for k,b in raw.items()}
assert all(i.size==(2048,2048) for i in img.values())
N=2048
TV=st[sf].astype(np.float64); LO=TV.min(1); HI=TV.max(1)
def bary(s,t):
    x=np.linalg.solve((t[1:]-t[0]).T,s-t[0]);return np.r_[1-x.sum(),x]
def locate(s):
    rows=np.flatnonzero(((LO<=s)&(HI>=s)).all(1))
    out=[]
    for i in rows:
        if abs(area2(TV[i]))<1e-18:continue
        bc=bary(s,TV[i])
        if min(bc)>=-1e-8:
            out.append({'face_row':int(i),'indexed_uv_component':int(srcfaces[i]),'barycentric':bc.tolist(),
                       'source_gltf_position_m':(bc@srcp[sf[i]]).tolist()})
    return out
def area2(u):
    a,b=u[1:]-u[0]
    return float(a[0]*b[1]-a[1]*b[0])
u0=UV[120][1].astype(np.float64); u77=UV[120][2].astype(np.float64)
anchor0=locate(u0); anchor77=locate(u77)
assert anchor0[0]['face_row']==698140 and anchor77[0]['face_row']==697800
assert len(anchor0)==len(anchor77)==1 and anchor0[0]['indexed_uv_component']==anchor77[0]['indexed_uv_component']==1031
assert np.array_equal(UV[122][1],u0)
assert locate(np.array([.5,.5]))[0]['indexed_uv_component']==51
def rgb(s,i):
    # GLTF bilinear footprint with normalized image origin at upper left.
    u=s[0]*N-.5; v=(1-s[1])*N-.5
    a=int(np.floor(u)); b=int(np.floor(v)); d=u-a; e=v-b
    return np.asarray(i.getpixel((a,b)))*(1-d)*(1-e)+np.asarray(i.getpixel((a+1,b)))*d*(1-e)+np.asarray(i.getpixel((a,b+1)))*(1-d)*e+np.asarray(i.getpixel((a+1,b+1)))*d*e

chart_rows=np.flatnonzero(srcfaces==1031); chart=TV[chart_rows]
assert len(chart)==1734
def edgemap(ff,sel):
    d=defaultdict(list)
    for i in sel:
        f=ff[i]
        for j in range(3):
            a,b=int(f[j]),int(f[(j+1)%3]); d[tuple(sorted((a,b)))].append((a,b,int(i)))
    return d
c_edges=edgemap(sf,chart_rows)
rim=np.asarray([s for s,g in c_edges.items() if len(g)==1])
assert len(rim)>10 and max(map(len,c_edges.values()))==2
edges=st[rim].astype(np.float64)
def min_point_seg(p,a,b):
    d=b-a; n=float(d@d); return np.linalg.norm(p-(a+np.clip((p-a)@d/n,0,1)*d)) if n else np.linalg.norm(p-a)
def unsigned_seg(a,b,c,d):
    # Actual continuous segment distance; includes a proper cut at 0.
    r=b-a; v=d-c; s=c-a
    cross=lambda x,y:float(x[0]*y[1]-x[1]*y[0])
    den=cross(r,v)
    if abs(den)>1e-22 and 0<=cross(s,v)/den<=1 and 0<=cross(s,r)/den<=1:return 0.
    return min(min_point_seg(a,c,d),min_point_seg(b,c,d),min_point_seg(c,a,b),min_point_seg(d,a,b))
def point_inside_convex(p,poly):
    return all(area2(np.r_[np.stack([a,b]),p[None]])>0 for a,b in zip(poly,np.roll(poly,-1,axis=0)))
def clearance(poly):
    if any(point_inside_convex(p,poly) for p in edges.reshape(-1,2)):return 0.
    return min(unsigned_seg(a,b,c,d) for a,b in zip(poly,np.roll(poly,-1,axis=0)) for c,d in edges)*N

# Instead of picking an empty atlas slot, fit to texels living in the exact
# neighboring fleece chart, with the original sew edge as the hard scale pin.
# The source AABB is not used as proof: exact rim cut tests follow below.
scale=np.linalg.norm(u0-u77)/np.linalg.norm(P[0]-P[77])
metric={(a,b):scale*np.linalg.norm(P[a]-P[b]) for a,b in [(0,103),(77,103),(103,81),(77,81),(0,81)]}
def points(w):
    a,b=np.asarray(w).reshape(2,2)
    return {0:u0,77:u77,103:u0+a/N,81:u0+b/N}
def uv_fit(w):
    x=points(w)
    return sum((np.linalg.norm(x[a]-x[b])/l-1)**2 for (a,b),l in metric.items())
def chart_polygon(w):
    ps=points(w)
    return np.stack([ps[i] for i in [77,0,103,81]])
def orient_margin(w):
    p=chart_polygon(w)
    return np.asarray([area2(p[[i,(i+1)%4,(i+2)%4]])*N*N-12. for i in range(4)])
x0=[8,16,20,22]
# Subregion traced inside the source fleece patch. Enforce full nonlinear
# segment padding in a second independent test instead of trusting bounds.
res=minimize(uv_fit,x0,method='SLSQP',bounds=[(5,16),(9,19),(15,24),(14,25.0)],
             constraints=[{'type':'ineq','fun':orient_margin}],options={'ftol':1e-11,'maxiter':200})
assert res.success,res
poly=chart_polygon(res.x).astype(UV[120].dtype).astype(np.float64)
assert point_inside_convex(poly.mean(0),poly)
# Require a four-texel conservative footprint guard, not a runtime mip claim.
padding=clearance(poly)
assert padding>=4.0,padding
low, high=np.min(poly,0),np.max(poly,0)
# Exclude other chart occupancy over the entire actual output polygon,
# not just sample points. Clip each ROI nonowner triangle against the
# convex output perimeter and measure the retained UV area.
def clip_area(A, cv):
    p=list(A)
    for a,b in zip(cv,np.roll(cv,-1,axis=0)):
        old=p;p=[]
        for x,y in zip(old,np.roll(np.asarray(old),-1,axis=0)) if old else []:
            dx,dy=area2(np.stack([a,b,x])),area2(np.stack([a,b,y]))
            if dx>=0:p.append(x)
            if dx*dy<0:p.append(x+(y-x)*dx/(dx-dy))
    return abs(sum(area2(np.stack([p[0],p[j],p[j+1]])) for j in range(1,len(p)-1))) if p else 0.
foreign=np.flatnonzero(((LO<=high)&(HI>=low)).all(1) & (srcfaces!=1031))
foreign_overlaps=[int(i) for i in foreign if clip_area(TV[i],poly)>1e-13]
assert not foreign_overlaps,foreign_overlaps
# Verify all sampled interior points recover source component 1031 uniquely;
# compute exact source source-UV bounds and certified margin for artifacts.
samp=[]
for aa in np.linspace(0,1,13):
    for bb in np.linspace(0,1,13):
        s=(poly[0]*(1-aa)+poly[1]*aa)*(1-bb)+(poly[3]*(1-aa)+poly[2]*aa)*bb
        samp.append(s)
for p in [poly.mean(0),*poly]:
    assert {r['indexed_uv_component'] for r in locate(p)}=={1031}
for p in samp:
    # Box pre-indexing keeps exact triangle lookup inexpensive and selects
    # only the chart. Distinct source face IDs are preserved in the report.
    A=chart
    k=np.flatnonzero(((A.min(1)<=p)&(A.max(1)>=p)).all(1))
    assert any(min(bary(p,A[i]))>=-1e-8 for i in k if abs(area2(A[i]))>1e-18),p
chartp={i:poly[j] for j,i in enumerate([77,0,103,81])}
# Barycentric old inside support's tangent location on the 3D base triangle:
base=P[[77,0,103]]
bb=np.linalg.lstsq((base[1:]-base[0]).T,P[104]-base[0],rcond=None)[0]
bc=np.r_[1-bb.sum(),bb]
assert bc.min()>.1
chartp[104]=bc@np.stack([chartp[i] for i in [77,0,103]])
new={i:u.copy() for i,u in UV.items()}
for i in dart:new[i]=np.asarray([chartp[j] for j in F[i]],dtype=UV[i].dtype)
assert np.array_equal(new[122][0],UV[120][2]) and np.array_equal(new[122][1],UV[120][1])
assert all(area2(new[i])>1e-6 for i in dart)
assert abs(sum(area2(new[i]) for i in dart)-sum(area2(poly[[0,a,a+1]]) for a in [1,2]))<1e-8
assert all(np.array_equal(UV[j],new[j]) for j in F if j not in dart)
g=edgemap(F,F)
seams=[]
for e,rrs in edgemap(F,dart).items():
    if len(rrs)>1:continue
    a,b,i=rrs[0]
    adj=next((rr[-1] for rr in g[e] if rr[-1]!=i),None)
    ours=np.array([new[i][F[i].index(a)],new[i][F[i].index(b)]])
    has=adj is not None
    theirs=np.array([UV[adj][F[adj].index(a)],UV[adj][F[adj].index(b)]]) if has else None
    kind='SOURCE_FLEECE_PBR_CONTINUOUS_FIXED_120' if adj==120 else ('EXPLICIT_PENDING_SEAM_OTHER_FACE' if has else 'TRUE_OUTER_OPEN_EDGE')
    if adj==120:assert np.array_equal(ours,theirs)
    seams.append({'directed_edge':[a,b],'neighbor_face':adj,'kind':kind,'dart_uv':ours.tolist(),
                  'neighbor_uv':theirs.tolist() if has else None})
assert np.array_equal(P,q['bind']) and np.array_equal(OP,q['open'])
def hash_uv(ids,source):
    return sha(b''.join(np.ascontiguousarray(source[i]).tobytes() for i in sorted(ids)))
near=lambda v:abs(v)<1e-8
before=sorted(i for i in F if near(area2(UV[i])))
after=sorted(i for i in F if near(area2(new[i])))
assert before==[72,78,82,83,84,85,86,87,105,106,108,111,119,122,123,124,125]
assert after==[i for i in before if i not in dart]
# Negative: an unchecked metric unfold exits this exact source chart.
naive=np.array([.92622429,.47199749]); assert not any(r['indexed_uv_component']==1031 for r in locate(naive))
witness_sources={}
for label,s in {'cuff_v0':u0,'cuff_v77':u77,'diagnostic_0p5':np.array([.5,.5]),'cap_v95':UV[118][0],
    'cap_v84_and_85':UV[119][0],'cap_v96':UV[119][2],'naive_metric_v81':naive,
    **{f'dart_v{i}':chartp[i] for i in [77,0,103,81,104]}}.items():
    witness_sources[label]={'uv':s.tolist(),'source_faces':locate(s),'bilinear_pbr_rgb':{k:rgb(s,v).tolist() for k,v in img.items()}}
samp_range={}
for k,i in img.items():
    C=np.asarray([rgb(s,i) for s in samp]); samp_range[k]=[C.min(0).tolist(),np.median(C,0).tolist(),C.max(0).tolist()]
def uv_row_custody(i):
    t=UV[i]; qa=[]
    for j,a in enumerate(F[i]):
        b=F[i][(j+1)%3]; k=tuple(sorted((a,b)))
        neighbors=[int(m[-1]) for m in g[k] if m[-1]!=i]
        loc=locate(t[j])
        qa.append({'vertex':a,'original_pinned_uv':t[j].tolist(),'source_custody_faces':[[q['face_row'],q['indexed_uv_component']] for q in loc],
                  'directed_next_edge':[a,b],'neighbor_rows':neighbors,'approved_source_assignment':False})
    return {'row':i,'do_not_modify_under_scope':i in locked or i==88, 'corners':qa}
r={'local_status':'DART_UV_CUSTODY_ONLY','whole_glove':'HOLD_OTHER_UV_ROWS_AND_ART_AUTHORITY',
   'untouched_face_rows':sorted(i for i in F if i not in dart),'geometry_unchanged_hash_bind_open':[sha(P.tobytes()),sha(OP.tobytes())],
   'locked_76_uv_corners_hash_before_and_after':[hash_uv(locked,UV),hash_uv(locked,new)],
   'locked_pressure_88_uv_corners_hash_before_and_after':[hash_uv([88],UV),hash_uv([88],new)],
   'unaffected_uv_corners_hash_before_and_after':[hash_uv(set(F)-set(dart),UV),hash_uv(set(F)-set(dart),new)],
   'source_actual_component':1031,'same_source_chart_triangle_count':len(chart),
   'source_boundary_edge_count':len(edges),'sampler_texel_footprint_safeguard_min_pixels':padding,
   'source_poly_uv_bounds':[low.tolist(),high.tolist()],
   'checked_nearby_foreign_source_chart_faces':len(foreign),'foreign_source_chart_face_overlap_ids':foreign_overlaps,
   'raw_matched_source_PBR_maps_sha256':{k:sha(v) for k,v in raw.items()},'PBR_patch_min_median_max_sample_RGB':samp_range,
   'source_position_chart_and_uv_witnesses':witness_sources,'changed_four_rows':dart,'dart_chart_uv':{i:new[i].tolist() for i in dart},
   'turn_preservation_no_geometric_change':True,'dart_signed_doubled_uv_areas':{i:area2(new[i]) for i in dart},
   'singular_near_collinear_rows_before':before,'singular_near_collinear_rows_after':after,
   'seam_authority_edges':seams,'unchanged_unresolved_row_custody':[uv_row_custody(i) for i in after],'no_unrelated_closure_or_approval':True}
assert r['locked_76_uv_corners_hash_before_and_after'][0]==r['locked_76_uv_corners_hash_before_and_after'][1]
assert r['unaffected_uv_corners_hash_before_and_after'][0]==r['unaffected_uv_corners_hash_before_and_after'][1]
np.savez_compressed(here/'editable_dart_uv_only.npz',original_face_ids=list(F),triangles=list(F.values()),bind=P,open=OP,corner_uv=[new[i] for i in F],
 changed_rows=dart,source_fleece_component_rows=chart_rows,source_fleece_boundary_uv=edges,dart_uvs=[chartp[i] for i in (77,0,103,81,104)])
dump=json.dumps(r,indent=2)+'\n'; (here/'result.json').write_text(dump); print(dump,end='')
