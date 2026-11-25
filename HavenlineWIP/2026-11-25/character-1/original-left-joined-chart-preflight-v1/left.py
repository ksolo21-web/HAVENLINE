from source import *
from collections import Counter,defaultdict
from scipy.sparse.csgraph import connected_components
qpath=Path('../hvn-c1-retained-tool-scope-independent-v1.KckaW8/result.json')
assert digest(qpath)=="61ef85840ffd75124bd3747ad97c4db3375907a675c3c880122847338ec64a96"
q=json.loads(qpath.read_text())['L/distal_connected_to_owned_glove']
hold={(i,j) for i,j,*_ in q['rows']}
assert len(hold)==92
E=s['L_loop_source_vertex_edges']; tt=s['L_loop_source_edge_t']; tr=P[E[:,0]]*(1-tt[:,None])+P[E[:,1]]*tt[:,None]
g0=tr.mean(0); cut=np.linalg.svd(tr-g0)[2][-1];cut*=np.sign((P[J['sides']['L']['palm_vertex']]-g0)@cut)
dd=(P-g0)@cut; own=(P[:,0]>.52)&(dd>0)
ids=np.flatnonzero(own); ee=bis[own[bis].all(1)]; ix=np.searchsorted(ids,ee)
_,lab=connected_components(coo_matrix((np.ones(len(ix)),(ix[:,0],ix[:,1])),shape=(len(ids),len(ids))).tocsr(),directed=False)
band=set(np.flatnonzero(((abs(A[T,2]+.26)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-.073)<3e-5)).all(1)).tolist())
assert len(band)==28 and {276,277,302,303}<=band
labs={i:int(lab[np.searchsorted(ids,F[i][0])]) for i,j in hold}
roles=[k for k,n0 in enumerate(names) if n0.endswith('.01.L')]
primary=W[:,roles].argmax(1);mx=W[:,roles].max(1)
th,idx=[next(j for j,k in enumerate(roles) if str(names[k]).startswith(z)) for z in ('thumb.','index.')]
ok=(mx[ee]>300).all(1)&(((primary[ee[:,0]]==th)&(primary[ee[:,1]]==idx))|((primary[ee[:,0]]==idx)&(primary[ee[:,1]]==th)))
web=ee[ok]
_,inv,nc=np.unique(np.c_[P[ids],V[ids]],axis=0,return_inverse=True,return_counts=True)
# Also retain source position aliases with any held difference (rest seam).
_,ri,rc=np.unique(P[ids],axis=0,return_inverse=True,return_counts=True)
alias=set(ids[(nc[inv]>1)|(rc[ri]>1)])
locks=alias|set(E.ravel())|set(web.ravel())
keepchart=set(labs.values())
eligible=np.flatnonzero(own[F].all(1));eligible=eligible[np.isin(lab[np.searchsorted(ids,F[eligible,0])],list(keepchart))]
assert {i for i,j in hold}<=set(eligible)
ad=defaultdict(list)
outer=np.flatnonzero((P[F,0]>.52).any(1))
for i in outer:
 t=F[i]
 for a,b in zip(t,np.roll(t,-1)):ad[tuple(sorted((int(a),int(b))))].append(int(i))
def indexed(rows):
 g=defaultdict(list)
 for i in sorted(rows):
  t=F[i]
  for a,b in zip(t,np.roll(t,-1)):g[tuple(sorted((int(a),int(b))))].append(int(i))
 return g
tl,th=tool.min(1),tool.max(1)
def intersects_edge(ed):
 a,b=V[list(ed)]; e=b-a
 lo,hi=np.minimum(a,b),np.maximum(a,b)
 hits=[]
 for j in np.flatnonzero((tl<=hi).all(1)&(th>=lo).all(1)):
  t=tool[j];o=t[0];x,y=t[1:]-o; h=np.cross(e,y); det=x@h
  if abs(det)<1e-15:continue
  d=a-o; uu=d@h/det; c=np.cross(d,x); vv=e@c/det; zz=y@c/det
  if min(uu,vv,1-uu-vv,zz,1-zz)>1e-8:hits.append([int(j),float(zz)])
 return hits
