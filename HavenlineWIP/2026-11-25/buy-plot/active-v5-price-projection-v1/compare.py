"""Cross-check independently sourced projection and summarize baseline sizing."""
import json, math, sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
s=json.loads((p/"result.json").read_text()); a=json.loads((p/"native.json").read_text())
assert a["viewport"]==s["source_inputs"]["viewport"]==[1280,720]
assert a["proj"]==a["keep"]==1 and a["cam_size"]==s["source_inputs"]["camera_height_span"]
r={}
for k, data in a["label"].items():
    label=s["labels"][k]; x,y=[v/30 for v in data["px_axis_x_for_30"]],[v/30 for v in data["px_axis_y_for_30"]]
    assert data["font_size"]==30 and data["fallback_font"]=="Open Sans SemiBold"
    assert math.isclose(data["bounds_m_height"],s["source_inputs"]["fitted_dims_m"][1],abs_tol=1e-6)
    assert math.isclose(data["label_m_above_anchor"],s["source_inputs"]["label_y_m_above_anchor"],abs_tol=1e-6)
    assert math.isclose(math.hypot(*x),math.hypot(*label["one_font_px_x_to_screen_xy"]),abs_tol=2e-6)
    assert math.isclose(math.hypot(*y),math.hypot(*label["one_font_px_line_vertical_to_screen_xy"]),abs_tol=2e-6)
    assert len(data["glyph_texture_metrics"])==len(data["text"].replace(" ",""))
    r[k]={"text":data["text"],"whole_line_advance_px":data["string_metrics"][0]*math.hypot(*x),
          "max_glyph_atlas_height_in_local_text_direction_px":max(g["size"][1] for g in data["glyph_texture_metrics"])*math.hypot(*y),
          "world_line_advance_m":data["string_metrics"][0]*label["world_per_font_pixel_m"]}
    if k=="Cost":
        zero=data["glyph_texture_metrics"][0]; assert zero["character"]=="3"; w,h=zero["size"]
        r[k]["first_glyph_atlas_box_projected_aabb_px"]=[w*abs(x[j])+h*abs(y[j]) for j in (0,1)]
print(json.dumps(r,sort_keys=True,indent=2))
