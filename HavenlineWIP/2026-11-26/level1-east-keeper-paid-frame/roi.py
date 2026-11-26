"""Project exact authored mechanism group silhouettes into V4 paid-camera coordinates."""
from hashlib import sha256
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json, re
import numpy as np
def compare(h,control,out,ref):
 obj=h/'staged/HavenlineLevel1/previews/clearance_gate/owner_assets'
 ms={}
 for i,f in enumerate(('GateLeaf.obj','GateLeaf_Right.obj')):
  vertices=[]; tris=[]; group=None
  for l in (obj/f).read_text().splitlines():
   if l.startswith('g '):group=l[2:]
   elif l.startswith('v '):vertices.append([float(v) for v in l.split()[1:]])
   elif l.startswith('f ') and group in ('front_handle_rosette','front_handle_owned_bar','front_receiver_keeper'):
    tris.append((group,[int(v)-1 for v in l.split()[1:]]))
  ms[i]=(np.array(vertices),tris)
 a=np.array(Image.open(control/'paid-first-frame.png').convert('RGB')).astype(int)
 b=np.array(Image.open(out/'paid-first-frame.png').convert('RGB')).astype(int)
 assert a.shape==b.shape==(720,1280,3)
 delta=np.max(np.abs(a-b),axis=2)
 look=np.array([7,11,11])/np.linalg.norm([7,11,11]);right=np.cross([0,1,0],look);right/=np.linalg.norm(right)
 proj=np.vstack((right,-np.cross(look,right)))*720/13
 bound={}; axis_registration=None
 from metrics import masks
 hinge=masks(control)
 union=np.zeros((720,1280),bool)
 for name,axis,front in [('gate-south',[1,0,0],[0,0,1]),('gate-east',[0,0,-1],[1,0,0])]:
  assert ref['gates'][name]['angle']==0
  tr=np.column_stack((proj@axis,proj@[0,1,0],proj@front))
  bands={}
  for i,(own,tris) in ms.items():
   x,y,xt,yt=hinge[name][i]
   assert abs(x-xt)<1e-6 and abs((yt-y)-1.35*tr[1,1])<1e-3
   if name=='gate-east' and i==1:
    hinge_l=np.array(hinge[name][0][:2])
    delta_old=np.array([x,y])+tr@[-1.135,.681,.0565]-(hinge_l+tr@[1.107,.681,.058])
    delta_new=delta_old+tr[:,1]*.0692915
    axis=tr[:,0]/np.linalg.norm(tr[:,0])
    perp=np.array([-axis[1],axis[0]])
    old_error=float(delta_old@perp); new_error=float(delta_new@perp)
    assert abs(old_error)>1.8 and abs(new_error)<.1
    axis_registration={'nominal_axis_perp_error_old_px':old_error,'nominal_axis_perp_error_new_px':new_error,
      'projected_nominal_center_delta_old_xy_px':delta_old.tolist(),'projected_nominal_center_delta_new_xy_px':delta_new.tolist(),
      'does_not_require_raw_screen_y_alignment':True}
   points=np.array([x,y])+own@tr.T
   groups=sorted(set(t[0] for t in tris))
   for g in groups:
    m=Image.new('L',(1280,720))
    canvas=ImageDraw.Draw(m)
    for label,face in tris:
     if label==g:canvas.polygon([tuple(points[j]) for j in face],fill=255)
    if name=='gate-east' and g=='front_receiver_keeper':
     assert i==1 and -tr[1,1]*.0692915>2.9
     shifted=Image.new('L',(1280,720))
     painter=ImageDraw.Draw(shifted)
     for label,face in tris:
      if label==g:painter.polygon([tuple(points[j]+.0692915*tr[:,1]) for j in face],fill=255)
     old_roi=np.array(m)>0
     shifted_roi=np.array(shifted)>0
     assert shifted_roi.sum()>6 and np.any(old_roi^shifted_roi)
     canvas=ImageDraw.Draw(m)
     for label,face in tris:
      if label==g:canvas.polygon([tuple(points[j]+.0692915*tr[:,1]) for j in face],fill=255)
    core=np.array(m)>0
    assert core.sum()>6
    rim=(np.array(m.filter(ImageFilter.MaxFilter(5)))>0)&~core
    union|=core|rim
    def desc(img,where):
     p=img[where]
     y=p@np.array([.2126,.7152,.0722])
     return {'p50_Y':float(np.median(y)),'p90_Y':float(np.percentile(y,90)), 'clip_pixels':int(np.sum(np.max(p,axis=1)>=250))}
    bands[g]={'pixel_bounds_xyxy':list(m.getbbox()),'pixels':int(core.sum()),
     'v4':desc(a,core),'candidate':desc(b,core),
     'changes_at_5_rgb_core':int((delta[core]>=5).sum()),'changes_at_5_rgb_guard_rim':int((delta[rim]>=5).sum())}
  bound[name]=bands
 return {'scope':'Projected group masks include self-occlusion; classifies RGB not hardware identity or glow',
   'east_projected_axis_registration':axis_registration,'old_and_new_east_keeper_projected_displacement_px': float(-proj[1,1]*.0692915),'groups_at_each_gate':bound,'changed_pixels_outside_all_2px_padded_masks_at_least_5_rgb':int((delta[~union]>=5).sum()),
   'v4_paid_frame_hash':sha256((control/'paid-first-frame.png').read_bytes()).hexdigest()}
