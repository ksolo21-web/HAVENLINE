"""Provenance-bound four-face dart UV continuation onto the owner's exact fleece chart."""
import gzip, hashlib, io, json, struct
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
d=here.parent/'hvn-l1-c1-glove-uv-custody-v1'; m=d/'SHA256SUMS'
assert sha(m.read_bytes())=='25d381d1c5ba5e82c23b1a71b828178228b63e40ddb9538c374c5f02a8cc7f9b'
for line in m.read_text().splitlines():
    h,f=line.split(maxsplit=1); assert sha((d/f).read_bytes())==h,f
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
def rgb(s,i):
    # GLTF bilinear footprint with normalized image origin at upper left.
    u=s[0]*N-.5; v=(1-s[1])*N-.5
    a=int(np.floor(u)); b=int(np.floor(v)); d=u-a; e=v-b
    return np.asarray(i.getpixel((a,b)))*(1-d)*(1-e)+np.asarray(i.getpixel((a+1,b)))*d*(1-e)+np.asarray(i.getpixel((a,b+1)))*(1-d)*e+np.asarray(i.getpixel((a+1,b+1)))*d*e


from scipy.spatial import cKDTree
q=np.load(d/'editable_dart_uv_only.npz')
uv={int(i):u for i,u in zip(q['original_face_ids'],q['corner_uv'])}
faces={int(i):f.tolist() for i,f in zip(q['original_face_ids'],q['triangles'])}
p=q['bind'];o=q['open']
S=srcp[:,[0,2,1]].astype(np.float64);S[:,1]*=-1.
SN=accessor(prim['attributes']['NORMAL'])[:,[0,2,1]].astype(np.float64);SN[:,1]*=-1.
SV=S[sf]; centers=SV.mean(1); rad=np.linalg.norm(SV-centers[:,None],axis=2).max(1)
Ctree=cKDTree(centers); Vtree=cKDTree(S)
max_rad=float(rad.max())
assert max_rad<.04
def clip_projection(P,T):
    e=T[:,1]-T[:,0]; v=T[:,2]-T[:,0]; w=P-T[:,0]
    dd=lambda a,b:np.einsum('ij,ij->i',a,b)
    ee,vv,ev=dd(e,e),dd(v,v),dd(e,v); we,wv=dd(w,e),dd(w,v)
    det=ee*vv-ev**2; safe=np.maximum(det,1.e-32)
    u=(vv*we-ev*wv)/safe; t=(ee*wv-ev*we)/safe
    B=np.stack([1-u-t,u,t],axis=1)
    candidates=[B]
    for a,b in [(0,1),(1,2),(2,0)]:
        E=T[:,b]-T[:,a]; n=dd(E,E)
        f=np.clip(dd(P-T[:,a],E)/np.maximum(n,1e-30),0.,1.)
        q=np.zeros((len(T),3));q[:,a]=1-f;q[:,b]=f;candidates.append(q)
    B=np.stack(candidates,axis=1)
    D=np.linalg.norm(np.einsum('tik,tkj->tij',B,T)-P,axis=2)
    D[:,0][(np.min(B[:,0],axis=1)<0)|(det<1e-30)]=np.inf
    j=np.argmin(D,axis=1);jj=np.arange(len(D))
    return D[jj,j],B[jj,j]
def nearest(P):
    bound,vi=Vtree.query(P)
    assert np.isfinite(bound)
    ids=np.asarray(Ctree.query_ball_point(P,bound+max_rad+1.e-7),dtype=int)
    ids=ids[np.linalg.norm(centers[ids]-P,axis=1)<=bound+rad[ids]+1.e-7]
    D,B=clip_projection(P,SV[ids]); k=int(np.argmin(D)); i=ids[k]; b=B[k]
    assert D[k]<=bound+1e-8
    tied=np.unique(srcfaces[ids[D<=D[k]+1.e-6]]).tolist()
    t=SN[sf[i]].T@b;t/=np.linalg.norm(t)
    n=np.cross(SV[i,1]-SV[i,0],SV[i,2]-SV[i,0]);n/=np.linalg.norm(n)
    return int(i),b,float(D[k]),t,n,tied
def adict(v,F):
    e=defaultdict(list)
    for i in v:
        f=list(F[i])
        for a,b in zip(f,f[1:]+f[:1]):e[tuple(sorted((a,b)))].append((i,a,b))
    return e
