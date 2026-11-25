import hashlib,json,numpy as np,pathlib,struct,sys
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
a,b=(pathlib.Path(x).read_bytes() for x in sys.argv[1:3])
assert a==b and hashlib.sha256(a).hexdigest()=="79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e"
span_source=pathlib.Path(sys.argv[3]).read_bytes()
assert hashlib.sha256(span_source).hexdigest()=='5c099d5163453d428bb72226feb34fbf4eaaf65624b2eb1fe0dcc2c94d0fe1a5'
observed=json.loads(span_source)
l=struct.unpack_from('<I',a,12)[0];j=json.loads(a[20:20+l]);q=a[28+l:];x=j['meshes'][0]['primitives'][0]
assert j['nodes']==[{'mesh':0,'name':'t09_harvest_axe'}]
def rd(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];d=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]); k={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
 return np.ndarray((a['count'],k),dtype=d,buffer=q,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',k*d.itemsize),d.itemsize)).copy()
v=rd(x['attributes']['POSITION']);faces=rd(x['indices']).reshape(-1,3);col=rd(x['attributes']['COLOR_0'])
u,inv=np.unique(np.round(v.astype('float64'),6),axis=0,return_inverse=True);r=inv[faces];st=r.ravel(); en=r[:,[1,2,0]].ravel()
nc,lab=connected_components(csr_matrix((np.ones(len(st)),(st,en)),shape=(len(u),len(u))),directed=False)
components=[]
for k in range(nc):
 ids=np.where(lab[inv]==k)[0];f=faces[np.isin(faces,ids).all(1)]
 assert len(np.unique(col[ids],axis=0))==1
 g=v[ids]
 components.append({'color':col[ids][0].round(6).astype(float).tolist(),'face_count':len(f),'min':g.min(axis=0).astype(float).tolist(),'max':g.max(axis=0).astype(float).tolist(),'max_radius_xz':float(np.max(np.linalg.norm(g[:,[0,2]],axis=1)))})
assert len(components)==8 and sum(c['face_count'] for c in components)==512
wood=sorted((c for c in components if c['max'][1]<.001),key=lambda c:c['min'][1])
core=next(c for c in components if c['min'][1]<0<c['max'][1]);assert core['max'][1]>.26
head=min(c['min'][1] for c in components if c['min'][1]>0)
union_bottom=min(c['min'][1] for c in components)
covered_lower=[c for c in wood if c['face_count']==56]
assert len(covered_lower)==3 and abs(head-.005)<1e-6
cuts=sorted(set([union_bottom,head,core['min'][1]]+[c[k][1] for c in covered_lower for k in ['min','max']]))
cuts=[c for c in cuts if c<=head]
sections=[]
for lo,hi in zip(cuts,cuts[1:]):
 cands=[c for c in [core]+covered_lower if c['min'][1]<(lo+hi)*.5<c['max'][1]]
 top=max(cands,key=lambda d:d['max_radius_xz'])
 sections.append({'open_span_y_m':[lo,hi],'upper_model_radius_bound_mm':top['max_radius_xz']*1000,'component_color':top['color']})
fits={}
for action in ['carry','chop','mine']:
 s=observed['actions'][action]['summary'];d=s['span_mm'];r=s['lower_hand_counts']
 maxd=d[1]
 # Pure axial feasibility in the conservative head-free interval only.
 # Whole shaft-wrap clearance unknown. Equal projected width and end exclusion mirrored around midpoint.
 fits[action]={'observed_span_mm':d,'lower_ids':r,'max_equal_full_width_before_head_or_end_beyond_bounded_interval_mm':(head-union_bottom)*1000-maxd,'fixed_260mm_manifest_min_max_signed_separation_error_mm':[d[0]-260,d[1]-260]}
print(json.dumps({'tool_git_blob':'9d7ab5e3cbb42f64b3ce0451e6e5171954dc172e','exact_asset_bytes':len(a),'components':components,'axial_envelope_open_m':[union_bottom,head],'open_axial_sections':sections,'fit_geometric_upper_bounds':fits},sort_keys=True,indent=2))
