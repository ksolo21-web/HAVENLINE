from left import *
ind=Path('../hvn-c1-owner-left-band-independent-v1.OcUl7w/result.json')
assert digest(ind)=='00bffb04ab76fde8180e17e8054b7e8dd8f6aee5ccd04a7b62f44e6775ca684f'
assert len(json.loads(ind.read_text())['incident_pairs_analytical_common_point_only'])==7
physical=np.arange(len(P)); groups=defaultdict(list)
for i,k in zip(ids,inv):groups[int(k)].append(int(i))
for g0a in groups.values():physical[g0a]=min(g0a)
protected=set(E.ravel())|set(web.ravel())
def join(v):
 return tuple(sorted(physical[list(v)].tolist()))
p_ad=defaultdict(list)
for e,rr in ad.items():
 for rr0 in rr:p_ad[join(e)].append((e,rr0))
p_pool=set(eligible)
target=set(active)
loops_a=[]
for step in range(20):
 ied=indexed(target); pg=defaultdict(list)
 for e,rr in ied.items():pg[join(e)].extend((e,i) for i in rr)
 border={e:inc[0] for e,inc in pg.items() if len(inc)==1}
 assert all(len(t)<=2 for t in pg.values())
 bd_deg=Counter(np.array(list(border)).ravel())
 bad={}; pins={}
 for e,(vis,parent) in border.items():
  hh=intersects_edge(vis)
  w1=winding(V[e[0]]);w2=winding(V[e[1]]);wm=winding(V[list(e)].mean(0))
  if hh or max(abs(w1),abs(w2),abs(wm))>.5:
   bad[e]=(vis,parent,hh,w1,w2,wm)
 for i,z in bd_deg.items():
  if z!=2:pins[int(i)]=int(z)
 invalid=[(e[0],e[1],p[1],p[2]) for e,p in sorted(bad.items())]
 loops_a.append({'faces':len(target),'physical_boundary_size':len(border),'solid_crossing_or_inside_edges':invalid,'bad_degree':pins})
 if not bad and not pins:break
 extras=set()
 for e,p in bad.items():
  if any(v in protected for j in e for v in groups[inv[np.searchsorted(ids,j)]]):continue
  for ee,fid in p_ad[e]:
   if fid in p_pool and fid not in target:extras.add(fid)
 # Fill small remaining wedge at any doubled-point branch, but only when
 # its incident faces are within the same scope and vertices remain unedited.
 for g,z in pins.items():
  for edge,(e,i) in border.items():
   if g in edge:
    extras.update(f for _,f in p_ad[edge] if f in p_pool and f not in target)
 if not extras:break
 target.update(extras)
hand_ids=np.flatnonzero(own[F].all(1)); hand=V[F[hand_ids]]
# Exact geometry exterior test by whole-hand orthographic coverage:
# for a known tool-buried boundary edge of joined UV charts, project each
# deterministic oblique view and test opposite sides of the indexed edge.
seams=[]
for e,inc in pg.items():
 if len(inc)==2 and inc[0][0]!=inc[1][0]:
  g=V[list(e)]
  for f in (.25,.5,.75):
   p=g[0]*(1-f)+g[1]*f
   if abs(winding(p))>.5:seams.append((e,inc,p,f))
cut_faces=np.array(sorted(target)); own_f=np.unique(F[cut_faces])
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def project_geometry(d,geom):
 xx=np.cross(d,[0.,0.,1.])
 if np.linalg.norm(xx)<.01:xx=np.cross(d,[0.,1.,0.])
 xx/=np.linalg.norm(xx); yy=np.cross(d,xx)
 B0=np.vstack([xx,yy]); a=geom@B0.T
 return B0,a
def covered(x,q):
 v1=q[:,1]-q[:,0];v2=q[:,2]-q[:,0];v3=x-q[:,0]
 det=cross2(v1,v2); safe=np.where(abs(det)>1e-17,det,1)
 u=cross2(v3,v2)/safe;v=cross2(v1,v3)/safe
 return (abs(det)>1e-17)&(u>1e-9)&(v>1e-9)&(u+v<1-1e-9)
samples=[]
for eh in (-60,-40,-20,0,20,40,60):
 el=np.deg2rad(eh)
 for az in range(0,360,10):
  q=np.deg2rad(az); direction=np.array([np.cos(el)*np.cos(q),np.cos(el)*np.sin(q),np.sin(el)])
  basis,g=project_geometry(direction,hand)
  lo=g.min(1);hi=g.max(1)
  for ed,inc,p,f in seams:
   cen=p@basis.T; ex=(V[ed[1]]-V[ed[0]])@basis.T
   if np.linalg.norm(ex)<.0001:continue
   e_normal=np.array([-ex[1],ex[0]])/np.linalg.norm(ex)
   eps=np.array([.00002,.00005,.0001,.0002])
   hit=[]
   for sign in (-1,1):
    tt=[]
    for g0a in eps:
     p0=cen+sign*g0a*e_normal
     chosen=np.flatnonzero((lo<p0).all(1)&(hi>p0).all(1))
     ii=chosen[covered(p0,g[chosen])]
     tt.append(hand_ids[ii].tolist())
    hit.append(tt)
   if all(not h for h in hit[0]) and all(hit[1]) or all(not h for h in hit[1]) and all(hit[0]):
    samples.append({'edge':ed,'edge_fraction':f,'elevation_deg':eh,'azimuth_deg':az,'one_side_uncovered_other_side_covered_faces':hit,
                    'same_point_full_tool_winding':winding(p),'edge_original_indexed_faces':inc})
