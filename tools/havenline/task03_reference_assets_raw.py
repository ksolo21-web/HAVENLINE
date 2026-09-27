#!/usr/bin/env python3
"""Exact-source T03 art authoring; preserves all 11H gameplay transforms.

The frozen mesh helper is copied by value to this task-owned tool. Only Model,
rotation and TAU are used; no T05 asset or generator is imported or changed.
"""
from __future__ import annotations
import argparse,base64,copy,hashlib,json,math,re,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
from task03_mesh_authoring import Model,rotation,TAU
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'HavenlineGodot/assets/t03_boundary_v2'
BASE='e1e7bb2d68d1d53025d1242011ad4c885f08c307'
INTEGRATION_BASE='99c51e556c160f4b74d63e94d319165969328c2f'


def fit_visual_envelope(model,minimum,maximum):
    v=np.concatenate([p.vertices for p in model.parts]);lo=v.min(0);hi=v.max(0)
    minimum=np.asarray(minimum);maximum=np.asarray(maximum);scale=(maximum-minimum)/(hi-lo)
    for part in model.parts:
        part.vertices=(part.vertices-lo)*scale+minimum
        part.normals=part.normals/scale
        part.normals/=np.linalg.norm(part.normals,axis=1,keepdims=True)
    return model


def picket(m,name,x,height=1.40,radius=.108,depth=None,seed=0,ropes=True):
    if depth is None:depth=radius
    seg=12;rows=6;v=[];f=[];ys=np.linspace(0,height-.36,rows)
    for y in ys:
        for i in range(seg):
            a=TAU*i/seg;ripple=1+.030*math.cos(a*7+seed*.3)+.018*math.sin(a*3+y*3+seed)
            v.append([x+radius*math.cos(a)*ripple,y,depth*math.sin(a)*ripple])
    for j in range(rows-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=b+seg;d=a+seg;f.extend([[a,b,c],[a,c,d]])
    bottom=len(v);v.append([x,0,0]);tip=len(v);v.append([x,height+.035,0])
    for i in range(seg):
        j=(i+1)%seg;f.extend([[bottom,j,i],[(rows-1)*seg+i,(rows-1)*seg+j,tip]])
    p=m.add(name+'_carved_timber','wood_light',v,f,tint=(1.,.90,.78),smooth=True)
    vv=p.vertices;angles=np.arctan2(vv[:,2]/depth,(vv[:,0]-x)/radius)
    p.colors[:,:3]=1.0
    p.uv=np.column_stack([(angles+math.pi)/math.pi,vv[:,1]/height*2.5+seed*.173])
    rings=[(0.,1.12),(.08,1.05),(.18,.80),(.29,.45),(.38,.12)]
    v=[];f=[];snow_base=height-.32
    for j,(yy,rr) in enumerate(rings):
        for i in range(seg):
            a=TAU*i/seg;scallop=.036*math.sin(5*a+seed*.47)+.018*math.sin(8*a+1.2);y=snow_base+yy
            if j==0:y+=scallop
            elif j==1:y+=scallop*.35
            v.append([x+radius*rr*1.09*math.cos(a),y,depth*rr*1.09*math.sin(a)])
    for j in range(len(rings)-1):
        for i in range(seg):
            a=j*seg+i;b=j*seg+(i+1)%seg;c=b+seg;d=a+seg;f.extend([[a,b,c],[a,c,d]])
    btm=len(v);v.append([x,snow_base-.01,0]);top=len(v);v.append([x,snow_base+.403,0])
    for i in range(seg):
        j=(i+1)%seg;f.extend([[btm,j,i],[(len(rings)-1)*seg+i,(len(rings)-1)*seg+j,top]])
    m.add(name+'_snow_crown','snow',v,f)
    if ropes:
        for y in [.34,.90]:
            for wrap in range(2):
                t=np.linspace(0,TAU,13)
                path=[(x+(radius+.019+wrap*.006)*math.cos(a),y+(-1 if wrap else 1)*.050*math.cos(a),(depth+.019+wrap*.006)*math.sin(a)) for a in t]
                m.tube(name+'_rope_wrap','cream',path,.018,4,tint=(.84,.76,.61))


def fence_panel():
    m=Model('fence_panel');span=2.9409;radius=.118;pitch=(span-radius*2)/11
    for i in range(12):
        x=-span/2+radius+i*pitch
        picket(m,'picket_%02d'%i,x,height=1.382+.027*math.sin(i*2.1),radius=radius,depth=.080,seed=i,ropes=True)
    for y in [.33,.88]:m.bevel_box('rear_support','wood',(span-.035,.09,.08),(0,y,.073),.018)
    return fit_visual_envelope(m,(-1.47045,0.,-.0806),(1.47045,1.465,.0706))


def gate_post():
    m=Model('gate_post');picket(m,'threshold_post',0,height=1.535,radius=.150,depth=.150,seed=4,ropes=True)
    return fit_visual_envelope(m,(-.168,0.,-.1724),(.168,1.605,.168))


def gate_leaf():
    m=Model('gate_leaf');length=2.9
    for i in range(10):
        x=-1.35+(i+.5)*2.7/10
        m.bevel_box('gate_board_%02d'%i,'wood_light',(.264,1.01,.068),(x,.63,0),.018,tint=(1.,.84+.04*math.sin(i),.67),variation=.055)
    for x in [-1.365,1.365]:m.bevel_box('gate_stile','wood_light',(.17,1.12,.11),(x,.61,-.012),.022,tint=(1.,.92,.81))
    for y in [.15,1.115]:m.bevel_box('gate_crossrail','wood_light',(length,.15,.13),(0,y,-.022),.024,tint=(1.,.92,.81),variation=.04)
    m.beam('gate_diagonal','wood_light',(-1.27,.25,-.061),(1.26,1.00,-.061),.12,.067,.016,tint=(1.,.94,.86))
    for i in range(9):
        x=-1.285+i*.321
        m.snow('gate_top_snow_%02d'%i,(x,1.203,0),(.188,.055,.083),i,14,5)
    for x in [-1.34,1.34]:
        for y in [.155,1.11]:m.loft('gate_frame_bolt','metal',[(-.010,.022),(.007,.026),(.016,.020)],(x,y,-.099),8,matrix=rotation(x=math.pi/2),tint=(.8,.83,.85))
    for part in m.parts:
        if part.material=='wood_light':
            lo=part.vertices.min(0);hi=part.vertices.max(0);d=hi-lo
            if d[0]>d[1]*2:
                part.uv=np.column_stack([(part.vertices[:,1]-lo[1])/max(d[1],.001),(part.vertices[:,0]-lo[0])*1.5])
            else:part.uv=np.column_stack([(part.vertices[:,0]-lo[0])/max(d[0],.001),(part.vertices[:,1]-lo[1])*2.3])
            part.colors[:,:3]=1.0
    return fit_visual_envelope(m,(-1.45,.01,-.07),(1.45,1.21,.10))


def export_obj(model,path):
    mapping={'wood':'timber_dark','wood_light':'timber','snow':'snow','cream':'rope','metal':'blue'}
    lines=['# HAVENLINE supplied-reference T03 sculpted visual candidate','mtllib boundary_v2.mtl','o '+model.name,'s 1'];base=1
    for p in model.parts:
        lines.append('usemtl '+mapping[p.material])
        for v,c in zip(p.vertices,p.colors):lines.append('v '+' '.join(f'{x:.8g}' for x in [*v,*c[:3]]))
        for uv in getattr(p,'uv',np.zeros((len(p.vertices),2))):lines.append('vt '+' '.join(f'{x:.8g}' for x in uv))
        for n in p.normals:lines.append('vn '+' '.join(f'{x:.8g}' for x in n))
        for f in p.faces:lines.append('f '+' '.join(f'{base+int(i)}/{base+int(i)}/{base+int(i)}' for i in f))
        base+=len(p.vertices)
    Path(path).write_text('\n'.join(lines)+'\n')


def topology_errors(v,f):
    v,inv=np.unique(np.round(v,8),axis=0,return_inverse=True);f=inv[f]
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ordered=np.sort(edges,axis=1)
    _,ix,count=np.unique(ordered,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));errors=[]
    if not np.all(count==2):errors.append('open/nonmanifold')
    if not np.all(balance==0):errors.append('inconsistent winding')
    p=v[f];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    if (np.linalg.norm(cross,axis=1)<1e-12).any():errors.append('degenerate')
    if np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6<=1e-12:errors.append('inward/zero volume')
    return errors


