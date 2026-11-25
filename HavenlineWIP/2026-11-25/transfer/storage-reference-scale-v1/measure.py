#!/usr/bin/env python3
"""Private source checks; emit numeric measurements only, never frames."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes,label
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=Path(sys.argv[1]); extra=Path(sys.argv[2]); native=Path(sys.argv[3])
spec={
 'B-008.00':(b/'B-008.00.png','8544aee9feba9bdb5d3060ec8449bd2ba07f7ad4092c70599979120e3d09c65b',(264,545,565,755),(381,612,454,678),(500,1152,603,1290)),
 'B-010.00':(b/'B-010.00.png','10e434c1b949d18f76e9a510c8376895e4996413d7f8ae1b2f3df924aa848e8c',(491,742,797,958),(611,811,684,883),(487,1151,567,1279)),
 'B-direct-27.5':(extra/'b27.5-LOCAL.png','71f9ab0e599c661b7e2a9082e96058781fd82ea6ca1f90e2599698fd71f664b8',(545,822,853,1047),(663,893,738,969),(509,1178,612,1288)),
}
def boxmask(img,r,kind):
 x,y,xx,yy=r
 a,b,c=img[y:yy,x:xx].transpose(2,0,1).astype(np.int16)
 if kind=='plate':
  # Low warm luma of slate excluding cream/fence/floor; largest connected exact field.
  z=(a>=45)&(a<=132)&(a-b<43)&(a-b>0)&(a-b>=b-c)
 else:
  # Outline of the warm painted mark is outside its brightest gold center.
  # Include black-brown outline and saturated bark/cut, excluding quiet field.
  rgb=img[y:yy,x:xx].astype(np.int16)
  rim=np.concatenate([rgb[:3].reshape(-1,3),rgb[-3:].reshape(-1,3),rgb[:,:3].reshape(-1,3),rgb[:,-3:].reshape(-1,3)])
  field=np.median(rim,axis=0)
  z=np.max(abs(rgb-field[None,None]),axis=2)>17
  if kind=='gold':
   z=(a>=190)&(b>=145)&(c>=80)
 L,k=label(z,structure=np.ones((3,3)))
 hist=np.bincount(L.ravel());hist[0]=0
 region=binary_fill_holes(L==np.argmax(hist))
 Y,X=np.where(region)
 return [int(X.min()+x),int(Y.min()+y),int(X.max()+x+1),int(Y.max()+y+1)]
def dims(B):return [B[2]-B[0],B[3]-B[1]]
out={}
for k,(p,d,roi,iroi,avatar) in spec.items():
 assert h(p)==d
 a=np.asarray(Image.open(p).convert('RGB'))
 assert a.shape==(2520,1080,3)
 f,m,go=boxmask(a,roi,'plate'),boxmask(a,iroi,'icon'),boxmask(a,iroi,'gold')
 W,H=dims(f); w,j=dims(m); ah=dims(avatar)[1]
 out[k]={'frame_sha256':d,'field_box_halfopen':f,'field_wh':dims(f),'warm_log_mark_box_halfopen':m,'warm_log_mark_wh':dims(m),'warm_bright_core_threshold_wh':dims(go),
         'avatar_manual_box_hood_to_boots_excludes_payload_and_sweep_marks':avatar,'avatar_height_manual_px':ah,
         'field_to_avatar_height_wh':[W/ah,H/ah], 'mark_to_field_wh':[w/W,j/H],
         'manual_avatar_height_tolerance_px':5}
proof={}
ray=np.array([7.,11.,11.]);ray/=np.linalg.norm(ray); axis=np.cross([0,1,0],ray);axis/=np.linalg.norm(axis)
up=np.cross(ray,axis)
for tag,pin in [('far','566ffdd64dbd85e36f1ce6d4d58aeefd9509af95bbe0594e30d690c5f379d718'),('near','30e8ed8a7f5e861eef16bf4c79c9b26df85f9da1da0c0ac6ddb7af33a3e96c08'),('moving','eeda1086089dfc30e3d96cfc5c04eae35b4438d56a8871aaa7e108ada091a5c0'),('before','3f14eb2162971a738f0ebfce0b2389c51972dca7dd7433d32a35f287d20c97c6')]:
 p=native/'funded'/(tag+'.json')
 assert h(p)==pin
 d=json.loads(p.read_text()); assert sum(len(x['triangles']) for x in d)==288003
 v=np.concatenate([np.asarray(x['positions'])[np.unique(x['triangles'])] for x in d])
 proof[tag]=(np.ptp(v@np.array([axis,up]).T,axis=0)*720/13).tolist()
for name,pin in [('b27-LOCAL.png','4434403f962cbce176cc3a40e5f3053da80c6d130e11ec9f5d00db4cedaa3c5a'),('b28-LOCAL.png','3e983101885a727eb32fcc0d132fcacf8be8c439d2dfefcb267b45326065ee18')]:
 assert h(extra/name)==pin
plate=Path('../hvn-l1-wood-storage-art-v1/result.json')
assert h(plate)=='0d7f4a818d1f8ff5851c9674ae98503306fb283fba358e7e97f092b93369ea90'
bounds=np.asarray(json.loads(plate.read_text())['source_checked']['bounds_xyz'])
v2p=Path('../hvn-l1-storage-paint-v2-independent-v1.DQjTNM/pixels.json')
assert h(v2p)=='28a3eeede823b4526348061695f8037ba58671fcfca8987c29bd30d1912e7652'
v2=json.loads(v2p.read_text())
bvh=np.asarray(v2['roi_dark_support_bbox_px'])
bh=proof['far'][1]
import struct
GLB=Path('../hvn-l1-wood-storage-paint-repair-v2/wood_storage_empty.glb')
assert h(GLB)=='3db8ed722b3a41b31003a7a43b85c1b1344fc3e98dcd3c9c94a9f96d34838045'
bl=GLB.read_bytes();nn=struct.unpack_from('<I',bl,12)[0];gg=json.loads(bl[20:20+nn])
i=gg['meshes'][0]['primitives'][0]['attributes']['POSITION']
q=gg['bufferViews'][gg['accessors'][i]['bufferView']]
v=np.frombuffer(bl[28+nn+q['byteOffset']:28+nn+q['byteOffset']+q['byteLength']],dtype='<f4').reshape(-1,3)
sw=np.ptp(v@np.array([axis,up]).T,axis=0)*720/13
genn=4.4
print(json.dumps({'same_shot_reference_measures':out,'hero_cpu_skinned_66bone_11c_normal_camera_snapshot_bbox_px':proof,
                  'candidate_v2_dark_mask_bbox_to_exact_stock_camera_hero_height':(bvh/bh).tolist(),
                  'reference_storage_identity':'Same back corner rear-fence dark plot beneath the log pictogram; separate later wood stacking on it, not front counter/green cash/white labeled buy plot.',
                  'exact_v2_flat_top_projected_geometry_bbox_px_not_actual_ink':sw.tolist(),
                  'same_default_camera_horizontal_candidate_scale_prior_to_world_placement':genn,
                  'detached_target_flat_top_projected_geometry_bbox_px_not_rendered':(sw*genn).tolist(),
                  'detached_target_flat_top_to_hero_height':(sw*genn/bh).tolist(),
                  'detached_target_bounds_XYZ_m_keep_8mm_unchanged':((bounds[1]-bounds[0])*[genn,1,genn]).tolist(),
                  'detached_target_v2_mask_projection_budget_not_rendered_px':(bvh*genn).tolist(),
                  'detached_target_v2_mask_to_stock_hero_height':(bvh*genn/bh).tolist(),
                  'detached_target_v2_icon_bounds_projection_budget_not_rendered_px':(np.asarray(v2['thresholded_bright_warm_dot_bbox_px'])*genn).tolist(),
                  'storage_fill_frame_pair_requested_seek_s':[27.5,28.0],
                  'reference_avatar_size_comparison_basis':'manual visible hood-to-boots, no payload/ground decals; calibration baseline B008+B010 (27.5 running corroborates identity, not scale).',
                  'proposed_wood_local_center_spacing_mm_unchanged':104.835,
                  'target_fraction_of_nominal_unshifted_camp_axes_WH':[.2886400079727173,.2837999850511551],
                  'unsupported_inference':'No footage real meters or exact camera conversion, no location or art change.'},indent=2,sort_keys=True))
