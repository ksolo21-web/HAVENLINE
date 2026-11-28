# Build and continue Havenline

## Current owner additions — November 28, 2026

Read the [pet combos, navigation map and automatic screen-fit requirements](Docs/Production/PET_COMBOS_MAP_DISPLAY.md) and [21-row contract](Docs/Production/PET_COMBOS_MAP_DISPLAY.json) before older orientation/count-specific directions. Every one of the seven pets needs a fitting automatic attack combo and retains its useful specialty. A minimap must expand into a useful larger map. Game/UI layout must adapt to the actual phone window, portrait and landscape, cutouts/insets and live fold/resize changes. **This owner instruction supersedes the former landscape-only restriction for new work.** Historical receipts retain their original scope.

The addendum preserves the current **10 worlds × 50 local levels**, World 1 first, and multiple useful pets/survivors. It maps the added requirements to existing tasks and records implementation/evidence as unverified. It changes no gameplay source/owner, task activation, dependency graph, assets or workflow. Existing packet/checker automation has not yet been wired to this addendum; old landscape-only checks cannot certify these features. See the addendum for exact precedence, source identities and next implementation steps.

## Current final acceptance

[Reference acceptance standard](Docs/Production/REFERENCE_ACCEPTANCE_STANDARD.md) · [Machine-readable policy](Docs/Production/REFERENCE_ACCEPTANCE_POLICY.json). Final reference-sensitive dimensions require at least **9.9** individually; the existing mandatory visual **exact-10** rules remain stronger. **9.5 is an interim checkpoint for reference-sensitive work.** Complete independent evidence, every mandatory check and zero known unapproved deviations are required. Historical receipts and the dated reference-audit snapshot retain their original meaning.

## Current plan and Codex evidence

**Latest observed update:** [Build13 and the fixed2f46 source delta](Docs/Production/Completeness/2026-11-27/LATEST_SOURCE_DELTA.md) records physical shelf/cash collection, roster/cargo corrections and new scoped evidence. Its reported game source is `2654f5019b7212968d28600cb071bf1c231c9030`; cutoff `2f46e72e300a719f34ca9b0e9b718282a5a88ddd` adds the QA package. The APK/media were not replayed by this planning audit;9.5 checkpoints and scoped9.9 reports do not substitute for current final gates.

Use the [2026-11-27 task-plan refresh](Docs/Production/TASK_PLAN_REFRESH_2026-11-27.md), [all T01–T80 requirements](Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md), and [pinned GitHub render catalogue](Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md) before new work. The earlier reference refresh pinned **Codex Build 11**, source `989edd9283148e9f712387fb937ea36038cbd9d2`, scene `res://field_opening.tscn`; [exact package and review scope](Docs/Production/ReferenceRefresh/2026-11-27/LATEST_BUILD_EVIDENCE.json). Main and the older active-source instructions below remain preserved snapshots/branches; this documentation does not merge or reset current gameplay. Follow the newer Codex foundation with its actual owner/source binding. Historical task states are not current candidate approvals.

## Current whole-game decisions and gap closure

Use the [completeness standard](Docs/Production/COMPLETENESS_STANDARD.md), [24 gap dispositions and 12 selected decisions](Docs/Production/WHOLE_GAME_COMPLETENESS.json), and [T01–T80 task map](Docs/Production/Completeness/2026-11-27/TASK_COMPLETENESS_T01_T80.md). These select all-seven-pet combat, capable survivors with player-like logical carrying, recoverable stakes, 100 authored outcomes, material uses, clocks and landscape behavior. They supersede the prior D01–D05 open behavior choices while retaining unproved tuning and runtime evidence.

## Whole-game stakes, companions and resource value

Use the [gameplay-depth standard](Docs/Production/GAMEPLAY_DEPTH_STANDARD.md) and [T01–T80 responsibility crosswalk](Docs/Production/GameplayDepth/2026-11-27/TASK_GAMEPLAY_DEPTH_T01_T80.md) before new feature work. These add explicit stakes/recovery, useful survivor and pet jobs, delegated plot funding, substantial mixed carrying, complete animation and resource-value requirements. The [source audit and open decisions](Docs/Production/GameplayDepth/2026-11-27/README.md) distinguish pinned Build 11 behavior from proposed whole-game design. They do not activate tasks or certify game behavior.

## Active source