def model_checks(models):
    expected={'fence_panel':(74,7992,[-1.47045,0,-.0806],[1.47045,1.465,.0706]),
              'gate_post':(6,648,[-.168,0,-.1724],[.168,1.605,.168]),
              'gate_leaf':(28,2820,[-1.45,.01,-.07],[1.45,1.21,.10])}
    for name,m in models.items():
        count,tris,lo,hi=expected[name];v=np.concatenate([p.vertices for p in m.parts])
        assert len(m.parts)==count and sum(len(p.faces) for p in m.parts)==tris
        assert np.allclose(v.min(0),lo,atol=1e-8) and np.allclose(v.max(0),hi,atol=1e-8)
        for p in m.parts:
            assert np.isfinite(p.vertices).all() and np.isfinite(p.normals).all()
            assert not topology_errors(p.vertices,p.faces),(name,p.name,topology_errors(p.vertices,p.faces))
            assert np.allclose(np.linalg.norm(p.normals,axis=1),1,atol=1e-6)
            if hasattr(p,'uv'):assert np.isfinite(p.uv).all()
    probe=Model('negative');p=probe.bevel_box('cube','metal',(1,1,1))
    assert not topology_errors(p.vertices,p.faces)
    assert topology_errors(p.vertices,p.faces[:-1])
    assert topology_errors(p.vertices,p.faces[:,[0,2,1]])
    mixed=p.faces.copy();mixed[0]=mixed[0,::-1];assert topology_errors(p.vertices,mixed)


