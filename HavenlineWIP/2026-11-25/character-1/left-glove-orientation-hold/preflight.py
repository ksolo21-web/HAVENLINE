"""Exact full-left topology and UV preflight. Stop before shape if substrate parity conflicts."""
from collections import Counter,defaultdict,deque
from pathlib import Path
import numpy as np,hashlib,json
p=Path(__file__).resolve().parent
base=p.parent
def seal(folder,check):
 packet=base/folder
 sh=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
 assert sh(packet/'SHA256SUMS')==check
 for x in (packet/'SHA256SUMS').read_text().splitlines():
  h,n=x.split(maxsplit=1);assert sh(packet/n)==h
 return packet
tip=seal('hvn-l1-c1-left-tip-diagonal-v1','c951e28d0f03cebd6e621fc86f90ccbf30b2df470ae4494120d876128cd6e0d6')
rails=seal('hvn-l1-c1-intrinsic-sewing-v1','ea685b7d29314c7ce84d0d1a6bf050028b2786459313cf4115c3072f718ce416')
coarse=seal('hvn-l1-c1-left-coarse-sections-v1','3c059bdf29e6f300e2255dc89e1c332dadcbd46f702951373a12719efd4b12cc')
q=np.load(tip/'editable_left_tip_flip.npz');a=np.load(rails/'editable_intrinsic_panels.npz');t=np.load(coarse/'editable_left_coarse.npz')
F=q['combined_tri'];UV=q['corner_uv'];vo=q['open'];vb=q['bind'];pF=np.flatnonzero(np.all(np.isin(F,q['exact_pressure_source']),axis=1))
assert pF.size==1;pressure=int(pF[0])
def use(F):
 d=defaultdict(list)
 for i,f in enumerate(F):
  for j,k in ((0,1),(1,2),(2,0)):
   e=int(f[j]),int(f[k]);d[tuple(sorted(e))].append((i,e,j,k))
 return d
d=use(F)
bound=[list(e) for e,r in d.items() if len(r)==1]
bad={e:r for e,r in d.items() if len(r)==2 and r[0][1]==r[1][1]}
assert len(bound)==82 and not any(len(v)>2 for v in d.values()) and set(bad)=={(0,78),(41,78),(41,79)}
countDirected=sum(len(r) for r in d.values() if len(r)==1)+len(bad)
assert countDirected==85
existing=np.arange(77)
expected=np.r_[existing,[79,93,94,86,77]]
expectedE={tuple(sorted((int(u),int(v)))) for u,v in zip(expected,np.roll(expected,-1))}
assert expectedE=={tuple(x) for x in bound}
source=t['proximal_exact_source_rows']
assert source.size==77
assert np.array_equal(vo[existing],a['L_0_open'][519+source])
assert np.max(np.linalg.norm(vb[existing]-a['L_0_bind'][519+source],axis=1))==0
# Missing 443-edge complement in exact original rail perimeter order.
comp=[];cur=int(source[-1])
while True:
 comp.append(cur)
 if cur==source[0]:break
 cur=(cur-1)%519
assert len(comp)==444 and len(set(comp)&set(source))==2 and len(set(comp)|set(source))==519
# Actual face UV splits per directed distal rail edge. No synthetic palette.
def frozen_far_uv(k):
 n=len(a[k+'_open'])//2;s={}
 for f,uv in zip(a[k+'_indices'],a[k+'_uv']):
  for i,j in [(0,1),(1,2),(2,0)]:
   if f[i]>=n and f[j]>=n:
    sign=(int(f[i]-n),int(f[j]-n));s[sign]=[uv[i],uv[j]]
 return s
chart0=frozen_far_uv('L_0');chart1=frozen_far_uv('L_1')
exactComplementCorners=np.asarray([chart0[int(i),int(j)] for i,j in zip(comp,comp[1:])])
dorsal=[]
for i,j in zip(existing,existing[1:]):
 u,v=int(source[i]),int(source[j])
 old=d[i,j][0]
 assert old[1]==(j,i)
 x=UV[old[0],old[3]];y=UV[old[0],old[2]]
 assert np.array_equal([x,y],chart0[u,v])
 dorsal.append(old[0])
assert len(set(dorsal))==76
bridge=[0,77,86,94,93,79,76]
bridge_occ=[]
for i,j in zip(bridge,bridge[1:]):
 row=d[tuple(sorted((i,j)))]
 assert len(row)==1
 face,orientation,k,l=row[0]
 assert orientation==((i,j) if (i,j)==(79,76) else (j,i))
 bridge_occ.append((i,j,face,k,l,*orientation))
