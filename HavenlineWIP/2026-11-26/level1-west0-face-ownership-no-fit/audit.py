from pathlib import Path
import hashlib, numpy as np, json
r=Path(__file__).resolve().parent
p=r.parent/'hvn-l1-fence-33036-four-slot-source-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='a9b0f22c7a3dac86a3843d6960e1be2d24bef0eb544a34a4ae2159daa94050fd'
f=p/'compose.py'
a=f.read_text(); c={'__file__':str(f)};exec(a[:a.index('outer={}')],c)
q,C,G,SM=[c[k] for k in ('Q','C','G','SM')]
SM=np.array(SM)
U=G['West0'][0]; N={k:v for k,v in q.items() if k.startswith('West1/')}
def bounds(v): return [v.min((0,1)).tolist(),v.max((0,1)).tolist()]
def contacts(v=U,mask=np.ones(len(U),bool)):
 return {k:u for k,t in N.items() if (u:=C['culled_intersections'](t,v[mask],[k]*len(t),SM[mask]))}
def sections(T,z):
 lo=np.min(T[:,:,2],1);hi=np.max(T[:,:,2],1)
 res=[]
 for t in T[(lo<z)&(hi>z)]:
  for x,y in zip(t,np.roll(t,1,axis=0)):
   if (x[2]-z)*(y[2]-z)<0:
    res.append((x+(y-x)*((z-x[2])/(y[2]-x[2])))[:2])
 return np.asarray(res)
def b2(T):return [T.min(0).tolist(),T.max(0).tolist()]
safe=float(min(N['West1/soft_snow/whole'][:,:,2].min(),N['West1/amber_logs/whole'][:,:,2].min())-.0004)
xcap=b2(sections(U[SM=='timber'],safe))
zface=float(U[257,0,2]); snface=float(U[608,0,2])
rail={}
for h in ('lower','upper'):
 T=N['West1/front_rounded_rails/'+h]; z=float(T[:,:,2].min())
 sec=b2(sections(T,z+.0005))
 rail[h]={'suffix_start_Z_m':z,'source_signed_XY_bound_0p5mm_inside':sec,'absolute_axial_gap_after_safe_separate_cap_mm':1000*(z-safe),'outer_overhang_beyond_safe_cap_mm':1000*(xcap[0][0]-sec[0][0])}
 x=float(sec[0][0])
 # exact chamfer segment from known terminal cross edge, interpolate maximum reachable Z at that X
 e=U[258]
 ux,uz=np.unique(e[:,[0,2]],axis=0).T
 assert len(ux)==2 and ux[0]<=x<=ux[1]
 lim=float(np.interp(x,ux,uz))
 rail[h]['exact_original_timber_axial_gap_at_exterior_rail_X_mm']=1000*(z-lim)
print(rail)
result={'status':'HOLD: no geometry authored; contracted face reassignment cannot establish no cropped gap at protected stock terminal','group_contacts_original':contacts(),'timber_face_Z_m':zface,'snow_face_Z_m':snface,'safe_common_cut_Z_m_for_group_separation':safe,'exact_timber_section_XY_at_safe_cut':xcap,'rail_bounds':rail,'protected_stock_has_no_rail_or_rope_group': sorted(set(SM)),'geometry_changed':False}
(r/'result.json').write_text(json.dumps(result,indent=2)+'\n')
