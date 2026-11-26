"""Rebuild the boot and wolf-paw texture atlas with Python, NumPy and Pillow."""
from PIL import Image,ImageDraw,ImageFilter
from pathlib import Path
# Mask drawn at 4x. The green channel carries raised snow along the compressed rim.
s=256;atlas=Image.new('RGB',(s*2,s))
for kind in range(2):
 im=Image.new('L',(s,s));p=ImageDraw.Draw(im)
 def poly(points,v=215):p.polygon([(int(x*s),int(y*s)) for x,y in points],fill=v)
 def oval(cx,cy,rx,ry,v):p.ellipse(tuple(int(q*s) for q in (cx-rx,cy-ry,cx+rx,cy+ry)),fill=v)
 if not kind:
  oval(.50,.32,.267,.239,202);poly([(.247,.29),(.758,.30),(.705,.51),(.56,.58),(.512,.64),(.339,.622)],211)
  poly([(.34,.66),(.64,.65),(.683,.78),(.628,.858),(.46,.89),(.318,.85),(.293,.78)],225)
  for y in [.23,.32,.41,.49,.72,.79]:
   p.line([(int(.28*s),int((y+.03)*s)),(int(.46*s),int((y-.015)*s)),(int(.67*s),int((y+.008)*s))],fill=110,width=6)
 else:
  poly([(.22,.62),(.29,.54),(.40,.47),(.46,.40),(.55,.402),(.62,.48),(.73,.54),(.79,.63),(.75,.72),(.65,.77),(.52,.73),(.41,.78),(.28,.75)],224)
  for cx,cy,rx,ry in [(.231,.45,.094,.123),(.404,.31,.098,.135),(.595,.30,.098,.135),(.774,.445,.094,.122)]:
   oval(cx,cy,rx,ry,218);poly([(cx-.035,cy-ry-.025),(cx+.03,cy-ry-.025),(cx+.004,cy-ry-.09)],162)
 blurred=im.filter(ImageFilter.GaussianBlur(1.3));expand=im.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(2))
 import numpy as np
 full=np.asarray(blurred,dtype=float);rim=np.maximum(0,np.asarray(expand,dtype=float)-full);shade=np.zeros_like(full);shade[3:,2:]=full[:-3,:-2];lip=np.maximum(0,shade-full)*.35+rim*.65
 a=np.stack([full,lip,np.zeros_like(full)],axis=-1).clip(0,255).astype('B');atlas.paste(Image.fromarray(a),(kind*s,0))
out=Path(__file__).resolve().parents[2]/'assets/field_world'
out.mkdir(parents=True,exist_ok=True)
atlas.resize((256,128),Image.Resampling.LANCZOS).save(out/'snow_prints.png')
