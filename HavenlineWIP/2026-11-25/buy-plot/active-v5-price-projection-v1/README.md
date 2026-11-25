# Level 1: active V5 purchase-pad text projection
**HOLD for visual readability**, not a judgment of the exact pad art. This diagnostic targets the opt-in playable replacement preview pinned to `11c14a1c41971067c7dc97db69375f720a408f68` and its active V5 studio pad, not the detached V6 price-symbol tests or the legacy default scene.

An independent source calculation reads the six real pad surfaces from the pinned GLB, reconstructs the runtime wrapper's scale and seat, and projects the existing Label3D basis. A detached Godot 4.7.2 headless run instantiates the unmodified preview in a 1280×720 SubViewport and reports actual camera projections for both labels and the actual engine fallback font/glyph metrics. The fit and scale agree across both methods. `native.json` is the native readout only; the final run had no runtime diagnostics. An initial cache replay had missing OBJ import sidecars, fixed before the final readout. No source model, video, private profile, or imported cache is included.

At the authored fixed view the **3 WOOD** line advances roughly **8.29 logical px** end-to-end. The rectangle of the first font-atlas glyph projects to an approximately **2.03 × 1.41 logical px** display-axis box; the atlas glyph height projects to **1.37 logical px** along the text's tilted up direction. These are geometric dimensions (font-atlas rectangles may contain padding), not a measurement of lit pixels or the rendered text/outline after filtering. The physical 0.80 m pad footprint, 3-wood rule and access radius did not change. This establishes a text-size risk *even before placing the hero in the line of sight*. It does not prove a particular native raster is unreadable, device scaling, or Character 1 occlusion on V5. Merely reading the price on V6 from another approach does not answer this V5 problem.

Next candidate: the smallest detached presentation-only text scale/contrast trial on this exact V5 asset. Keep text on its authored deck and do not add a floating/HUD duplicate; preserve pay reach, timing, prices, pad pose, camera and hide-on-commit. Check positive unoccluded control and exact ordinary straight-south approach with Character 1 present, including unfunded and first funded states; use matching actual frames at normal and supported phone view before assigning an art score. No candidate trial, camera change, player movement, payment, final art or app store approval is claimed in this package.

```sh
python probe.py /path/to/repo > rebuilt-source.json
cmp rebuilt-source.json result.json
python compare.py > rebuilt-metrics.json
cmp rebuilt-metrics.json metrics.json
sha256sum -c SHA256SUMS
```

For native reproduction, take an isolated exact checkout, hydrate its studio assets with its existing tool, import the original assets with Godot 4.7.2 under a fresh disposable profile, copy `native_probe.gd` to `HavenlineLevel1/tests/v5_price_probe.gd` in that disposable project, then run `godot --headless --fixed-fps 60 --path HavenlineLevel1 --script res://tests/v5_price_probe.gd`. Check zero diagnostics and extract the single `V5_PRICE` JSON line. The probe neither grants camp nor writes a user save.
