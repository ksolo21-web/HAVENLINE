"""Validate post-draw images against actual frozen checkpoint authority and pixel hashes."""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import sys

d=Path(sys.argv[1])
expected={
    "fresh-spawn": (0,0,False,False,False),
    "paid-first-frame": (0,0,True,False,False),
    "south-bidirectional": (0,0,True,True,False),
    "east-bidirectional": (0,0,True,True,True),
    "writer-v2": (1,1,True,True,True),
    "cold-v2-no-replay": (1,1,True,False,False),
}
warn="WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver."
out={}
vsync_count={}
projective_trace={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
for role, names in (("write",list(expected)[:-1]),("cold",[list(expected)[-1]])):
    raw=(d/(role+".log")).read_bytes(); text=raw.decode()
    issues=[l for l in text.splitlines() if re.search(r"ERROR:|WARNING:|Parse Error|^FAIL|^DRAW_REJECT",l,re.I)]
    assert all(l==warn for l in issues) and len(issues)<=1
    gpu=re.findall(r"^OpenGL .* - Compatibility - Using Device: Mesa - llvmpipe .+$",text,re.M)
    assert len(gpu)==1
    rows=[json.loads(z) for z in re.findall(r"^L1_POST_DRAW (.+)$",text,re.M)]
    assert [r["phase"] for r in rows]==names
    checkpoint_rows=[json.loads(z) for z in re.findall(r"^L1_COMBINED_CHECKPOINT (.+)$",text,re.M)]
    for r in rows:
        tag=r["phase"]
        assert r["display"]=="X11" and r["image_px"]==r["viewport_px"]==[1280,720] and r["camera_ortho"]==13.0
        same=["stock","renewals","paid","camp_visible","pad_hidden","hearth_center_paid","south_open","east_open"]
        assert all(r["queued"][k]==r["draw"][k] for k in same)
        state=r["draw"]
        assert state["physics_frames"]-r["queued"]["physics_frames"] in (0,1)
        key=("stock","renewals","paid","south_open","east_open")
        assert tuple(state[k] for k in key)==expected[tag]
        assert state["hearth_center_paid"] and state["camp_visible"] is state["paid"] and state["pad_hidden"] is state["paid"]
        assert all(math.isfinite(v) for v in state["actor"]+state["offset"])
        cp=next(x for x in checkpoint_rows if x["phase"]==tag)
        assert cp["tick"]==r["queued"]["tick"] and (cp["published_wood"],cp["renewals"],cp["paid"])==expected[tag][:3]
        path=d/(tag+".png"); v=path.read_bytes()
        assert v[:8]==b"\x89PNG\r\n\x1a\n" and v[16:24]==bytes.fromhex("00000500000002d0")
        rgba=subprocess.check_output(["ffmpeg","-nostdin","-v","error","-i",str(path),"-pix_fmt","rgba","-f","rawvideo","-"])
        n=len({rgba[j:j+3] for j in range(0,len(rgba),4)})
        assert len(rgba)==1280*720*4 and n>=64
        rgb=subprocess.check_output(["ffmpeg","-nostdin","-v","error","-i",str(path),"-pix_fmt","rgb24","-f","rawvideo","-"])
        digest=sha(rgba)
        assert r["pixel_sha256"] in (digest,sha(rgb)) and len(rgb)==1280*720*3
        out[tag]={"png_sha256":sha(v),"matching_native_buffer_sha256":r["pixel_sha256"],"colors_at_least":n,
            "queued_tick":r["queued"]["tick"],"draw_queue_physics_delta":state["physics_frames"]-r["queued"]["physics_frames"],
            "wood":state["stock"],"renewals":state["renewals"],"paid":state["paid"],"south_open":state["south_open"],"east_open":state["east_open"]}
    vsync_count[role]=len(issues)
    projective_trace[role]={"graphical_raw_log_sha256":sha(raw),"backend_report":gpu[0]}
assert {p.stem for p in d.glob("*.png")}==set(expected)
assert len({v["matching_native_buffer_sha256"] for v in out.values()})==len(expected)
print(json.dumps({"actual_desktop_stock_camera_post_draw":True,"x11_software_llvmpipe_only":True,
    "image_px":[1280,720],"observed_existing_vsync_driver_warnings":vsync_count,
    "not_a_phone_render_graphics_quality_approval_or_performance_claim":True,
    "route_driver_physically_unchanged":True,"frames":out,"trace":projective_trace},sort_keys=True,indent=2))
