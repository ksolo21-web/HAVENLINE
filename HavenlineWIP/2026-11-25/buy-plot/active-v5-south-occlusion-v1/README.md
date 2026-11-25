# Active Level 1 V5 purchase-pad south occlusion

**Do not accept the typography-only trial as the south-approach fix.** Keep it as unoccluded-size evidence; no new gameplay, camera, pad or label changes are proposed here. This compares actual active V5 native line quads and glyph metric reports from independent trial ec46068… (local evidence seal d2e15b83…), not V6 graphics. V6's existing route log contributes only two grounded south actor transforms and one height sample; no V6 quads, screenshots or price positions enter the comparison.

Borrowed exact no-render 11c Character 1 CPU skinning: 96,001 native posed triangles from the 66-joint inboard counter stance, original idle 1.255624 s. The mesh is reused by translating its feet and changing only world yaw to match the measured 1.602 m and .901 m stations. The .720 m 3D boundary is a synthetic local-height interpolation using .901/1.101 m samples and held .901 yaw; it is not a captured V5 pose, an active walk pose, proof of approach continuity, or observation that a funded label is visible once committed. Stock visuals are not in the hero mesh. This finite result covers one physically plausible borrowed idle pose, not the full approach pose envelope.

Source orthographic ray is fixed at 7:11:11. Clip indexed occluder triangles to camera-side of each target plane and intersect exact projected union with each native line quad and a separable modeled 14-font-pixel support guard. Checking positive and negative normals separately produced the same results at these stations (winding sensitivity control, not material testing). This is geometric support, not ink or measured alpha/contrast; glyph atlas sizes indicate only logical-pixel extent, not exact placement or glyph bits.

| South station | Price native quad covered, original → trial | Price guard covered, original → trial |
|---|---:|---:|
| 1.602 m (clear hero control) | 0% → 0% | 0% → 0% |
| .901 m (borrowed idle at observed route coordinates) | 98.36% → 86.06% | 89.50% → 73.12% |
| .720 m (synthetic boundary) | 100% → 100% | 100% → 100% |

At .901 m action native quad is untouched in both; at synthetic .720 m both action native quads fully covered, guards 99.90% / 96.22%. The price's first-glyph atlas-height metric at unoccluded 1.602 m remains 1.37→2.14 logical px with longer text. Partial uncovered support cannot say which marks survive or whether they can be read. Even the larger trial gives no visible price support at the synthetic boundary under this pose; don't treat font scaling alone as resolving player occlusion. Exact V5 route-bound visual recording across prepay and funded-at-entry states plus a truly clear control remains the appropriate acceptance evidence. No device/visual pass.

Replay: `python audit.py EXACT_GIT_CHECKOUT EXACT_CPU_INBOARD_SURFACE_JSON` from fresh sibling directory with sealed label/route evidence available. NumPy and libgeos_c required. Only derived metrics, no raw geometry/input asset/screenshots, native engine, render, remote write or spend.