def dist_edge(p,a,b):
 e=b-a; zz=np.clip(((p-a)*e).sum(-1)/np.maximum((e*e).sum(-1),1e-40),0,1)
 return np.linalg.norm(a+zz[...,None]*e-p,axis=-1)
for t0 in samples:
 ed=t0['edge']; a,b=V[list(ed)]; p=a*(1-t0['edge_fraction'])+b*t0['edge_fraction']
 el=np.deg2rad(t0['elevation_deg']);az=np.deg2rad(t0['azimuth_deg'])
 d0=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
 basis,g=project_geometry(d0,hand); A0,B0,P0=(np.array([a,b,p])@basis.T)
 ii=np.array([pair[1] for pair in t0['edge_original_indexed_faces']]); j=np.searchsorted(hand_ids,ii)
 incident_signed=(cross2(B0-A0,g[j]-A0))
 assert (abs(incident_signed)>1e-12).sum()==2
 allother=np.ones(len(hand_ids),bool);allother[j]=False
 remain=g[allother]
 anyin=covered(P0,remain)
 outside_distance=np.min(dist_edge(P0,remain,np.roll(remain,-1,axis=1)))
 t0.update({'original_whole_left_hand_other_faces_covering_exact_projection':hand_ids[allother][anyin].tolist(),
            'minimum_projected_edge_radius_without_other_faces_mm':float(1000*outside_distance),
            'two_exact_seam_triangles_signed_projected_doubled_area_m2':incident_signed[abs(incident_signed)>1e-12].tolist(),
            'is_analytic_apparent_outline':bool(not anyin.any() and outside_distance>1e-10 and
              np.unique(np.sign(incident_signed[abs(incident_signed)>1e-12])).size==1)})
# Entire proposed interior pressure strip, not just the UV seam:
# find a true apparent-edge point, not a fixed-offset proxy.
inner_edges=[]; wanted=(.25,.5,.75)
for ed,inc in sorted(pg.items()):
 if len(inc)!=2:continue
 a,b=V[list(ed)]
 hits=[]
 for ff in wanted:
  ff0=a+ff*(b-a)
  if abs(winding(ff0))>.5:hits.append((ff,ff0))
 if not hits:continue
 thirds=[]
 for idx,fid in inc:
  fi=[row for row in F[fid] if row not in idx]
  assert len(fi)==1; thirds.append(fi[0])
 inner_edges.append((ed,inc,thirds,hits))
exact=[]
sampled=0
distance_cache={}
for eh in (-60,-40,-20,0,20,40,60):
 el=np.deg2rad(eh)
 for az in range(0,360,10):
  angle=np.deg2rad(az); direction=np.array([np.cos(el)*np.cos(angle),np.cos(el)*np.sin(angle),np.sin(el)])
  basis,projected=project_geometry(direction,hand)
  ll=projected.min(1);hh=projected.max(1)
  for ed,inc,thirds,hits in inner_edges:
   a,b=V[list(ed)]@basis.T
   ss=cross2(b-a,V[thirds]@basis.T-a)
   if min(abs(ss))<1e-10 or ss[0]*ss[1]<0:continue
   ffids=[fid for e,fid in inc]
   for f0,poi in hits:
    P0=poi@basis.T
    probe=np.flatnonzero((ll<P0+2e-8).all(1)&(hh>P0-2e-8).all(1)&~np.isin(hand_ids,ffids))
    sampled+=1
    if len(probe):
     rem=projected[probe]
     if covered(P0,rem).any() or np.min(dist_edge(P0,rem,np.roll(rem,-1,axis=1)))<2e-8:continue
    # A strict winding-one point at an actual original apparent-outline edge.
    # The whole exact distal hand is considered; original cuff is not cut.
    key=(ed,f0)
    if key not in distance_cache:distance_cache[key]=1000*min(closest(poi,t) for t in tool)
    exact.append({'source_physical_edge':ed,'indexed_incident_faces':ffids,'inside_sample_fraction':f0,
       'full_tool_winding':winding(poi),'angle_elevation_deg':eh,'angle_azimuth_deg':az,
       'projected_third_corner_signed_sides_m2':ss.tolist(),
       'no_other_glove_projection_within_mm':.00002,
       'nearest_full_tool_surface_mm':float(distance_cache[key])})
