from PIL import Image
import sys,json
import numpy as np
im=Image.open(sys.argv[1]).convert('RGB')
assert im.size==(1280,720)
a=np.array(im)
t=a[293:427,535:745]
lum=t@np.array([.2126,.7152,.0722])
dark=lum<113
y,x=np.where(dark)
i=a[334:384,608:672]
gold=((i[:,:,0].astype(float)-i[:,:,2])>65)&(i[:,:,1]>130)&(i[:,:,0]>170)
yc,xc=np.where(gold)
assert len(x)>0 and len(xc)>0
for quality in (96,94,92,90,88):
 im.save(sys.argv[2],quality=quality,optimize=True,subsampling=0)
 from pathlib import Path
 if Path(sys.argv[2]).stat().st_size<140000: break
assert Path(sys.argv[2]).stat().st_size<140000
print(json.dumps({'display_full_uncropped_px':[1280,720],'roi_dark_support_bbox_px':[int(np.ptp(x))+1,int(np.ptp(y))+1],
  'thresholded_bright_center_mark_area_px':int(gold.sum()),'thresholded_bright_center_mark_bbox_px':[int(np.ptp(xc))+1,int(np.ptp(yc))+1],
  'context_dependent_pixel_thresholds':'display-only heuristic; not calibrated per-glyph or device',
  'jpeg_quality':quality,'jpeg_bytes':Path(sys.argv[2]).stat().st_size},indent=2,sort_keys=True))
