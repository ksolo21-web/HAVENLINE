"""Read back exact endpoint section diagnostics and source outline witnesses."""
from pathlib import Path
import hashlib,json,numpy as np
p=Path(__file__).resolve().parent;b=p.parent
q=json.loads((p/'result.json').read_text())
S0=np.load(b/'hvn-l1-c1-approved-rear-fold-v1.kD1WNv/new-rear-panel.npz')
AA=np.load(b/'hvn-l1-c1-rear-pocket-volume-v1.hftpls/pocket-solids.npz')
F=S0['tri']; approved=set(S0['region'].tolist())
def zmax_vertices(s,z):
    A=np.asarray(s,dtype=float)[F];lo=A[:,:,2].min(1);hi=A[:,:,2].max(1)
    out=[]
    ids=np.flatnonzero((lo<=z)&(hi>=z));s=A[ids]
    for j,k in [(0,1),(1,2),(2,0)]:
        a=s[:,j,:];b=s[:,k,:];d=a[:,2]-b[:,2]
        ids0=np.flatnonzero(np.abs(d)>1e-15);t=(a[ids0,2]-z)/d[ids0]
        take=(t>=-1e-12)&(t<=1+1e-12)
        pts=a[ids0[take]]+(b[ids0[take]]-a[ids0[take]])*t[take,None]
        out.extend((int(i),p0) for i,p0 in zip(ids[ids0[take]],pts))
        flat=np.flatnonzero((np.abs(d)<=1e-15)&(abs(a[:,2]-z)<=1e-13))
        out.extend((int(ids[c]),p0) for c in flat for p0 in s[c,[j,k]])
    return out
R={}
for name,D in [('neutral',S0['v']),('held_0ms',AA['retained'][-1])]:
    H=[]
    for f,line in zip(q['placed_stations'],q['measurements'][name]):
        x=f['station_m'];W=[]
        P=np.unique(np.asarray(line['section_faces']).reshape(-1,3),axis=0)
        for v in P:
            cand=zmax_vertices(D,float(v[2]));assert cand
            j,src=max(cand,key=lambda u:u[1][1]);jmin,minv=min(cand,key=lambda u:u[1][0]);jmax,maxv=max(cand,key=lambda u:u[1][0]);jf,front=min(cand,key=lambda u:u[1][1]); 
            rec={'candidate_position_m':v.tolist(),'actual_source_posterior_face':j,'actual_source_posterior_position_m':src.tolist(),
               'candidate_posterior_minus_owner_side_envelope_mm':float(1000*(v[1]-src[1])),
               'candidate_max_front_side_overrun_mm':float(1000*max(v[0]-maxv[0],minv[0]-v[0],front[1]-v[1]))}
            W.append(rec)
        e=max(W,key=lambda x:x['candidate_posterior_minus_owner_side_envelope_mm'])
        extra={}
        for key in ('lower_attachment','upper_attachment'):
            t=np.asarray(f[key][name]); Q=zmax_vertices(D,float(t[2])); si,sv=max(Q,key=lambda x:x[1][1])
            extra[key]={'held_pure_bone_rail_seat_m':t.tolist(),'actual_source_side_posterior_face':si,
                'source_face_is_within_authorized_old_rear':si in approved,'source_side_posterior_m':sv.tolist(),
                'seat_posterior_minus_current_projection_mm':float(1000*(t[1]-sv[1]))}
        e['reference_source_face_within_approved_old_rear']=e['actual_source_posterior_face'] in approved
        H.append({'station_m':x,'samples':len(W),'full_source_side_posterior_at_sample_worst':e,
                  'max_protected_front_and_lateral_overrun_mm':max(d['candidate_max_front_side_overrun_mm'] for d in W), 'support_rail_envelope':extra,
                  'rest_material_arc_length_mm':f['rest_length_of_two_lobe_material_arc_m']*1000,
                  'exact_state_rail_chord_mm':line['exact_chord_m']*1000, 'two_lobe_posterior_reach_mm':line['symmetric_clock_arc_h_m']*1000})
    R[name]=H
out={'status':'ENDPOINT_LOCATION_WITNESSES_NOT_INTERVAL_OR_FULL_MESH',
     'projection_convention':'Exact source right shell max posterior/front/lateral at each source Z plane, subset is tested CAD vertices only. A positive posterior result falsifies preservation of exact side projection at that vertex; interpretation under scoped visibly approved rear shape goes to owner/critic.',
     'proof':R}
(p/'outline_readback.json').write_text(json.dumps(out,indent=2)+'\n')
for k,w in R.items():print(k,[(q['station_m'],round(q['full_source_side_posterior_at_sample_worst']['candidate_posterior_minus_owner_side_envelope_mm'],3),round(q['max_protected_front_and_lateral_overrun_mm'],3))for q in w])