for i,j in hold:assert crosses(V[F[i]],tool[j]) or crosses(tool[j],V[F[i]])
# Minimal prospective cut, no UV welding. Include two local annuli only
# where chart custody and owner constraints permit, for transition space.
ep=set(eligible)
active={i for i,j in hold}
seed_edge=indexed(active)
for _ in range(2):
 g=indexed(active)
 for e,v in g.items():
  if len(v)==1 and not set(e)&locks:
   active.update(i for i in ad[e] if i in ep)
hist=[]
for _ in range(12):
 g=indexed(active)
 rim={e:v[0] for e,v in g.items() if len(v)==1}
 hits=[]
 for e,i in rim.items():
  x=intersects_edge(e)
  if x:hits.append({'vertices':list(e),'from_parent_face':i,'other_source_faces':[j for j in ad[e] if j!=i],'strict_hits':[x0 for x0 in x],
                   'fixed_cuff_alias_or_web':sorted(set(e)&locks)})
 hist.append({'rows':len(active),'edges':len(rim),'crossing_boundary':hits})
 if not hits:break
 add=set()
 for x in hits:
  outside=x['other_source_faces']
  if not x['fixed_cuff_alias_or_web'] and len(outside)==1 and outside[0] in ep:add.add(outside[0])
 if not add:break
 active.update(add)
def winding(p):
 m=tool-p
 aa,bb,cc=m.transpose(1,0,2)
 ar,br,cr=(np.linalg.norm(z,axis=1) for z in (aa,bb,cc))
 det=(np.cross(aa,bb)*cc).sum(1);div=ar*br*cr+(aa*bb).sum(1)*cr+(aa*cc).sum(1)*br+(bb*cc).sum(1)*ar
 return float(np.arctan2(det,div).sum()/(2*np.pi))
vs=sorted(set(np.array(list(rim)).ravel()))
weights=np.array([winding(p) for p in V[vs]])
inside=np.array(vs)[np.abs(weights)>.5]
ev=[(i,j) for i,j in rim]
mid=np.array([winding(p) for p in V[ev].mean(1)])
loop_degree=Counter(np.array(ev).ravel())
report={'status':'HOLD','source_hashes':expected,'source_classification_file_digest':digest(qpath),'replayed_strict_left_pairs':len(hold),'left_off_assigned_band_replayed_pairs':sum(j not in band for i,j in hold),
 'original_left_assigned_band_id':276,'original_assigned_band_tool_triangle_ids':sorted(band),
 'indexed_chart_authority': {int(k):{'vertices':int((lab==k).sum()),'collisions':sum(labs[i]==k for i,j in hold),'assigned_band_collisions':sum(labs[i]==k and j in band for i,j in hold)} for k in keepchart},
 'exact_left_web_edges_preserved':web.tolist(),'candidate_cut_attempts':hist,'selected_face_ids':sorted(active),
 'perimeter_non_two_degree_ids':{int(k):int(v) for k,v in loop_degree.items() if v!=2},
 'perimeter_immutable_inside_vertices':inside.tolist(),'perimeter_inside_midpoints':[list(ev[i]) for i in np.flatnonzero(np.abs(mid)>.5)],
 'perimeter_immutable_alias_ids':sorted(set(vs)&alias),'original_cuff_min_distance_mm':float(1000*dd[np.unique(F[list(active)])].min())}
tool_xyz=tool.reshape(-1,3);_,ti=np.unique(tool_xyz,axis=0,return_inverse=True)
TC=ti.reshape(-1,3)
cad=defaultdict(list)
for ca in TC:
 for i,j in zip(ca,np.roll(ca,-1)):cad[tuple(sorted((int(i),int(j))))].append((int(i),int(j)))
watertight=all(len(w)==2 and w[0]==w[1][::-1] for w in cad.values())
assert watertight
def closest(a,t):
 x,y,z=t; u,v=y-x,z-x; p=a-x
 b0=np.linalg.solve([[u@u,u@v],[v@u,v@v]],[p@u,p@v])
 near=[np.linalg.norm(p-b0[0]*u-b0[1]*v)] if min(*b0,1-b0.sum())>=0 else []
 for x,y in zip(t,np.roll(t,-1,axis=0)):
  u=y-x;z=np.clip((a-x)@u/(u@u),0,1);near.append(np.linalg.norm(a-x-z*u))
 return min(near)
