"""Pinned carry-lane archaeology and one reversible offline structure comparison."""
from pathlib import Path
import ast, hashlib, json, re, sys
import numpy as np

here=Path(__file__).resolve().parent
baseline=Path(sys.argv[1])
witness=Path(sys.argv[2])
packet=Path(sys.argv[3])
assert hashlib.sha256(witness.read_bytes()).hexdigest()=="4177456c7ef5cef10c62c851ccd3a2d59429f968aa7d27b70a3f1b10e30d1208"
for line in (here/"SOURCE-GIT-LOCK.txt").read_text().splitlines():
    digest,local,_=line.split()
    payload=(packet/local).read_bytes()
    assert hashlib.sha1(f"blob {len(payload)}\0".encode()+payload).hexdigest()==digest,local

def src(name): return (packet/name).read_text()
old=src("historical-carry.gd"); main=src("historical-main.gd")
current=(baseline/"wood_stock_view.gd").read_text()
opening=(baseline/"previews/integrated_opening.gd").read_text()
layout=json.loads((baseline/"layout.json").read_text())
q=json.loads(src("hold.json"))
base=next(line for line in src("historical-native.txt").splitlines() if line.startswith("EXAM_SUPPORT_INPUT "))
carry_hist=json.loads(base.split(" ",1)[1])
assert "request_dispatched\":false" in src("historical-native.txt")
assert "float(nonzero.size() - 1) * CARRY_LANE_GAP" in old and "var cursor := -total_width * 0.5" in old
assert "lane_centers := carry_lane_centers(nonzero)" in old
assert "stack.position = Vector3(0, .65, -.42)" in main
assert "xyz(sim.position) + Vector3(0,1.0,-.35)" in main
assert "transfer_feedback.transfer(kind,origin,target" in main
assert "payload: Node3D" in current and "TechnicalWoodBundleRepresentative" in current
assert "wood_stock_view.install(hero_visual)" in opening
assert "red column stays with the avatar" in src("counter-reference.md")
assert "not an on-screen release from the blue character's back" in src("rear-reference.md")
neighbor_gap=float(re.search(r"CARRY_LANE_GAP := ([0-9.]+)",old)[1])
tier_gap=float(re.search(r"CARRY_TIER_GAP := ([0-9.]+)",old)[1])
width_section=re.search(r"const AUTHORED_SCALED_WIDTH := \{([^}]+)",old)[1]
width={k:float(v) for k,v in re.findall(r'"([a-z]+)": ([0-9.]+)',width_section)}
initial_left=-(width["wood"]+width["stone"]+neighbor_gap)/2
historic_stone=initial_left+width["wood"]+neighbor_gap+width["stone"]/2
basis=np.asarray(carry_hist["mount"][1:]).T
assert np.max(abs(basis.T@basis-np.eye(3)))<6e-6
f=np.asarray(carry_hist["camera"][3])
native_camera_in_actor_space=np.linalg.solve(basis,f)
depart=[]
for p in carry_hist["plan"]:
    w0=np.asarray(p["key"][0]); w1=np.asarray(p["key"][1])
    assert np.max(abs(w0-p["source"][0]))<1e-8 and np.max(abs(np.asarray(p["source"][1:]).T-basis))<1e-9
    delta=np.linalg.solve(basis,w1-w0)
    assert delta[0]<-.939 and max(abs(delta[1:]))<5e-7
    depart.append(delta.round(9).tolist())

