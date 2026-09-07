# 0.4.5 environment refinement — development candidate

The requested target is 10/10 environment quality plus sustained native 4K/60.
Neither is certified by this implementation. The previous source's independent
8B critic reported visible material/lighting defects and sub-10 scores.

## Implemented

- Replace broad oval foliage with 645 closed narrow sprays on 43 irregular boughs
  per conifer, preserving three silhouettes and opaque Mobile-compatible cutaway.
- Preserve imported ArrayMesh LOD data and shadow meshes when compiling the
  single-mesh authored assets; retain the prior multi-mesh batching fallback.
- Add actual framed side windows to shelters, stronger wood/bark normal detail,
  concentric cut-log end grain and a fitted rounded-rectangular rack snow blanket.
- Add smooth ground-contact snowbank profiles and shallow compacted path shoulders.
  Actor, prop and terrain heights still use the same function.
- Remove grid-like thawed-ground noise artifacts, rebalance ambient daylight and
  daytime furnace light, and explicitly match shadow-filter quality on Android.
- Add Camp > Measure native 4K frame timing, with live on-screen progress,
  30-second warm-up, 30-minute measured target, saved JSON, interruption tracking,
  average/P99 timings and explicit non-certification of presentation/thermals.
- Add a separate wall-clock render benchmark that rejects --fixed-fps and
  headless/no-render execution; review captures are not benchmarks.

## Preservation

Original character/world GLBs are unchanged. Original opening progression,
movement-only proximity actions, unlimited logical carrying and the original
18-wood/6-stone first furnace upgrade remain. No missing NPC can work invisibly.
No domestic cats; approved animal roster is unchanged.

## Required next review

Run the regression suite, asset audit, actual Mobile multi-angle/day/night/blizzard
captures, native 4K capture, and an independent source-bound visual review.
Record failures instead of inflating scores. The software renderer can compare
workload and validate the measurement path, not certify a named Android device.
Physical device model, display presentation, thermals and completed-game load
remain unverified. This branch must not be merged as visually/performance approved.
