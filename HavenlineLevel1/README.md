# Havenline Level 1 replacement

**Branch checkpoint: source and reviewed furnace purchase behavior. Not a release or the full Level 1 playtest.** This project lives separately from `HavenlineGodot/` during replacement work. Nothing in the canonical project is deleted, and no workflow or default branch is changed by this checkpoint.

Base: `codex/havenline-sequential-task-01` at `f74a84a2a288ab3d3935fba7a6cb9b975c2df239`. The opening source is the independently retested V8-derived strict wood repair. It preserves the 3-wood price, rejects an inactive or unbound furnace pad without taking wood, and preserves the receipt across a clean restart. Independent scoped checks: 29 writer, 3 cold-reader, 10 adverse/eligibility, and 7 scripted movement/input checks. No live rendered or device pass, typed fish transfer, customer, enemy, or Level 2 unlock claim.

## Asset status

The seven source-identical character and pine files are present as existing Git blobs. The four exact studio GLBs listed below are needed to reproduce the original candidate, and are tracked by digest. Do not substitute older models or claim this checkpoint runs as the exact candidate until they are present and verified.

```text
35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a  assets/studio/hearth_trial_02.glb
d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb  assets/studio/purchase_pad_v5.glb
31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554  assets/studio/starter_ground_wood_lod.glb
1004ea2f41751bf79ad10ab0165c60a05e5ee581d35095913a0794f16931abd9  assets/studio/wood_bundle_v3.glb
```

## Next integration slice

Keep the approved river and forest. Use the revised camp as the single active camp in this separate Level 1 project. Preserve the old project and original assets. First resolve the terrain bank and floor-height seam; then test both gates through ordinary input, fishing access, and loaded return routes on the exact integrated build. Do not enable a second camp ledger, a second fence network, or paths painted over exterior snow. Keep later tasks and the default branch untouched until independently verified in scope.
