from pathlib import Path
import numpy as np, hashlib,json
from PIL import Image
p=Path('../hvn-l1-grounded-construction-marker-v1/terrain-fit.py')
# Replay pinned actual V5 custody, orthographic projection and T02 height; no new mesh.
exec(p.read_text().split('q=np.zeros(',1)[0].replace("Path('fitcheck.py')","Path('../hvn-l1-grounded-construction-marker-v1/fitcheck.py')"))
b=Path('../hvn-l1-grounded-construction-marker-icon-v2-native-v1/graphics-evidence.UCJRgmak')
receipt=b/'v2-evidence.json'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(receipt)=='9f12f603bbf2960ad1763b7bdaadb4abf048704d4119e6e627dcf9ad65c289ef'
events=[json.loads(s.split(' ',1)[1]) for s in (b/'enabled.log').read_text().splitlines() if s.startswith('L1_PAD_DRAW ')][:2]
im=[b/'enabled'/(z['phase']+'.png') for z in events]
assert [sha(f) for f in im]==['9628c8a4f02575cb8fcbbf290859386c95f11e9b9a50a91b5a2c499ac68eb2a8','599a0dd87f8e8c103c5bbfb83999a5f4f6357af3a7fe49cb41966c23f3999544']
# A reserve inside the convex radial reach limit; suppress wide theoretical
# square corner points and leave separate ~59mm outer bracket reservation.
ko=np.stack((xx,yy),axis=-1)
sol=np.array([[place(s,.006) for s in row] for row in ko])
fit=np.array([[ok(x,z,.511,.073) and np.linalg.norm([x,z])<=.711 for x,z in row] for row in sol])
vac=[]
for e,f in zip(events,im):
 ax,ay=e['draw']['label_anchor_px']; a=np.asarray(Image.open(f))[:,:,:3].astype(int)
 x,y=np.floor(ko+[ax,ay]).astype(int).transpose((2,0,1)); RGB=a[y,x]; R,G,B=np.moveaxis(RGB,2,0)
 # Broad neutral bright measured pixels are snow candidates, not depth proof.
 # Require blue-gray snow rather than neutral cream clothing/white inlays.
 snowcolor=(R>=134)&(B>=R+13)&(B<=R+47)&(B>=G+5)&(G>=R+3)
 # Existing exact blue-grey authored ink/support (not a whole-actor stencil).
 slate=(R==89)&(G==100)&(B==107)
 # No assumption of unknown left-of-hero reuse.
 vac.append((slate|snowcolor)&(xx>=5))
mask=fit&vac[0]&vac[1]
def test(w,h):
 a=scan(mask,(w,h))
 x,y=a['best_xy']; yy_,xx_=np.where((xx>=x+.5)&(xx<x+w+.5)&(yy>=y+.5)&(yy<y+h+.5)); q=sol[yy_,xx_]
 return dict(missing=a['best_missing'],xy=a['best_xy'],complete_boxes=a['n_complete'],max_radius_m=float(np.max(np.linalg.norm(q,axis=1))))
out={'native_scale':1.,'same_camera_phone_linear_960x540':.75,'same_camera_phone_linear_844x475':475/720,
 'proposed_gray_half_extent_m':.511,'footprint_nominal_span_cap_m':1.14,'radial_paint_guard_m':.711,
 'true_price_reach_kept_m':.72,'controller_or_appear_change':False,
 'two_pose_bright_snow_or_existing_slate_proxy':{f'{w}x{h}':test(w,h) for w,h in ((14,8),(12,12),(15,10),(18,10),(19,11),(20,11),(22,12),(22,13),(23,13))},
 'note':'Actual screens but proxy classification and virtual footprint only; cannot meet phone readability or actual avatar depth.'}
print(json.dumps(out,indent=2))
