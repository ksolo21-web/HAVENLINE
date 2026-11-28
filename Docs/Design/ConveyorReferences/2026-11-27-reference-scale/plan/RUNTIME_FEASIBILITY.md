# Conveyor and resource revision — runtime feasibility

## Finding

A concrete native playback path exists: Godot **4.7.2.stable.official.ed1daf0bf** is installed, and an earlier complete gameplay project is available locally. The current selected source is **`trial/world-one-expansion-2026-11-26` at `fad3af0a45e94262737077ae513827b5042adb41`**, freshly read at 2026-11-28T04:56:06.336234+00:00. This audit made no gameplay or branch changes and did not launch/import Godot. It provides implementation evidence, not runtime approval.

## Source and ownership

The repository's `CURRENT_GAMEPLAY_SOURCE.json`, read from art commit `2fc474bbbb03d9a242b216d33e8588e028de4ce5`, selects `HavenlineLevel1/project.godot` and `res://field_opening.tscn` on the trial branch. Its historical observed head is Build13; the live head is newer. Main and `alfred/level-1-replacement` are preserved alternatives, not the default continuation target.

The exact active gameplay editor/owner is **unresolved**. Current `PATH_OWNERSHIP.json` has `active_owners: []`; the legacy workstream registry has no assignment for this Level1 project or trial branch. “Havenline Studio” is the current commit's author display name and “primary-integration-owner” is a generic registry role; neither establishes a current path assignment. This does not prevent read-only snapshots or art preparation, but it must be reconciled before production edits.

## What is physically available

| Item | Verified result |
|---|---|
| Earlier complete checkout | `/workspace/scratch/e15437dc7c94/HAVENLINE-current-gameplay` at `2f46e72e300a719f34ca9b0e9b718282a5a88ddd` |
| Earlier Level1 physical contents | **817/817 files**, **243,933,482 bytes**, every Git blob matches; zero missing files, zero LFS-pointer placeholders |
| Exact current Level1 tree | **872 files**, **272,712,703 bytes**, 444 asset files and 69 GLBs; remote recursive tree is not truncated |
| Minimal current-source delta | Reuse **770 exact files**, fetch **102 files / 29,269,653 bytes**: 45 changed and 57 new |
| Removals to respect | `assets/field_world/tower_sightline.gdshader` and its `.uid` |
| Complete current checkout | Not yet materialized; the older checkout must not be described as current |
| Engine | `/usr/local/bin/godot` and `godot4`, Godot 4.7.2 |
| Display | No current `DISPLAY`, Wayland display, X socket, or `/dev/dri`; graphical Godot not tested |
| Concrete display candidate | `/usr/bin/Xorg`, its dummy video driver and `/etc/X11/xorg.conf` exist; no private display was launched |
| Android delivery | `adb` and local Godot export templates absent; no APK/install claim |

The separate native desktop successfully opened and played the original reference video through Kdenlive. That establishes access to the mounted video path, not graphical Godot access from this shell.

## Current dependencies and behavior to preserve

The bounded check read ten current scripts and resolved **58/58 literal `res://` references** against the exact current project tree. It did not execute imports or resolve every dynamic dependency. Complete GLB paths, bytes and Git identities are listed in the JSON and `STATIC_DEPENDENCY_CHECK.json`.

The current counter already preloads `assets/customer_counter/self_service_counter.glb` and names itself `NorthSelfServiceCounter`. Its GLB is 413,468 bytes, Git blob `15f893a016025846d3c6a0759ce07a0585adf05b`. Restoring an older Build14 counter snapshot would discard newer gameplay. Current Beta T01 records carry forward Build16 foundations; their existing test results are historical evidence and were not rerun here.

Transport has native connected-kit plus Meshy straight/corner/incline assets. The eight typed routes are `meal_to_store`, `stored_meal`, `meal`, `meat`, `wood`, `planks`, `stone`, and `blocks`. Early food automation retains the serial store/request links. A new PNG conveyor sheet is not a replacement for those native meshes, routes and interactions.

`field_art.gd` sizes assets by their largest horizontal dimension. Several callers override its central default: conveyor transit calls `Art.make(lane, .45)` and shelf/product scaling also exists. Consistent enlarged resource scale therefore requires checking the native asset, carry/drop presentations, belt spacing, machine ports, output stock, counter sale and cash presentation. Changing only the image or central default would leave inconsistencies.

## Smallest path to actual playback

1. Materialize a disposable exact-current project using the 770 locally verified blobs and 102-file delta. Check all hashes against the current tree and exclude the two removed shaders. No repository history download is needed.
2. Import the isolated project with installed Godot 4.7.2, then resolve actual import errors. This audit has not run that step.
3. Establish a working graphical session. Private Xorg with the installed dummy driver/software rendering is available to investigate; success remains untested.
4. Use `field_opening.tscn` with the existing fresh disposable profile contract. The profile must be a single `/tmp/havenline-l1-v3-<token>` directory with at least six token characters and the exact `L1-DISPOSABLE` marker. Its marker content is `HAVENLINE-ALFRED-V3-DISPOSABLE` followed by one newline. The existing helper is `tests/lifecycle_test_profile.gd`.
5. Exercise `tests/qa_paid_conveyors.gd` with its phase prerequisites. It supports initial, interruption, finish and film coverage, normal/pinch views, and `HAVENLINE_CONVEYOR_VIEWS` output. A blank profile should not be assumed valid for every later phase.
6. Adapt native art and every affected width/offset/collision/spacing/service call site, preserving newer counter/economy/forest changes. Independently review actual motion, processing, full/blocked outputs, restart conservation, carry stacks, customer pickup and cash against the locked footage and approved scale sheets.

## Animal and fish scope

Current wildlife contains **Tundra Stag**, ID `wildlife_tundra_stag`, using `assets/field/tundra_stag.glb`; its drop key is shared `meat`. The hostile wolf asset also exists. Current field inventory contains `wood`, `stone`, `meat`, `coal`, `slate`, and `metal`. This evidence does not establish individual meat inventories or a fish-species catalogue in the selected live field.

The ten recovered meat identities and requested fish variants remain authorized visual variants. They do not claim new spawn tables, drops, economy, recipes or a working fish processing line. Runtime scope must be implemented and checked explicitly.

## Evidence and remaining limits

[Machine-readable report](RUNTIME_FEASIBILITY.json) contains exact source identities, GLB dependencies, display findings, the profile contract and an evidence-file SHA256 index. Source snapshots and readback receipts are in [runtime-feasibility-sources](runtime-feasibility-sources/). The earlier project's all-file verification is `LOCAL_COMPLETE_CHECKOUT_HASH_AUDIT.json`; current branch readback is `LIVE_BRANCH_READBACK.json`; project delta is `live-vs-local-delta.json`.

The audit is complete within its read-only scope. Current assigned ownership, current-project materialization/import, graphical access, revised native asset integration and actual gameplay acceptance remain unverified. No independent runtime score is awarded.
