#!/usr/bin/env python3
"""Single detached exact-V2 XZ geometry enlargement; no transform or scene."""
from pathlib import Path
import hashlib,struct,json,sys
import numpy as np
S=(4.4,1.0,4.4)
def hash0(b):return hashlib.sha256(b).hexdigest()
def parse(b):
 m,v,k,n,t=struct.unpack_from('<4sIIII',b)
 assert (m,v,k,t)==(b'glTF',2,len(b),0x4e4f534a)
 d=json.loads(b[20:20+n]);z,q=struct.unpack_from('<II',b,20+n)
 assert q==0x004e4942 and z==len(b)-28-n
 return d,b[28+n:]
def encode(d,raw):
 j=json.dumps(d,separators=(',',':'),sort_keys=True).encode()
 j+=b' '*((-len(j))%4)
 assert len(raw)%4==0
 return struct.pack('<4sIIII',b'glTF',2,28+len(j)+len(raw),len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw
def view(d,data,i):
 v=d['bufferViews'][i];off=v.get('byteOffset',0);return data[off:off+v['byteLength']]
src=Path(sys.argv[1]).read_bytes()
assert hash0(src)=='3db8ed722b3a41b31003a7a43b85c1b1344fc3e98dcd3c9c94a9f96d34838045'
measure=Path(sys.argv[2]).read_bytes()
measure_expected='a142a105af37cdc3c81d988f4afa2af717870b04108b3fdd74879ff63da9a431'
manifest=Path(sys.argv[2]).with_name('SHA256SUMS').read_bytes()
assert hash0(manifest)==measure_expected 
ext=next(t.split()[0].decode() for t in manifest.splitlines() if t.endswith(b'  result.json'))
assert hash0(measure)==ext
base,raw=parse(src);modified=json.loads(json.dumps(base));buf=bytearray(raw)
pr=base['meshes'][0]['primitives']; assert len(pr)==2
assert base['nodes']==[{'mesh':0,'name':'WoodStoragePlate_Empty'}]
access_changes={}; views_changed=set()
old_all=[];new_all=[]
def read(d,bin0,ind,c):
 az=d['accessors'][ind]
 ib=az['bufferView']; vb=d['bufferViews'][ib]
 assert 'byteStride' not in vb and az.get('byteOffset',0)==0 and vb['buffer']==0
 assert az['componentType']==(5126 if c==3 else 5123)
 m=np.frombuffer(view(d,bin0,ib),dtype=('<f4' if c==3 else '<u2')).reshape(-1,c)
 assert len(m)==az['count']
 return m,ib
for p in pr:
 for k,indices in p['attributes'].items():
  if k not in ('POSITION','NORMAL'):continue
  m,ib=read(base,raw,indices,3); v=base['bufferViews'][ib]
  if k=='POSITION':
   n=(m.astype(float)*np.array(S)).astype('<f4')
   assert np.array_equal(n[:,1],m[:,1])
   old_all.append(m);new_all.append(n)
  else:
   n=m.astype(float)/np.array(S)
   n=(n/np.linalg.norm(n,axis=1,keepdims=True)).astype('<f4')
  off=v['byteOffset']; assert len(n.tobytes())==v['byteLength']
  buf[off:off+v['byteLength']]=n.tobytes()
  modified['accessors'][indices]['min']=n.min(0).astype(float).tolist()
  modified['accessors'][indices]['max']=n.max(0).astype(float).tolist()
  access_changes[indices]=k;views_changed.add(ib)
new=encode(modified,bytes(buf));out,bre=parse(new)
assert len(raw)==len(bre)
for j in range(len(base['bufferViews'])):
 if j not in views_changed:assert view(out,bre,j)==view(base,raw,j)
for k in ('images','textures','samplers','materials','nodes','scenes','meshes','buffers','bufferViews'):
 assert out[k]==base[k]
assert len(out['accessors'])==len(base['accessors'])
for i,(a,b) in enumerate(zip(out['accessors'],base['accessors'])):
 if i in access_changes:
  assert dict(a,min=b['min'],max=b['max'])==b
 else:assert a==b
old_all=np.concatenate(old_all); new_all=np.concatenate(new_all)
active=json.loads(measure)['detached_target_bounds_XYZ_m_keep_8mm_unchanged']
assert np.max(abs(np.ptp(new_all.astype(float),axis=0)-active))<1e-6
tri_count=0; maximum_normal_residual=0.
for p in pr:
 ax=p['attributes']
 pos,ib=read(out,bre,ax['POSITION'],3); n,ib=read(out,bre,ax['NORMAL'],3); jj,ib=read(out,bre,p['indices'],1)
 tris=pos[jj.reshape(-1,3)].astype(float)
 k=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
 assert (np.linalg.norm(k,axis=1)>1e-10).all()
 k/=np.linalg.norm(k,axis=1,keepdims=True)
 er=float(abs(k-n[jj.reshape(-1,3)[:,0]]).max())
 maximum_normal_residual=max(maximum_normal_residual,er)
 assert er<1e-4
 tri_count+=len(tris)
assert tri_count==312
Path('wood_storage_empty.glb').write_bytes(new)
paint=out['images'][0]['bufferView']; png=view(out,bre,paint)
assert hash0(png)=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
gfile=Path(sys.argv[3]).read_bytes()
assert hash0(gfile)=='0d7f4a818d1f8ff5851c9674ae98503306fb283fba358e7e97f092b93369ea90'
gauges=json.loads(gfile)['rest_gauges']
gm=np.asarray(gauges['positions_xyz_m']);c=np.array(gauges['crown_bounds_conservative_xyz_m'])[[0,2]]
assert np.array_equal(gm,np.array([[0,0,-.0524175],[0,0,.0524175]]))
axes=gm[:,[0,2]]
corners=np.concatenate([center+np.array([[sx,sz] for sx,sz in ((-1,-1),(-1,1),(1,-1),(1,1))])*c/2 for center in axes])
pos,ib=read(out,bre,pr[0]['attributes']['POSITION'],3)
rim=pos[1::3][:,[0,2]].astype(float); flat=np.roll(rim,-1,axis=0)-rim
candidates=corners[:,None,:]-rim[None,:,:]
sign=np.sign(flat[:,0]*(-rim[:,1])-flat[:,1]*(-rim[:,0]))
d=(flat[None,:,0]*candidates[:,:,1]-flat[None,:,1]*candidates[:,:,0])*sign[None,:]/np.linalg.norm(flat,axis=1)
assert d.min()>0
assert abs(abs(axes[1,1]-axes[0,1])-c[1]-gauges['axis_gap_m'])<1e-12
data={'exact_baseline_glb_sha256':hash0(src),'output_glb_sha256':hash0(new),'unchanged_embedded_v2_texture_png_sha256':hash0(png),
 'approved_art_comparison_only_factor_x_y_z':S,'output_glb_bytes':len(new),'primitive_count':len(pr),'triangle_count':tri_count,
 'original_xyz_dimensions_m':np.ptp(old_all.astype(float),axis=0).tolist(),'candidate_xyz_dimensions_m':np.ptp(new_all.astype(float),axis=0).tolist(),
 'dimensions_y_exact_and_floor_datum_unchanged':True,'position_and_inverse_transpose_corrected_normal_accessor_ids':access_changes,
 'max_triangle_normal_check_component_residual':maximum_normal_residual,'unchanged_uv_index_material_roughness_images_nodes_scene':True,
 'unchanged_two_original_log_rest_center_gauges_mm':(gm*1000).tolist(),
 'detached_dimensional_sizing_gauge_min_projected_rim_clearance_mm':float(d.min()*1000),
 'log_center_z_pitch_mm_unchanged':104.835,'nominal_one_mm_between_unscaled_sizing_envelopes':True,
 'this_glb_has_no_payload_nodes_and_avoids_scale_inheritance':True,'world_placement_capacity_stability_and_readability':None}
print(json.dumps(data,indent=2,sort_keys=True))