def ab(A):return np.array(A)
E=adict(faces,faces)
all_near=[72,78,82,83,84,85,86,87,105,106,108,111,119]
roles={'dorsal_leather_and_cuff_transition':[78,82,83,84,85,105,106,108],
       'thumb_web_and_nested_garment':[86,87,111],
       'cap_pressure_side_fold':[119]}
assert sorted(sum(roles.values(),[]))==sorted(set(all_near)-{72})
sl=[]
for i in range(6):
    for j in range(6-i):sl.append([i/5,j/5,(5-i-j)/5])
SAMP=ab(sl)
def num(x):return float(x)
def audit_face(k):
    v=p[faces[k]]; n=np.cross(v[1]-v[0],v[2]-v[0]);n/=np.linalg.norm(n)
    W=[]
    for b in SAMP:
        x=b@v; i,s,r,t,g,Q=nearest(x)
        XY=s@st[sf[i]]
        W.append({'closest_face_row':i,'component':int(srcfaces[i]),'source_uv':XY.tolist(),'source_face_barycentric':s.tolist(),
                  'source_sample_material_PBR':{k:rgb(XY,m).tolist() for k,m in img.items()},'distance_mm':r*1000,
                  'owner_normal_dot':num(t@n),'owner_triangle_normal_dot':num(g@n),
                  'source_normal_unit':t.tolist(),'tested_face_barycentric':b.tolist(),'micron_tie_components':Q})
    dd=ab([v['distance_mm'] for v in W]); G=ab([v['owner_triangle_normal_dot'] for v in W]);T=ab([v['owner_normal_dot'] for v in W])
    s0=lambda v:[num(v.min()),num(np.median(v)),num(v.max())]
    components=dict(Counter(w['component'] for w in W))
    return {'target_face_row':k,'target_vertex_ids':faces[k],'target_bind_normal_unit':n.tolist(),
            'target_distance_mm_min_median_max':s0(dd),'owner_normal_dot_min_median_max':s0(T),
            'owner_geometric_normal_dot_min_median_max':s0(G),
            'interpolated_normals_opposite_count':int(sum(T<0)),'geometric_normals_opposite_count':int(sum(G<0)),
            'source_chart_counts':components,'samples':W}
A={i:audit_face(i) for i in sorted(set(all_near)-{72}|{120,123})}
def patch_rim(rows):
    R=[];r=adict(rows,faces)
    for e,hh in r.items():
        if len(hh)!=1:continue
        i,a,b=hh[0];j=next((k for k,c,d in E[e] if k!=i),None)
        if j is None:
            R.append({'edge':[a,b],'candidate_row':i,'outside_row':None,'state':'OPEN_FREE_EDGE'})
            continue
        oo=uv[j][[faces[j].index(a),faces[j].index(b)]]
        cs=[]
        for x in oo:
            src=locate(x)
            cs.append([[s['face_row'],s['indexed_uv_component']] for s in src])
        if j==123:
            assert all(c and c[0][1]==1031 for c in cs)
            state='CUSTODY_PROVEN_CREAM_SIDE_ONLY'
        elif j in all_near:state='FROZEN_NEXT_PENDING_ROLE'
        else:state='DIAGNOSTIC_OR_UNPROVEN_BOUNDARY_CORNERS_NOT_TEXTURE_AUTHORITY'
        R.append({'edge':[a,b],'candidate_row':i,'outside_row':j,'outside_exact_corner_uv':oo.tolist(),
                  'outside_source_face_component_custody':cs,'state':state})
    return R

# Test the only dense single-chart candidate in one direct exact texture
# transfer from owner triangle interiors. This is a negative, not a graft.
f=faces[78]; projected=[]
for x in p[f]:
    i,b,r,_,_,Q=nearest(x)
    assert srcfaces[i]==1046
    projected.append(b@st[sf[i]])
projected=ab(projected); owner=TV[srcfaces==1046]
srcsign=ab([area2(w) for w in owner])
assert len(owner)==2224 and (srcsign>0).all()
assert area2(projected)<0.
assert A[78]['source_chart_counts']=={1046:21} and A[78]['interpolated_normals_opposite_count']==21
assert A[120]['interpolated_normals_opposite_count']==0
# Distance in UV to a true source indexed chart border. Work with projected
# triangle edges, rejecting cut-through or a contained chart boundary/hole.
def min_point_seg(p,a,b):
    d=b-a; n=float(d@d); return np.linalg.norm(p-(a+np.clip((p-a)@d/n,0,1)*d)) if n else np.linalg.norm(p-a)
