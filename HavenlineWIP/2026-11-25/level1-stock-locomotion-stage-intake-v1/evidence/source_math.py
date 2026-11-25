import math,re,numpy as np
from functools import lru_cache
import os
from pathlib import Path
pin=Path(os.environ['HVN_EXACT_STOCK_ROOT'])
def tuplef(s):return tuple(map(float,re.findall(r'[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?',s)))
def array(src,pattern):return re.search(pattern,src,re.S).group(1)
source=(pin/'river_geometry.gd').read_text()
river=[tuplef(v) for v in re.findall(r'Vector2\(([^)]*)\)',array(source,r'const ANCHORS := \[(.*?)\]'))]
widths=tuplef(array(source,r'const WIDTHS := \[(.*?)\]'))
shape=(pin/'accepted_t02_surface.gd').read_text()
banks=[tuplef(v) for v in re.findall(r'Vector4\(([^)]*)\)',array(shape,r'for bank in \[(.*?)\]'))]
endpoints=[tuplef(v) for v in re.findall(r'Vector2\(([^)]*)\)',array(shape,r'for endpoint in \[(.*?)\]'))]
def clamp(v,a=0,b=1):return max(a,min(b,v))
def smooth(a,b,v):
 t=clamp((v-a)/(b-a));return t*t*(3-2*t)
def lerp(a,b,t):return a+(b-a)*t
def seg(x):return next((i for i in range(len(river)-1) if x<=river[i+1][0]),len(river)-2)
def slope(i):
 a=river[max(0,i-1)];b=river[min(len(river)-1,i+1)]
 return (b[1]-a[1])/(b[0]-a[0])
def center(x):
 i=seg(x);a,b=river[i:i+2];h=b[0]-a[0];t=clamp((x-a[0])/h);m,n=slope(i),slope(i+1)
 z=(2*t**3-3*t*t+1)*a[1]+(t**3-2*t*t+t)*h*m+(-2*t**3+3*t*t)*b[1]+(t**3-t*t)*h*n
 dz=((6*t*t-6*t)*a[1]+(3*t*t-4*t+1)*h*m+(-6*t*t+6*t)*b[1]+(3*t*t-2*t)*h*n)/h
 k=math.hypot(1,dz)
 return (z,1/k,dz/k,lerp(widths[i],widths[i+1],t*t*(3-2*t)))
def shore(x,z):
 q=clamp(x,-31,31)
 for j in range(4):
  s,tx,tz,w=center(q)
  q=clamp(q+((x-q)*tx+(z-s)*tz)*tx,-31,31)
 s,tx,tz,w=center(q)
 return abs(-(x-q)*tz+(z-s)*tx)-w*.5
@lru_cache(None)
def vertex(x,z):
 sd=shore(x,z)
 sin,cos,exp=math.sin,math.cos,math.exp
 ripple=sin(x*.53+sin(z*.26))*cos(z*.48)*.055
 drift=smooth(13.5,24,max(abs(x),abs(z)*.86))*(.64+.52*sin(x*.19+z*.15)**2)
 bumps=sum(a*exp(-((x-bx)**2+(z-bz)**2)/(2*w*w)) for bx,bz,a,w in banks)
 path=[]
 for ex,ez in endpoints:
  ez-=.2
  t=clamp((x*ex+(z-.2)*ez)/(ex*ex+ez*ez))
  path.append(math.hypot(x-t*ex,z-.2-t*ez))
 path=min(path)
 shoulders=(.052*exp(-((path-.85)/.30)**2)-.055*exp(-(path/.48)**2))*smooth(2,5,math.hypot(x,z))
 wd_x=abs(x)-9.75+.78;wd_z=abs(z-2.8)-4.3+.78
 wd=math.hypot(max(0,wd_x),max(0,wd_z))+min(max(wd_x,wd_z),0)-.78
 result=lerp(.008*sin(x*.22)*sin(z*.26),-.035+ripple+drift+bumps+shoulders,smooth(-.12,1.8,wd))+.12*exp(-((wd-.36)/.62)**2)
 h=lerp(-.34-.82,.15,smooth(-.42,1.,sd))+.18*exp(-((sd-1.14)/.34)**2)
 return float(np.float32(lerp(h,result,smooth(1.,1.45,sd))))
def height(x,z):
 a=math.floor(x*4)/4;b=math.floor(z*4)/4
 u=(x-a)*4;v=(z-b)*4
 ha,hb,hc,hd=[vertex(i,j) for i,j in [(a,b),(a+.25,b),(a,b+.25),(a+.25,b+.25)]]
 return ha+(hb-ha)*u+(hc-ha)*v if u+v<=1 else hd+(hb-hd)*(1-v)+(hc-hd)*(1-u)