g3=V[F]
whole=[]; candidate_views=set()
for witness in sorted(exact,key=lambda r:-r['nearest_full_tool_surface_mm']):
 az=witness['angle_azimuth_deg'];el=witness['angle_elevation_deg']
 key=min((az,el),((az+180)%360,-el))
 if key in candidate_views:continue
 candidate_views.add(key)
 az0,el0=np.deg2rad([az,el]);d=np.array([np.cos(el0)*np.cos(az0),np.cos(el0)*np.sin(az0),np.sin(el0)])
 basis,g=project_geometry(d,g3)
 a,b=V[list(witness['source_physical_edge'])]
 x0=a+(b-a)*witness['inside_sample_fraction'];q0=x0@basis.T
 ii=np.flatnonzero((g.min(1)<=q0+2e-8).all(1)&(g.max(1)>=q0-2e-8).all(1)&
                   ~np.isin(np.arange(len(F)),witness['indexed_incident_faces']))
 if len(ii):
  rem=g[ii]
  if covered(q0,rem).any() or np.min(dist_edge(q0,rem,np.roll(rem,-1,axis=1)))<2e-8:continue
 whole.append(witness)
 if len(whole)==4 or len(candidate_views)>=12:break
guard={
 'on_original_cuff_cut_vertices':sorted(set(own_f)&set(E.ravel())),
 'on_left_protected_web_vertices':sorted(set(own_f)&set(web.ravel())),
 'right_or_body_vertices':int((~own[own_f]).sum()),
 'closest_source_vertex_to_preserved_cuff_cut_mm':float(1000*dd[own_f].min())}
# An overlapped tool may visually hide the old outline on the combined mesh;
# this source-only audit concerns the specified protected hand outline itself.
status='HOLD_NO_AUTHORED_LEFT_MESH_OUTLINE_NOT_ISOLATED' if exact else 'HOLD_UNCERTIFIED_NO_AUTHOR'
out={'status':status,'new_geometry_authored':False,'source_hashes':expected,
 'exact_independent_left_reference_SHA256':digest(ind),
 'left_scope_changed_neither_frozen_right_candidate_nor_206_retained_right_pairs':True,
 'source_joined_cut_steps':loops_a,'source_candidate_indexed_face_ids':cut_faces.tolist(),
 'physical_seam_adjacency_welded_for_diagnostic_only_no_index_or_uv_write':True,
 'strict_perimeter_clear':not loops_a[-1]['solid_crossing_or_inside_edges'] and not loops_a[-1]['bad_degree'],
 'protected_scope':guard,
 'exact_source_tool_faces':len(tool),'distinct_buried_material_seam_samples':len(seams),
 'fixed_offset_material_seam_near_boundary_samples_not_exact':samples,
 'buried_candidate_interior_edges':len(inner_edges),'strict_projected_contour_predicate_tests':sampled,
 'exact_original_distal_hand_outline_inside_tool_view_sample_count':len(exact),
 'whole_original_character_predicate_checks':len(candidate_views),
 'original_projected_distal_hand_outline_WIP_witnesses':sorted(exact,key=lambda r:-r['nearest_full_tool_surface_mm'])[:15],
 'whole_original_character_outline_witnesses':whole}
def vectors(w):
 ed=w['source_physical_edge']; a,b=V[list(ed)]
 p=a+w['inside_sample_fraction']*(b-a)
 surf=np.array([closest(p,t) for t in tool]); m=int(np.argmin(surf))
 def nvec(t):
  n=np.cross(t[1]-t[0],t[2]-t[0]);return (n/np.linalg.norm(n)).tolist()
 ea,az=np.deg2rad([w['angle_elevation_deg'],w['angle_azimuth_deg']])
 ray=[np.cos(ea)*np.cos(az),np.cos(ea)*np.sin(az),np.sin(ea)]
 return dict(outbound_view_direction_owner_xyz=ray,edge_source_row_fraction=w['inside_sample_fraction'],
             original_edge_incident_triangle_unit_normals=[nvec(V[F[i]]) for i in w['indexed_incident_faces']],
             nearest_exact_tool_facet=m,nearest_exact_tool_facet_unit_normal=nvec(tool[m]),
             section_distance_to_original_left_cuff_cut_mm=float((p-g0)@cut*1000))
out['exact_witness_normal_and_point_locator']=[]
for rec in (whole if whole else sorted(exact,key=lambda r:-r['nearest_full_tool_surface_mm'])[:4]):
 out['exact_witness_normal_and_point_locator'].append(dict(rec,**vectors(rec)))
out['application_actual_camera_or_owner_front_side_mapping']='UNVERIFIED: isolated exact held 52-joint pose has no trusted camera/scene mapping; neither custom underside/oblique direction nor isolated orthographic Character 1 silhouette is actual game-view/render evidence'
print(json.dumps(out,indent=2,sort_keys=True,default=int))
