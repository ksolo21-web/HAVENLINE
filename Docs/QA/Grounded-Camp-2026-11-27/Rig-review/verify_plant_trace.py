from pathlib import Path
import sys,json,numpy as np
from itertools import groupby
from pathlib import Path
import sys, json,struct
import numpy as np
d=Path(sys.argv[1]); meta=json.loads((d/'native-meta.json').read_text());rows=[json.loads(l) for l in (d/'native.jsonl').read_text().splitlines()]
def m4(a):
 a=np.array(a,float).reshape(-1,3,4);b=np.broadcast_to(np.array([0,0,0,1]),(len(a),1,4));return np.concatenate((a,b),axis=1)
f=(d/'native-geom.bin').open('rb');arr=[]
for typ in ['f','i','f','i']:
 n=struct.unpack('<I',f.read(4))[0];arr.append(np.frombuffer(f.read(n),dtype=typ))
p=arr[0].reshape(-1,3);N=len(p);w=arr[2].reshape(N,-1);bi=arr[3].reshape(N,-1);inds=np.where(p[:,1]<.24)[0];pp=np.c_[p[inds],np.ones(len(inds))];bb=bi[inds];ww=w[inds];q=[];allfeet={}
ib=m4(meta['ib'])
for row in rows:
 local=m4(row['bones'])@ib
 world=m4(row['root'])[0]@local
 q.append(np.einsum('nvij,nj,nv->ni',world[bb,:,:][:,:,:3,:],pp,ww))
q=np.array(q);raw=p[inds];gait=np.array([r['state'] for r in rows]);t=np.arange(len(rows))/120;speed=np.array([r['speed'] for r in rows]);idx_window=np.arange(84,270); travel=np.linalg.norm(np.diff(np.array([r['actor'][3::4] for r in rows]),axis=0),axis=1)*120
sustain=np.abs(travel[idx_window-1]-np.median(speed[idx_window]))<.04
# Exclude moving into a collider even if CharacterBody3D.velocity still contains the requested maximum.
stop=np.where(~sustain)[0];steady=idx_window[:int(stop[0]) if len(stop) else None]
assert len(steady)>115
foot_ys=[];debug={}

def runs(x):
 return [(k,np.asarray(list(v))) for k,v in groupby(range(len(x)),key=lambda i:bool(x[i]))]
def mm(x):return round(float(x)*1000,1)
report={'method':'Actual normal-input physics at 120Hz. For each complete loading interval with minimum boot height under 6 mm, keep one original material vertex that stays in contact longest. Keep that vertex fixed until it leaves the 6 mm band. Separately report tangential velocity of the active lowest material when support rolls from heel to toe. Snow top is y=0. Values include no screen-based threshold.','feet':{}}
for s,sgn in [('L',1),('R',-1)]:
 sole=np.flatnonzero((raw[:,0]*sgn>0)&(raw[:,1]<.049));f=q[steady][:,sole];ys=f[:,:,1];ev=[]
 for active,idx in runs(ys.min(1)<.006):
  if not active or len(idx)<4 or idx[0]==0 or idx[-1]==len(f)-1:continue
  z=ys[idx];v=list();longest=[]
  for j in range(len(sole)):
   hr=[ix for on,ix in runs(z[:,j]<.006) if on];longest.append(max(hr,key=len) if hr else np.array([],int))
  j=max(range(len(sole)),key=lambda k:len(longest[k]));loc=idx[longest[j]];world=f[loc,j][:,[0,2]];dif=world-world[0];mag=np.linalg.norm(dif,axis=1)
  for ti,tn in zip(idx[:-1],idx[1:]):
   k=(ys[ti]+ys[tn]).argmin();dlt=np.linalg.norm(f[tn,k,[0,2]]-f[ti,k,[0,2]])*120;v.append(float(dlt))
  ev.append({'start_tick':int(steady[idx[0]]),'stop_tick':int(steady[idx[-1]]),'support_ms':round(len(idx)*1000/120,1),'original_native_vertex':int(inds[sole[j]]),'same_patch_ms':round(len(loc)*1000/120,1),'same_patch_max_drift_mm':mm(mag.max()),'active_patch_speed_median_m_s':round(float(np.median(v)),3),'active_patch_speed_peak_m_s':round(float(max(v)),3)})
 report['feet'][s]=ev
print({k:[(v['same_patch_max_drift_mm'],v['active_patch_speed_median_m_s']) for v in a] for k,a in report['feet'].items()}); (d/'Planted-material.json').write_text(json.dumps(report,indent=2))
