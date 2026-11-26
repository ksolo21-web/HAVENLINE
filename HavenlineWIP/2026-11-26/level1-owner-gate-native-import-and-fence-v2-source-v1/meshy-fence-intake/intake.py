from pathlib import Path
import hashlib,io,json,math,struct,sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix,csgraph
source=Path(sys.argv[1])
raw=source.read_bytes()
sha=lambda x:hashlib.sha256(x).hexdigest()
expected='352dce12b2910cf35feca462cb12a22fdef1dbe86bec8ffe83d4f89c45235908'
assert sha(raw)==expected
magic,ver,total=struct.unpack_from('<4sII',raw)
assert magic==b'glTF' and ver==2 and total==len(raw)
J,kind=struct.unpack_from('<I4s',raw,12)
assert kind==b'JSON'
doc=json.loads(raw[20:20+J])
K,kind=struct.unpack_from('<I4s',raw,20+J)
assert kind==b'BIN\0' and 28+J+K==len(raw)
bs=memoryview(raw)[28+J:]
def acc(ix):
    q=doc['accessors'][ix]; b=doc['bufferViews'][q['bufferView']]
    t=np.dtype({5125:'<u4',5126:'<f4'}[q['componentType']]);n={'SCALAR':1,'VEC2':2,'VEC3':3}[q['type']]
    assert b.get('byteStride',n*t.itemsize)==n*t.itemsize and not q.get('sparse')
    return np.frombuffer(bs,dtype=t,offset=b.get('byteOffset',0)+q.get('byteOffset',0),count=q['count']*n).reshape(-1,n)
P=acc(0);UV=acc(1);N=acc(2);F=acc(3).reshape(-1,3)
assert np.isfinite(P).all() and np.isfinite(UV).all() and np.isfinite(N).all() and F.min()>=0 and F.max()<len(P)
T=P[F]
areas=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)*.5
U=UV[F]
du=U[:,1]-U[:,0];dv=U[:,2]-U[:,0]
ua=.5*np.abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])
def connected(P,F,with_edges=False):
    E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[0,2]]])
    E=E[E[:,0]!=E[:,1]]
    G=coo_matrix((np.ones(len(E),dtype=np.uint8),(E[:,0],E[:,1])),shape=(len(P),len(P))).tocsr()
    _,ids=csgraph.connected_components(G,directed=False)
    counts=np.bincount(ids)
    per=np.bincount(ids[F[:,0]],minlength=len(counts))
    tops=[]
    for c in np.argsort(per)[-10:][::-1]:
        v=P[ids==c]
        tops.append({'faces':int(per[c]),'vertices':int(counts[c]),'bbox':np.stack((v.min(0),v.max(0))).tolist()})
    edges={}
    if with_edges:
        es,count=np.unique(np.sort(E,axis=1),axis=0,return_counts=True)
        edges={'boundary_edges':int((count==1).sum()),'nonmanifold_edges':int((count>2).sum()),'two_face_edges':int((count==2).sum())}
    return {'connected_components_all':len(counts),'components_with_faces':int((per>0).sum()),'tops':tops,**edges}
weld,wrev=np.unique(P,axis=0,return_inverse=True)
raw_conn=connected(P,F)
weld_conn=connected(weld,wrev[F],True)
pmin,pmax=P.min(0),P.max(0);ext=pmax-pmin
scale=float(1.465/ext[1]);limit=.29484
images=[]; atlas=None
for i,v in enumerate(doc['images']):
    s=doc['bufferViews'][v['bufferView']]
    b=bytes(bs[s['byteOffset']:s['byteOffset']+s['byteLength']])
    im=Image.open(io.BytesIO(b)); a=np.asarray(im.convert('RGB'))
    if i==0:atlas=a
    sm=a[::31,::31,:]
    images.append({'mime':v['mimeType'],'encoded_sha256':sha(b),'encoded_bytes':len(b),'dimensions':list(im.size),'stored_mode':im.mode,
        'sample_channel_min_max':np.stack((sm.min((0,1)),sm.max((0,1)))).tolist(),
        'sample_channel_means':sm.mean((0,1)).tolist()})
