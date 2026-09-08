# HAVENLINE Agent Instructions

## Required starting point

Read `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md` and `Docs/Production/task-gates.json` FIRST, then `Docs/AI/HavenlineProjectContext.md`, `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md`, its source manifest, and the actual reference pixels. Inspect the current source and evidence for newer work. `Docs/AI/UnityProjectContext.md` is historical.

## Latest user instruction: one task at a time

Only the active task may be implemented. All subsequent tasks stay LOCKED until the active task's frozen-scope checks AND independent critics pass. The intermediate task minimum is **9.0/10 in EVERY mandatory dimension**, with **10/10 as the target**. This supersedes earlier exact-10 instructions for intermediate task progression only; the final full-game release gate remains separate and unchanged. Never retrospectively promote an old failure.

Use the sequence BUILD -> TEST -> ACTUAL CAPTURES -> INDEPENDENT CRITICS -> FIX -> FRESH EVIDENCE -> REVIEW. Two separately executed review roles are required: reference fidelity and technical/visual integrity. Disclose shared model families; two processes are not two diverse expert models. Builder self-review, code tests, geometry counts, saved agent definitions and successful workflow execution are not independent visual approval.

No averaging, rounding, missing-area exclusion, unchanged rescoring to obtain a desired number, invented scores or unresolved mandatory defects. Missing, invalid, truncated, low-confidence or incomplete required evidence blocks progression. Verify model observations against actual pixels/geometry; preserve raw unsupported observations and genuine failures rather than blindly adopting or deleting them.

Freeze each task's scope and evidence before scoring. A tree-only pass cannot approve terrain, buildings, gameplay or release. Later tasks remain mandatory, not waived. A regression reopens the earlier task and locks progression until repaired. Infrastructure and validation needed for the active task are allowed; unrelated next-task implementation is not.

Work through genuine failures: diagnose, preserve working checkpoints, change approach when justified, and continue within the active task. Do not replace building with repeated planning. Save exact source/asset/capture hashes, tests, reviewer results, unresolved defects and the next executable action.

## Visible progress

Show an explicit progress bar in COMMENTARY BEFORE substantial tools, then update at verified milestones DURING execution. Include current stage, completed/total count, latest verified result and next step/blocker. A final-answer-only bar fails the requirement. Separate active-task iteration progress from approved tasks and whole-game completion. No time-based fake percentage, native-widget claim or unscheduled background-work promise.

## Preserve the actual project

- Active Android project: `HavenlineGodot/`, Godot 4.7.2. Unity was explicitly retired. No Unity installation, license, runtime, build step or IL2CPP path is allowed. Preserve historical files outside the active build.
- Preserve all original character/model identities, geometry, skinning, textures, saves and validated fixes. Never silently revert to an older character checkpoint.
- C1 and C2 are selectable leads; the unselected lead is a helper alongside C3 and C4. Unlimited logical carrying and movement/proximity gathering, fighting, rescue, deposit, build and repair remain required. No manual-action-button substitute.
- **C2–C4 rigging fixes and final rig reviews stay LAST at the final character stage, not waived.** Require actual rendered full animation cycles, transitions, skinning, clipping, feet/knees, equipment and gameplay-scale evidence. Import or GLB inspection alone is not rig approval.
- Customers are a separate reusable pool of two male/two female bases with individual persistent identities. Additional male/female survivors and animal companions are not copies replacing the custom crew.
- Missing authored NPCs cannot become invisible working actors or primitive stand-ins. Keep readiness explicit in `data/npc-catalog.json`.
- Animals are exactly dogs, lions, tigers, bears, wolves, owls and foxes. No domestic cats. Use the seven registered expedition-style animal references. Images are not rigged models. Legacy cat saves migrate to foxes without losing identity/recruitment/assignment/rescue progress; restart safety remains required.
- Preserve explicit historical progression and save contracts; record conflicts with newer reference requirements rather than silently rewriting distinct actions or prices.

## Both reference videos are authoritative

The recordings ending `124839` and `124510` are the observable visual and gameplay standard, not loose inspiration. Inspect actual source pixels and motion. A filenames-only or builder-summary-only comparison is UNREVIEWED.

Both loops remain required: fishing/food production/customer service/reinvestment, AND harvesting/hunting/camp supply/weapon upgrades/defenses. Match bright sculpted winter scenery, dense blue-white forest, warm cleared work zones, fences, machinery, tall moving resource/cash stacks, crowds, helpers, ground pads and paid visible transformations. A generic cabin/furnace clearing is not the target. Preserve old shelter assets without forcing the old two-cabin composition. More realistic bark/noise or polygons is not inherently closer to the reference. No primitive-looking blockout or unfinished/default/debug materials may be passed as final art.

Environment/reference correction remains the priority, following the ordered tasks. The full scope also retains the ten connected biomes, transportation, weather/day/night, sound, Google identity/cloud and complete production/progression systems. Configuration and plans are not implementation.

## Phones, tablets and release remain separate mandatory gates

Shipping gameplay is landscape, automatically adapting to phones AND tablets, including applicable foldable transitions. Verify safe areas, camera scale, readable text, touch controls, menus, resizing, lifecycle and saved-state continuity; do not add a manual device selector or stretch the world.

Require native internal width >=3840 AND height >=2160, render scale 1.0, with sustained >=60 FPS on named representative physical phones AND tablets under completed-game load for at least 30 minutes. Preserve presentation timing, resolution and thermal evidence. Neither an emulator/software renderer, 4K screenshot, fixed-step capture nor engine counter certifies physical presentation/thermals. Never silently lower resolution, count upscaling as native4K, or generalize one device to all hardware. Protect rendering workload during earlier tasks; repeat final measurements after all content and character fixes.

**Kaleb must not receive unfinished APKs or be asked to test or benchmark them.** Internal isolated-package builds may continue. Final delivery requires complete functionality, reference fidelity, final independent approval, no placeholder art, full motion review, save/auth/cloud correctness and physical phone/tablet 4K60 evidence. Missing test access is a blocker to solve, not work reassigned to Kaleb.

Read `Docs/QA/PHONE_TABLET_RELEASE_CONTRACT.md` and run `tools/havenline/release_gate.py` for final delivery. That evidence validator is neither an AI critic, a connected device lab nor a branch-protection change. Task-specific reviews do not replace full-state/motion reference comparison or the final release gate.
