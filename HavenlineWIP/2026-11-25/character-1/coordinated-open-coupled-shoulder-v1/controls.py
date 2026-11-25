"""Fast exact named relative sleeve and hard torso controls for authored prototype."""
from pathlib import Path
src=Path('audit.py').read_text()
exec(compile(src[:src.index('# Full posed character')],'audit.py','exec'))
c_body=json.loads(Path('result.json').read_text())
idx=np.setdiff1d(np.arange(len(F)),local['removed'])
assert len(c_body['body_self_clearance']['first_20_new_face_indices_and_relative_types'])>=3
def touch(a,b,arr):
 x=arr[F[a]]; y=arr[F[b]]
 return bool(crosses(x,y) or crosses(y,x))
old=[(44477,51156),(44477,51158)]
new=[tuple(map(int,idx[[a,b]])) for a,b,_,_ in c_body['body_self_clearance']['first_20_new_face_indices_and_relative_types'][:3]]
ans=[]
for class_name,examples in [('old_fixed_elbow_reject',old),('new_coordinated_shoulder_reject',new)]:
 for a,b in examples:
  ft=F[[a,b]]
  region=np.asarray(names)[np.argmax(Rsource[ft].mean(1),axis=-1)]
  before,after=touch(a,b,V),touch(a,b,source_positions)
  if class_name.startswith('new'):assert not before and after
  else:
   assert not before and not after
   wr=np.array(J['sides']['R']['shoulder'])
   q,_=Qp['R'][1]
   norm=np.linalg.norm(source_positions[ft.ravel()]-rot_apply(V[ft.ravel()],wr,q),axis=1)
   assert norm.max()<2e-7
  ans.append({'source_faces':[a,b],'case':class_name,'dominant_source_regions':region.tolist(),'strict_original':before,'strict_candidate':after})
print(json.dumps({'explicit_body_pair_controls':ans,'torso_hit_by_side':{side:len(v) for side,v in mix0.items()}},indent=2,sort_keys=True))
