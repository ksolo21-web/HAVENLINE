"""Audit conservation, progression, travel and crossings from the recorded 60 Hz play."""
import collections
import json
import math
import sys
from pathlib import Path

run = Path(sys.argv[1])
prerequisites = {
    "center_hearth": [], "expansion_1": ["center_hearth"],
    "storage_wood": ["expansion_1"], "storage_stone": ["expansion_1"], "storage_meat": ["expansion_1"],
    "expansion_2": ["storage_wood", "storage_stone", "storage_meat"],
    "watchtower": ["expansion_2"], "orbit_upgrade": ["expansion_2"],
}
events = json.loads((run / "world-events-complete.json").read_text())
counts = collections.Counter(e["event"] for e in events)
landings, crossings, visits = {}, [], {}
maximum_travel = 0.0
largest_stamp_sample = collections.Counter()
wolf_ids, boss_ids, cells = set(), set(), set()
active_in_camp, enemies_in_camp, paid_before_sanctuary = [], [], None
previous, last = None, None
phases = {}
source_counts = collections.Counter()

with (run / "observations.jsonl").open() as fp:
    for index, line in enumerate(fp):
        r = json.loads(line)
        f = r["field"]
        assert r["tick"] == index and r["same_camera"] and not f["save_blocked"], (index, r["stage"])
        phases.setdefault(r["stage"], index / 60)
        if index == 0:
            assert not f["build_order"] and sum(f["carried"].values()) == 0 and sum(f["stored"].values()) == 0
        counts_by_token = f.get("unique_token_counts", {})
        if not counts_by_token:
            counts_by_token = collections.Counter(f["collected"].values())
        for kind in f["carried"]:
            spent = sum(receipt.get(kind, 0) for receipt in f["paid"].values())
            assert counts_by_token.get(kind, 0) == f["carried"][kind] + f["stored"][kind] + spent, (index, kind)
        for order_index, offer in enumerate(f["build_order"]):
            assert set(prerequisites[offer]) <= set(f["build_order"][:order_index])
            assert f["paid"][offer] == f["costs"][offer]
            landings.setdefault(offer, index / 60)
        for wolf in f["wolves"]:
            wolf_ids.add(wolf[0])
            if wolf[1]: boss_ids.add(wolf[0])
            x,z = wolf[4][0], wolf[4][2]
            xmin,zmin,xmax,zmax = f["perimeter"]
            if r["camp_visible"] and xmin < x < xmax and zmin < z < zmax:
                enemies_in_camp.append([index, wolf[0], x, z])
        if f.get("inside") and f.get("orbit_active"):
            active_in_camp.append(index)
        cells.add(tuple(f.get("terrain_cell", [])))
        if f.get("stamp_tick") == index:
            largest_stamp_sample |= collections.Counter(f["stamp_sample"])
        maximum_travel = max(maximum_travel, math.hypot(r["pos"][0],r["pos"][2]))
        if r["stage"] == "Follow the south side to the reserved bay" and math.dist([r["pos"][0],r["pos"][2]],[5.5,3.2]) < .4:
            visits["reserved_southeast"] = index / 60
        if previous:
            a=previous
            if a["camp_visible"] and r["camp_visible"] and a["field"]["perimeter"]==f["perimeter"]:
                for gate,axis,other in [("gate-south",2,0),("gate-east",0,2)]:
                    center=f["gate_centers"][gate]
                    x0=a["pos"][axis]-center[axis];x1=r["pos"][axis]-center[axis]
                    if (x0 > 0) == (x1 > 0): continue
                    frac = -x0 / (x1-x0)
                    offset = a["pos"][other]+frac*(r["pos"][other]-a["pos"][other])-center[other]
                    if abs(offset)>1.1: continue
                    assert next(g["open"] for g in r["gates"] if g["id"]==gate), (index,gate)
                    crossings.append({"gate":gate,"stage":f.get("stage_number"),"direction":"out" if x1>x0 else "in","simulation_s":round((index-1+frac)/60,3),"center_offset_m":round(offset,3),"from_orbit_active":a["field"].get("orbit_active"),"to_orbit_active":f.get("orbit_active"),"from_visible_heads":a["field"].get("visible_heads"),"to_visible_heads":f.get("visible_heads")})
        previous=r;last=r
assert last and set(last["field"]["build_order"])==set(prerequisites)
assert counts["purchase"]==8 and counts["tower_fire"]>=1 and counts["tower_hit"]>=1 and last["field"]["tool_count"]==3
assert set((c["gate"],c["direction"]) for c in crossings)=={(g,d) for g in ["gate-south","gate-east"] for d in ["in","out"]}
assert counts["regrow_wood"]>=1 and counts["regrow_stone"]>=1 and counts["defeat"]>=1 and counts["impact_wood"]>=3 and counts["impact_stone"]>=3
assert max(last["field"]["stored"].values())>0 and all(counts["deposit_"+k]>0 for k in ("wood","stone","meat"))
assert maximum_travel>=98 and visits.get("reserved_southeast")
assert not active_in_camp,active_in_camp[:8]
assert not enemies_in_camp,enemies_in_camp[:8]
assert largest_stamp_sample["boots"]>0 and largest_stamp_sample["paws"]>0 and largest_stamp_sample["inside"]==0,largest_stamp_sample
receipt={"physics_hz":60,"physics_frames":last["tick"]+1,"route_seconds":round(last["tick"]/60,3),"same_normal_camera_all_ticks":True,"all_tokens_conserved_every_tick":True,"purchases":landings,"resources_spent":{k:counts["spend_"+k] for k in ("wood","stone","meat")},"final_carried":last["field"]["carried"],"final_stored":last["field"]["stored"],"final_paid":last["field"]["paid"],"crossings":crossings,"reserved_corner":visits,"farthest_m":round(maximum_travel,2),"streamed_actor_cells":sorted(cells),"world_events":dict(counts),"natural_wolf_ids":sorted(wolf_ids),"natural_boss_ids":sorted(boss_ids),"stamp_sample_peaks":dict(largest_stamp_sample),"inside_orbit_violations":len(active_in_camp),"inside_wolf_centers":len(enemies_in_camp),"phase_starts_s":phases}
(run/"route-result.json").write_text(json.dumps(receipt,indent=2)+"\n")
print("PASS",receipt["route_seconds"],"seconds,",len(crossings),"open gate crossings,",receipt["farthest_m"],"m excursion")