def seg(a,b,c,d):
    r=b-a; v=d-c; s=c-a
    cross=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
    den=cross(r,v)
    if abs(den)>1e-22 and 0<=cross(s,v)/den<=1 and 0<=cross(s,r)/den<=1:return 0.
    return min(min_point_seg(a,c,d),min_point_seg(b,c,d),min_point_seg(c,a,b),min_point_seg(d,a,b))
own=adict(np.flatnonzero(srcfaces==1046),sf)
rim=st[[e for e,m in own.items() if len(m)==1]].astype(np.float64)
poly=projected[::-1]
pdist=min(seg(a,b,c,d) for a,b in zip(poly,np.roll(poly,-1,axis=0)) for c,d in rim)*N
inside=lambda x:all(area2(ab([a,b,x]))>0 for a,b in zip(poly,np.roll(poly,-1,axis=0)))
if any(inside(x) for x in rim.reshape(-1,2)):pdist=0.
border=patch_rim(sorted(set(all_near)-{72}))
gw=sha(q['bind'].tobytes()); ow=sha(q['open'].tobytes()); uw=sha(q['corner_uv'].tobytes())
r={'decision':'HOLD_ALL_REMAINING_SOURCE_PBR_TRANSFERS','no_mutation_geometry_topology_uv_or_textures':True,
   'upstream_bind_open_uv_hashes':[gw,ow,uw],
   'owner_original_GLTF_sha256':sha(B),'atlas_RGB_metalrough_normal_source_hashes':{k:sha(v) for k,v in raw.items()},
   'fixed_faces_excluded':[72,88,122,123,124,125],
   'editable_groups':{k:{'defined_face_rows':v,'group_open_and_join_edges':patch_rim(v)} for k,v in roles.items()},
   'editable_group_outer_edges':border,
   'actual_closest_surface_reference_controls':{'row120':'verified local cuff exterior with agreeing donor normals; excludes a global frame-reflection explanation','row123':'originally mapped safe dart island; its texture coordinates were not changed; closest-owner normal directions are a separate 3D diagnostic'},
   'sample_grid_pose':'neutral bind; see each exact nearest published owner-triangle witness, not comparative rendered evidence',
   'true_projection_attempt_failed':{'target_row':78,'owner_chart':1046,'positive_source_triangle_count':len(owner),
    'mapped_source_uv_rejected':projected.tolist(),'mapped_signed_doubled_area':area2(projected),'closest_source_true_padding_uv_texels':pdist,
    'negative_under_real_chart_orientation':True,'has_negative_owner_normal_margin':A[78]['owner_normal_dot_min_median_max']},
   'per_face_exact_source_surface_custody':A,
   'handoff':{'first':'resolve whether dorsal shell is intended outer or interior in exact reference and whether its outward-facing topology/locked seams allow direct material transfer; certify with complete surface and normal/tangent framing before rerouting',
     'next':'if no authenticated continuous original atlas transfer exists, use an explicitly separately authored same-style leather swatch with own bordered texture/sampler (or authorized new material island), not unrelated atlas pixels',
     'needs':'source-backed brown leather exterior and distinct supported thumb/palm/cap segmentation; preserve cream cuff and certified dart; verify exact open/neutral charts, UV winding, tape and padding, and actual PBR match and runtime seams. Row 72 stays pinned.',
     'scope':'no right, closure, render, spend or game changes'}}
np.savez_compressed(here/'editable_custody_map.npz',original_face_ids=q['original_face_ids'],triangles=q['triangles'],bind=q['bind'],open=q['open'],exact_unchanged_corner_uv=q['corner_uv'],
                    target_editable_rows=sorted(set(all_near)-{72}),protected_cuff_uv_row_72=np.asarray([72]),original_source_1046_boundary_uv=rim,
                    failed_row_78_uv=projected,failed_row_78_source_face_ids=[int(nearest(x)[0]) for x in p[f]],measurement_barycentric_grid=SAMP)
samples={str(i):v.pop('samples') for i,v in A.items()}
detail=json.dumps(samples,separators=(',',':')).encode()
(here/'original_surface_witness_samples.json.gz').write_bytes(gzip.compress(detail,mtime=0))
r['decompressed_source_sample_data_sha256']=sha(detail)
dump=json.dumps(r,indent=2)+'\n';(here/'result.json').write_text(dump)
print(json.dumps({'status':r['decision'],'roles':roles,'failed':r['true_projection_attempt_failed'],
                  'face_summaries':A},indent=2))
