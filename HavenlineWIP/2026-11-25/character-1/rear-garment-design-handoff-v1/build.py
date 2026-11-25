import os
from pathlib import Path
import hashlib,json,numpy as np
P=Path(__file__).resolve().parent
dirs={k:Path(os.environ[var]) for k,var in {'approved': 'C1_APPROVED_REAR_DATA', 'occupancy': 'C1_REAR_POCKET_DATA', 'cut': 'C1_REAR_CUT_DATA'}.items()}
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['1a64d744fc99d4b3cc1af7e7e4d790aa1611fc0b9b929f1659c7c33c5a348e30','73cee1151bcd82f9de6d9a3cbedf700595b91af61d21186297824a8f0c9db59f','0bcd2165f76806ac59597ad3a262222740fd09fca4e83893df6d0663909be752','aaa19c60d3aab56082ca7290e0c28cbef85d48938381452027b0a5d40e47a9ac']
source_seals=dict(zip(('approved','occupancy','cut','anterior'),expected))
assert h(dirs['approved']/'new-rear-panel.npz')=='023ed33af9ac04e8c6223fb6abfd2f2002d3b3b8a06c00b50dba0b581ad389bf'
assert h(dirs['occupancy']/'pocket-solids.npz')=='9e5aa05dcd139dcfecad78ef790af5b8d612067137cf43ee87612a75b74f9038'
assert h(dirs['cut']/'measurements.json')=='fdd96e98d20636efec3f60a00972fd0f25f0e328b61e16a033cb97d420a103bc'
A=np.load(dirs['approved']/'new-rear-panel.npz');old=np.load(dirs['occupancy']/'pocket-solids.npz');cut=json.loads((dirs['cut']/'measurements.json').read_text())
mk=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz');assert h(mk)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
D=np.load(mk)
T=A['tri'];V=A['v'];state={'neutral':V,'held-original-0ms':old['retained'][-1].astype(float)}
assert np.array_equal(T,old['shell_tri'])
assert np.max(np.abs(V-old['retained'][0]))<1e-7
e=T[:,((0,1),(1,2),(2,0))].reshape(-1,2)
ue,c=np.unique(np.sort(e,axis=1),axis=0,return_counts=True);rim=ue[c==1];assert len(rim)==162
region=set(map(int,A['region'])); collar_vid=set(rim.ravel())
# Protected side/front section = endpoint support of full source, not a narrowed regional bounds box.
def section(t,axis,s):
 hits=[]
 for i in range(3):
  a,b=t[i],t[(i+1)%3]; da=a[axis]-s;db=b[axis]-s
  if abs(da)<1e-11:hits.append(a)
  if da*db<0:hits.append(a+(b-a)*da/(da-db))
 u=np.unique(np.round(hits,11),axis=0)
 if len(u)==2 and np.linalg.norm(u[0]-u[1])>1e-9:return u
def sections(x,axis,stations):
 y=x[T];lo=y[:,:,axis].min(1);hi=y[:,:,axis].max(1)
 out=[]
 for s in stations:
  z=[]
  for j in np.flatnonzero((lo<=s)&(s<=hi)):
   zz=section(y[j],axis,s)
   if zz is not None:z.append([int(j),zz.tolist()])
  out.append({'value_m':s,'segments':z})
 return out
