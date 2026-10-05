"""Deterministically materialize the bounded reference fence/gate and terrain joins.

Authoring uses a frozen exact-source CPU chord snapshot. Runtime route, collision,
terrain and panel transform authority remain untouched. --verify changes nothing.
"""
from pathlib import Path
import argparse, collections, hashlib, json, math, re, tempfile
import numpy as np
import task03_reference_primitives as authored
from task03_mesh_authoring import basis_from_y
ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/"HavenlineGodot/assets/t03_boundary_v2"
namespace={k:getattr(authored,k) for k in ["fit_visual_envelope","fence_panel","gate_post","picket","export_obj","topology_errors"]}
Model=authored.Model;rot=authored.rotation;original_box=Model.bevel_box

def compact(m,name,mat,size,center=(0,0,0),bevel=0,matrix=None,tint=(1,1,1),variation=0):
 h=np.array(size)*.5
 if bevel:
  x,y,z=h;b=min(bevel,x*.3,y*.3);outline=[(-x+b,-y),(x-b,-y),(x,-y+b),(x,y-b),(x-b,y),(-x+b,y),(-x,y-b),(-x,-y+b)]
 else:
  x,y,z=h;outline=[(-x,-y),(x,-y),(x,y),(-x,y)]
 n=len(outline);v=[[x,y,zz]for zz in [-z,z]for x,y in outline];f=[]
 for i in range(n):
  j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i]])
 for i in range(1,n-1):f.extend([[0,i+1,i],[n,n+i,n+i+1]])
 return m.add(name,mat,v,f,center,matrix,tint,smooth=False,variation=variation)

def box_override(self,name,*args,**kwargs):
 if name=='rear_support':return compact(self,name,*args,**kwargs)
 return original_box(self,name,*args,**kwargs)
Model.bevel_box=box_override

def leaf():
 m=Model('gate_leaf');length=2.9
 for i in range(10):
  x=-1.35+(i+.5)*2.7/10;compact(m,'gate_board_%02d'%i,'wood_light',(.264,1.01,.068),(x,.63,0),.018)
 for x in [-1.365,1.365]:compact(m,'gate_stile','wood_light',(.17,1.12,.11),(x,.61,-.012))
 for y in [.15,1.115]:compact(m,'gate_crossrail','wood_light',(length,.15,.13),(0,y,-.022))
 a=np.array((-1.27,.25,-.061));b=np.array((1.26,1.,-.061))
 from task03_mesh_authoring import basis_from_y
 compact(m,'gate_diagonal','wood_light',(.12,np.linalg.norm(b-a),.067),(a+b)*.5,matrix=basis_from_y(a,b))
 for i,x in enumerate([-.94,0,.94]):m.loft('gate_top_snow_%02d'%i,'snow',[(-.023,0),(-.023,.54),(.03,.40),(.06,0)],(x,1.19,0),6,radii=(1,.15))
 for x in [-1.34,1.34]:
  for y in [.155,1.11]:m.loft('gate_frame_bolt','metal',[(-.01,.022),(.016,.02)],(x,y,-.099),4,matrix=rot(x=math.pi/2))
 for p in m.parts:
  if p.material=='wood_light':
   lo=p.vertices.min(0);d=p.vertices.max(0)-lo
   if d[0]>d[1]*2:p.uv=np.column_stack([(p.vertices[:,1]-lo[1])/max(d[1],.001),(p.vertices[:,0]-lo[0])*1.5])
   else:p.uv=np.column_stack([(p.vertices[:,0]-lo[0])/max(d[0],.001),(p.vertices[:,1]-lo[1])*2.3])
   p.colors[:,:3]=1.
 return namespace['fit_visual_envelope'](m,(-1.45,.01,-.07),(1.45,1.21,.10))
def fence_visible_contacts():
 m=namespace['fence_panel']()
 # Extend functional rails to the fixed source envelope, without altering placement.
 for p in m.parts:
  if p.name=='rear_support':
   lo=p.vertices.min(0);hi=p.vertices.max(0)
   p.vertices[:,0]=(p.vertices[:,0]-lo[0])/(hi[0]-lo[0])*2.9409-1.47045
   p.vertices[:,2]=(p.vertices[:,2]-lo[2])/(hi[2]-lo[2])*.035
 # Replace hidden closed rear wraps with two closed crossed front ties per rail.
 m.parts=[p for p in m.parts if not p.name.endswith('_rope_wrap')]
 for p in list(m.parts):
  if p.name.endswith('_carved_timber'):
   x=(p.vertices[:,0].min()+p.vertices[:,0].max())*.5
   for y in [.325,.87]:
    for sign in [-1,1]:
     m.tube(p.name+'_front_cross_tie','cream',[(x-.090,y-sign*.065,.055),(x+.090,y+sign*.065,.055)],.013,3,tint=(.84,.76,.61))
 return namespace['fit_visual_envelope'](m,(-1.47045,0.,-.0806),(1.47045,1.465,.0706))

