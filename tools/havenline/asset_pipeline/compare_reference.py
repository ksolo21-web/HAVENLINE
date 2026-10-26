#!/usr/bin/env python3
"""Source-bound visual evidence helper, NOT an AI judge and NEVER an approval.

Compare an original owner render to a native Godot screenshot. No automatic
resize / alignment is allowed to claim exact pixel-level fidelity: sizes,
angles, source SHA and capture kind are disclosed in the JSON report.
"""
import argparse,hashlib,json,pathlib,sys
from PIL import Image,ImageChops,ImageDraw,ImageEnhance,ImageOps,ImageStat

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def preview(im,size=(640,640)):
    image=ImageOps.contain(im.convert("RGB"),size,Image.Resampling.LANCZOS)
    page=Image.new("RGB",size,(24,35,51))
    page.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2))
    return page

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",required=True)
    p.add_argument("--native",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--asset-id",required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--native-scene",choices=("actual_shipping","isolated_import"),required=True)
    p.add_argument("--reference-sha256",required=True)
    a=p.parse_args()
    folder=pathlib.Path(a.out)
    folder.mkdir(parents=True,exist_ok=True)
    if sha(a.reference)!=a.reference_sha256:raise SystemExit("Owner image SHA mismatch. Refusing wrong reference.")
    if len(a.source_sha)!=40 or any(c not in "0123456789abcdef" for c in a.source_sha.lower()):
        raise SystemExit("A real 40-character source commit SHA is required")
    with Image.open(a.reference) as x, Image.open(a.native) as y:
        original_dims=x.size
        native_dims=y.size
        left,right=preview(x),preview(y)
    canvas=Image.new("RGB",(1280,700),(20,29,42))
    canvas.paste(left,(0,45));canvas.paste(right,(640,45))
    draw=ImageDraw.Draw(canvas)
    draw.text((16,15),"Owner reference: original pixels are authority",fill="white")
    draw.text((656,15),"Godot "+a.native_scene.replace("_"," ")+": candidate",fill="white")
    draw.text((15,660),"Comparative contact sheet. Framing normalized ONLY FOR DISPLAY; no visual approval.",fill=(220,225,230))
    canvas.save(folder/"reference_vs_native.png")
    overlay=Image.blend(left,right,.5);overlay.save(folder/"unaligned_overlay.png")
    difference=ImageChops.difference(left,right)
    ImageEnhance.Contrast(difference).enhance(3).save(folder/"unaligned_difference.png")
    stats=ImageStat.Stat(difference).mean
    report={
        "schema_version":1,"asset_id":a.asset_id,
        "candidate_source_commit":a.source_sha,"reference_sha256":sha(a.reference),
        "native_png_sha256":sha(a.native),
        "reference_dimensions":list(original_dims),"native_dimensions":list(native_dims),
        "capture_kind":a.native_scene,"reference_pixels_reviewed_by_human":False,
        "independent_critic_run":False,"style_fidelity_score":None,
        "owner_approval":False,"pass":False,
        "unaligned_display_only_rgb_difference":list(stats),
        "caveat":"The difference is not a reliable fidelity score: camera, framing, lighting and scale may differ. Always visually review source images."
    }
    (folder/"comparison_evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