def guard(s):
 tmp=np.array([line for j,line in s['segments']]); cr=tmp.reshape(-1,3)
 show=[]
 for k,axis,fn in [('front',1,np.argmin),('minX',0,np.argmin),('maxX',0,np.argmax)]:
  i=int(fn(cr[:,axis]));show.append([k,s['segments'][i//2][0],cr[i].tolist()])
 return {'z_m':s['value_m'],'sampled_extrema':show}
core=range(42528,42534);assert set(core)<=region
motion={'sha256':h(mk),'times_ms':[0,75,150],'bone_order':['Thigh','Shin','Foot','ToeBase'],'right_bone_delta_matrices_raw_local':D['bones'][:,1].tolist(),'source_origin_raw':D['source_origin'].tolist(),'source_to_m_scale':float(D['scale']),'rest_to_held':'Bone shortest proper rotations and linear raw translation, inherited analytical source at frozen 0 ms; 75/150 are unchanged future validation, not passed. For raw evaluation use point_m / scale + source_origin; then subtract source_origin and multiply scale.'}
pack={'coordinate_axes':'metres, +X model left, +Y posterior, +Z up; both frames common model space','source_seals':source_seals,'vertex_skin_conventions':'Exact neutral/held visible shell source IDs; four stored entries are Thigh/Shin/Foot/ToeBase. Material UV by original triangle corner, no transfer claim. Anterior exact four rows protected separately, not transferred from another mesh by inference.','motion':motion,'approved_posterior_faces':[{ 'id':i,'vertex_ids':T[i].tolist(),'uv':A['u'][i].tolist(),'protected_from_bounded_cut':i not in cut['partition_source_face_ids'],'critical_overrun':i in core} for i in sorted(region)],'approved_boundary_vertices':A['boundary'].tolist(),'bottom_and_toe_contract':'Keep original entire boot sole and ToeBase. Wire bottom slices below are locator references, not remodeled sole.','collar_boundary_edge_vertex_ids':rim.tolist(),'previous_exact_rail_source':cut['rail_source'],'previous_cut_m':cut['bounds_m'],'previous_failed_corridor_z_m':[.402,.487],'anterior_source_native_rows':[13484,13613,14018,14078],'states':{}}
# OBJ includes sparse actual layers and disconnected guide wires. Distinguish reject occupancy.
F=P/'posterior-neutral-and-bent.obj'; fh=F.open('w');cnt=0
def obj(name,V,inds,kind):
 global cnt
 fh.write('o '+name+'\n')
 for q in V:fh.write('v %.10f %.10f %.10f\n'%tuple(q))
 for f in inds:fh.write(kind+' '+' '.join(str(cnt+int(i)+1) for i in f)+'\n')
 cnt+=len(V)
def wire(name,lines):
 x=np.array(lines).reshape(-1,3);obj(name,x,np.arange(len(x)).reshape(-1,2),'l')
for k,(name,X) in enumerate(state.items()):
 widx=np.unique(np.r_[T[A['region']].ravel(),rim.ravel()]); rr={int(v):j for j,v in enumerate(widx)}
 wire(name+'_protected_collar_perimeter',X[rim]); obj(name+'_critical_rear_source_faces_42528_to_42533',X[widx],[[rr[i] for i in T[q]]for q in core],'f')
 obj(name+'_approved_rear_other_source_faces',X[widx],[[rr[i] for i in T[q]]for q in sorted(region-set(core))],'f')
 sq=sections(X,0,[-.1505,-.1425,-.1305,-.1205,-.1055,-.0895]); ss=sections(X,2,[.4015,.4245,.4305,.4435,.4565,.4715,.4865]); lowest=float(X[:,2].min()); outsole=sections(X,2,[lowest+.0025,lowest+.0085,lowest+.0155])
 for j,a in enumerate(sq):
  t=[ln for _,ln in a['segments'] if min(z[2] for z in ln)>.340 and max(z[2] for z in ln)<.560]
  wire(name+f'_sagittal_section_{j}',t)
 for j,a in enumerate(ss):wire(name+f'_transverse_section_{j}',[ln for _,ln in a['segments']])
 for j,a in enumerate(outsole):wire(name+f'_protected_sole_locator_{j}',[ln for _,ln in a['segments']])
 for n in ('shin','thigh','roll'):
  obj(name+'_REJECTED_overlay_occupancy_'+n,old[n][0 if k==0 else -1],old[n+'_tri'],'f')
 for n,r in cut['rail_source'].items():
  pts=np.array([q['bary']@X[T[q['face']]] for q in r]).reshape(3,7,3);wire(name+'_previous_'+n+'_source_rails',[s for row in pts for s in zip(row,row[1:])])
 pack['states'][name]={'exact_rear_and_collar_vertices':{int(i):X[i].tolist() for i in widx},'sagittal_x_stations':sq,'transverse_z_stations':ss,'outline_guard_samples':[guard(a) for a in ss],'sole_guard_samples':[guard(a) for a in outsole]}
fh.close()
(P/'sections-and-motion.json').write_text(json.dumps(pack,separators=(',',':')))
print('faces',len(region),'collar',len(rim),'OBJ rows',cnt,'frames',list(state))
