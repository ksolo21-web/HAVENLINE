# Active V5 purchase-pad typography-only study — visual HOLD

Exact isolated candidate from 11c14a1c41971067c7dc97db69375f720a408f68 and root witness seal f62ddaddca3699c7c455650a00bb977808c8ce41221cb59a8cd609abb1f6ae43. The patch changes only Action pixel_size .0037 → .0047 and Cost .0032 → .0050 in pad_v5_view.gd. Label text, original fallback font/size/outline, deck positions and tilt, .80 m fitted pad, asset data, materials, camera, action states, trigger reach, three-wood cost, payment, hide-on-commit and any test-only staging or saving API are unmodified. Patch applied and reversed in scratch; exact original/patched blob identifiers accompany it. No changes to the playable checkout or repository.

The evidence reads native root font advance and line metrics at 30 font px and clips a conservative centered box (advance/full line + documented 12 px default outline and 2 additional font px margin on every side) against all 256 actual coplanar top deck triangles. GDScript still relies on the original Godot outline property. The margin is a modeling allowance, not native pixel coverage or guarantee of actual glyph bounds. Each proposed box is fully covered by those triangles, neither touches the corner-inlay AABB, no overlap area, positive modeled separation 4.415 mm in world space. Smallest passing increments in 0.0001 scale steps relative to illustrative projected first-atlas-box milestones: BUILD 2.0 logical px, 3 WOOD 2.1. These are deliberately a geometry experiment target, not a readability threshold, a visual score or a gate. Current scales are negative controls for those milestones.

At nominal 1280x720 root view, modeled price advance goes 8.29 → 12.95 logical px and its first glyph atlas rectangle projects 1.37 → 2.14 logical px along the label's tilted up axis. The BUILD line goes 7.07 → 8.98 px advance and 1.58 → 2.01 px along the same kind of axis. Both improvised doubled-scale labels overlap by the modeled boxes (5.59 cm overlap depth in world space). Enlarging only cost to .018 leaves 68.9% deck coverage and reaches inlay space; both rejected controls are stricter-fit diagnostics, not shipped alternatives.

    python3 fit.py /path/to/exact/local/checkout /path/to/root/witness > reproduced.json
    cmp result.json reproduced.json
    sha256sum -c SHA256SUMS

Next independent test: use native glyph geometry or actual screenshot comparisons for both labels under identical camera/asset settings; check line fit, straight south approach with player occlusion plus unoccluded control, unfunded and first funded gameplay phase, configured phone viewport/filter behavior, and no-cost/HUD/interaction changes. The 2.14 px atlas estimate is still a serious readability limit; no headless engine, renderer, phone, payment rerun or occlusion experiment in this packet.

[Godot Label3D property defaults](https://docs.godotengine.org/en/stable/classes/class_label3d.html#class-label3d-property-outline-size)