def joined_model(base_models,inputs):
 rows=inputs["rows"];contacts=inputs["contacts"];pairs={(0,1),(1,2),(4,5)}
 selected=[c for c in contacts if tuple(c["panels"]) in pairs];assert len(selected)==3
 m=Model('diagnostic_panel_joins');proof=[];base=base_models['fence_panel'];allbase=np.concatenate([p.vertices for p in base.parts]);worlds=[]
 for row in rows:
  B=np.array([row['basis_x'],row['basis_y'],row['basis_z']]).T;worlds.append(allbase@B.T+row['origin'])
 worldbounds=np.concatenate(worlds);globalmin=worldbounds.min(0);globalmax=worldbounds.max(0)
 for c in selected:
  ids=c['panels'];first=len(m.parts);point=np.array(c['endpoint_authority_a']);bases=[]
  for index,end in zip(ids,c['ends']):
   row=rows[index];B=np.array([row['basis_x'],row['basis_y'],row['basis_z']]).T;sign=-1 if end=='a' else 1;bases.append(B@np.array([sign*1.47045,0,0])+row['origin'])
  rooty=min(x[1]for x in bases);cap=min(worlds[i][:,1].max()for i in ids);height=min(1.382,cap-rooty-.086)
  temp=Model('joinlog');namespace['picket'](temp,'join_log',0,height=height,radius=.112,depth=.078,seed=ids[0],ropes=False)
  for p in temp.parts:
   p.vertices+=np.array([point[0],rooty,point[1]]);p.name='join_%d_%d_'%tuple(ids)+p.name;m.parts.append(p)
  for k,l in enumerate(c['levels']):
   a=np.array(l['rail_center_a']);z=np.array(l['rail_center_b']);center=(a+z)*.5;length=np.linalg.norm(z-a)+.055
   p=compact(m,'join_%d_%d_rail_%d'%(*ids,k),'wood',(.091,length,.040),center,.008,basis_from_y(a,z))
   # UVs along connector grain, no fallback primitives or new default materials.
   p.uv=np.column_stack([(p.vertices[:,1]-center[1])/.10+.5,(p.vertices[:,0]-center[0])*2.5]);p.colors[:,:3]=1
   for sign in [-1,1]:m.tube('join_%d_%d_tie_%d'%(*ids,k),'cream',[(point[0]-.095,center[1]-sign*.065,point[1]+.062),(point[0]+.095,center[1]+sign*.065,point[1]+.062)],.013,3,tint=(.84,.76,.61))
  verts=np.concatenate([p.vertices for p in m.parts[first:]])
  def distance(v,row):
   a=np.array(row['a']);z=np.array(row['b']);d=z-a;t=np.clip((v-a)@d/(d@d),0,1);return np.linalg.norm(v-(a+t[:,None]*d),axis=1)
  dist=np.minimum(distance(verts[:,[0,2]],rows[ids[0]]),distance(verts[:,[0,2]],rows[ids[1]]));assert dist.max()<=.32
  assert (verts.min(0)>=globalmin-1e-7).all() and (verts.max(0)<=globalmax+1e-7).all()
  proof.append({'pair':ids,'join_anchor':point.tolist(),'root_y':float(rooty),'cap_y':float(cap),'authored_log_height':float(height),'max_distance_to_reserved_line':float(dist.max()),'triangles':sum(len(p.faces)for p in m.parts[first:])})
 errors=[(p.name,namespace['topology_errors'](p.vertices,p.faces))for p in m.parts if namespace['topology_errors'](p.vertices,p.faces)];assert not errors,errors
 return m,proof

def verify_authority(repo, inputs):
 for name,digest in inputs['authority_sha256'].items():
  assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest, 'Join authority changed; regenerate/review inputs: '+name
 view=(repo/'HavenlineGodot/scripts/camp_boundary_view.gd').read_text()
 for name,digest in inputs['view_method_sha256'].items():
  body=re.search(r'^func '+name+r'\(.*?(?=^func |\Z)',view,re.M|re.S)
  assert body and hashlib.sha256(body.group(0).encode()).hexdigest()==digest, 'Panel transform authority changed: '+name