def colors(uv):
    im=atlas; h,w=im.shape[:2]
    x=np.clip(np.floor(uv[:,0]*w).astype(int),0,w-1)
    y=np.clip(np.floor(uv[:,1]*h).astype(int),0,h-1)
    return im[y,x,:]
def access_views(sign,nx=210,ny=125):
    # Orthographic numerical ray probes, no screenshot, no output map.
    bounds=P.min(0),P.max(0)
    x=np.linspace(bounds[0][0],bounds[1][0],nx)
    y=np.linspace(bounds[0][1],bounds[1][1],ny)
    alt=np.full((ny,nx),np.nan); rgb=np.zeros((ny,nx,3),dtype=np.uint8)
    a=T[:,0].astype(float);b=T[:,1]-a;c=T[:,2]-a
    area=b[:,0]*c[:,1]-b[:,1]*c[:,0]
    ylo=T[:,:,1].min(1); yhi=T[:,:,1].max(1)
    world_xyz=np.zeros((ny,nx,3),dtype=np.float32)
    triangle=np.full((ny,nx),-1,np.int32)
    for j,y0 in enumerate(y):
        ids=np.flatnonzero((ylo<=y0)&(yhi>=y0)&(np.abs(area)>1e-15))
        if not len(ids):continue
        A,B,C,Q=a[ids],b[ids],c[ids],area[ids]
        dy=y0-A[:,1];dx=x[:,None]-A[:,0]
        t=(dx*C[:,1]-dy*C[:,0])/Q
        s=(B[:,0]*dy-B[:,1]*dx)/Q
        match=(t>=0)&(s>=0)&(t+s<=1)
        d=A[:,2]+t*B[:,2]+s*C[:,2]
        z=np.where(match,sign*d,-np.inf)
        q=z.argmax(1)
        ix=np.arange(nx)
        good=np.isfinite(z[ix,q]);xx=ix[good];v=q[good]
        face=ids[v]
        uv=U[face,0]+t[xx,v,None]*du[face]+s[xx,v,None]*dv[face]
        alt[j,good]=d[xx,v]
        rgb[j,good]=colors(uv)
        world_xyz[j,good]=np.stack((x[good],np.repeat(y0,len(xx)),d[xx,v]),axis=1)
        triangle[j,good]=face
    return x,y,alt,rgb,triangle
def cluster(c):
    R,G,B=np.moveaxis(c.astype(float),-1,0)
    snow=(R>145)&(G>145)&(B>150)&(R-B<38)&(G-B<40)
    cream=(R>=120)&(G-R>=-68)&(B-R<-25)&(B-G<-12)
    wood=(R>=50)&(R-G>42)&(G-B>10)
    return snow,cream,wood
def runs(val):
    groups=[]; i=0
    while i<len(val):
        if not val[i]:i+=1;continue
        a=i
        while i<len(val) and val[i]:i+=1
        groups.append([a,i-1])
    return groups
out={}
raw_view={}
for s in (-1,+1):
    x,y,d,c,hit=access_views(s)
    snow,cream,wood=cluster(c)
    covered=hit>=0
    raw_view[s]=(d,cream & covered,covered)
    # Count first-hit snow tips and ridge extent by sampled elevation. No
    # unsupported semantic counting by topological component labels.
    counts=[]
    for f in (.82,.84,.86,.88,.90,.92,.94,.96,.98):
        k=min(len(y)-1,int(round(f*(len(y)-1)))); gr=runs(snow[k]&covered[k])
        counts.append({'fraction_from_base':f,'snow_runs_min_3_cols':[[round(float(x[a]),4),round(float(x[b]),4)] for a,b in gr if b-a>=2],
                       'covered_columns':int(covered[k].sum())})
    # Along y, depth extremity summarized across central ownership region
    # not just longest or tiny outlier. Helps compare raised physical rails.
    cm=(x>pmin[0]*.91)&(x<pmax[0]*.91)
    zi=np.where(np.isfinite(d[:,cm]),s*d[:,cm],np.nan)
    hull=np.full(len(y),np.nan);cent=np.full(len(y),np.nan)
    ix=np.isfinite(zi).any(1)
    hull[ix]=np.nanquantile(zi[ix],.85,axis=1);cent[ix]=np.nanmedian(zi[ix],axis=1)
    groups=[]
    for f in ((.065,.26),(.47,.72)):
        y0,y1=map(lambda q:int(round(q*(len(y)-1))),f)
        ysub=[]
        for j in range(y0,y1+1):
            ysub.append([round(float(j/(len(y)-1)),4),round(float(hull[j]),5),round(float(cent[j]),5),
                int((cream[j]&covered[j]).sum())])
        groups.append(ysub)
    out['positive_Z' if s==1 else 'negative_Z']={'snow_probe_rows':counts,'rail_band_samples_heightfrac_outer85_m_median_m_cream_count':groups,
       'valid_frontmost_samples':int(covered.sum()),'heuristic_color_pixel_counts':{n:int((k&covered).sum()) for n,k in [('snow',snow),('cream',cream),('wood',wood)]}}
