import itertools, json, subprocess, sys
from pathlib import Path
def git(*a):
    return subprocess.check_output(["git","-C",sys.argv[1],*a],text=True).strip()
opening="11c14a1c41971067c7dc97db69375f720a408f68"
audit={}
def source(sha,path,*tokens):
    text=git("show", f"{sha}:{path}")
    assert all(t in text for t in tokens),path
    audit[f"{sha}:{path}"]=git("rev-parse",f"{sha}:{path}")
    return text
p="HavenlineLevel1/"
source(opening,p+"previews/integrated_opening.gd","resource_tree.build(CONIFERS[0], true)")
source(opening,p+"opening.gd","if resource_tree.regrows and resource_tree.starter_credit_seen:","resource_tree.mark_credited()\n\t\telse:\n\t\t\t_collect_wood_source(ResourceTreeScript.TREE_ID)","marker.visible = row.id not in ledger.collected")
source(opening,p+"opening_ledger.gd",'const COST := {"wood": 3}','const KNOWN_WOOD := ["wood-a", "wood-b", "wood-c"]',"source in collected","stock.wood += 1","stock.wood -= COST.wood","var remaining := verified.size()","remaining -= int(COST.wood)")
source(opening,p+"resource_tree.gd","const REGROW_SECONDS := 5.0","starter_credit_seen = true","func _regrow() -> void:")
test=source(opening,p+"tests/test_integrated_tree_regrowth.gd","fall_and_regrow(1)","repeat tree cuts cannot pay for the camp")
assert test.count("await fall_and_regrow(1)") == 2
sim="HavenlineGodot/scripts/simulation.gd"
for t,k in [("07","integrated_source"),("08","integrated_source"),("09","candidate_commit")]:
    doc=json.loads(source(opening,f"Docs/Production/T{t}/verified-completion.json"))
    source(doc[k],sim,"if resource.respawn >= 90:","resource.units -= 1","inventory[resource.kind] += 1")
    source(opening,f"Docs/Production/T{t}/FROZEN_SCOPE.md")
assert len({v for k,v in audit.items() if k.endswith(sim)})==1
# Exhaustive arithmetic model of the quoted v1 restore invariant; not a Godot run.
cases=[(n,n-3) for n in range(4) if n-3>=0]
assert cases==[(3,0)]
print(json.dumps({"commit_blobs":audit,"paid_restore_feasible_unique_sources_and_stock":cases,"native_rerun":False},indent=2))
