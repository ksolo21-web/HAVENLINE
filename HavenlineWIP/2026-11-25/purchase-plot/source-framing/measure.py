"""Detached source projection only; reads immutable local review evidence."""
import math,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import tempfile
from PIL import Image
root=Path(__file__).resolve().parent.parent
read=lambda p: p.read_bytes()
sha=lambda p:hashlib.sha256(read(p)).hexdigest()
pose=root/'hvn-l1-counter-facing-feasibility-v1'
v6=root/'havenline-buyplot-v6-render-pin.89MiFa/repo'
rc2=root/'havenline-l1-plot-camera-rc2'
old=root/'havenline-buy-plot-footprint-study-v8'
raw_v6='83efcd4e5e5eead175c9addc7ad6f5a8d4848978'
baseline='11c14a1c41971067c7dc97db69375f720a408f68'
asset='HavenlineLevel1/previews/plot_art/construction_three_wood.svg'
import subprocess
def git(*a): return subprocess.check_output(['git','-C',str(v6),*a],stderr=subprocess.DEVNULL)
assert git('show',raw_v6+':'+asset)==read(rc2/asset)
for f in (asset,'HavenlineLevel1/previews/construction_plot_ground.gd'):
 assert subprocess.run(['git','-C',str(v6),'cat-file','-e',baseline+':'+f],stderr=subprocess.DEVNULL).returncode!=0
for f in ('HavenlineLevel1/accepted_t02_surface.gd','HavenlineLevel1/terrain_source.gd','HavenlineLevel1/river_geometry.gd','HavenlineLevel1/layout.json','HavenlineLevel1/previews/hero_locomotion.gd'):
 assert git('show',raw_v6+':'+f)==git('show',baseline+':'+f)
assert sha(rc2/'SHA256SUMS')=='512c9a4d3e6d861bccb0a86681b6e853ae68256d4ab7a169b462ed0f09dec9f2'
assert sha(rc2/asset)=='b59289ae5772fb85855823a3c7daaea78f1846b97e2964340ef9ecfe72eb4476'
runtime=git('show',baseline+':HavenlineLevel1/previews/integrated_opening.gd').decode()
assert 'if not _within_logical_reach(pad_anchor, .72):' in runtime
assert 'purchase_pad_view.install_exact()' in runtime
assert 'rotated(Vector3.UP, atan2(7.0, 11.0))' in runtime
for line in (old/'STUDY_SHA256').read_text().splitlines():
 h,n=line.split('  ',1); assert sha(old/n)==h
