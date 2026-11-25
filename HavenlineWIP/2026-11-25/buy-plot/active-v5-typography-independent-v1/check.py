import argparse, ctypes as C, hashlib, json, math, re, struct, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("repo"); p.add_argument("packet"); p.add_argument("--quads"); p.add_argument("--native-ab")
a=p.parse_args(); d=Path(a.packet)
pin="11c14a1c41971067c7dc97db69375f720a408f68"
def source(f): return subprocess.check_output(["git","-C",a.repo,"show",pin+":HavenlineLevel1/"+f])
def sha(b): return hashlib.sha256(b).hexdigest()
assert sha((d/'SHA256SUMS').read_bytes())=="f62ddaddca3699c7c455650a00bb977808c8ce41221cb59a8cd609abb1f6ae43"
subprocess.run(["sha256sum","-c","--status","SHA256SUMS"], cwd=d,check=True)
native=json.loads((d/'native.json').read_bytes()); assert native["viewport"]==[1280,720] and native['proj']==native['keep']==1
cam=tuple(map(float,re.search(rb"camera.position = actor.position \+ Vector3\(([^)]+)\)",source('previews/integrated_opening.gd'))[1].split(b",")))
assert cam==(7.,11.,11.) and native['cam_size']==13.
f=math.hypot(cam[0],cam[2]); k=720/13
R=(11/f,0,-7/f); U=(-77/(f*math.sqrt(291)),f/math.sqrt(291),-121/(f*math.sqrt(291)))
b=source('assets/studio/purchase_pad_v5.glb'); assert sha(b)=="d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb"
size,typ=struct.unpack_from("<II",b,12); assert typ==0x4e4f534a
g=json.loads(b[20:20+size]); binary=memoryview(b)[28+size:]
prim={}
for n in g['nodes']:
 assert set(n)=={'mesh','name'}
 pr,=g['meshes'][n['mesh']]['primitives']; prim[n['name']]=pr
def acc(i):
 ac=g['accessors'][i]; bv=g['bufferViews'][ac['bufferView']]
 assert not ac.get('sparse') and 'byteStride' not in bv
 fmt={5126:'fff',5123:'H',5125:'I'}[ac['componentType']]
 return list(struct.iter_unpack('<'+fmt,binary[bv['byteOffset']+ac.get('byteOffset',0):bv['byteOffset']+ac.get('byteOffset',0)+struct.calcsize('<'+fmt)*ac['count']]))
verts={n:acc(p['attributes']['POSITION']) for n,p in prim.items()}
lo=[min(v[j] for s in verts.values() for v in s) for j in range(3)]
hi=[max(v[j] for s in verts.values() for v in s) for j in range(3)]
s=.8/max(hi[0]-lo[0],hi[2]-lo[2])
def place(v): return ((v[0]-(lo[0]+hi[0])/2)*s,(v[1]-lo[1])*s+.008,(v[2]-(lo[2]+hi[2])/2)*s)
dname='PurchaseDeck_Surface'; deck=list(map(place,verts[dname])); roof=max(v[1] for v in deck)
p3={}; 
for key, px in [('Action',.0037),('Cost',.0032)]:
 n=native['label'][key]
 X=(R[0]*k*s*px,-U[0]*k*s*px); Y=(-R[2]*k*s*px,U[2]*k*s*px)
 err=max(abs(q-r/30) for v,w in zip((X,Y),(n['px_axis_x_for_30'],n['px_axis_y_for_30'])) for q,r in zip(v,w))
 assert err<2e-6 and X[0]*Y[1]-X[1]*Y[0]<0
 advance=n['string_metrics'][0]*math.hypot(*X)
 p3[key]={'signed_X':X,'signed_Y':Y,'advance_px':advance,'max_signed_axis_error':err}
lib=C.CDLL('libgeos_c.so.1')
ptr=C.c_void_p
def bind(n,rest,*args):
 f=getattr(lib,n); f.restype=rest; f.argtypes=args; return f
bind('initGEOS',None,ptr,ptr)(None,None)
read=bind('GEOSGeomFromWKT',ptr,C.c_char_p); union=bind('GEOSUnaryUnion',ptr,ptr)
cover=bind('GEOSCovers',C.c_byte,ptr,ptr); diff=bind('GEOSDifference',ptr,ptr,ptr)
area=bind('GEOSArea',C.c_int,ptr,C.POINTER(C.c_double))
def getarea(geom):
 val=C.c_double(); assert geom and area(geom,C.byref(val))==1; return val.value
def loop(poly): return '('+','.join(f'{x:.12g} {z:.12g}' for x,z in [*poly,poly[0]])+')'
def polys_union(polys):
 w='MULTIPOLYGON('+','.join('('+loop(q)+')' for q in polys)+')'
 ans=union(read(w.encode())); assert ans; return ans
def footprint(poly): return read(('POLYGON('+loop(poly)+')').encode())
ids=[x[0] for x in acc(prim[dname]['indices'])]
faces=[[deck[j] for j in ids[i:i+3]] for i in range(0,len(ids),3)]
polys=[]
for f in faces:
 if min(v[1] for v in f)<roof-.0001: continue
 poly=[(v[0],v[2]) for v in f]
 (x,z),(u,w),(v,t)=poly
 if abs((u-x)*(t-z)-(v-x)*(w-z))>1e-16: polys.append(poly)
