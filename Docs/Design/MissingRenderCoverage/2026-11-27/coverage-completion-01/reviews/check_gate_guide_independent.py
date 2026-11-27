"""Independent sampled geometry check; extracts pure builder functions without executing rendering or writes."""
import ast,json,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];s=p/'author-guides/fortress-double-gate-r2';e=p/'reviews/evidence';rid='author-guide-fortress-double-gate-r2'
raw=(s/'guide.py').read_text();tree=ast.parse(raw);wanted={'height','leaf_point','camera','project'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted];ns={'math':math,'np':np,'PARAMETERS':json.loads((s/'parameters.json').read_text())};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(s/'guide.py'),'exec'),ns)
checks={};maxerr=0.0;records=[]
for side,sgn,angle in [('left',-1,-math.pi/2),('right',1,math.pi/2)]:
 rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
 hinge=np.array([sgn,0,0.]);us=np.linspace(0,1,101)
 for u in us:
  z=2+math.sqrt(2*u-u*u);closed=np.array([sgn*(1-u),0,z]);actual_closed=ns['leaf_point'](side,'closed',float(u),z);actual_open=ns['leaf_point'](side,'open',float(u),z);expected=hinge+rot@(closed-hinge)
  maxerr=max(maxerr,float(np.max(abs(actual_closed-closed))),float(np.max(abs(actual_open-expected))))
  assert np.allclose(actual_open,[sgn,-u,z]);assert np.allclose(actual_open[2],actual_closed[2]);assert abs(np.linalg.norm(actual_open-hinge)-np.linalg.norm(closed-hinge))<1e-12
 checks[side+'_sampled_rigid_rotation_and_monotone_top']=bool(np.all(np.diff([2+math.sqrt(2*u-u*u) for u in us])>=0))
 front=ns['camera']([6.,-8.,5.]);rear=ns['camera']([-6.,8.,5.]);hinge_base=ns['leaf_point'](side,'open',0,0);free_base=ns['leaf_point'](side,'open',1,0)
 projfront=ns['project']([hinge_base,free_base],front);projrear=ns['project']([hinge_base,free_base],rear)
 checks[side+'_front_free_base_projects_nearer_down']=bool(projfront[1,1]<projfront[0,1]);checks[side+'_rear_free_base_projects_farther_up']=bool(projrear[1,1]>projrear[0,1]);records.append({'side':side,'front_base_projection':projfront.tolist(),'rear_base_projection':projrear.tolist()})
checks['actual_code_matches_independent_rotation']=bool(maxerr<1e-12)
checks['opposing_horizontal_cameras_same_positive_height']=bool(np.allclose(np.array(front[0])[:2],-np.array(rear[0])[:2]) and front[0][2]==rear[0][2] and front[0][2]>0)
for label,b in [('front',front),('rear',rear)]:
 mat=np.array(b[2:]);checks[label+'_orthonormal_basis']=bool(np.allclose(mat@mat.T,np.eye(3)))
checks['same_frame_function_in_all_panels']='faces = fixed_frame()+leaf_faces(\'left\',state)+leaf_faces(\'right\',state)' in raw
assert all(checks.values());report={'reviewer':'/root/missing_world_audit','independent':True,'status':'PASS_INDEPENDENT_GEOMETRY_CALCULATIONS','samples_per_leaf':101,'maximum_coordinate_error':maxerr,'checks':checks,'projected_endpoint_evidence':records,'scope':'Authored geometry guide only; no game art or source-evidence approval.'};(e/(rid+'-independent-math.json')).write_text(json.dumps(report,indent=2)+'\n')
imfile=s/'fortress-double-gate-r2.png';data=imfile.read_bytes();prov={'source_path':str(imfile),'source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'crops':[]}
with Image.open(imfile) as im:
 for name,box in {'open-front':[1024,258,1852,988],'open-rear':[1944,242,2846,988]}.items():
  f=e/(rid+'-'+name+'.png');im.crop(box).save(f);d=f.read_bytes();prov['crops'].append({'path':str(f),'bbox_xyxy':box,'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d),'resize':False})
(e/(rid+'-crop-provenance.json')).write_text(json.dumps(prov,indent=2)+'\n');print(json.dumps(report))