D0,C0,V0=raw_view[-1]
D1,C1,V1=raw_view[1]
same=V0&V1
g=np.abs(D0+D1)
center_plane=(pmin[2]+pmax[2])*0.5
band_result={}
for title,(f0,f1) in {'lower':(.062,.185),'upper':(.55,.665)}.items():
    i,j=[round(f*(len(y)-1)) for f in (f0,f1)]
    p,q=C0[i:j+1],C1[i:j+1]
    def mask_shape(mask):
        pairs=sum(sum(b-a>=1 for a,b in runs(col))>=2 for col in mask.T)
        return {'vertical_columns_with_two_separate_cream_runs':int(pairs),'cream_total_hits':int(mask.sum())}
    g2=g[i:j+1][same[i:j+1]]
    band_result[title]={'median_matched_surface_depth_mirrored_delta_mm':float(np.median(g2)*1000),
        'cream_symmetric_location_iou':float((p&q).sum()/(p|q).sum()),
        'negative_Z':mask_shape(p),'positive_Z':mask_shape(q)}
k0=int(round(.34*(len(y)-1))); k1=int(round(.43*(len(y)-1)))
profiles=[]
for sign,dp in [(-1,D0),(1,D1)]:
    window=sign*dp[k0:k1]; ok=np.isfinite(window).any(0); vfill=np.full(window.shape[1],-1.); vfill[ok]=np.nanmedian(window[:,ok],axis=0)
    finite=np.flatnonzero(vfill>-1)
    from scipy.signal import find_peaks
    peaks,_=find_peaks(vfill,prominence=.025,distance=15)
    profiles.append({'side':sign,'body_depth_peaks_x_m':[float(x[p]) for p in peaks],
                     'medial_y_height_fraction':(.34,.43)})
res={'measured_front_rear_depth_and_colour_no_raster':{'both_face_mask_region':int(same.sum()),
      'median_paired_surface_mirror_delta_mm_about_origin':float(np.median(g[same])*1000),
      'median_paired_surface_mirror_delta_mm_about_bbox_z_center':float(np.median(np.abs(D0+D1-2*center_plane)[same])*1000),
      'belt_heuristic':band_result,'body_depth_peaks':profiles},'exact_glb_sha256':expected,'file_bytes':len(raw),'mesh_indices':len(F)*3,'triangles':len(F),'vertices':len(P),
     'geometric_degenerate_faces_at_1e12_m2':int((areas<1e-12).sum()),'exact_position_weld_vertex_count':len(weld),
     'raw_connectivity':raw_conn,'geometric_welded_connectivity':weld_conn,'bounds_min_max_m':np.stack((pmin,pmax)).tolist(),
     'extents_m_XYZ':ext.tolist(),'height_scale_to_1_465':scale,'height_fitted_depth_m':scale*float(ext[2]),
     'height_fitted_span_m':scale*float(ext[0]),'protected_depth_m':limit,'required_relative_depth_scale':limit/(scale*float(ext[2])),
     'textures':images,'UV0_triangle_area_sum_unit_square':float(ua.sum()),'UV0_degenerate_triangles_at_1e12':int((ua<1e-12).sum()),
     'UV0_triangle_area_sum_not_union_or_transfer_certification':True,'scripts_no_native_or_staging':True,'front_back_probe':out,
     'attrs':doc['meshes'][0]['primitives'][0]['attributes'],'material':doc['materials'][0]}
print(json.dumps(res,indent=2))
