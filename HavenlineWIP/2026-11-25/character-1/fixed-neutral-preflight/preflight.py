#!/usr/bin/env python3
"""One closed-form elbow pole proposal; no geometry writes, DCC, or search."""
import argparse, hashlib, json, math
from pathlib import Path

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,b): return tuple(x*b for x in a)
def sub(a,b): return add(a,mul(b,-1))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a): return mul(a,1.0/norm(a))
def angle(p,q): return math.degrees(math.acos(max(-1.0,min(1.0,dot(unit(p),unit(q))))))
def seq(p): return [round(x,9) for x in p]

p=argparse.ArgumentParser()
p.add_argument("chest_result",type=Path)
p.add_argument("chest_source",type=Path)
p.add_argument("axe_original",type=Path)
args=p.parse_args()
pins={
 "chest_result": "b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed",
 "chest_source": "9e8c8e069e98a333cbd250c8e6aba4a61c9701f54a599faed544d7925eb0a657",
 "axe_original": "79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e",
}
assert all(digest(getattr(args,name))==sha for name,sha in pins.items())
j=json.loads(args.chest_result.read_text())
assert j["status"]=="HOLD_OPEN_STAGE" and j["unchanged_lower_to_parent_exact"]
out={ "status":"HOLD_NOT_AUTHORED", "pins":pins, "staging_screen_degrees":15,
   "lineage":"same held chest geometric target and intrinsic axe; vary only detached elbow pole, no DCC", "sides":{} }
for k,item in j["sides"].items():
    S,W,old_E=[tuple(item[field]) for field in ("shoulder","wrist","elbow")]
    a,b=item["links_m"]
    u=unit(sub(W,S)); d=norm(sub(W,S))
    assert abs(a-b)<d<a+b
    x=(a*a-b*b+d*d)/(2*d)
    radius=math.sqrt(a*a-x*x)
    center=add(S,mul(u,x))
    # Reconstruct exact face-aligned hand longitudinal direction from witness.
    inward=mul(item["outward"],-1.0)
    forward=(0.0,-1.0,0.11 if k=="R" else -0.11)
    h=unit(sub(forward,mul(inward,dot(forward,inward))))
    hperp=sub(h,mul(u,dot(h,u)))
    # E = center + radius*q, q perpendicular to u. Maximize h⋅(W-E)/b.
    proposed_E=sub(center,mul(unit(hperp),radius))
    negative_E=add(center,mul(unit(hperp),radius))
    exact_best_dot=((d-x)*dot(h,u)+radius*norm(hperp))/b
    measured=angle(sub(W,proposed_E),h)
    previous=angle(sub(W,old_E),h)
    negative=angle(sub(W,negative_E),h)
    closed=math.degrees(math.acos(max(-1.0,min(1.0,exact_best_dot))))
    assert abs(closed-measured)<1e-9
    assert abs(previous-item["forearm_to_hand_deg"])<2e-5
    assert negative>previous>measured
    assert max(abs(norm(sub(proposed_E,S))-a),abs(norm(sub(W,proposed_E))-b))<1e-12
    out["sides"][k]={
     "fixed_shoulder_m":seq(S), "fixed_wrist_m":seq(W), "target_hand_longitudinal":seq(h),
     "fixed_links_m":seq((a,b)), "shoulder_wrist_reserve_mm":round(1000.0*(a+b-d),6),
     "prior_elbow_m":seq(old_E), "optimistic_point_only_elbow_m":seq(proposed_E),
     "proposed_elbow_shift_mm":round(1000*norm(sub(proposed_E,old_E)),6),
     "prior_angle_deg":round(previous,6), "optimistic_min_angle_deg":round(closed,6),
     "opposite_elbow_control_angle_deg":round(negative,6),
     "nominated_exact_tool_face":item["surface_face_index"], "nominated_palm_vertex":item["palm_vertex"],
     "grip_center_intrinsic_axe_m":item["grip_center_in_original_axis"],
     "prior_off_band_pairs_not_new_variant":item["out_of_assigned_band_pairs"],
     "prior_signed_grip_prism_intrusion_mm_not_new_variant":item["deepest_exact_vertex_in_assigned_grip_prism_mm"],
     "staging_angle_pass":closed<=15.,
    }
assert out["sides"]["R"]["staging_angle_pass"] and not out["sides"]["L"]["staging_angle_pass"]
print(json.dumps(out,indent=2,sort_keys=True))
