"""Read only exact git objects and sealed measurements; write JSON to stdout."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess

PIN = "11c14a1c41971067c7dc97db69375f720a408f68"
GLBS = {
    "back_representative": "assets/studio/wood_bundle_v3.glb",
    "loose_pickup": "assets/studio/starter_ground_wood_lod.glb",
    "character": "assets/characters/Character1.glb",
}
FILES = [
    "wood_stock_view.gd", "starter_ground_wood_view.gd", "opening.gd",
    "previews/integrated_opening.gd", "layout.json", "resources/typed_receiver.gd",
    "tests/test_wood_stock_view.gd", "tests/test_starter_ground_wood_view.gd",
    "docs/LOOSE_WOOD_RENDER_VERIFICATION.md",
]
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(repo, *args):
    return subprocess.check_output(["git", "-C", repo, *args])

def source(repo, entry):
    spec = f"{PIN}:HavenlineLevel1/{entry}"
    raw = git(repo, "show", spec)
    return raw, {"path":"HavenlineLevel1/"+entry,
                 "git_blob":git(repo,"rev-parse",spec).decode().strip(),
                 "sha256":sha(raw), "bytes":len(raw)}

def load_glb(raw):
    magic, ver, total, json_len, jmark = struct.unpack_from("<4sIII4s", raw)
    assert (magic, ver, total, jmark) == (b"glTF", 2, len(raw), b"JSON")
    body_at = 20 + json_len
    size, kind = struct.unpack_from("<I4s",raw,body_at)
    assert kind == b"BIN\x00" and size == len(raw)-(body_at+8)
    gltf = json.loads(raw[20:body_at])
    assert not gltf.get("extensionsRequired") and len(gltf["buffers"]) == 1
    return gltf, memoryview(raw)[body_at+8:]

def union(boxes):
    return [[fn(box[k][axis] for box in boxes) for axis in range(3)]
             for (k, fn) in [(0,min),(1,max)]]

def span(box):
    return [box[1][i]-box[0][i] for i in range(3)]

def bounds(g, buf, index):
    ac=g["accessors"][index]
    assert ac["type"]=="VEC3" and ac["componentType"]==5126 and not ac.get("sparse")
    view=g["bufferViews"][ac["bufferView"]]
    assert view["buffer"]==0
    begin, stride=view.get("byteOffset",0)+ac.get("byteOffset",0),view.get("byteStride",12)
    out=union([[p,p] for p in (struct.unpack_from("<3f",buf,begin+i*stride) for i in range(ac["count"]))])
    assert all(abs(out[a][i]-ac[key][i])<1e-6 for a,key in [(0,"min"),(1,"max")] for i in range(3))
    return out

def report_asset(role, raw):
    g,buf=load_glb(raw)
    node_order=[]
    def walk(i, parent):
        n=g["nodes"][i]
        path=parent+[i]
        node_order.append(path)
        for c in n.get("children",[]):
            walk(c,path)
    for i in g["scenes"][g.get("scene",0)]["nodes"]:
        walk(i,[])
    out=[]
    for path in node_order:
        i=path[-1]
        n=g["nodes"][i]
        if "mesh" not in n:
            continue
        # Strictly limited to these exact mesh paths, where only trivial transforms occur.
        offsets=[]
        for link in path:
            o=g["nodes"][link]
            assert "matrix" not in o and o.get("scale",[1,1,1])==[1,1,1] and o.get("rotation",[0,0,0,1])==[0,0,0,1]
            offsets.append(o.get("translation",[0,0,0]))
        offset=[sum(o[k] for o in offsets) for k in range(3)]
        if role != "character":
            assert offset == [0,0,0] and path == [i]
        mr=g["meshes"][n["mesh"]]
        parts=[]
        for p in mr["primitives"]:
            assert p.get("mode",4)==4
            idx=p["indices"]
            tri,rem=divmod(g["accessors"][idx]["count"],3)
            assert rem==0
            pos=p["attributes"]["POSITION"]
            b=bounds(g,buf,pos)
            parts.append({"material":g["materials"][p["material"]]["name"],
                          "xyz": [[q[k]+offset[k] for k in range(3)] for q in b],
                          "triangles":tri,"position_records":g["accessors"][pos]["count"]})
        node_box=union([p["xyz"] for p in parts])
        out.append({"node_id":i,"node_path":path,"name":n.get("name"),"mesh_name":mr.get("name"),"scene_translation":offset,
                     "xyz":node_box,"extents_m":span(node_box),"surfaces":parts})
    box=union([n["xyz"] for n in out])
    anchors=[{"node_id":i,"name":n.get("name"),"extras":n.get("extras")}
             for i,n in enumerate(g["nodes"]) if re.search("carry|pack|socket|marker|inventory|stock|receiver|landing",n.get("name",""),re.I) or "extras" in n]
    return {"nodes_in_scene":len(node_order),"mesh_nodes":out,"bound_xyz":box,"extents_m":span(box),
             "animations":[a.get("name") for a in g.get("animations",[])],
             "skin_count":len(g.get("skins",[])),
             "triangles":sum(p["triangles"] for n in out for p in n["surfaces"]),
             "potential_explicit_carry_receive_names_or_node_extras":anchors}

def describe(repo, lip):
    assert git(repo,"rev-parse",PIN).decode().strip()==PIN
    assets, files, texts={}, {}, {}
    for role, path in GLBS.items():
        raw, identity=source(repo,path)
        assets[role]={"identity":identity,**report_asset(role,raw)}
    for path in FILES:
        raw, files[path]=source(repo,path)
        texts[path]=raw.decode()
    assert texts["wood_stock_view.gd"].count("Wood.instantiate()") == 1
    assert 'var back := measured_actor.position.z - CLEARANCE' in texts["wood_stock_view.gd"]
    match=re.search(r"const CAP := Vector3\(([^)]+)\)",texts["wood_stock_view.gd"])
    cap=[float(n) for n in match.group(1).split(",")]
    clearance=float(re.search(r"const CLEARANCE := ([.0-9]+)",texts["wood_stock_view.gd"]).group(1))
    layout=json.loads(texts["layout.json"])
    actor=assets["character"]; actor_height=layout["actor_height"]
    actor_scale=actor_height/max(.01,actor["extents_m"][1])
    unfit=assets["back_representative"]
    wood_scale=min(cap[k]/unfit["extents_m"][k] for k in range(3))
    back_z=-actor["extents_m"][2]*actor_scale*.5-clearance
    fit_pos=[0,actor_height*.68,back_z-unfit["extents_m"][2]*wood_scale*.5]
    fit_extents=[wood_scale*s for s in unfit["extents_m"]]
    assert "func sync_progress_visuals()" in texts["opening.gd"] and "wood_stock_view.reflect_stock(int(ledger.stock.wood))" in texts["opening.gd"]
    references={}
    for p, terms in {
        "wood_stock_view.gd":["func install","candidate.scale","candidate.position","func reflect_stock","payload.visible"],
        "starter_ground_wood_view.gd":["const ExactLod","func _ready","add_child"],
        "opening.gd":["func model", "func fund_opening_receiver","func _collect_wood_source","func sync_progress_visuals", "marker.visible ="],
        "previews/integrated_opening.gd":["const CAMP_SHIFT","func point","hero_visual := model", "actor.add_child(wood_stock_view)", "piece.position = point","wood_visuals[row.id] = piece"],
        "resources/typed_receiver.gd":["Opt-in transfer planning","func project_rows","func plan_transfer"],
    }.items():
        references[p]={term:[i+1 for i,l in enumerate(texts[p].splitlines()) if term in l] for term in terms}
    tree=git(repo,"ls-tree","-r","--name-only",PIN,"HavenlineLevel1").decode().splitlines()
    summary=lip.read_bytes()
    assert sha(summary)=="003830845e656ba700745dd73ea5e951f7f21e7e72460397c9a91dcd8b45ce33"
    lip_contents=json.loads(summary)
    return {"status":"HOLD_REAL_TRANSFER_PRESENTATION_AUTHORING",
        "base_commit":PIN,"scripts":files,"source_line_index":references,
        "pinned_project_scene_paths":[x for x in tree if x.endswith(".tscn")],
        "pinned_project_glb_paths":[x for x in tree if x.endswith(".glb")],
        "geometry":assets,
        "existing_mounts_bind_geometry_derived_not_a_native_pose":{
          "actor_scale":actor_scale,"actor_height_m":actor_height,"physical_capsule_radius_m":layout["actor_radius"],
          "actor_bind_box_extents_m":[v*actor_scale for v in actor["extents_m"]],
          "actor_build_bundle_scale":wood_scale,"carry_representative_effective_extents_m":fit_extents,
          "carry_representative_center_actor_local_m":fit_pos,"carry_back_clearance_m":clearance,
          "ledger_link":"one visibility-only whole bundle plus count while wood > 0, not one mesh per unit",
          "default_ground_anchor_xz_m":{v["id"]:v["xz"] for v in layout["wood_nodes"] if v["id"]!="wood-a"},
          "integrated_ground_anchor_xz_m":{v["id"]:[v["xz"][0]-3.25,v["xz"][1]+5.8] for v in layout["wood_nodes"] if v["id"]!="wood-a"},
          "integrated_ground_y":"accepted terrain sampling, not recomputed or invented",
          "loose_pickup_runtime_local_scale":1.0,
          "source_visual_log_components":"each actual whole object contains three distinct baked-in log components, plus lashing/tails",
        },
        "counter_measurement_role":{
           "summary_sha256":sha(summary),"native_study_manifest_sha256":"7bd474cebcd6a0c4779b80b6476675ca92df65b9c4d5fbee86c3d3760da55d7d",
           "wood_lip_measured_footprint_m":[0.05,0.05],
           "inboard_point_m":lip_contents["sides"]["inboard"]["actual_board_rest"]["point"],
           "outboard_point_m":lip_contents["sides"]["outboard"]["actual_board_rest"]["point"],
           "independent_of_gameplay":"unbound geometry only; not authored destination or real handoff"},
        "isolated_52_endpoint_role":{"step_m":0.035,"nominal_center_span_placeholder_xyz_m":[0.245,0.210,0.0],
                    "rest_cannot_be_certified":"no accepted discrete piece pose/pivot/orientation nor exact receiving footprint. Neither whole bundle fits even one measured lip square in its existing orientation/scale. No rescale, transform changes, or projection of the fixture through game."}
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("local_git_checkout")
    parser.add_argument("sealed_counter_lip_summary",type=Path)
    args=parser.parse_args()
    print(json.dumps(describe(args.local_git_checkout,args.sealed_counter_lip_summary),indent=2,sort_keys=True))
