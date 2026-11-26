from pathlib import Path
import json,hashlib,numpy as np,itertools
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parent;P=R.parent
src=P/'hvn-l1-fence-33036-embossed-shared-perp-v1'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(src/'SHA256SUMS')=='c71ccb5157f54aefaabb97411995d08ac649fa94c5b24a87dbe08f6e3b70c0b7'
d={'__file__':str(src/'join.py')}
text=(src/'join.py').read_text()
exec(text[:text.index('# More robust left point control')],d)
T=d['T'];C=d['N']['n']['V'];b=C['culled_intersections']
mat=np.array(C['labels']); base=C['tr']
A=C['panels'](base,True)
pins=P/'hvn-l1-fence-33036-bold-wrap-v3/build-result.json'
center=np.array([r['log_x_center_m'] for r in json.loads(pins.read_text())['modules']])
logs=np.isin(mat,['amber_logs','meshy_bold_amber_front','soft_snow'])
post_idx=np.argmin(abs(base[:,:,0].mean(1)[:,None]-center),axis=1)
# Only scope is the two named terminal assemblies. Source path tests use real authored
# owner neighbor geometries (never a narrow stock bridge).
rows={}
for nb,piece,k0,endpoint,ax,dir in [('SW1','SW0','post8',0,0,1),('West1','West2','post1',7,2,-1)]:
 old_post=T[piece+'/'+k0];old_cap=T[piece+'/'+k0+'_icing']
 axis=2 if ax==0 else 0
 lane=9.8 if ax==0 else -8.25; nsign=1 if ax==0 else -1
 V=A[nb][0]
 Y=V[~(logs&(post_idx==endpoint))]
 cuts=(logs&(post_idx==endpoint))
 vmat=mat[~cuts]
 assert cuts.sum()==360
 pos=(old_post.min((0,1))+old_post.max((0,1)))*.5
 Q={k:v for k,v in T.items() if k.startswith(piece+'/') and k not in (piece+'/'+k0,piece+'/'+k0+'_icing')}
 terminal_group=[]
 # Stop-go curtain: joint contour large enough to accept positive material
 # around all terminal cap directions must still clear nearest fixed roots.
 pts=[]
 for k,t in Q.items():
  if 'post' in k:continue
  tip=(t[:,:,ax].max() if dir==1 else t[:,:,ax].min())
  cap=t[(np.abs(t[:,:,ax]-tip)<1e-8).all(1)]
  if len(cap):pts.extend(cap.reshape(-1,3))
 # owner-level terminal band profiles: .1324 front/-.1365 back for SW carried inward
 # seat; root is frozen. Shape remains faceted wood instead of round-stock fallback.
 layout={'clip_axial_half_span_m':.124 if ax==0 else .168,
         'face_inboard_to_outboard_relative_lane_m':[-.143,.144],
         'end_height_m':float(old_cap[:,:,1].max())}
 # generous guarded polygon no direct carving. This is a necessary envelope only.
 if pts:
  pts=np.unique(np.round(pts,9),axis=0)
  axial=np.abs(pts[:,ax]-pos[ax]); normal=(pts[:,axis]-lane)*nsign
  possible=((axial+.002<=layout['clip_axial_half_span_m'])&(normal-.002>=-.143)&(normal+.002<=.144))
 else:pts=np.empty((0,3));possible=[]
 contact={}
 for name,W in Q.items():
  zz=b(W,Y,[name]*len(W),vmat)
  if zz:contact.update(zz)
 votes={'exact_remaining_src_owners_equivalent_donor_union':int(sum(x['pairs'] for x in contact.values())),
        'remaining_exact_categories_after_dropping_only_duplicated_other_timber_cap':contact,
        'scope_neighbor_removed_actual_corner_post_and_cap_faces':360,'existing_unchanged_owner_post_ids_removed_for_test':[piece+'/'+k0,piece+'/'+k0+'_icing'],
        'exact_root_xyz_frozen':pos.tolist(),'scope_guarded_terminal_containment':layout,
        'known_planar_cap_sample_qty':len(pts),'cap_samples_outside_even_rectangular_admissible_body_w_2mm_guard':int(len(pts)-np.sum(possible))}
 if len(pts):
  votes['actual_extremal_cap_axes_in_exact_world_m']=[pts.min(0).tolist(),pts.max(0).tolist()]
 # Minimum signed cut movement to even enter this deliberately generous volume.
 if len(pts):
  need_low=pos[ax]-layout['clip_axial_half_span_m']+.002
  need_hi=pos[ax]+layout['clip_axial_half_span_m']-.002
  votes['minimum_signed_termination_adjustment_m']=[max(0.,float(need_low-pts[:,ax].min())),max(0.,float(pts[:,ax].max()-need_hi))]
  # Compute placement using the actual existing neighbor caps at closest axial end,
  # not the already rejected stock bridges.
 N=V[~logs]
 vb=N[:,:,ax]
 far_ax=((vb.max() if dir==-1 else vb.min()))
 volume_start=pos[ax]-layout['clip_axial_half_span_m']+.002
 vol_end=pos[ax]+layout['clip_axial_half_span_m']-.002
 cap_req=max(volume_start-far_ax,far_ax-vol_end,0.)
 votes['retained_owner_neighbor_last_axial_tip_and_additional_seat_travel_required_m']=[float(far_ax),float(cap_req)]
 # Terminals jointly shaped to avoid old round cap assumption. Circular rod
 # appearance allowed only where actual containment survives the existing boundary.
 body=e_body=[]
 profile=np.array([[-.88,-1.],[.88,-1.],[1.,-.82],[1.,.85],[.89,1.],[-.89,1.],[-1.,.85],[-1.,-.82]])
 base_y=old_post[:,:,1].min()
 def rings(level,scale):
  P=np.empty((8,3));P[:,ax]=pos[ax]+profile[:,0]*layout['clip_axial_half_span_m']*scale
  P[:,axis]=lane+nsign*(.002+profile[:,1]*.142*scale)
  P[:,1]=level;return P
 from itertools import combinations
 polys=d['D']['polys']
 oak=polys(np.array([rings(v,k) for v,k in [(base_y-.035,.94),(base_y,.985),(base_y+.03,1.),(layout['end_height_m']-.28,1.),(layout['end_height_m']-.125,.81)]]),True)
 snow=polys(np.array([rings(v,k) for v,k in [(layout['end_height_m']-.26,.94),(layout['end_height_m']-.20,1.),(layout['end_height_m']-.14,.93),(layout['end_height_m']-.072,.71),(layout['end_height_m']-.027,.40),(layout['end_height_m'],.045)]]),True)
 J=np.r_[oak,snow]
 hull=ConvexHull(np.unique(oak.reshape(-1,3),axis=0)).equations
 signed=(pts@hull[:,:3].T+hull[:,3]).max(1) if len(pts) else []
 votes['first_real_beveled_body_full_cap_min_mm']=float(-max(signed)*1000) if len(signed) else None
 votes['first_real_beveled_body_faces']=len(J)
 hits={}
 for k,t in Q.items():
  if not ('post' in k or 'icing' in k):continue
  hits.update(b(J,t,[nb]*len(J),[k]*len(t)))
 m=b(J,Y[np.isin(vmat,['amber_logs','meshy_bold_amber_front','soft_snow'])],[nb]*len(J),['owner_neighbor_protected']*len(Y[np.isin(vmat,['amber_logs','meshy_bold_amber_front','soft_snow'])]))
 votes['terminal_new_vs_retained_body_crown_intersections']=dict(hits,**m)
 votes['constructed_blank_depth_m']=[float(np.min((J[:,:,axis]-lane)*nsign)),float(np.max((J[:,:,axis]-lane)*nsign))]
 # Entire existing neighbor full-cap profiles against the same real rooted body.
 az_tip=float(votes['retained_owner_neighbor_last_axial_tip_and_additional_seat_travel_required_m'][0])
 ra=Y[np.isin(vmat,['front_rounded_rails','ivory_hemp_warm','ivory_hemp_cream'])]
 # Original donor planar rail caps are protected real source facets.
 near=ra[np.any(abs(ra[:,:,ax]-az_tip)<.012,axis=1)]
 vv=near.reshape(-1,3)
 sc=vv@hull[:,:3].T+hull[:,3]
 votes['actual_neighbor_near12mm_strip_hull_min_mm']=float(-np.max(sc)*1000) if len(sc) else None
 exact_near=[]
 rail=Y[vmat=='front_rounded_rails']
 ymid=np.mean([rail[:,:,1].min(),rail[:,:,1].max()])
 for k0,band in enumerate([rail[rail[:,:,1].mean(1)<ymid],rail[rail[:,:,1].mean(1)>=ymid]]):
  gate_tip=float(band[:,:,ax].min() if dir==1 else band[:,:,ax].max())
  cp=np.unique(np.round(band[(np.abs(band[:,:,ax]-gate_tip)<1e-8).all(1)].reshape(-1,3),9),axis=0)
  exp=cp@hull[:,:3].T+hull[:,3]
  needed=None
  for d0 in np.arange(0,.081,.0005):
   cp1=cp.copy();cp1[:,ax]-=dir*d0
   if (cp1@hull[:,:3].T+hull[:,3]).max()<-.002:
    needed=float(d0);break
  ix=np.unravel_index(exp.argmax(),exp.shape)
  exact_near.append({'planar_actual_neighbor_rail_cap_band':k0,'cap_plane_world_m':gate_tip,'cap_vertices':len(cp),
                    'maximum_outermost_convex_face_excursion_mm':float(exp.max()*1000),
                    'minimum_scanned_exact_local_cap_inward_travel_to_2mm_screen_mm':None if needed is None else needed*1000,
                    'violating_xyz':cp[ix[0]].tolist(),'hull_support_face_xyz_normal':hull[ix[1],:3].tolist()})
 votes['actual_neighbor_rail_cap_only_support_tests']=exact_near
 seats={}
 for tag,t in Q.items():
  if 'icing' in tag or 'post' in tag:continue
  seats.update(b(oak,t,[nb+'_oak']*len(oak),[tag]*len(t)))
 seats.update(b(oak,ra,[nb+'_oak']*len(oak),['owner_neighbor_'+str(q) for q in range(len(ra))]))
 votes['positive_strict_oak_band_seats_count']=sum(v['pairs'] for v in seats.values())
 votes['owner_and_neighbor_seat_groups']={'owner':sum(k.split(' / ')[1].startswith(piece+'/') for k in seats), 'neighbor':sum(k.split(' / ')[1].startswith('owner_neighbor_') for k in seats)}
 foot=rings(base_y-.035,.94); ff=np.array([C['height'](p[[0,2]]) for p in foot])
 votes['bottom_ring_exact_sample_y_clearance_range_mm']=[float((foot[:,1]-ff).min()*1000),float((foot[:,1]-ff).max()*1000)]
 all_depth=np.concatenate([q for q in [*Q.values(),Y,J]])[:,:,axis]
 ext=(all_depth-lane)*nsign
 votes['complete_two_arm_depth_range_mm_geometry_only']=[float(ext.min()*1000),float(ext.max()*1000)]
 # A source-local degree of fit, not full terrain support/camera/material acceptance.
 votes['new_shell_peak_stock_source_px']=float((J[:,:,1].max()-J[:,:,1].min())*720/13*.7643)
 votes['disposition']='HOLD source single shell fit only, no reproduced whole neighbor material/join interplay'
 if 'new_assets' not in globals():new_assets={}
 new_assets[nb+'/timber']=oak;new_assets[nb+'/snow']=snow
 rows[nb]=votes
(R/'result.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print({k:(v['exact_remaining_src_owners_equivalent_donor_union'],v['known_planar_cap_sample_qty'],v['cap_samples_outside_even_rectangular_admissible_body_w_2mm_guard']) for k,v in rows.items()})

r=['# Detector-only source shapes, not installed']; i=1
for name,T in sorted(new_assets.items()):
 r.append('o '+name.replace('/','_'))
 for f in T:
  for p in f:r.append('v '+' '.join(f'{z:.9f}' for z in p))
  r.append(f'f {i} {i+1} {i+2}');i+=3
(R/'PairedTerminals_HOLD.obj').write_text('\n'.join(r)+'\n')