# Algebraic parity over the exact fixed joined source. Unknown complement
# faces could only attach to incidence=1; no solution to fixed internal
# parity. Provide cohorts and one explicit rail-to-bearing parity proof.
G=defaultdict(list)
for e,r in d.items():
 if len(r)==2:
  i,j=r[0][0],r[1][0];z=r[0][1]==r[1][1]
  G[i].append((j,bool(z),e));G[j].append((i,bool(z),e))
assignment={pressure:False};parent={};front=deque([pressure])
while front:
 i=front.popleft()
 for j,z,e in G[i]:
  qv=assignment[i]^z
  if j in assignment:
   assert assignment[j]==qv
   continue
  assignment[j]=qv;parent[j]=(i,z,e);front.append(j)
assert len(assignment)==len(F)
flips=sorted(k for k,v in assignment.items() if v)
assert set(flips)==set(dorsal)
railWitness=int(dorsal[0]);cursor=railWitness;pas=[]
while cursor!=pressure:
 owner,diff,e=parent[cursor]
 pas.append({'from_face':cursor,'to_face':owner,'edge':list(e),'relative_flip_odd':diff})
 cursor=owner
assert sum(s['relative_flip_odd'] for s in pas)%2==1
# Exact arithmetic negative: simply appending all complementary outer
# faces, however oriented, cannot alter these three interior incidences.
for e in bad:
 assert e not in expectedE and len(d[e])==2
ordinary={i:False for i in range(len(F))}
assert all(ordinary[x[0][0]]==ordinary[x[1][0]] for x in bad.values())
# A typed synthetic regular parity behavior guards solver direction.
def pair_bad(F):
 return [e for e,r in use(F).items() if len(r)==2 and r[0][1]==r[1][1]]
assert not pair_bad(np.array([[1,0,3],[0,1,2]]))
assert pair_bad(np.array([[1,0,3],[1,0,2]]))==[(0,1)]
out={'status':'HOLD_COMPLETE_LEFT_REQUIRES_PROXIMAL_REAUTHOR','full_glove_built':False,
 'all_exact_source_open_edges_undirected':len(bound),'open_loop_directed_only_including_existing_internal_defects':countDirected,
 'original_L0_matched_edges':len(dorsal),'missing_L0_rail_edges':len(comp)-1,'missing_bridge_edges':len(bridge)-1,
 'independent_L1_perimeter_edges':len(chart1),'boundary_undirected_degree_two':True,'six_edge_bridge_wrong_winding_on':[79,76],
 'actual_same_directed_internal_edges':[{'vertices':list(e),'old_face_rows':[r[0][0],r[1][0]],'actual_directions':[r[0][1],r[1][1]]} for e,r in bad.items()],
 'fixed_pressure_anchor_face':pressure,'immutable_matched_cuff_rail_face':railWitness,'odd_parity_connection_pressure_to_rail':pas,
 'faces_required_flipped_if_pressure_fixed':flips,'face_count_if_reversing_pressure_and_complement_instead':len(F)-len(flips),
 'proposed_full_native_skipped':True,'reason':'Adding exterior faces at true boundary cannot alter pre-existing same-directed incidence on three internal edges.'}
# Compact exact editable UV/role authority map. No attached candidate geometry.
np.savez_compressed(p/'editable_missing_join_graph.npz',existing_neutral=vb,existing_open=vo,existing_faces=F,existing_corner_uv=UV,
 complete_old_boundary_indices=expected,unattached_L0_source_complement_rows=comp,unattached_L0_source_open=a['L_0_open'][519+np.array(comp)],
 unattached_L0_source_neutral=a['L_0_bind'][519+np.array(comp)],unattached_L0_source_corner_uv=exactComplementCorners,
 verified_existing_L0_source_rows=source,verified_existing_L0_face_rows=dorsal,six_edge_bridge_indices=bridge,
 six_edge_bridge_source_face_and_corner=bridge_occ,independent_L1_far_open=a['L_1_open'][48:],independent_L1_far_bind=a['L_1_bind'][48:],
 independent_L1_far_source_edges=list(chart1),independent_L1_far_source_uv=list(chart1.values()),
 pressure_vertex_indices=q['exact_pressure_source'],nonorientable_before_internal_edge_ids=np.asarray(list(bad)))
(p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n')
print(json.dumps(out,indent=2,default=lambda x:x.item()))
