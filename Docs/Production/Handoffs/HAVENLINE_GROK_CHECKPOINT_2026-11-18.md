# HAVENLINE — authoritative handoff to Grok
**Audit date:** 2026-11-18 (America/Detroit)  
**Repository:** https://github.com/ksolo21-web/HAVENLINE  
**State:** development only; **NO game release or T05 asset promotion authorized**.

## 1. Git source of truth and exact audit anchors
- Repository is currently **public**. Owner allows game art/source renders to be public during development and plans to make it private at completion. Future private status cannot revoke public copies.
- Default `main`: `0c3625b745d1729121ec13e3e0a267eb3a91e68b` (2026-08-02). GitHub reported `protected=false`; verify any applicable rulesets before changing policies.
- Active Godot integration `codex/havenline-sequential-task-01`: `f74a84a2a288ab3d3935fba7a6cb9b975c2df239` (2026-10-05); **1,502 commits ahead of main**.
- Current T05 working branch `havenline/T05-r18-visual-corrections-20261025`: **pre-handoff head** `b982a2a3339b172b6aaaefac1ae24ecea63307ab` (2026-10-29 13:04 UTC), **401 commits ahead of integration, zero behind**. This handoff commit will advance the branch but does not change game assets.
- Branches: **79 total**: default main (1), open-PR heads (19), branches without open PR (59). Exactly 19 open pull requests observed.
- GitHub Actions artifacts expire: persist accepted source, hashes, failed critic decisions and useful evidence in Git. Do not use a temporary artifact as the single saved copy.
- The active game is `HavenlineGodot/` with Godot **4.7.2**, Android ARM64 review build through `.github/workflows/havenline-godot-android.yml`; historical Unity content stays as source, not the Android build path. GitHub is the canonical development/build platform; free tools and **no new accounts**.

## 2. Full-game progress — separate technical implementation from release approval
See `README.md`, `Docs/AI/HavenlineProjectContext.md`, `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md`, and `HavenlineGodot/data/release-status.json` in the T05 branch.
- Existing simulated/engine-checked capabilities include movement and proximity actions, gathering, delivery, inventory, furnace, rescue, construction/repair, helpers, early wolves/frontier logic, persistence, weather/day/night and adaptive UI checks. Prior internal tests are not end-to-end visual or physical device acceptance.
- The `codex/havenline-sequential-task-01` integration PR #5 describes T01–T10 as approved within that development lineage and T11 as prepared; this is **not** approval of the complete game, its graphics, physical performance or later tasks.
- Missing/unapproved: exact full reference video composition and rendered gameplay loops; original premium dense snowy environment; all author-quality C1–C4 animations and critic evidence; customer, survivor and seven animal-species NPC models (the tracked 13 required NPC slots remain undelivered); full processing/worker loops and production chains; ten connected biomes/transport; Google identity/cloud saves; audio completeness; true Android lifecycle and on-device performance.
- User's mandatory source videos: `Screen_Recording_20260817_124839_YouTube.mp4` and `Screen_Recording_20260817_124510_YouTube.mp4`. The actual footage is authoritative; lock is at `Docs/Design/ReferenceVideoLock/`. Sampled frame audit is not proof of complete motion compliance.
- Original acceptance remains **exact reference-style/observable gameplay fidelity (10/10 on mandatory comparison states)**, independent critics and owner approval. Physical named phone AND tablet sustained native **>=3840×2160 and >=60 presented FPS for >=30 minutes** remains an unpassed release gate. Configurable graphics/FPS presets requested for device range are design requirements, not proof of benchmarked performance.
- Do **not** deliver unfinished development APKs to the owner or ask the owner to be the test device.

## 3. T05 cooker — the active critical-path art blocker
**The standalone saw is promising, not final-approved; all whole-cooker models remain visually rejected.**
Owner's original, exact SHA-verified images are committed under `Docs/Art/SourceReferences/T05/`:
- `32451.jpg` — 1536×1536 original front three-quarter; SHA256 `70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4`.
- `32450.jpg` — 1536×1147 right side; SHA256 `5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719`.
- `32441.png` — 1536×903 rear, JPEG bytes under .png filename; SHA256 `0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510`.