geo=polys_union(polys)
def contained(poly): return cover(geo,footprint(poly))==1
def rectangle(x,z,w,h): return [(x-w/2,z-h/2),(x+w/2,z-h/2),(x+w/2,z+h/2),(x-w/2,z+h/2)]
assert contained(rectangle(0,0,.10,.10)) and not contained(rectangle(.399,.399,.02,.02))
results={'projection':p3,'roof_y':roof,'roof_support_triangles':len(polys),'roof_support_area_m2':getarea(geo),'states_needed':['unfunded','first funded','committed hidden']}
for key,zoff,px in [('Action',-.17,.0037),('Cost',.18,.0032)]:
 row=native['label'][key]; z=s*(zoff-(hi[2]+lo[2])/2); x=-s*(hi[0]+lo[0])/2
 w,h=[q*s*px for q in row['string_metrics']]
 low,high=0.,10.
 for _ in range(35):
  mult=(low+high)/2
  if contained(rectangle(x,z,w*mult+.02,h*mult+.02)): low=mult
  else: high=mult
 results[key]={'proxy_with_10mm_edge_margin_max_scale_at_fixed_center':low,'proxy_local_extent_m':[w,h],'max_30fontpx_atlas_height_along_projected_text_up':low*24*math.hypot(*p3[key]['signed_Y'])}
if a.native_ab:
 results['actual_native_ab']={}
 for variant in ('base','trial'):
  dat=json.loads((Path(a.native_ab)/(variant+'-native.json')).read_text())
  assert dat['viewport']==[1280,720] and dat['cam_size']==13 and dat['proj']==dat['keep']==1
  extrema={}
  for key in ('Action','Cost'):
   r=dat['label'][key]; assert r['text']==native['label'][key]['text'] and r['font_size']==30 and r['outline']==12 and r['texture_filter']==3
   pts=r['runtime_aabb']; assert len(pts)==8 and len(r['triangles'])==6
   mn=[min(q[i] for q in pts) for i in range(3)]; mx=[max(q[i] for q in pts) for i in range(3)]
   for i in range(3):
    assert min(q[i] for q in r['triangles'])==mn[i] and max(q[i] for q in r['triangles'])==mx[i]
   assert abs(mn[1]-roof-.008)<1e-6 and mx[1]-mn[1]<1e-6
   px=math.hypot(*r['px_axis_x_for_30'])/30
   py=math.hypot(*r['px_axis_y_for_30'])/30
   world_per_px=(mx[0]-mn[0])/r['string_metrics'][0]
   guard=14*world_per_px
   x,z=(mn[0]+mx[0])/2,(mn[2]+mx[2])/2
   ext=(mn[2]-guard,mx[2]+guard)
   extrema[key]=ext
   result={'aabb_width_m':mx[0]-mn[0],'aabb_length_m':mx[2]-mn[2],'advance_px':r['string_metrics'][0]*px,'atlas_height_px':r['glyph_texture_metrics'][0]['size'][1]*py,
           'fully_over_finite_roof':contained(rectangle(x,z,mx[0]-mn[0],mx[2]-mn[2])),
           'with_14fontpx_per_side_proxy_over_finite_roof':contained(rectangle(x,z,mx[0]-mn[0]+2*guard,mx[2]-mn[2]+2*guard)),
           'actual_height_above_deck_mm':(mn[1]-roof)*1000}
   assert result['fully_over_finite_roof'] and result['with_14fontpx_per_side_proxy_over_finite_roof']
   results['actual_native_ab'][variant+'_'+key] = result
  assert extrema['Cost'][0]>extrema['Action'][1]
  results['actual_native_ab'][variant+'_guarded_gap_mm']=(extrema['Cost'][0]-extrema['Action'][1])*1000
if a.quads:
 q=json.loads(Path(a.quads).read_text()); results['candidate_per_glyph']={}
 for key in ('Action','Cost'):
  supplied=q[key]; expected=native['label'][key]['text'].replace(' ','')
  assert ''.join(g['glyph'] for g in supplied)==expected
  for i,g in enumerate(supplied):
   label=key+':'+str(i)
   xyz=g['corners_XYZ_world_m_at_zero_yaw_relative_to_pad_anchor']
   assert len(xyz)==4 and all(len(r)==3 and all(math.isfinite(v) for v in r) for r in xyz)
   poly=[(x,z) for x,y,z in xyz]; shape=footprint(poly); assert shape and getarea(shape)>1e-9
   outside=getarea(diff(shape,geo))
   ys=[y for x,y,z in xyz]
   assert max(ys)-min(ys)<1e-5  # horizontal label plane contract
   results['candidate_per_glyph'][label]={'outside_roof_m2':outside,'legible_not_assessed':True,'above_deck_roof_mm':(min(ys)-roof)*1000,
    'deck_only':outside<1e-10 and min(ys)>roof}
print(json.dumps(results,sort_keys=True,indent=2))
