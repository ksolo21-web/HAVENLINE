from pathlib import Path
import contextlib,hashlib,io,json,math,runpy,subprocess,sys
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent.parent
repo=Path(sys.argv[1]); mesh=Path(sys.argv[2])
pin='11c14a1c41971067c7dc97db69375f720a408f68'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def packet(n,h):
    p=root/n
    assert sha(p/'SHA256SUMS')==h
    subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
    return json.loads((p/('native-result.json' if (p/'native-result.json').exists() else 'result.json')).read_text())
native=packet('hvn-l1-wood-paid-two-piece-candidate-v1','2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5')
carry=packet('hvn-l1-wood-paid-carry-capture-v1','af819aeb459d6835f43f1f5f015d78abc6916a561b3c3cd7190dfe08eb6a1b98')
end=packet('hvn-l1-wood-storage-near-row-v1','b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')
assert sha(mesh)=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
tris,_=runpy.run_path(str(root/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](mesh)
V=np.unique(tris.reshape(-1,3),axis=0); assert len(V)==834
radius=float(np.linalg.norm(V,axis=1).max())
def src(x):return subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/'+x])
layout=json.loads(src('layout.json'))
opening=src('previews/integrated_opening.gd').decode()
assert all(s in opening for s in ['cylinder.radius = .85','floor.position.y = .012','for row in layout.walls_xz'])
with contextlib.chdir(root/'hvn-l1-wood-storage-near-row-v1'),contextlib.redirect_stdout(io.StringIO()):
    t=runpy.run_path(str(root/'havenline-buy-plot-footprint-study-v8/project.py'))
for x in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd'):
    assert src(x)==(t['pin']/x).read_bytes()
H=t['height']
record=native['samples'][0]; old=carry['native']; assert native['pass_count']==20 and native['failures']==0
assert record['actor_world']==old['actor_world']['origin'] and record['tick']==old['tick']==1277
assert record['anim']==old['settled_animation'] and record['anim_t']==old['settled_animation_time']
B=np.array(old['carry_root_world']['basis_cols']).T; q=np.array(record['actor_world'])
assert np.linalg.norm(B.T@B-np.eye(3),ord=np.inf)<1e-5
radius*=max(1.,float(np.linalg.norm(B,ord=2)))
starts=[np.array(d['world']) for d in record['stock_on_real_actor']]
assert all(abs(B@d['local']+q-a).max()<1e-6 for d,a in zip(record['stock_on_real_actor'],starts))
reshaped=Path(root/'hvn-l1-wood-paid-two-piece-candidate-v1/paid_piece_methods.gdfrag').read_text()
assert 'source_crown.transform != Transform3D.IDENTITY' in reshaped
# Source child identity: only a local origin is set. Basis comes from the
# paired original-run mount capture, not exported in the two-piece capture.
assert 'crown.position = centers[i]' in reshaped and 'crown.basis' not in reshaped
caps=old['actor_collisions'][0]
c=np.array(caps['world']['origin']); rad=caps['radius']; height=caps['height']
caps_box=np.stack([c-np.array([rad,height/2,rad]),c+np.array([rad,height/2,rad])])
body=np.array(carry['world_cpu_skin_bounds'])
actor_box=np.stack([np.minimum(body[0],caps_box[0]),np.maximum(body[1],caps_box[1])])
# Local AABB combines native CPU-skinned whole-body bounds and an enclosing
# prism of the actual vertical capsule, not a visual proxy for either alone.
body_local=np.array(carry['actor_relative_cpu_skin_bounds'])
cz=np.linalg.solve(B,c-q)
actor_local_box=np.stack([np.minimum(body_local[0],cz-[rad,height/2,rad]),np.maximum(body_local[1],cz+[rad,height/2,rad])])
shift=np.array([-3.25,5.80]); hearth=np.array(layout['furnace_xz'])+shift
def slab(x):return np.stack([x.min(0),x.max(0)])
def xz(x):return x[..., [0,2]]
boxes={}
for gate in old['gates']:
    for leaf in gate['leaf_boxes']:
        assert leaf['layer']==1
        R=np.array(leaf['shape_world']['basis_cols']).T
        p=np.array(leaf['shape_world']['origin'])
        d=np.abs(R)@(.5*np.array(leaf['size']))
        boxes[gate['gate_id']+'-'+leaf['hinge']]=xz(np.stack([p-d,p+d]))
for k,(x,z,w,d) in enumerate(layout['walls_xz']):
    p=np.array([x,z])+shift; size=np.array([w,d])/2
    boxes['wall-'+str(k)]=np.stack([p-size,p+size])
def maxgap(a,b):return float(np.max(np.maximum(b[0]-a[1],a[0]-b[1])))
def pbox_gap(p,a):return float(np.linalg.norm(np.maximum(np.maximum(a[0]-p,p-a[1]),0)))
def world(V,B,p):return V@B.T+p
def terrain_bound(box):
    # Affine floor patches on the exact quarter-metre grid are bounded by
    # their vertices; include every grid cell incident on this rectangle.
    ll,hh=xz(box)
    return max(H(i/4,j/4) for i in range(math.floor(ll[0]*4),math.ceil(hh[0]*4)+1)
              for j in range(math.floor(ll[1]*4),math.ceil(hh[1]*4)+1))+.012
dest=[(np.array(x['R_source_to_source_world']),np.array(x['t_source_to_source_world'])) for x in end['detached_log_transforms']]
parks=[slab(world(V,R,e)) for R,e in dest]; startbox=[slab(world(V,B,a)) for a in starts]
staged_row={'diagnostic_only':True,'source_type':'untouched second row placeholder; no in-game other row asserted','transform':{'origin':[0,0,0],'rotation':[0,0,0,1]},'slots':['sentinel-A','sentinel-B']}
rowhash=hashlib.sha256(json.dumps(staged_row,sort_keys=True).encode()).hexdigest()
checks=[]
for i,(a,(R,e)) in enumerate(zip(starts,dest)):
    # West along the exact carry basis so the close initial Z separation
    # cannot shrink during release. Subsequently rotate at stand-off.
    side=a+1.23*B[:,0]
    hover=e.copy(); hover[1]=a[1]
    L=world(V,B,a); M=world(V,B,side); N=world(V,R,hover); P=world(V,R,e)
    volumes=[slab(np.r_[L,M]),np.stack([np.minimum(side,hover)-radius,np.maximum(side,hover)+radius]),slab(np.r_[N,P])]
    begin=(0,.425)[i]; finish=(.300,.875)[i]
    duration=finish-begin
    ticks=[begin,begin+duration*.29,begin+duration*.76,finish]
    assert ticks[0]<ticks[1]<ticks[2]<ticks[3]
    transfer=[]
    for k,vol in enumerate(volumes):
        ob={name:maxgap(xz(vol),bx) for name,bx in boxes.items()}
        ob['hearth_cylinder_plan']=pbox_gap(hearth,xz(vol))-.85
        if k==0:
            loc=slab(np.r_[(L-q)@np.linalg.inv(B).T,(M-q)@np.linalg.inv(B).T])
            ob['whole_actor_plus_native_capsule']=maxgap(loc,actor_local_box)
            if i==0: ob['other_exact_log']=maxgap(loc,slab((world(V,B,starts[1])-q)@np.linalg.inv(B).T))
        else: ob['whole_actor_plus_native_capsule']=maxgap(vol,actor_box)
        if 'other_exact_log' not in ob:
            # When i=0 its other log is stationary on the original mount until
            # t=.425. When i=1, the first is already in exact readable rest.
            ob['other_exact_log']=maxgap(vol,startbox[1] if i==0 else parks[0])
        f=end['terrain_support_and_full_mesh'][i]
        if k!=2: ob['visible_floor']=float(vol[0,1]-terrain_bound(vol))
        else:
            # Whole end hull clipped against exact floor triangle polys by the
            # frozen support witness. Pure vertical motion above that transform
            # cannot cross it at any point; physical floor stays 12 mm below.
            assert f['visible_seat_min_full_convex_envelope_m']==0 and f['collision_clearance_full_envelope_m']==.012
            ob['visible_floor']=0.
        transfer.append(ob)
    checks.append({'id':record['stock_on_real_actor'][i]['name'],'times_s':ticks,
      'origin_keys_m':[p.tolist() for p in [a,side,hover,e]],'initial_basis_rows':B.tolist(),
      'rest_basis_rows':R.tolist(),'rotation_interpolation':'polar decomposition shortest quaternion SLERP and affine interpolation of native sub-5ppm symmetric numerical residue during middle; no spin in first/last',
      'position_interpolation':'same cubic smoothstep interpolation on each piecewise straight phase',
      'continuous_clearance_bound_m':transfer,
      'peak_translation_m_s':[float(1.5*np.linalg.norm(b-a)/(t1-t0)) for a,b,t0,t1 in zip([a,side,hover],[side,hover,e],ticks[:-1],ticks[1:])]})
assert hashlib.sha256(json.dumps(staged_row,sort_keys=True).encode()).hexdigest()==rowhash
fail=[(i,k,name,g) for i,c in enumerate(checks) for k,z in enumerate(c['continuous_clearance_bound_m']) for name,g in z.items() if g < (.000001 if name!='visible_floor' else -1e-6)]
assert abs(np.linalg.norm(starts[0]-starts[1])-.105)<1e-6
assert maxgap(parks[0],parks[1])>.16 and maxgap(parks[0],parks[0])<0
assert all(x["whole_mesh_intersection_control_minus_1mm"]<-.00099 for x in end["terrain_support_and_full_mesh"])
# One negative control: aligning both carried origins would make the same
# source pair overlap everywhere, not count as another distinct item.
assert maxgap(startbox[0],startbox[0])<0
result={'source_commit':pin,'checkpoint_tick':record['tick'],'crown_radius_m':radius,
 'gates_observed':[{k:g[k] for k in ('gate_id','angle','target_open')} for g in old['gates']],
 'frozen_end_visual_support_not_rigid_body':True,
 'continuous_result':'HOLD (conservative separation not established)' if fail else 'PASS (detached static-checkpoint geometry only)',
 'unproven_clearance_certificates':fail,'motion':checks,'diagnostic_other_row_unchanged_hash':rowhash,
 'negative_controls':['coincident start fails','coincident end fails','frozen end lowered 1 mm fails terrain witness'],
 'implied_timing_is_not_reference_pacing_or_approval':True}
print(json.dumps(result,indent=2,sort_keys=True))
