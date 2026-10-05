#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageStat

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="t08-final-visual")
    ap.add_argument("--candidate",required=True)
    args=ap.parse_args()
    root=Path(args.root)
    audit=json.loads((root/"primitive-audit.json").read_text())
    assert audit.get("passed") is True and audit.get("finding_count")==0,audit
    probe=json.loads((root/"video-probe.json").read_text())
    stream=probe["streams"][0]
    assert int(stream["width"])>=3840 and int(stream["height"])>=2160,stream
    num,den=map(int,stream["avg_frame_rate"].split("/"))
    fps=num/den
    duration=float(probe["format"]["duration"])
    assert fps>=59.9,(fps,stream)
    assert duration>=3.0,duration
    stills=[]
    for path in sorted((root/"stills").glob("*.png")):
        image=Image.open(path).convert("RGB")
        assert image.size[0]>=3840 and image.size[1]>=2160,(path,image.size)
        assert max(ImageStat.Stat(image).stddev)>=8.0,path
        stills.append({"path":str(path),"width":image.size[0],"height":image.size[1],"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(stills)>=4,len(stills)
    video=root/"T08-final-visual-4k60.mp4"
    manifest={
      "schema_version":1,"task_id":"T08","candidate_sha":args.candidate,
      "source_bound":True,"primitive_audit_passed":True,"primitive_findings_count":0,
      "stills":stills,"stills_count":len(stills),
      "motion_video":str(video),"motion_video_sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
      "motion_video_seconds":duration,"internal_resolution":[int(stream["width"]),int(stream["height"])],
      "capture_fps":fps,"physical_device_native_4k60_certified":False,
      "user_visual_approval":False,"effective_approval":False,"ready_for_user_visual_review":True
    }
    (root/"review-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":
    main()
