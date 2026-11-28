# Havenline T07 beta repair

The reviewed runtime is `42c8d275d2d72a46094e48930fe38d83ee61868e` on the T07 beta branch. Codex made the patch and `gameplay_review` independently reviewed the source, gameplay controls, camp reveal and forest finish. [Runtime changes](https://github.com/ksolo21-web/HAVENLINE/commit/42c8d275d2d72a46094e48930fe38d83ee61868e)

## Verified repairs

- Moving over the camp plot keeps the indicator white and blocks payment. Stopping turns it green before the first parcel flies. Moving away preserves the paid amount. Returning completes the purchase once.
- The mounted compass directs the truck to the garage. Dismounting restores the pedestrian route. The truck tests cover center-blade contact on a tree, mining bank and wolf, recovery at a gate corner, full docking with the throttle held, and a closed shutter without entering the camp behind the garage.
- In the off-site camp test, the survivor fed two workshops, stocked the counter, banked proceeds from eight sales, repaired a gate and paid for an authorized conveyor. The player stayed outside the camp radius.
- The camp reveal hides all four legacy gate markers. The pine-bank finish softens the cyan bands while retaining the original Havenline textures and meshes. The corrected HUD fixture now accounts for sold meals in the current market ledger.

## Evidence

The separate review replay contains 183 consecutive engine frames at 3840×2160 and 60 fps over 3.05 seconds. All seven runtime checks passed. The still set includes a two-times zoom capture taken through the normal pinch controls.

The source audit scanned 203 text files and found zero forbidden shipping primitives or materials. All 13 regression suites, 20 native control assertions, 44 HUD assertions and 44 truck assertions passed. The viewport captures include standard touch entry through the south gate, with opening and camp views across phone, cover, unfolded and tablet layouts.

The sampled headless routes completed 900 consecutive simulation ticks at 2.920 to 3.698 ms p95. The observed camp layouts reached 584 draw calls and 849,782 primitives. Those measurements describe the cloud runner and the exercised routes. Physical-device certification was waived for this beta.

The locked A and B clips show when the plot indicates readiness, when materials start to transfer, and how the camp reveals. B also shows the pale, distinctly separated pine tiers used for the whole-frame comparison. [Locked A and B clips](https://github.com/ksolo21-web/HAVENLINE/tree/9617201b63318b6f9292a140cbe7eb79560a4b39/Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/Locked-sequences) · [Original A16 and B06 frames](https://github.com/ksolo21-web/HAVENLINE/tree/f55128d744d3ac610dc6667673c9d040770a9da2/Docs/Production/T05/ReferenceFrames)

GitHub built the exact runtime and completed the 4K replay in run 46146893415. The run retains the Linux review pack, runtime and export hashes, off-site test, gameplay trace, stills and movie. [GitHub build and replay artifact](https://github.com/ksolo21-web/HAVENLINE/actions/runs/46146893415/artifacts/15264472970)

## Open review

The exact 10/10 gate remains open. The shared pine canopies still have rounder, joined tiers in the full scene. The complete C6 performance and C11 accessibility review and the owner's visual signoff remain pending. The source and gameplay results above apply to the current beta candidate. [Current acceptance standard](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/REFERENCE_ACCEPTANCE_STANDARD.md) · [Hosted build and replay](https://github.com/ksolo21-web/HAVENLINE/actions/runs/46146893415)
