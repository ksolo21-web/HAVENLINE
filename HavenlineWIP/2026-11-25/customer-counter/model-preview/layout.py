from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
p=Path(__file__).parent
reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(size, b=False): return ImageFont.truetype(bold if b else reg, size)
sheet=Image.new('RGB',(1100,1500),'#101b2b')
d=ImageDraw.Draw(sheet)
ice='#a8c4d9'; white='#f4f6f8'; accent='#f1ac6d'
d.text((36,25),'HAVENLINE  /  LEVEL 1',fill=accent,font=font(22,True))
d.text((34,62),'Customer counter',fill=white,font=font(55,True))
d.text((36,132),'Actual WIP model  ·  Blender preview, not gameplay',fill=ice,font=font(25))
def panel(file,label,b, size, crop=None):
 x,y=b; im=Image.open(p/(file+'.png')).convert('RGB')
 if crop: im=im.crop(crop)
 box=Image.new("RGB",size,"#c9d0d6"); im.thumbnail(size,Image.Resampling.LANCZOS)
 if file=="front": im=im.resize(size,Image.Resampling.LANCZOS)
 box.paste(im,((size[0]-im.width)//2,(size[1]-im.height)//2)); im=box
 d.text((x,y),label,fill=white,font=font(28,True))
 sheet.paste(im,(x,y+43))
panel('front','Customer side',(34,196),(1032,623),(15,20,1085,666))
panel('inside','Camp side',(34,885),(502,321),(15,0,1085,680))
panel('fit','Fence placement study',(564,885),(502,321),(0,0,1280,490))
d.text((34,1280),'The counter replaces one north-fence section.',fill=white,font=font(30,True))
d.text((34,1333),'Plain side sections are the current test wall, not finished fence art.',fill=ice,font=font(24))
d.text((34,1375),'Counter art and in-game readability are still under review.',fill=ice,font=font(24))
sheet=sheet.crop((0,0,1100,1434))
sheet.save(p/'Havenline-Level-1-Counter-Preview.jpg',quality=93,optimize=True)
