# Build and continue Havenline

## Current plan and Codex evidence

Use the [2026-11-27 task-plan refresh](Docs/Production/TASK_PLAN_REFRESH_2026-11-27.md), [all T01–T80 requirements](Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md), and [pinned GitHub render catalogue](Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md) before new work. The newest verified receipt found is **Codex Build 11**, source `989edd9283148e9f712387fb937ea36038cbd9d2`, scene `res://field_opening.tscn`; [exact package and review scope](Docs/Production/ReferenceRefresh/2026-11-27/LATEST_BUILD_EVIDENCE.json). Main and the older active-source instructions below remain preserved snapshots/branches; this documentation does not merge or reset current gameplay. Follow the newer Codex foundation with its actual owner/source binding. Historical task states are not current candidate approvals.

## Active source

Continue Level 1 development on **alfred/level-1-replacement**. The consolidated source snapshot is **2706cd6b0c6bfa7b4e8ad31d792a365aaf456d08**; the active branch may advance independently. Always resolve its actual head before starting another change.

The full game plan is [HAVENLINE_BUILD_PLAN_V2.md](Docs/Production/HAVENLINE_BUILD_PLAN_V2.md). [REPOSITORY_INDEX.md](REPOSITORY_INDEX.md) links the preserved task plans, completion records and reference material. The dated task-custody index explains historical status disagreements without rewriting the original records.

## Open the Level 1 checkpoint

Prerequisites declared by the preserved project: Python 3.11 or later, Git LFS for historical LFS-backed references, and Godot 4.7.2.

From the repository root:

    git lfs pull
    python3 HavenlineLevel1/tools/hydrate_assets.py

The hydration script verifies all four studio assets and reconstructs the exact furnace GLB from the three tracked parts. Open **HavenlineLevel1/project.godot** in Godot 4.7.2.

For the current combined river, camp, HUD and Character 1 preview, use the fresh disposable checkout and isolated-profile procedure in [HavenlineLevel1/README.md](HavenlineLevel1/README.md). Its exact scene is [integrated_opening.tscn](HavenlineLevel1/previews/integrated_opening.tscn). In that isolated desktop runner, launch it explicitly with:

    godot --path HavenlineLevel1 --scene res://previews/integrated_opening.tscn

Pressing F5 runs the deliberately unchanged V8 default scene, res://opening.tscn. It does not select the current combined preview. Preserve this source setting; consolidation does not change the game's main scene.

A disposable headless import uses:

    godot --headless --path HavenlineLevel1 --editor --import --quit

Read [HavenlineLevel1/README.md](HavenlineLevel1/README.md) and [ONE_CAMP_DESIGN.md](HavenlineLevel1/docs/ONE_CAMP_DESIGN.md), then the exact slice's verification record under HavenlineLevel1/docs. These commands open/import the checkpoint; they do not certify a full game, device build or visual pass.

## Preserve the two source roles

**HavenlineLevel1/** is the current isolated replacement. **HavenlineGodot/** remains the preserved prior integration source. Do not replace current Level 1 files with older runtime files simply because a historical task record says approved.

Historical T01–T11 closeout records, active visual holds and later prepared task packets stay distinct. After Level 1 is accepted, review T01–T11 against actual current evidence before continuing the task plan. Archival preparation does not activate later runtime tasks.

## Reference custody

Use the original reference-video lock and source manifests under Docs/Design/ReferenceVideoLock. Both original recording hashes and declared sizes are retained. Full privately held original-video/editable-source custody is still explicitly unverified.

Generated turnarounds, selected aliases, rejected versions and delivered references retain their filenames and provenance. Static reference approval is not native mesh, rig, animation or runtime approval.

## Recovery

[Source snapshots](Docs/RepositoryArchive/SOURCE_SNAPSHOT.json) bind every captured branch to its full SHA. [Media custody](Docs/RepositoryArchive/MEDIA_CUSTODY.json) binds original media paths, Git blobs, SHA-256 hashes and retained locations. Historical alternatives under Docs/RepositoryArchive are recovery/reference sources, not active runtime overrides.
