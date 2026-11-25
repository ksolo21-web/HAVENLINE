# Character 1 exact-source anatomical digit specimen: HOLD

This is a deliberately rejected detached, static, source-space pose specimen for a right thumb articulation step, not a playable feature, approved pose, animation export, or grip test pass. It uses the exact held 52-joint lineage, original 512-facet axe, fixed observed chest frame, and sealed right pressure surface. It does not substitute the 66-joint PR108 or its clip, move either assigned shaft station, or prescribe permitted angle or slide/roll gameplay limits.

## What this specimen measures
- Independently replays the v2 weight-repair source recipe from the pinned original indexed bind/weights. The source records 11,714 changed indexed rows. The reconstructed v2 ad hoc ancestry matters: **thumb.02 has weight on four frozen right-palm seam vertices**, even though the original pre-repair matrix showed none. The rooted .02 branch cannot be moved as-is under the fixed seam rule. The tip .03 uses none of the frozen seam, cuff edge endpoints, named web aliases/join points, or newly reauthored palm rows. Fingertip and surrounding weights are not modified.
- Derives signed axes for the actual thumb.02 and thumb.03 along with control index.02/middle.02 from low/high projected quantile section centroids on exact indexed bind and held rows. Unique physical samples are counted once per section. Noncollinear point registration from pure-weight rows is preferred. For joints lacking pure rows, the exact static authored shoulders/forearm/wrist are the only changed source transforms; frozen hand inheritance is confirmed using actual dominant bind/held paired rows and a tight held no-op control. The palmar sign is anchored on nearby actual held source vertices around the recorded right palm vertex; the 28 incident triangle normals face the shaft (median cosine .9871) and are not inferred from label names. Helix sign is formed from section tangent cross projected palm/opposition direction, never fixed local X.
- Parses the pinned skeleton's bind pivots rather than using a point-picked new joint. One +3° **diagnostic sample** is authored in the actual signed thumb.03 basis. This is neither a gameplay limit nor a closure sweep. Dual-quaternion deformation on chosen affected source rows compares against all actual frozen held rows before applying the candidate-relative delta. On 140 actual distal source samples the signed specimen moves palmward a median of +2.207 mm; reversing its axis moves them −2.228 mm. All unaffected original positions are retained byte-for-byte. The regenerated held positions are hashed in the result; raw geometry and asset exports are not included.
- Checks the actual shaft's finite triangles against all affected source faces (unchanged unrelated faces can stay held); exact old set size 206 recovers preceding right off-band evidence. Comparing the selected pose shows 206 strict pairs again, 42 removed and 42 new. The original queried distal vertices inside the solid increase from 149 to 151. Neither number is a penetration-depth report. The new palm coating, custom local seam, weight assignments, original axe remain unchanged. The same grip is still invalid; no remaining geometry/renderer/native/gameplay gate is claimed.

## Next engineering choice
Do not use this sample or iterate arbitrary thumb angles. The palmward movement is real but is closing an already enclosed thumb. An open-to-approach anatomical posture or a newly joined, appropriately placed thumb base may be needed. Start by independently locating which signed thumb motion/control can represent entry from outside the full solid while retaining the exact cuff, pressure seam, hand profile, both finite original grip bands, and source identity. A new author cannot approve slide/roll or define permitted contact arbitrarily. Untouched left/other stages, actual right bearing, independent skin and dynamic/authored animation/raster review are still mandatory.

## Reproduce
Run inside this output directory adjacent to the pinned dependencies. Requires Python with NumPy, SciPy and Pillow as in the prior original-GLB evidence utility.

```sh
bash run.sh /path/to/exact/held_owner.npz > replay.json
cmp replay.json result.json
sha256sum -c SHA256SUMS
```

The result is a bounded authoring diagnostic only. No GLB, blend, engine, native clip, renderer, source payload, remote modification, spending, or playable change was produced.
