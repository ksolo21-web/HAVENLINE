from source import *
D=Path('../hvn-c1-owner-left-joined-chart-preflight-v1')
assert digest(D/'SHA256SUMS')=='c721aaf2aa324a4d6c1161ee561ed5875c01763e4a2c26c3113d135221e69eda'
assert {t.split()[1]:t.split()[0] for t in (D/'SHA256SUMS').read_text().splitlines()}['result.json']==digest(D/'result.json')
R=json.loads((D/'result.json').read_text())
E=s['L_loop_source_vertex_edges']; u=s['L_loop_source_edge_t']; trace=(1-u[:,None])*P[E[:,0]]+u[:,None]*P[E[:,1]]
o=trace.mean(0); n=np.linalg.svd(trace-o)[2][-1];n*=np.sign((P[J['sides']['L']['palm_vertex']]-o)@n)
def test(edge,inc,fraction,az,el):
 a,b=V[list(edge)]; q=a+(b-a)*fraction
 theta,phi=np.deg2rad([az,el]); v=np.array([np.cos(phi)*np.cos(theta),np.cos(phi)*np.sin(theta),np.sin(phi)])
 side=np.cross([0.,0.,1.],v); side/=np.linalg.norm(side); ab=np.stack([side,np.cross(v,side)],axis=1)
 tri=V[F]; Q=q@ab
 # Orthogonally projected full source skin, with the two analytic edge incidences removed.
 xy=tri@ab; boxes=((xy.min(1)-2e-8<=Q).all(1)&(xy.max(1)+2e-8>=Q).all(1))
 rest=np.flatnonzero(boxes&~np.isin(np.arange(len(F)),inc))
 covered=[]; guard=[]
 for i in rest:
  z=xy[i]; A=(z[1:]-z[0]).T
  if abs(np.linalg.det(A))>1e-18:
   g=np.linalg.solve(A,Q-z[0])
   if min(*g,1-g.sum())>=-1e-11:covered.append(int(i))
  for p0,p1 in zip(z,np.roll(z,-1,axis=0)):
   seg=p1-p0
   t=np.clip((Q-p0)@seg/max(seg@seg,1e-30),0,1)
   if np.linalg.norm(Q-p0-t*seg)<2e-8:guard.append(int(i));break
 thirds=[next(x for x in V[F[i]] if not (np.array_equal(x,a) or np.array_equal(x,b))) for i in inc]
 vals=np.cross(b-a,np.array(thirds)-a)@v
 # Tool witness checked against finite triangles, independent of the body projection.
 x=tool[:,1]-tool[:,0]; y=tool[:,2]-tool[:,0]; A=tool[:,0]; nd=np.cross(x,y)
 raylens=[]
 nearest=(np.inf,None)
 for i,f in enumerate(tool):
  N=nd[i]/np.linalg.norm(nd[i]); p=q-((q-f[0])@N)*N
  M=np.array([x[i],y[i]]).T; u=np.linalg.lstsq(M,p-f[0],rcond=None)[0]
  if min(*u,1-u.sum())>=0: nearest=min(nearest,(np.linalg.norm(q-p),i))
  for k,l in zip(f,np.roll(f,-1,axis=0)):
   h=l-k;t=np.clip((q-k)@h/(h@h),0,1)
   nearest=min(nearest,(np.linalg.norm(q-k-t*h),i))
 for direction in [(1.,.573,.317),(-.271,.811,1.),(.413,-1.,.642)]:
  direction=np.array(direction); count=0
  for i,f in enumerate(tool):
   den=nd[i]@direction
   if abs(den)<=1e-14: continue
   t=(f[0]-q)@nd[i]/den
   if t<=0:continue
   k=np.linalg.lstsq(np.array([x[i],y[i]]).T,q+t*direction-f[0],rcond=None)[0]
   if min(*k,1-k.sum())>1e-9:count+=1
  raylens.append(count)
 a,b=P[list(edge)]; bind_q=a+(b-a)*fraction
 return dict(az_el=[az,el],edge=edge,third_signed=vals.tolist(),occluding_other_skin_source_faces=covered,near_guard_source_faces=guard,
 tool_forward_ray_counts=raylens,nearest_full_tool_surface_mm=float(nearest[0]*1000),closest_facet=nearest[1],
 correct_rest_cuff_distance_mm=float((bind_q-o)@n*1000),mixed_frame_not_a_distance=float((q-o)@n*1000))
out=[]
for w in R['whole_original_character_outline_witnesses']:
 t=test(w['source_physical_edge'],w['indexed_incident_faces'],w['inside_sample_fraction'],w['angle_azimuth_deg'],w['angle_elevation_deg'])
 assert np.prod(t['third_signed'])>0 and not t['occluding_other_skin_source_faces'] and not t['near_guard_source_faces']
 assert all(i%2 for i in t['tool_forward_ray_counts'])
 assert abs(t['nearest_full_tool_surface_mm']-w['nearest_full_tool_surface_mm'])<1e-8
 assert t['correct_rest_cuff_distance_mm']>0
 out.append(t)
w=R['fixed_offset_material_seam_near_boundary_samples_not_exact'][0]
neg=test(w['edge'],[712165,712323],w['edge_fraction'],w['azimuth_deg'],w['elevation_deg'])
assert 711793 in neg['occluding_other_skin_source_faces'] and np.prod(neg['third_signed'])<0
print(json.dumps({'whole_original_skin_positive':out,'internal_atlas_trace_negative':neg},indent=2,sort_keys=True))
