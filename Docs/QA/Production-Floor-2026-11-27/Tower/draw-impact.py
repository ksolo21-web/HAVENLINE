from PIL import Image,ImageDraw,ImageFilter
import math
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Write the six-frame contact effect to a supplied game art directory.')
parser.add_argument('output',type=Path)
d=parser.parse_args().output
N=288
sheet=Image.new('RGBA',(96*6,96))
radii=[.46,.86,1.0,.91,.78,.62]
alpha=[1.,1.,.96,.72,.44,.18]
angles=[-.13,.55,1.15,1.91,2.48,3.19,3.76,4.43,5.07,5.58]
length=[1.,.42,.70,.93,.40,.78,.54,.83,.50,.96]
for i in range(6):
 im=Image.new('RGBA',(N,N));dr=ImageDraw.Draw(im);size=N*.41*radii[i];cx=cy=N*.5
 def point(a,r):return (cx+math.cos(a)*r,cy+math.sin(a)*r)
 for scale,color in [(1.,(255,153,41)),(.79,(255,221,88)),(.48,(255,249,191))]:
  pts=[]
  for a,k in zip(angles,length):
   pts.extend((point(a-.11,size*(.22-.015*i)*scale),point(a,size*k*scale),point(a+.13,size*.22*scale)))
  dr.polygon(pts,fill=(*color,round(255*alpha[i])))
 if i>=2:
  for a,k in [(-1.04,.88),(2.81,.74),(.34,.71)]:
   rad=N*.41*(.45+.135*i)*k;x,y=point(a,rad);rr=int(N*.018*(1.1-.11*i));dr.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(255,226,122,round(255*alpha[i])))
 sheet.paste(im.resize((96,96),Image.Resampling.LANCZOS),(96*i,0))
sheet.save(d/'ballista_impact.png')
