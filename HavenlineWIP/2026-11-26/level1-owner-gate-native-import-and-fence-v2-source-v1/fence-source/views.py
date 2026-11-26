"""No screenshots or game/renderer; actual serialized mesh depth projection."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
p=Path(sys.argv[1])
source=p.read_text().splitlines()
vertices=np.array([[float(x) for x in l.split()[1:4]] for l in source if l.startswith('v ')])
fs=[]; m=[]; key=''
for l in source:
    if l.startswith('usemtl '):key=l.split()[1]
    if l.startswith('f '):
        fs.append([int(x.split('/')[0])-1 for x in l.split()[1:]])
        m.append(key)
tri=vertices[np.array(fs)]
labels=['amber_logs','soft_snow','front_rounded_rails','ivory_hemp_warm','ivory_hemp_cream']
L=np.array([labels.index(x) for x in m])
limbs=np.full(len(L),-1,dtype=np.int16)
for signed,lab in enumerate((3,4)):
    f=np.flatnonzero(L==lab)
    assert len(f)==4320
    for k in range(2):
        Q=f[k*2160:k*2160+960]
        x=tri[Q,:,0].mean(1)
        b=np.clip(np.floor((x+1.47045)/(2.9409/8)).astype(int),0,7)
        limbs[Q]=signed*16+k*8+b
world_upgrade=[1.956/2.9409,1,1.95]
def inspect(T,c,ppu,ns=2):
    c=np.asarray(c,dtype=float); c/=np.linalg.norm(c)
    X=np.cross([0.,1.,0.],c);X/=np.linalg.norm(X);Y=np.cross(c,X)
    P=T@np.stack((X,-Y,c),axis=1)
    P[:,:,:2]*=ppu;lo=P[:,:,:2].min((0,1));hi=P[:,:,:2].max((0,1))
    ysize,xsize=np.ceil((hi-lo)[::-1]*ns).astype(int)+4
    depth=np.full((ysize,xsize),-np.inf); own=np.full(depth.shape,-1,dtype=np.int8); limb=np.full(depth.shape,-1,dtype=np.int8)
    for t,tag,ll in zip(P,L,limbs):
        q=(t[:,:2]-lo)*ns+1
        a=np.floor(q.min(0)).astype(int);b=np.ceil(q.max(0)).astype(int)
        x,y=np.meshgrid(np.arange(a[0],b[0]+1)+.5,np.arange(a[1],b[1]+1)+.5)
        u,v=q[1]-q[0],q[2]-q[0];D=u[0]*v[1]-u[1]*v[0]
        if abs(D)<1e-11:continue
        x-=q[0,0];y-=q[0,1]
        A=(x*v[1]-y*v[0])/D;B=(u[0]*y-u[1]*x)/D
        z=t[0,2]+A*(t[1,2]-t[0,2])+B*(t[2,2]-t[0,2])
        D=depth[a[1]:b[1]+1,a[0]:b[0]+1];O=own[a[1]:b[1]+1,a[0]:b[0]+1]
        take=(A>=0)&(B>=0)&(A+B<=1)&(z>D)
        D[take]=z[take];O[take]=tag;limb[a[1]:b[1]+1,a[0]:b[0]+1][take]=ll
    marks=[]
    for i in range(16):
        a,b=[np.argwhere(limb==q) for q in (i,i+16)]
        def columns(z):return {int(x): z[z[:,1]==x,0] for x in np.unique(z[:,1])}
        aa,bb=map(columns,(a,b))
        pair=sorted(set(aa)&set(bb))
        yy=np.array([float(np.median(aa[x])-np.median(bb[x]))/ns for x in pair])
        marks.append({'level':i//8,'log':i%8,'visible_area_each_px':[len(a)/ns**2,len(b)/ns**2],
         'projected_cream_above_gold_columns_px':float((yy>=1.0).sum()/ns),
         'projected_gold_above_cream_columns_px':float((yy<=-1.0).sum()/ns),
         'both_visible_with_reciprocal_vertical_order':bool((yy>=1).any() and (yy<=-1).any())})
    return {'projected_size_px_at_listed_scale':(hi-lo).tolist(),
            'material_visible_area_px2_equivalent':{k:float((own==i).sum()/ns**2) for i,k in enumerate(labels)},
            'visible_front_limb_order':marks,'front_reciprocal_motif_count':sum(r['both_visible_with_reciprocal_vertical_order'] for r in marks)}
T=tri*np.array(world_upgrade)
side={'front_0_exterior_plus_Z':[0,0,1],'right_90_plus_X':[1,0,0],
      'rear_180_interior_minus_Z':[0,0,-1],'left_270_minus_X':[-1,0,0]}
# Axis scale equivalent to the regular southwest outer mounted panel;
# 55.3846px/m is the actual saved 720/13 normal-view vertical scale.
out={key:inspect(T,value,720/13) for key,value in side.items()}
assert out['front_0_exterior_plus_Z']['material_visible_area_px2_equivalent']['front_rounded_rails'] > 6*out['rear_180_interior_minus_Z']['material_visible_area_px2_equivalent']['front_rounded_rails']
assert all(out[k]['material_visible_area_px2_equivalent']['front_rounded_rails']>1 for k in ('right_90_plus_X','left_270_minus_X'))
out['stock_southwest_paid_camera_direction_7_11_11']=inspect(T,[7,11,11],720/13)
# Map coordinate conventions onto existing wall run axes. Rotation does not
# change gameplay shape. Exact logical shift (-3.25,+5.80) inherited; no asset
# insertion or launch performed.
mounts={
'South runs 0/1 exterior +Z':{'yaw_deg':0,'x_axis_pts':'world +X','front_axis':'world +Z','logical_row_z':4},
'East runs 2/3 exterior +X':{'yaw_deg':90,'x_axis_pts':'world -Z','front_axis':'world +X','logical_row_x':5},
'North run 4 exterior -Z':{'yaw_deg':180,'x_axis_pts':'world -X','front_axis':'world -Z','logical_row_z':-4},
'West run 5 exterior -X':{'yaw_deg':-90,'x_axis_pts':'world +Z','front_axis':'world -X','logical_row_x':-5}}
build=json.loads((p.parent.parent/'build-result.json').read_text())
lo,hi=map(np.array,build['geometry_min_max'])
dims=hi-lo
recenter=.00975
old=.14742
bound=[float(lo[2]*1.95+recenter),float(hi[2]*1.95+recenter)]
assert bound[0]>=-old and bound[1]<=old
slack=(old-bound[1],old+bound[0])
per={'positive_depth_remaining_mm':slack[0]*1000,'negative_depth_remaining_mm':slack[1]*1000,
     'profile_depth_m':dims[2]*1.95,'wall_collision_depth_m':.30,
     'old_protected_visual_depth_m':2*old,
     'nominal_log_gap_range_mm_unscaled':[(v*1000) for v in (
         np.min([min(vertices[np.array(fs)][168*(i+1):168*(i+2),:,0].ravel())-max(vertices[np.array(fs)][168*i:168*(i+1),:,0].ravel()) for i in range(7)]),
         np.max([min(vertices[np.array(fs)][168*(i+1):168*(i+2),:,0].ravel())-max(vertices[np.array(fs)][168*i:168*(i+1),:,0].ravel()) for i in range(7)]))]}
print(json.dumps({'asset_sha':hashlib.sha256(p.read_bytes()).hexdigest(),'analytic_orthographic_material_visibility_not_frame':out,
  'coordinates_4_sides':mounts,'bounds_budget':per,'no_stock_wall_or_gate_source_changes':True},indent=2))