def generate(folder, inputs):
 models={'fence_panel':fence_visible_contacts(),'gate_post':namespace['gate_post'](),'gate_leaf':leaf()}
 joins, contacts=joined_model(models, inputs)
 models['panel_joins']=joins
 rows={}
 folder.mkdir(parents=True,exist_ok=True)
 for name,model in models.items():
  for part in model.parts:
   assert not namespace['topology_errors'](part.vertices,part.faces),(name,part.name)
   assert np.isfinite(part.vertices).all() and np.isfinite(part.normals).all()
  path=folder/(name+'.obj')
  # Object name is preserved from the independently reviewed prototype.
  namespace['export_obj'](model,path)
  rows[name]={'triangles':sum(len(p.faces)for p in model.parts),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'minimum':np.concatenate([p.vertices for p in model.parts]).min(0).tolist(),'maximum':np.concatenate([p.vertices for p in model.parts]).max(0).tolist()}
 for name,digest in inputs['base_asset_sha256'].items():
  assert rows[name]['sha256']==digest,'Base shape changed; regenerate/review joins: '+name
 counts={'fence_panel':16,'gate_leaf':12,'gate_post':12,'panel_joins':1}
 old={'fence_panel':640,'gate_leaf':84,'gate_post':176,'panel_joins':0}
 addition=sum((rows[n]['triangles']-old[n])*counts[n]for n in rows)
 assert [rows[n]['triangles']for n in ['fence_panel','gate_post','gate_leaf','panel_joins']]==[1208,240,476,456]
 assert addition==15016 and 162332+addition<=180000
 return {'assets':rows,'instance_counts':counts,'all_instance_triangle_addition':addition,'conservative_combined_delta':162332+addition,'unchanged_incremental_cap':180000,'remaining_headroom':180000-162332-addition,'join_contacts':contacts,'zero_topology_errors':True,'source':inputs['source'],'task_approved':False,'production_visual_approval':False}

def main():
 ap=argparse.ArgumentParser()
 modes=ap.add_mutually_exclusive_group(required=True)
 modes.add_argument('--write',action='store_true');modes.add_argument('--verify',action='store_true')
 ap.add_argument('--asset-dir',type=Path,default=ASSETS)
 ap.add_argument('--repo-root',type=Path,default=ROOT)
 args=ap.parse_args();assets=args.asset_dir.resolve()
 inputs=json.loads((assets/'panel_join_authoring.json').read_text())
 verify_authority(args.repo_root.resolve(),inputs)
 with tempfile.TemporaryDirectory()as temp:
  folder=Path(temp);report=generate(folder,inputs)
  for name,row in report['assets'].items():
   destination=assets/(name+'.obj')
   if args.write:destination.write_bytes((folder/(name+'.obj')).read_bytes())
   else:assert destination.read_bytes()==(folder/(name+'.obj')).read_bytes(),f'Unmaterialized boundary asset: {name}'
  manifest_path=assets/'manifest.json'
  manifest=json.loads(manifest_path.read_text())
  if args.write:
   manifest['revision']=18;manifest['kit']='Havenline reference timber/rope boundary R17'
   manifest['prior_art_assets']=manifest['assets']
   by_name={r['name']:r for r in manifest['assets']}
   features={'fence_panel':['rounded carved logs with reference UV wood grain','paired rails and visible crossed front rope ties','closed pointed snow crowns','unchanged base envelope and placement transforms'], 'gate_post':['rounded carved timber with rope bindings','closed snow crown','unchanged threshold placement and scale'],'gate_leaf':['ten layered timber planks and diagonal bracing','snow on upper rail','unchanged hinges, openings and placement'], 'panel_joins':['three rounded visual joining logs and snow','six closed rail connectors touching adjoining rails','twelve front tie segments','inside existing fence world bounds and reserved collision footprint']}
   manifest['assets']=[dict(by_name.get(n,{'name':n,'path':'HavenlineGodot/assets/t03_boundary_v2/'+n+'.obj'}),triangles=row['triangles'],sha256=row['sha256'],features=features[n])for n,row in report['assets'].items()]
   manifest['reference_target']=['Fence_a4860b7_4K.png','Gate_a4860b7.png']
   manifest['reference_art_revision']=report
   manifest['candidate_for_user_review']=True;manifest['production_visual_approval']=False
   manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
  else:
   for n,row in report['assets'].items():
    actual=next(a for a in manifest['assets']if a['name']==n)
    assert actual['sha256']==row['sha256'] and actual['triangles']==row['triangles']
  print(json.dumps(dict(report,passed=True),indent=2))

if __name__=='__main__':main()
