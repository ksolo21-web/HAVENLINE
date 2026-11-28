from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).parent
im=Image.open(p/'wood.png').convert('RGB')
w=1420
sheet=Image.new('RGB',(w,741),'#101b2b')
d=ImageDraw.Draw(sheet)
def f(size,bold=False): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
d.text((38,18),'HAVENLINE  /  LEVEL 1',font=f(24,True),fill='#f1ac6d')
d.text((37,52),'Wood transfer: source models',font=f(49,True),fill='#f4f6f8')
d.text((39,119),'Offline studio comparison • Matching display size, not game scale',font=f(25),fill='#b5cade')
sheet.paste(im,(0,158))
for x,label in ((58,'Legacy environment log'),(552,'Unapproved world log'),(1040,'Current carry bundle')):
 d.text((x,693),label,font=f(25,True),fill='#f4f6f8')
sheet.save(p/'Havenline-Wood-Transfer-Source-Models.jpg',quality=91,optimize=True)
