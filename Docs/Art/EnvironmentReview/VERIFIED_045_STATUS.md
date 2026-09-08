# Havenline 0.4.5 — verified development build, NOT a release approval

## Exact build and corrective verification
Game source: `22c9a4eba92f57fa5cdef6989575b57640d6b348`.
Tested PR merge: `d7a14dffde8e52b2b5e2dcbe7e6fd75525429f7d`.
Original Actions build: `34159224288`.
Successful corrective verification: `34160345428`.
APK SHA256: `8d77d9061dda984aa0f0e5ec58e17d65ff95867ecfc28da1cd09750261ae7c12`.
Package `com.kaleb.havenline.review`, code405, version `0.4.5-environment-review`.
Verifier correction and actual-render publication commit: `3f8dc7309d5f846f8fe905bea56312b565f38efa`.

The original build exported and signed the APK successfully. Its final checker failed because it still expected404/0.4.4. The corrected strict version guard preserves package isolation, rejects stale/unknown versions and adds six regression cases. The exact unchanged APK was successfully reverified; the original failed report remains in the artifacts. This does not relabel the original failed workflow as successful.

## Implemented work
- Reworked conifer bough/needle geometry and snow pockets; added cabin side windows; refined bark/endgrain materials, wood-rack snow and terrain/path surfaces.
- Retained imported mesh LOD data in the static batching fast path. The matched native3840x2160 opening view submits1,913,981 primitives versus2,758,517 previously, with47 draw calls in both:30.6156% less submitted geometry, NOT a30.6%FPS improvement.
- Added a Camp-menu30-minute frame measurement with live elapsed-time/resolution/scale/FPS readout, warmup/interrupt accounting and JSON output. It measures engine render/submission intervals, not certified display presentation or thermals.
- Preserved all16 original GLBs and the original gameplay contract. Characters2–4 rigging fixes and final reviews remain last. No new NPC models are claimed.

## Verified results
391/391 Godot regression checks passed locally and on GitHub. The exported APK passed13/13base package checks,17/17environment package checks,26/26checker regressions and apksigner signature verification. Fourteen actual Mobile/software-Vulkan views were produced. Native3840x2160 at scale1.0 was captured. Images and source binding are in `captures/provenance.json` and `CURRENT_RENDER_REVIEW.md`.

## Independent critic: received evidence FAILS10/10
Workflow `34159273656` runs a separate Qwen3-VL8B quantized vision model in seven parallel processes. This is one model family, not seven distinct expert models. Original-image hashes, resized-model-input hashes, model revision, runtime and raw outputs are preserved in workflow artifacts.

Snapshot: four of fourteen views have returned valid reports. The other jobs were still running at the last check; no complete14-view certification is claimed.

| Returned view | Lowest dimension |
|---|---:|
|outpost-tree-detail|7.8/10|
|mobile-left|8.0/10|
|mobile-three-quarter|8.0/10|
|outpost-native-4k|8.0/10|

These scores are the model's actual returned opinions, not builder scores or a full-environment final rating. No returned view passes10/10. Confirmed remaining concerns include flat-looking snow surfaces, weak material variation and overly uniform bark. The builder also observed repetitive environment shapes and a relatively empty snowfield. Model assertions about asymmetrical snow, floating or chimney clipping are not accepted as proven geometry errors without corresponding pixel/geometry verification. Raw results are not rewritten to force approval.

## Actual performance evidence — NOT Android60FPS
A separate non-fixed-timestep CI benchmark measured27engine intervals across60.808181seconds at native3840x2160/scale1.0:0.444019FPS on Linux llvmpipe(LLVM20.1.2) software rendering. That is a real software benchmark, not a phone result and not a predictor of physical Android FPS. No player save was accessed.

A named physical Android target, installation/touch/fold testing, sustained presented-frame timing and thermal behavior remain unverified. The completed game's missing NPC/render load is also not represented. Screenshots, counters and software rendering cannot certify native4K/60.

## Release state
Environment10/10: FAILED on received evidence, with full review coverage still incomplete.
Physical sustained native4K/60: UNVERIFIED.
Whole game: INCOMPLETE.
PR4: remain unmerged and unapproved for production.

Highest priority remains the confirmed environment material/composition defects, followed by fresh source-bound render/review and separate physical-device performance verification. Do not lower resolution, round scores up or substitute upscaling. Development signing may not update an earlier installation; do not uninstall a saved game merely to bypass a signing conflict.