**Preserve:** `Docs/Production/T05/ArtisanMaster/SawWIP/T05_SAW_ARTISAN_MASTER.blend` and `T05_SAW_ARTISAN_MODULE.glb`: source-traced silver arch, **19-tooth saw**, axle, orange handle, **16 meshes / 7,088 triangles**. Owner called gear/blade promising. Do not distort the geometry to fit the housing. Verified preserved source fingerprint is in `Docs/Production/T05/ArtisanMaster/Assembly01/STATUS.json`.
**Reject as modeling foundations:** early R28–R37 improvised/AI-blob meshes; R38 fused projection volume (looks closer only from supported camera poses, fails off-angle); Assembly01 blue box/pallet lumber. The explicit owner rejection is `Docs/Production/T05/ArtisanMaster/Assembly01/OWNER_VISUAL_REJECTION.md`.
**Latest work (2026-10-29):** source-traced frontal shapes with original-image correct coordinate ratio **1536/1280 = 1.2**, physical carved eave, rear service panel with **5 through-slots**, lathed right pressure hardware with **4 physical rods**, isolated original source material samples and untouched original saw meshes. Builder `tools/havenline/task05/build_source_contour_frontage.py` plus `source_carved_eave.py`, `source_rear_service_five_slots.py`, `source_right_pressure.py`. Technical GitHub run [40878589613](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40878589613) **SUCCESS** with unexpired (at audit) unapproved GLB artifact; **no complete source-faithful 3D cooker or independent critic pass**. Preserve any useful trial output in durable Git before artifact expiration, labeled non-shipping.
**T05 remaining:** reference-registered front/side/rear plus off-angle artist-quality geometry; curved blue enclosure truly mounted around intact saw, separately carved load-bearing timber, distinct raw beef cuts and crate (visual left), prepared portions and right tray, textured layered snow/overhangs, open chimney and believable animated plume, correct side crank and rear panel fit. Review each new part in Blender/Three.js then actual Godot with physically credible attachment, not flat projection/boxed geometry. No old 12,424 triangle hard cap; design high-detail master then LOD and on-device performance evidence.

## 4. Latest GitHub CI results: never conflate green job with release
As of October 29 source head:
- [40878589613](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40878589613) T05 original-source 3D frontage **technical SUCCESS; art FAIL**.
- [40878589799](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40878589799) isolated candidate guard **FAIL**: `T05 visual repair authorization does not match exact branch/scope`. Respect fail-closed registry; do not bypass.
- [40878599194](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40878599194) latest full Godot Android build **CANCELLED**; no final APK or game-readiness claim for that run.
- [40878599241](https://github.com/ksolo21-web/HAVENLINE/actions/runs/40878599241) phone/tablet *gate-workflow* **SUCCESS**, but its physical/full-game enforcing step was **SKIPPED** by applicability; not a physical device test.
- T03 repaired visual critic workflow showed a failure in the same push batch; separately review if/when T03 is active.

## 5. Branch cleanup inventory and rules
**Detailed, exhaustive classification (all 79 branches, exact names):** [BRANCH_CLEANUP_AUDIT_2026-11-18.md](BRANCH_CLEANUP_AUDIT_2026-11-18.md).

Summary from GitHub ancestry comparisons:
- 17 non-open-PR branch heads fully contained in retained `codex/havenline-sequential-task-01`.
- 4 more non-open-PR heads fully contained in retained T05 branch (but **not** the integration head).
- 4 redundant branch names among divergent heads can be removed while **one exact-tip twin remains** (1 T03 duplicate + 3 T13/T14 duplicates).
- **34 remaining non-open-PR branches carry unique commits** relative to both retained heads and are **NOT safe to delete blindly**.
- **19 open-PR head branches** and `main` must not be swept away by automatic cleanup.
- Never delete the default branch, the canonical integration branch or the currently working T05 branch before accepted content is secured. No branch was deleted during this audit.

Keep work linear by creating a release-safe, protected `main` after genuine integrated build verification; resolve the existing PR #2 → #4 → #5 integration ancestry and T05 #99 → #100 → #101 stacking *in order*, without merging a failed T05 candidate. Audit unique commits on other branches and consolidate governance PRs #13–19, #88, #92, #103, #105, #106 before closing/removing. Use short-lived feature branches, squash-merge reviewed changes and enable delete-head-after-merge only when historical recovery and reviewers are protected. Owner must approve actual destructive cleanup.

## 6. Dependency-aware next actions / acceptance checklist
1. **Before anything destructive:** create a durable immutable checkpoint/tag of `main`, integration, active T05 and all branches with unique unmerged commits; verify exact HEADs, branch rulesets and PR head references.
2. Review `Docs/Production/T05/ArtisanMaster/SawWIP/`, lock geometry hashes and exact three owner images; use those actual files, not a synthetic generated view.
3. Artist-model curved blue shoulder and timber sculpt as genuinely separate 3D parts with reference camera registration; perform native front/right/rear plus two off-angle inspection. Correct any failure before adding food, snow and motion. Do not reuse rejected box housing.
4. Once source fidelity passes internally, obtain genuinely independent C1/C2 visual review and owner approval at exact source standard. Mark missing evidence FAIL/UNTESTED, not a passing average.
5. Integrate accepted cooker into `HavenlineGodot/` only after visual acceptance, verify real gameplay and full scene, then build graphics presets/LODs and physical Android phone/tablet thermal and FPS evidence.
6. Reconcile fail-closed candidate registration with integration owner **legitimately** before PR promotion. Finish blocked gameplay/characters/world requirements; production release stays locked.
7. Triage open PRs and 34 unique branches, preserve unique work, then delete only verified redundant refs and update the branch map. Never force-push or auto-merge to conceal failed critic checks.

**Checkpoint verdict:** Source facts and tech CI verified; **T05 visual critic FAIL, full game NOT COMPLETE, physical release UNTESTED.** This document is a handoff, not evidence of a new art-model approval.
