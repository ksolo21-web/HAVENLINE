from source import *
from collections import Counter,defaultdict
p=Path('../hvn-c1-owner-right-palm-independent-v1.ehRf1T')
assert digest(p/'SHA256SUMS')=='62a67afd7a76e8e319024078ad4dcbda379fcb1dbac74402a924f31425a9861f'
line=next(t for t in (p/'SHA256SUMS').read_text().splitlines() if t.endswith('independent.json'))
assert digest(p/'independent.json')==line.split()[0]
q=json.loads((p/'independent.json').read_text())['original_retained_tool_crossings']
assert len(q)==298 and len(set(map(tuple,q)))==298
from scipy.sparse.csgraph import connected_components
labels={}
bands={k:set(np.flatnonzero(((abs(A[T,2]-z)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-rad)<3e-5)).all(1)).tolist()) for k,z,rad in [('R',-.10,.071),('L',-.26,.073)]}
assert all(len(x)==28 for x in bands.values())
for side,sign in (('L',1),('R',-1)):
 E=s[side+'_loop_source_vertex_edges']; tt=s[side+'_loop_source_edge_t']; trace=P[E[:,0]]*(1-tt[:,None])+P[E[:,1]]*tt[:,None]
 c=trace.mean(0); n=np.linalg.svd(trace-c)[2][-1]; n*=np.sign((P[J['sides'][side]['palm_vertex']]-c)@n)
 D=(P-c)@n
 assert abs(D[J['sides'][side]['palm_vertex']])>.001 and abs((trace-c)@n).max()<1e-6
 # Match exact original cut's distant-body rejection. Use original-coordinate indexed
 # topology; exact positional aliases only for adjacency, never authoring/UV equivalence.
 own=(P[:,0]*sign>.52)&(D>1e-9)
 vi=np.flatnonzero(own); ee=bis[own[bis].all(1)]
 _,inv=np.unique(P[vi],axis=0,return_inverse=True)
 r=inv[np.searchsorted(vi,ee)]
 g=coo_matrix((np.ones(len(r)),(r[:,0],r[:,1])),shape=(int(inv.max())+1,)*2).tocsr()
 _,lab=connected_components(g,directed=False)
 ids=vi[lab[inv]==lab[inv[np.searchsorted(vi,J['sides'][side]['palm_vertex'])]]]
 fore=set(map(tuple,s[side+'_forearm_collision_ids'].tolist()))
 labels[side]=dict(palm_cut_mm=float(D[J['sides'][side]['palm_vertex']]*1000),D=D,main=np.isin(np.arange(len(P)),ids),face_trace=set(s[side+'_loop_source_faces'].tolist()),fore=fore)
ln=defaultdict(list)
for f,j in q:
 tri=F[f]; sx=P[tri,0]; side='L' if (sx>.52).all() else 'R' if (sx<-.52).all() else '?'
 if side=='?':
  cls='outside_distal_lateral_guard_unclassified'
  dmin=dmax=None; traced=False; fore=False
 else:
  pp=labels[side]; ed=pp['D'][tri]; dmin,dmax=(float(x*1000) for x in (min(ed),max(ed)))
  traced=f in pp['face_trace']; fore=(f,j) in pp['fore']
  cls='crosses_indexed_cuff_cut' if dmin<=0<dmax else 'proximal_to_cuff_cut_non_glove' if dmax<=0 else 'distal_connected_to_owned_glove' if pp['main'][tri].all() else 'distal_other_component_not_classified'
 ln[side+'/'+cls].append([f,j,dmin,dmax,traced,fore])
summary={}
for key,rows in sorted(ln.items()):
 ids=sorted({p[0] for p in rows})
 rgb=np.array([rgb_samples(F[i]) for i in ids])
 side=key[0]; own=bands.get(side,set()); opposite=bands.get({'L':'R','R':'L'}.get(side),set())
 summary[key]={'palm_reference_cut_mm':labels.get(side,{}).get('palm_cut_mm'), 'owned_band_pairs':sum(p[1] in own for p in rows), 'opposite_band_pairs':sum(p[1] in opposite for p in rows),'neither_band_pairs':sum(p[1] not in own|opposite for p in rows),'pairs':len(rows),'unique_faces':len(ids),'actual_tool_facet_histogram':dict(Counter(p[1] for p in rows)),
 'face_range_from_cut_mm':(min(p[2] for p in rows),max(p[3] for p in rows)) if rows[0][2] is not None else None,
 'exact_fixture_cuff_trace_pairs':sum(p[4] for p in rows),'historical_forearm_weight_pair_overlap':sum(p[5] for p in rows),
 'atlas_corner_rgb_median':np.median(rgb.reshape(-1,3),axis=0).tolist(),
 'rows':rows}
print(json.dumps(summary,indent=2,sort_keys=True))
