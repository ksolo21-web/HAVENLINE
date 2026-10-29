#!/usr/bin/env python3
"""Actual owner-pixel cooker component segmentation for isolated neural meshing.

Only masks visible pixels, never fabricates sides/depth or an alternate style.
Exact original hashes are required. All results are unapproved candidates.
"""
import json,hashlib,argparse
from pathlib import Path
from PIL import Image,ImageDraw
REFS={
 'raw_meat_crate':{'file':'32451.jpg','sha256':'70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4',
 'outline':[(97,614),(121,598),(202,570),(258,576),(322,568),(385,558),(485,551),(544,557),(619,565),(681,577),(758,615),(772,668),(768,786),(747,816),(642,837),(497,833),(359,835),(245,828),(148,809),(100,747)]},
 'finished_food_tray':{'file':'32450.jpg','sha256':'5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719',
 'outline':[(488,662),(507,637),(553,616),(584,594),(626,581),(699,569),(824,561),(886,571),(952,601),(999,626),(1024,655),(1032,701),(1005,752),(972,779),(550,795),(510,757),(486,722)]},
 'saw_window_and_handle':{'file':'32451.jpg','sha256':'70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4',
 'outline':[(833,488),(845,464),(864,439),(903,419),(957,419),(990,438),(1019,480),(1019,555),(1009,604),(1028,614),(1045,644),(1038,667),(993,681),(891,698),(859,689),(838,657)]}
}
def prepare(root,out):
 root=Path(root);out=Path(out);out.mkdir(exist_ok=True,parents=True);receipt=[]
 for name,v in REFS.items():
  path=root/v['file'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
  assert sha==v['sha256'],f'{name}: original source hash differs'
  image=Image.open(path).convert('RGB')
  mask=Image.new('L',image.size,0)
  points=[(round(x*1.2),round(y*1.2)) for x,y in v['outline']] if v['file']=='32451.jpg' else v['outline']
  ImageDraw.Draw(mask).polygon(points,fill=255)
  bbox=mask.getbbox();assert bbox
  original=Image.new('RGB',image.size,(128,128,128));original.paste(image,(0,0),mask)
  crop=original.crop(bbox);cw,ch=crop.size;scale=min(430/cw,430/ch)
  resized=(max(1,round(cw*scale)),max(1,round(ch*scale)))
  output=Image.new('RGB',(512,512),(128,128,128))
  output.paste(crop.resize(resized,Image.Resampling.LANCZOS),
    ((512-resized[0])//2,(512-resized[1])//2))
  output.save(out/f'{name}.png')
  receipt.append({'component':name,'source':v['file'],'source_sha256':sha,
   'visible_pixel_bbox':bbox,'image':f'{name}.png','source_view_only':True,
   'hidden_geometry_verified':False,'T05_critic_approved':False})
 (out/'receipt.json').write_text(json.dumps({
   'status':'SOURCE_VISIBLE_COMPONENT_MASKS_NOT_FABRICATED_REFERENCE_VIEWS',
   'components':receipt},indent=2)+'\n')
 return receipt
if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--source-dir',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();print(json.dumps(prepare(a.source_dir,a.out),indent=2))