def git_bytes(ref,path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)


def authority_checks():
    paths=['HavenlineGodot/scripts/camp_boundary.gd','HavenlineGodot/scripts/river_geometry.gd',
           'HavenlineGodot/scripts/reference_forest.gd','HavenlineGodot/scripts/outpost_surface.gd',
           'HavenlineGodot/shaders/outpost_snow.gdshader','HavenlineGodot/scripts/camera_composition.gd',
           'HavenlineGodot/scripts/main.gd','HavenlineGodot/data/reference-contract.json',
           'HavenlineGodot/tests/test_task03_boundary.gd']
    for path in paths:assert (ROOT/path).read_bytes()==git_bytes(INTEGRATION_BASE,path),path
    path='HavenlineGodot/scripts/camp_boundary_view.gd'
    old=git_bytes(BASE,path).decode();new=(ROOT/path).read_text()
    def neutral(text):
        text=re.sub(r'^const WOOD_REFERENCE_ALBEDO=.*\n','',text,flags=re.M)
        start=text.index('func _material(');end=text.index('func _segment_transform(')
        return text[:start]+text[end:]
    assert neutral(old)==neutral(new),'11H layout/hinge/authority transform drift'
    assert 'WOOD_REFERENCE_ALBEDO.create_texture()' in new
    assert '"rope"' in new
    shader=(OUT/'t03_boundary_v2.gdshader').read_text()
    assert 'cull_disabled' not in shader and 'use_reference_grain' in shader
    assert 'newmtl rope' in (OUT/'boundary_v2.mtl').read_text()
    texture=(OUT/'wood_reference_albedo.gd').read_text()
    encoded=re.search(r'const PNG_BASE64 := """(.*?)"""',texture,re.S).group(1)
    png=base64.b64decode(''.join(encoded.split()),validate=True)
    assert hashlib.sha256(png).hexdigest()=='f85c0beb09a5110da4281e765abf659403e9234d7307898416a8363f2989c437'
    assert png[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',png[16:24])==(48,96)
    return paths


def manifest_for(models,hashes):
    baseline=json.loads(git_bytes(BASE,'HavenlineGodot/assets/t03_boundary_v2/manifest.json'))
    m=copy.deepcopy(baseline)
    m['revision']=17;m['kit']='Havenline supplied-reference palisade art v17'
    m['production_visual_approval']=False;m['candidate_for_user_review']=True
    features={'fence_panel':['twelve carved timber pickets','crossed rope wraps','closed scalloped snow crowns','same exact source envelope and unchanged 11H layout transforms'],
              'gate_post':['matching carved timber','two rope bindings','closed snow crown','unchanged threshold scaling and terrain seating'],
              'gate_leaf':['ten solid planks','single diagonal brace per leaf mirrored by existing placement','snow lip on the top rail','unchanged hinge, opening and source-length authority']}
    m['prior_art_assets']=baseline['assets']
    for row in m['assets']:
        name=row['name'];row['triangles']=models[name].metrics()['triangles'];row['sha256']=hashes[name]
        row['features']=features[name]
    m['reference_art_revision']={
        'reference_images':['18590.png','18595.png','18596.png','18598.png'],
        'reference_role':'Visual construction/material language, not literal dimensions or new gameplay requirements.',
        'wood_albedo_source_sha256':'bc95d8be5769951c7b75073952662d17d3a40e80017a14fdee2a6fe6ec8a79fc',
        'wood_albedo_crop':[416,780,530,895],'wood_albedo_size':[48,96],
        'wood_albedo_sha256':'f85c0beb09a5110da4281e765abf659403e9234d7307898416a8363f2989c437',
        'authoritative_geometry_source':BASE,'closed_component_counts':{n:len(x.parts) for n,x in models.items()},
        'geometry_transforms_preserved':True,'task_approved':False,'visual_approved':False}
    return m


def main():
    ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true');mode.add_argument('--verify',action='store_true');mode.add_argument('--model-only',action='store_true')
    args=ap.parse_args();models={f.__name__:f() for f in [fence_panel,gate_post,gate_leaf]};model_checks(models)
    if args.model_only:
        print(json.dumps({'local_model_checks':True,'models':{n:m.metrics() for n,m in models.items()},'source_authority_verified':False,'visual_approved':False},indent=2));return
    protected=authority_checks();hashes={};payloads={}
    with tempfile.TemporaryDirectory() as tmp:
        for name,model in models.items():
            path=Path(tmp)/(name+'.obj');export_obj(model,path);first=path.read_bytes();export_obj(model,path)
            assert first==path.read_bytes(),name
            payloads[path.name]=first;hashes[name]=hashlib.sha256(first).hexdigest()
            lines=first.decode().splitlines();assert sum(x.startswith('f ') for x in lines)==model.metrics()['triangles']
        payloads['manifest.json']=(json.dumps(manifest_for(models,hashes),indent=2)+'\n').encode()
    for name,raw in payloads.items():
        if args.write:(OUT/name).write_bytes(raw)
        else:assert (OUT/name).read_bytes()==raw,'Generated bytes missing or changed: '+name
    print(json.dumps({'passed':True,'mode':'write' if args.write else 'verify','protected_files':protected,
                      '11h_transforms_preserved':True,'model_count':3,'closed_outward_components':108,
                      'negative_controls':3,'triangles':{n:m.metrics()['triangles'] for n,m in models.items()},
                      'sha256':hashes,'task_approved':False,'visual_approved':False,'independent_critic':False},indent=2))


if __name__=='__main__':main()