The preserved gameplay-depth baseline records the then-observed `trial/world-one-expansion-2026-11-26` source at `3fad812b384335bd8ca9b5e47dc9d9557110eb4a`: [bounded current-source changes and evidence](Docs/Production/GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md). It supersedes the relevant Build 11 cash/carry/drop/hearth observations, without claiming a new validated build or merging that branch into main.

**Continue gameplay from the newer Codex foundation:** [CURRENT_GAMEPLAY_SOURCE.json](Docs/Production/CURRENT_GAMEPLAY_SOURCE.json) selects `trial/world-one-expansion-2026-11-26`, observed at `2f46e72e300a719f34ca9b0e9b718282a5a88ddd` (Build13 reported game source `2654f5019b7212968d28600cb071bf1c231c9030`), project `HavenlineLevel1/project.godot`, main scene `res://field_opening.tscn`. Resolve its live head and active owner before editing. The selector grants no ownership change or new build approval.

The `alfred/level-1-replacement` snapshot at `2706cd6b0c6bfa7b4e8ad31d792a365aaf456d08` is preserved historical recovery material. The commands below belong to that checkpoint and do not launch the selected newer field build.

The full game plan is [HAVENLINE_BUILD_PLAN_V2.md](Docs/Production/HAVENLINE_BUILD_PLAN_V2.md). [REPOSITORY_INDEX.md](REPOSITORY_INDEX.md) links the preserved task plans, completion records and reference material. The dated task-custody index explains historical status disagreements without rewriting the original records.

## Open the historical Level 1 checkpoint

Prerequisites declared by the preserved project: Python 3.11 or later, Git LFS for historical LFS-backed references, and Godot 4.7.2.

From the repository root:

    git lfs pull
    python3 HavenlineLevel1/tools/hydrate_assets.py

The hydration script verifies all four studio assets and reconstructs the exact furnace GLB from the three tracked parts. Open **HavenlineLevel1/project.godot** in Godot 4.7.2.

For the preserved combined river, camp, HUD and Character 1 preview, use the fresh disposable checkout and isolated-profile procedure in [HavenlineLevel1/README.md](HavenlineLevel1/README.md). Its exact scene is [integrated_opening.tscn](HavenlineLevel1/previews/integrated_opening.tscn). In that isolated desktop runner, launch it explicitly with:

    godot --path HavenlineLevel1 --scene res://previews/integrated_opening.tscn

Pressing F5 runs the deliberately unchanged V8 default scene, res://opening.tscn. It does not select the combined checkpoint preview or the newer Codex field build. Preserve this source setting; consolidation does not change the game's main scene.

A disposable headless import uses:

    godot --headless --path HavenlineLevel1 --editor --import --quit

Read [HavenlineLevel1/README.md](HavenlineLevel1/README.md) and [ONE_CAMP_DESIGN.md](HavenlineLevel1/docs/ONE_CAMP_DESIGN.md), then the exact slice's verification record under HavenlineLevel1/docs. These commands open/import the checkpoint; they do not certify a full game, device build or visual pass.

## Preserve the two source roles

On main, **HavenlineLevel1/** is the preserved replacement checkpoint and **HavenlineGodot/** is the preserved prior integration source. The selected newer Codex branch uses the same Level 1 project path with its own field scene; follow the selector, not a historical filename alone. Do not replace current Level 1 files with older runtime files simply because a historical task record says approved.

Historical T01–T11 closeout records, active visual holds and later prepared task packets stay distinct. After Level 1 is accepted, review T01–T11 against actual current evidence before continuing the task plan. Archival preparation does not activate later runtime tasks.

## Reference custody

Use the original reference-video lock and source manifests under Docs/Design/ReferenceVideoLock. Both original recording hashes and declared sizes are retained. Full privately held original-video/editable-source custody is still explicitly unverified.

Generated turnarounds, selected aliases, rejected versions and delivered references retain their filenames and provenance. Static reference approval is not native mesh, rig, animation or runtime approval.

## Recovery

[Source snapshots](Docs/RepositoryArchive/SOURCE_SNAPSHOT.json) bind every captured branch to its full SHA. [Media custody](Docs/RepositoryArchive/MEDIA_CUSTODY.json) binds original media paths, Git blobs, SHA-256 hashes and retained locations. Historical alternatives under Docs/RepositoryArchive are recovery/reference sources, not active runtime overrides.
