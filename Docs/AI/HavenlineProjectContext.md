# HAVENLINE current project context

## Latest required starting point

Read `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md` and its `reference-video-sources.json`. Kaleb supplied the recordings ending `124839` and `124510` and explicitly required the game to be EXACTLY like them. The lock records inspected timestamps, both gameplay loops, observed art/camera/interface characteristics, known current-build mismatches and the mandatory comparison states. Actual reference pixels are required for review; prose alone is not enough.

The 0.4.5 candidate's sparse cabin/furnace clearing is not the target. Correct the dense blue-white stylized forest framing, warm fenced work areas, lake/fishing and food production, animated tall resource/cash stacks, busy customer queues, helpers, marked paid upgrades, harvesting/hunting and functioning defenses. Preserve earlier assets and source as work/history rather than treating them as the approved composition. The old requirement to show both shelters in the normal shot is superseded.

This reference audit changes instructions and evidence tooling, not game runtime, and grants no new critic score or performance approval. Environment correction remains the first production priority; integrate the visible gameplay needed for faithful in-use comparison. Unrelated expansions must not displace it.

## Engine and project provenance

User direction, 2026-09-07: continue from GitHub, build the complete Android game without Unity, preserve the original premium stylized 3D game, reject primitive art, require native 4K/60 or better.

The active native project is `HavenlineGodot/`. The baseline branch is `codex/havenline-godot-android`; environment/refinement work is on `codex/havenline-environment-review` in unmerged PR #4. The native lineage was based on `agent/havenline-production-art-gate` (`7cee199`). Historical Unity source is retained for provenance and excluded from the Godot build; no Unity tool or license is needed.

The historical gameplay source was recovered from `ksolo21-web/Hummer`, branch `havenline-unity-reference-rebuild`, commit `1ba652af21f4c06229aa94ed2ab1c48f94c9b094`. Its contract 1.3.1 remains verbatim in `data/reference-contract.json`. Engine-specific historical fields are provenance, not active build configuration. `HistoricalGameplayLock.md` records the original design; its Unity-only statements are superseded by the explicit engine change.

## Preserve explicit project-specific requirements

Landscape play, oblique/orthographic-style camera, C1/C2 selectable leads with the other lead plus C3/C4 active, unlimited logical inventory and automatically gather/fight/rescue/deposit/build/repair by proximity; no manual action-button substitute. Recompose portrait reference layouts for automatic phone and tablet landscape presentation without stretching or losing readable world/actor proportions.

Historical progression rules remain recorded: furnace L2 at 18 wood AND 6 stone; warmth 4.5 to 8; 2.2-second rescue; north barricade at 8 wood AND 3 stone; wave gated on those three prerequisites, first delay 48 seconds and three wolves. The original rescued survivor is additional to the custom crew. The earlier external reference was https://youtube.com/shorts/JicjHsoUj68. These earlier rules cannot justify omitting either newly required uploaded-video loop or forcing the wrong opening/layout. Keep distinct actions distinct, record conflicts explicitly, preserve old saves, and never silently rewrite the historical contract or invent unshown prices/timing.

Character1 uses the exact supplied `Character-Rig-Fixed-1.glb`. Characters2–4 use recovered V7 staging files with identities/hashes documented in historical context. They remain candidates, not approved production assets. Preserve geometry, skinning, UVs and textures. Import/render validation is not whole-rig, locomotion, action-animation or clipping approval. C2–C4 rigging fixes and final review remain LAST, not waived.

Customers are reusable male/female bases with persistent individual identities, separate from additional male/female survivors and custom playable companions. Approved animal companions are dogs, lions, tigers, bears, wolves, owls and foxes; no domestic cats. Use the supplied expedition-style animal references. Do not substitute missing authored models with invisible working actors or primitive stand-ins.

Production scope also includes additional helper jobs, processing chains, persistent connected biomes (frozen, forest, desert, underwater, sky, volcanic, swamp, ruins, underground, alien), vehicles/connectors, weather/day/night and verified Google identity/cloud saves. Configuration or plans do not constitute feature completion.

## Release and user handoff

The required reference/visual score is exactly 10/10 for every mandatory dimension/state with complete independent evidence and no known mandatory defects. Preserve raw failures. No average, rounding, unchanged rescore, unavailable view, code-only review or builder self-review can manufacture approval.

Automatic phone AND tablet behavior is required: layout, safe areas, touch, camera, text, saves and lifecycle, including relevant fold transitions. Native internal >=3840x2160 at scale 1.0 and sustained >=60 FPS needs named physical phone AND tablet full-load evidence over at least 30 minutes each, with presented-frame timing, resolution and thermal data. Software screenshots, fixed-timestep captures, emulators and engine labels are not certification. Do not lower resolution to pass or generalize one device result to all Android hardware.

Kaleb explicitly does NOT want to test unfinished builds. Do not send another development APK or ask him to run a benchmark before full functionality, reference fidelity, independent critics, no-placeholder art and physical phone/tablet performance gates pass. Internal isolated-package builds remain permitted. Missing test access is an honest blocker, not a testing task transferred to Kaleb.

Release also requires complete motion/rig review, production features, Android lifecycle, authentication/cloud and save integrity. Environment approval alone is not whole-game approval. Show truthful progress bars in commentary BEFORE substantial work and at verified milestones during execution, not only in the final response.


## Verified adaptive-device implementation and delivery check

Read `Docs/QA/PHONE_TABLET_RELEASE_CONTRACT.md` and run `tools/havenline/release_gate.py`. Automatic layout checks are not physical-device approval. No unfinished APKs or player-run benchmarks; development builds remain internal. Preserve the newer reference-video lock, its full motion/state comparisons, all original gameplay and C2-C4 final rig work deferred until last. The delivery validator is supplementary to, not a replacement for, the reference-video acceptance protocol.
