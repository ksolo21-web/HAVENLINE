from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent; w=1240;s=Image.new('RGB',(w,601),'#101b2b');d=ImageDraw.Draw(s)
def f(n,b=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if b else '')+'.ttf',n)
d.text((36,22),'HAVENLINE  /  LEVEL 1',font=f(22,True),fill='#f1ac6d')
d.text((33,58),'Single-log art candidate',font=f(51,True),fill='#f4f6f8')
d.text((37,127),'Actual crown log isolated from the current pickup bundle',font=f(24),fill='#b5cade')
for i,(n,l) in enumerate((('crown-positive-end','End A'),('crown-negative-end','End B'),('crown-underside','Underside'))):
 x=28+398*i;im=Image.open(p/(n+'.png')).convert('RGB');im=im.resize((385,273),Image.Resampling.LANCZOS)
 s.paste(im,(x,185));d.text((x+6,470),l,font=f(23,True),fill='#f4f6f8')
d.text((36,538),'Studio preview only. No asset export, receiver placement, or gameplay approval.',font=f(22),fill='#b5cade')
s.save(p/'Havenline-Current-Crown-Log-Study.jpg',quality=93,optimize=True)
