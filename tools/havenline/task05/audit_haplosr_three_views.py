#!/usr/bin/env python3
"""Three-view silhouette overlap with APPROXIMATE poses (NOT visual critic)."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,cv2,trimesh
from PIL import Image
def projected(mesh,az,el,n=512):
 az,el=np.deg2rad([az,el]); pos=1.9*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
 forward=-pos/np.linalg.norm(pos)
 right=np.cross(forward,[0,0,1.]);right/=np.linalg.norm(right)
 up=np.cross(right,forward);up/=np.linalg.norm(up)
 v=mesh.vertices-pos
 cam=np.column_stack((v@right,v@up,v@forward))
 z=np.maximum(cam[:,2],1.e-5)
 f=n*.5/np.tan(np.deg2rad(40.)*.5)
 uv=np.rint(np.column_stack([cam[:,0],-cam[:,1]])/z[:,None]*f+n*.5).astype(np.int32)
 out=np.zeros((n,n),dtype=np.uint8)
 for face in mesh.faces:
  if (cam[face,2]>.01).all(): cv2.fillConvexPoly(out,uv[face],255)
 return out
def audit(mesh_path,input_dir,out_dir):
 p=Path(mesh_path);s=Path(input_dir);o=Path(out_dir);o.mkdir(parents=True,exist_ok=True)
 mesh=trimesh.load(p,force='mesh')
 scores=[]
 for view in json.loads((s/'poses.json').read_text()):
  n=512
  source=np.asarray(Image.open(s/view['mask']).convert('L'))>128
  actual=projected(mesh,view['azimuth_deg'],view['elevation_deg'],n)>128
  score=float(np.logical_and(actual,source).sum()/max(np.logical_or(actual,source).sum(),1))
  stem=Path(view['image']).stem
  cv2.imwrite(str(o/(stem+'_projected_mask.png')),actual.astype(np.uint8)*255)
  scores.append({'view':stem,'approximate_silhouette_iou':round(score,4)})
 result={'status':'THREE_VIEW_SILHOUETTE_DIAGNOSTIC_NOT_ART_APPROVAL',
  'glb_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
  'triangles':int(len(mesh.faces)),'views':scores,
  'mean_iou':round(float(np.mean([v['approximate_silhouette_iou'] for v in scores])),4),
  'estimated_camera_poses_not_calibrated':True,'independent_art_critic_passed':False,
  'owner_approved':False,'shipping_asset_installed':False,
  'limits':['silhouette only, not internal geometry or textures','unknown reference camera poses']}
 (o/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--mesh',required=True);ap.add_argument('--inputs',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();audit(a.mesh,a.inputs,a.out)