# Load only prior source-pinned decoder/math defs; no prior candidate or midpoint test is executed.
module=ast.parse(witness.read_text())
defs=[i for i in module.body if isinstance(i,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.FunctionDef))]
env={"__file__":str(witness),"ROOT":baseline}
exec(compile(ast.Module(body=defs,type_ignores=[]),str(witness),"exec"),env)
eye,ortho,size,height=env["check_source"]()
assert height==layout["actor_height"] and height==1.75
geom=env["GLB"](baseline/"assets/characters/Character1.glb")
skin,d=geom.triangles(skin=True)
unposed,_=geom.triangles()
b=env["bounds"](unposed); center=b.mean(axis=0);center[1]=b[0,1]
hero=(skin-center)*height/(b[1,1]-b[0,1])
assert len(hero)==96001 and d<.0002
actual_crown,_=env["GLB"](baseline/"assets/studio/starter_ground_wood_lod.glb").triangles("Pickup LOD - Crown log")
assert len(actual_crown)==1300
b=env["bounds"](actual_crown)
B=3.522754*(actual_crown-b.mean(axis=0))
e=env["bounds"](B)
assert np.allclose(e[1]-e[0],q["full_size_B_geometry_extents_m"],rtol=0,atol=1e-9)
native=np.asarray(carry_hist["body_padded_m"])
err=float(carry_hist["needle_m"])
pad=float(carry_hist["pad_m"][0])
tested=env["bounds"](hero)
rest_box=tested+np.array([-1,1])[:,None]*pad
# Counterfactual one-side rail: whole geometry on the wood side, with exact gap
# from both evidenced padded rear planes. Opposite half is not an actual second row.
outer_x=-neighbor_gap/2
rail_back_max=min(native[0,2],rest_box[0,2])-err*2
old_box=np.array(q["unchanged_stock_fit_bounds_m"])
rail_y=old_box.mean(axis=0)[1]
dy=e[1,1]-e[0,1]+tier_gap
anchor=np.array([outer_x-e[1,0],rail_y,rail_back_max-e[1,2]])
logs=[B+anchor+[0,j*dy,0] for j in (-1,0,1)]
boxes=[env["bounds"](g) for g in logs]
stack=env["bounds"](np.concatenate(logs))
gaps=[float(boxes[j+1][0,1]-boxes[j][1,1]) for j in (0,1)]
rest_z=float(rest_box[0,2]-stack[1,2]);native_z=float(native[0,2]-stack[1,2])
assert all(z>0 for z in gaps) and rest_z>err and native_z>err
assert stack[1,0]<0
spawn=env["one_camera"](hero,logs,eye,ortho,size)
near_angular=env["one_camera"](hero,logs,native_camera_in_actor_space,ortho,size)
# A pure negative-X translation strictly preserves pair tier and rear-body separation
# at this frozen pose; test full geometry for the one historical launch direction.
for delta in depart:
    end=stack+np.array([delta[0],0.,0.])
    assert end[1,0]<stack[1,0] and abs(end[1,2]-stack[1,2])<1e-12
# Compare projected actor baseline bounds and carry growth, not physical mount acceptability.
def screen_true_extent(T,n):
    z=np.array(n,float); z/=np.linalg.norm(z)
    x=np.cross([0,1,0],z);x/=np.linalg.norm(x)
    y=np.cross(z,x)
    uv=T@np.array([x,y]).T*size[1]/ortho
    return np.ptp(uv.reshape(-1,2),axis=0).tolist()
report={
  "class":"OFFLINE COUNTERFACTUAL HOLD",
  "source_commits":{"legacy_original_comparison":"2032b87895e8df7cdc953430e1ba1ca41d74bd40","starter":"11c14a1c41971067c7dc97db69375f720a408f68"},
  "historical_T08":{"required_stone_shift_to_recenter_without_wood_m":-historic_stone,
                    "old_stone_carried_center_with_wood_x_m":historic_stone,"old_stone_center_alone_x_m":0,
                    "horizontal_lane_gap_m":neighbor_gap,"vertical_tier_gap_m":tier_gap,
                    "actor_mount_translation_m":[0,.65,-.42],"old_world_relative_effect_start_m":[0,1,-.35],
                    "exact_frozen_second_row_transform_in_current_level1":None},
  "native_historical_launch":{"pair_exact_actor_local_first_leg_delta_m":depart,"dispatched":False,
                              "one_different_postpaid_route_only":True,
                              "padded_cpu_skin_plus_capsule_box_m":native.tolist()},
  "reference":{"counter_event":"One brown column launches while adjacent red stays fixed. Frames 793–822. No dimensions, facing-side sign or usable silhouettes beyond that visible segment.",
               "rear_event":"Exterior flight to low receiver. Frames 969–977 establish path/landing, not release from the player."},
  "side_rail_probe":{"actual_old_rest_and_historical_cpu_pad_boxes_are_not_interchanged":True,
                     "third_role_is_geometrically_clear_in_this_free_space_only":True,"centered_exact_actor_relative_rail_anchor_m":anchor.tolist(),
                     "box_m":stack.tolist(),"tier_gap_m":gaps,"min_lateral_overhang_past_rest_hero_m":float(tested[0,0]-stack[0,0]),
                     "behind_rest_padded_box_m":rest_z,"behind_historical_native_padded_box_m":native_z,
                     "entire_positive_x_half_left_untouched":True,
                     "positive_half_is_not_contract_for_other_row":True,
                     "no_physical_mount_structure_authored":True,
                     "normal_camera_sample_centers":spawn,"historical_near_camera_angle_on_rest_only":near_angular,
                     "normal_camera_hero_bbox_px":screen_true_extent(hero,eye),
                     "normal_camera_hero_and_stack_bbox_px":screen_true_extent(np.concatenate([hero,*logs]),eye)},
  "limits":["Frozen sampled bind mesh and separate historical native pose bound, not a moving actor proof.",
            "Analytic straight negative-X launch remains geometrically rearward for fixed transforms only; not approved first-leg spacing or a real receiver trajectory.",
            "Reference and historical two-side patterns do not determine the exact reserved opposite row, mount hardware, actual moving clearances, camera legibility, or acceptance."]}
print(json.dumps(report,sort_keys=True,indent=2))
