"""Check posed skin against original GLB triangles. Arguments: poses.json results.json game_directory."""
import json,struct,sys,os
import numpy as np, vtk
from pathlib import Path
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from collections import Counter
a=Path(sys.argv[3])/'assets'; poses=json.loads(Path(sys.argv[1]).read_text())
def mat(d):
 m=np.eye(4);m[:3,:]=np.array(d).T;return m
def read(f):
 b=f.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);raw=b[28+n:]
 def acc(k):
  a=j['accessors'][k];v=j['bufferViews'][a['bufferView']];typ={5120:'i1',5121:'u1',5122:'i2',5123:'u2',5125:'u4',5126:'f4'}[a['componentType']];n={'MAT4':16,'VEC4':4,'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
  return np.frombuffer(raw,dtype=typ,offset=a.get('byteOffset',0)+v.get('byteOffset',0),count=n*a['count']).reshape(-1,n)
 return j,acc
def poly(vtx,faces):
 d=vtk.vtkPolyData();pt=vtk.vtkPoints();pt.SetData(numpy_to_vtk(np.ascontiguousarray(vtx[:,:3]),deep=True)); d.SetPoints(pt)
 c=vtk.vtkCellArray();c.SetCells(len(faces),numpy_to_vtkIdTypeArray(np.c_[np.full(len(faces),3),faces].astype('int64').ravel(),deep=True));d.SetPolys(c);return d
def hit(a,b):
 det=vtk.vtkCollisionDetectionFilter(); xm=vtk.vtkMatrix4x4();xm.Identity();
 for i,thing in enumerate((a,b)):det.SetInputData(i,thing);det.SetMatrix(i,xm)
 det.SetCollisionModeToAllContacts();det.SetBoxTolerance(.00001);det.SetCellTolerance(.00001);det.SetNumberOfCellsPerNode(3);det.Update()
 c=det.GetContactCells(0)
 return [] if not det.GetNumberOfContacts() else vtk_to_numpy(c).tolist()

doc,ac=read(a/'settlement_people/survivor_male_01.glb')
skin=doc['skins'][0]; names=[doc['nodes'][k]['name'] for k in skin['joints']]; invB=ac(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
V=[]; W=[]; J=[];F=[]; labels=[]; groups=[];offset=0
for m in doc['meshes'][0]['primitives']:
 attr=m['attributes'];v=ac(attr['POSITION']).astype(float);idx=ac(m['indices']).ravel().reshape(-1,3);w=ac(attr['WEIGHTS_0']).astype(float); w/=np.maximum(w.sum(1,keepdims=True),.00001);joint=ac(attr['JOINTS_0']).astype(int)
 owners=joint[np.arange(len(v)),w.argmax(1)]; dom=owners[idx]
 faceowners=np.where(dom[:,1]==dom[:,2],dom[:,1],dom[:,0]);groups.extend(faceowners)
 F.append(idx+offset);offset+=len(v);V.append(np.c_[v,np.ones(len(v))]);J.append(joint);W.append(w);labels.extend(owners)
F=np.concatenate(F);V=np.concatenate(V);W=np.concatenate(W);J=np.concatenate(J);G=np.asarray(groups);L=np.asarray(labels)
j,geo=read(a/'field_world/camp_ballista.glb'); towers={}
for n in j['nodes']:
 if n['name'] in ('Footings','Cabin','EmplacementDeck'): continue
 verts=[];faces=[];offset=0
 for m in j['meshes'][n['mesh']]['primitives']:
  v=geo(m['attributes']['POSITION']); idx=geo(m['indices']).ravel().reshape(-1,3)
  verts.append(v);faces.append(idx+offset);offset+=len(v)
 v=np.concatenate(verts);towers[n['name']]=(np.c_[v,np.ones(len(v))],np.concatenate(faces))
measures=[];delta=[];prev=None
for info in poses:
 B=dict(info['bones']);M=np.asarray([mat(B[n]) for n in names])@invB
 moved=np.zeros_like(V)
 for k in range(4):moved+=W[:,k,None]*np.einsum('nij,nj->ni',M[J[:,k]],V)
 face_min=moved[F,:3].min(1);face_max=moved[F,:3].max(1)
 row=dict(id=info['id'],grips=info['gloves'],overlap={})
 for key,(pts,idx) in towers.items():
  t=mat(info['parts'][key])
  v=(pts@t.T)[:,:3]
  subset=np.all((face_max>=v.min(0)-.00001) & (face_min<=v.max(0)+.00001),axis=1)
  ids=np.flatnonzero(subset)
  hits=hit(poly(moved[:,:3],F[ids]),poly(v,idx)) if len(ids) else []
  row['overlap'][key]={names[k]:int(v) for k,v in Counter(G[ids[np.unique(hits).astype(int)]]).items()}
 for side in ('R','L'):
  boots=np.isin(L,[names.index('Foot.'+side),names.index('Toe.'+side)]);p=moved[boots,:3];sole=p[p[:,1]<p[:,1].min()+.018]
  yaw=np.deg2rad(info['id'][1]);x=sole[:,0]*np.cos(yaw)+sole[:,2]*np.sin(yaw);z=sole[:,2]*np.cos(yaw)-sole[:,0]*np.sin(yaw)
  row['sole_'+side]=[float(sole[:,1].min()),float(max(np.abs(x).max(),np.abs(z).max()))]
 if prev is not None:delta.append(np.linalg.norm(moved[:,:3]-prev,axis=1).max())
 prev=moved[:,:3];measures.append(row)
Path(sys.argv[2]).write_text(json.dumps({'frames':measures,'max_adjacent_vertex_displacement_m':float(max(delta))}))