fixed_inside=sorted(set(inside)&locks)
assert fixed_inside
second=[]
for i in fixed_inside:
 rest2=ids[ri==ri[np.searchsorted(ids,i)]]
 held2=ids[inv==inv[np.searchsorted(ids,i)]]
 d0=np.array([closest(V[i],t) for t in tool]); j=int(np.argmin(d0))
 second.append({'source_row':int(i),'winding':winding(V[i]),
       'closest_full_shaft_triangle_id':j,'actual_nearest_shaft_distance_mm':1000*float(d0[j]),
       'identical_original_bind_alias_rows':rest2.tolist(),
       'identical_original_bind_and_held_alias_rows':held2.tolist(),
       'actual_source_atlas_pair_UV_jump':float(np.linalg.norm(uv[rest2[0]]-uv[rest2[-1]])),
       'aliases_other_indexed_chart_labels':lab[np.searchsorted(ids,rest2)].tolist(),
       'actual_cuff_distance_mm':1000*float(dd[i]),
       'assigned_band_nearest':j in band})
rims=[]
for e,i in rim.items():
 if not set(e)&locks:continue
 hh=intersects_edge(e)
 if not hh:continue
 e0,e1=e
 b0=ids[inv==inv[np.searchsorted(ids,e0)]]
 b1=ids[inv==inv[np.searchsorted(ids,e1)]]
 variants=[]
 for a in b0:
  for b in b1:
   k=tuple(sorted([int(a),int(b)]))
   if k==e:continue
   if k in ad:
    variants.append({'exact_duplicate_edge':k,'adjacent_other_source_faces':ad[k]})
 rims.append({'source_seam_edge':e,'strict_original_axe_hits':hh,'separate_exact_alias_chart_edge_variants':variants})
report['tool_exact_position_weld_watertight_readonly']=watertight
report['hard_left_perimeter_material_lock_inside_tool']=second
report['hard_crossing_edges_and_texture_alias_counterparts']=rims
report['status']='HOLD_LEFT_AUTHORIZED_LOCAL_SURFACE_BLOCKED_BY_EXACT_IMMUTABLE_ATLAS_POINTS'
report['new_geometry_authored']=False
report['right_geometry_UV_or_off_band_pairs_changed']=False
from scipy.spatial import ConvexHull
src=V[fixed_inside[0]]
extremes={}
for uvs in ((0,1),(0,2),(1,2)):
 h2=ConvexHull(V[ids][:,uvs])
 extremes[str(uvs)]=[i for i in fixed_inside if i in ids[h2.vertices]]
fac=tool[277]; normal=np.cross(fac[1]-fac[0],fac[2]-fac[0]); normal/=np.linalg.norm(normal)
assert abs(winding(fac.mean(0)+normal*1e-5))<1e-6 and abs(winding(fac.mean(0)-normal*1e-5)-1)<1e-6
gap=float((fac[0]-src)@normal)
# Analytical hypothetical check only; no coordinates edited, no generated surface.
probe=src+normal*(gap+.000075)
h3=ConvexHull(V[ids])
assert not np.isin(fixed_inside,ids[h3.vertices]).any()
inc=np.flatnonzero(np.isin(F,fixed_inside).any(1))
report['only_readonly_future_motion_feasibility']={
 'inside_points_on_cardinal_projected_convex_silhouette':extremes,
 'inside_points_on_3d_original_left_glove_convex_hull':[],
 'affected_source_incident_faces':inc.tolist(),
 'all_incident_faces_entirely_distal_and_in_original_left_guard':bool(own[F[inc]].all()),
 'closest_incident_point_to_cuff_cut_mm':1000*float(dd[F[inc]].min()),
 'hypothetical_shared_offset_along_true_shaft_277_outward_mm':(gap+.000075)*1000,
 'hypothetical_both_copies_common_point_winding':winding(probe),
 'hypothetical_point_max_original_left_glove_convex_hull_halfspace_m':float((h3.equations[:,:3]@probe+h3.equations[:,3]).max()),
 'note':'Common point only, no changed rows and no mesh/seam redrawing. Not proof of remaining full edge/skin/texture or pixel contour validity.'}
