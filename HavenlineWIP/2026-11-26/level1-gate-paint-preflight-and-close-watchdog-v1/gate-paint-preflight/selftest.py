"""Matcher-only disposable fixture: never invokes Godot nor produces native evidence."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
def load(path):
    return json.loads(path.read_text())
with tempfile.TemporaryDirectory(prefix="hvn-gate-18591-validator-fixture-") as loc:
    out=Path(loc)
    for base in ("gate-evidence","functional","frame-evidence","r17-evidence"):
        shutil.copyfile(root/f"control-{base}.json",out/f"{base}.json")
    b=load(out/"frame-evidence.json")
    b["frames"]["paid-first-frame"]["matching_native_buffer_sha256"] = "a"*64
    (out/"frame-evidence.json").write_text(json.dumps(b))
    source=load(out/"gate-evidence.json")["candidate"]["leaves"]
    style={"board":(0,.42),"board_warm":(0,.73),"board_soft":(0,.57),"beam":(1,.70),"brace_back":(1,.58),
           "snow":(2,.50),"metal":(3,.50),"rope":(4,.70),"rope_dark":(4,.34)}
    shader="res://previews/clearance_gate/gate_18591_surface.gdshader"
    def overrides(side):
        return [{"surface":r["index"],"label":r["material"],"family":style[r["material"]][0],"tone":style[r["material"]][1],
                 "shader":shader,"effective":True,"whole_instance_override_or_overlay":False} for r in source[side]["ordered_surfaces"]]
    gates=["gate-south","gate-east"]
    w=["fresh-spawn","paid-first-frame","south-bidirectional","east-bidirectional","writer-v2"]+[f"{g}-{a}" for g in gates for a in (225,450,675)]
    def fixture(labels):
        return [{"label":label,"paint":{g:{"HingeLeft":overrides("left"),"HingeRight":overrides("right")} for g in gates}} for label in labels]
    def log(phase,rows):
        (out/(phase+".log")).write_text("".join("GATE_18591_PAINT_FRAME "+json.dumps(row)+"\n" for row in rows))
    write,cold=fixture(w),fixture(["cold-v2-no-replay"])
    log("cold",cold)
    log("write",write)
    def run():
        return subprocess.run([sys.executable,str(root/"validate_paint.py"),str(out),str(root)],capture_output=True,text=True)
    res=run()
    assert res.returncode==0,res.stderr
    assert json.loads(res.stdout)["per_capture_instance_surface_count"]==156
    for key,bad in [("effective",False),("whole_instance_override_or_overlay",True),("family",13),("tone",.01),("shader","stock")]:
        row=write[3]["paint"]["gate-east"]["HingeRight"][33]
        saved=row[key]
        row[key]=bad
        log("write",write)
        assert run().returncode!=0,key
        row[key]=saved
    write[1]["paint"]["gate-south"]["HingeLeft"].pop()
    log("write",write)
    assert run().returncode!=0,"missing override"
print("PASS matcher accepts valid structure, rejects ineffective/whole-leaf/wrong-family/wrong-tone/wrong-shader/missing; synthetic only")