ctx={'__file__':str(old/'project.py')}
src=(old/'project.py').read_text().split('for w in (.8,.98,1.0,1.02):')[0]
exec(compile(src,str(old/'project.py'),'exec'),ctx)
for line in (pose/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);assert sha(pose/n)==h
routes={r['id']:r for x in (pose/'native-route.log').read_text().splitlines() if x.startswith('ACTUAL_ANGLE ') for r in [json.loads(x[13:])]}
reference=next((root/'havenline-pad-v6-south-read-window').glob('replay.*/render.log'))
assert sha(reference)=='01b04d658be8e277c96ec098536741d0a482657a5a231a6491bd3b50add111d7'
assert (pose/'provenance.txt').read_text().splitlines()[0]==baseline
south={r['name']:r for x in reference.read_text().splitlines() if x.startswith('APPROACH ') for r in [json.loads(x[9:])]}
pose_result=json.loads((pose/'result.json').read_text())
doc=ET.fromstring(read(rc2/asset))
groups={'wood':[5,6,7,8],'digit':[9]}
masks={}
for label,which in groups.items():
 prop=ET.Element(doc.tag,doc.attrib)
 for i in which:prop.append(doc[i])
 with tempfile.TemporaryDirectory() as temp:
  input_file=Path(temp)/'glyph.svg'; png=Path(temp)/'glyph.png'
  input_file.write_bytes(ET.tostring(prop))
  subprocess.run(['inkscape',str(input_file),'--export-filename='+str(png)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  image=Image.open(png).convert('RGBA')
 alpha=np.asarray(image)[:,:,3]
 z,x=np.where(alpha[::2,::2]>=128)
 masks[label]=np.stack([2*x+.5,2*z+.5],axis=1)
 assert len(x)>90
yaws=[x for x in ('facing-inboard-+0','facing-inboard-+30','facing-inboard--30')]
reported=pose_result['measurements']
result={'scope':'Exact source-svg alpha samples, pinned terrain mesh port, captured live 11c14a1c Character1 idle samples reposed to prior V6 approach foot/yaw; geometric-only conditional, no load or frame review.', 'source':{'svg':sha(rc2/asset),'pose_log':sha(pose/'native-route.log'),'approach_log':sha(reference)},'checks':{}}
rx=np.array([11.,0.,-7.]);rx/=np.linalg.norm(rx)
def get_pose(n):
 f=pose/'native'/(n+'.json')
 result['source'][n]=sha(f)
 assert result['source'][n]==reported[n]['born_from_actual_mesh_sha256']
 row=routes[n]
 assert row['animation']=='l1_hero_preview/idle' and row['floor']
 data=json.loads(read(f)); assert len(data)==1 and data[0]['matrixes']==66
 V=np.array(data[0]['positions'])
 F=np.array(data[0]['triangles']).reshape(-1,3)
 assert len(F)==96001
 return V[F]-np.array(row['actor_foot']),row['retained_physics_yaw']
def rotate_y(x,t):
 c,s=math.cos(t),math.sin(t)
 return np.matmul(x,[[c,0,-s],[0,1,0],[s,0,c]])
def blocked(T,P,direction):
 ry=np.cross(direction,rx)
 B=np.stack((rx,ry,direction),axis=1)
 P=P@B;T=T@B
 eps=1e-8
 sel=((T[:,:,:2].min(1)<=P[:,:2].max(0)+eps)&(T[:,:,:2].max(1)>=P[:,:2].min(0)-eps)).all(1)
 T=T[sel]
 d=P[:,:2]; out=np.zeros(len(P),bool)
 for a in range(0,len(T),400):
  t=T[a:a+400]; v=t[:,0,:]; A=t[:,1,:]-v; B=t[:,2,:]-v
  den=A[:,0]*B[:,1]-A[:,1]*B[:,0]
  den=np.where(abs(den)>1e-14,den,np.nan)
  ex=d[:,0]-v[:,0,None];ey=d[:,1]-v[:,1,None]
  u=(ex*B[:,1,None]-ey*B[:,0,None])/den[:,None]
  w=(ey*A[:,0,None]-ex*A[:,1,None])/den[:,None]
  hit=(u>=-eps)&(w>=-eps)&(u+w<=1+eps)&(v[:,2,None]+u*A[:,2,None]+w*B[:,2,None]>P[:,2]+eps)
  out|=np.any(hit,axis=0)
 return out
for name in yaws:
 T,yaw=get_pose(name)
 for sn,row in south.items():
  body=np.array(ctx['tuplef'](row['actor_global']))
  t=rotate_y(T,row['actor_yaw_rad']-yaw)
  for ky,camera_h,field in [('V6',11,.8),('RC2',20.3,1.4),('steep',29,1.4),('steeper',42,1.4),('near_nadir',75,1.4),('overhead_86deg',math.hypot(7,11)*math.tan(math.radians(86)),1.4)]:
   if ky=='overhead_86deg' and (sn!='05-south-090cm' or name!=yaws[0]):continue
   direction=np.array([7,camera_h,11]);direction=direction/np.linalg.norm(direction)
   worlds={g:np.array([ctx['vector'](u,v,field) for u,v in mask])+[ctx['X'],ctx['Y'],ctx['Z']] for g,mask in masks.items()}
   checks=result['checks'].setdefault(ky,{})
   checks.setdefault(sn,{})[name]={g:[int(o.sum()),len(o)] for g,W in worlds.items() for o in [blocked(t,W-body,direction)]}
print(json.dumps(result,indent=2,sort_keys=True))
