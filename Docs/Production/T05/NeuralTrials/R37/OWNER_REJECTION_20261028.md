# T05 R37 — OWNER REJECTED: visual quality unacceptable

**Owner verdict (2026-10-28):** “That looks horrible.”

**Status: REJECTED. NOT A SHIPPING-ASSET CANDIDATE. NOT APPROVED.**

The three MIT/TripoSR component GLBs in the GitHub Actions artifact for run
[40776105618](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40776105618)
were produced from source-image crops of the raw-meat crate, prepared-food tray,
and saw assembly. Technical GLB export/import success does not imply artistic
success. Do not assemble, promote, retouch, or quietly substitute these meshes
for T05 shipping game art.

## Visible failures

- Meat portions read as amorphous blobs, not individually sculpted reference cuts.
- Saw assembly loses the recessed toothed blade, crisp steel arch, and precise handle construction.
- Wooden crate no longer has recognizably hand-carved joints and timber boards.
- Reconstructed objects have unwanted blobby/melted geometry, incorrect proportions and weak material definition.
- Source crop content contains occlusions and contextual neighboring surfaces; single-view object hallucination does not reliably infer each complete 3D component.

These failures are disqualifying, independently of triangle count or import success.

## Stop rules

1. Do **not** continue optimizing or refining R37 as a base mesh; **do not** promote R34–R37 into `HavenlineGodot/assets/`.
2. Do **not** call successful GitHub Actions runs, silhouette overlap, GLB imports, or Godot captures critic acceptance.
3. Do **not** repeat single-image generative inference on cropped screenshots expecting a source-exact cooker.
4. Keep all three authoritative original renders versioned at `Docs/Art/SourceReferences/T05/`.

## Actual route to T05 completion

Construct a **proper source-matched 3D reconstruction** from the three original image references in Blender, using calibrated multi-view reference boards, explicit rigid component separation, real 3D geometry, source-derived texture projection where appropriate, and careful authored reconstruction only where the reference does not reveal the surface. Preserve the intended front, right, rear arrangements and materials. Use Three.js for quick orbit inspection and native Godot for final viewport proof. Neither a 2D billboard nor a warped single-piece mesh is an acceptable substitute for the requested 3D model.

Use a **high-detail master without the old 12,424 triangle ceiling**; derive LODs later and measure actual Godot scene/phone performance. Compare exact source views at matched camera poses, and require passing independent source-bound visual criticism plus owner approval before shipping. Explicitly assess mechanical saw, structural wood construction, differentiated food forms, snow pillows and overhangs, chimney/smoke, rear panel and side pressure mechanics.

**Current acceptance:** T05 NOT COMPLETE. R37 and previous rejected meshes remain non-shipping evidence.
