# Havenline build-plan and reference custody

## Result

The requested 80-row custody catalog is ready. The repository contains **70 authoritative task definitions, T01–T70**. T71–T80 have explicit `SOURCE_NOT_FOUND` rows; no scope or status has been invented. Ten current-tip versions of `HAVENLINE_BUILD_PLAN_V2.md` all contain the same 70-task numbering range. The plan explicitly places its unnumbered post-launch roadmap outside release-critical T01–T70.

The proposed preservation payload contains **830 distinct archival files / 3,236,736 bytes**. Every file retains its original bytes and Git blob identity. Ordinary destinations use `Docs/RepositoryArchive/Plans/<full-source-commit>/<original-path>`. Two case-colliding orientation records use `Docs/RepositoryArchive/Plans/<full-source-commit>/Variants/<git-blob-SHA>/<original-path>` so both remain distinct on case-insensitive filesystems. The manifest retains each exact original `source_path`, source commit and byte identity separately from its archival destination. Current plan, registry, scope and task paths remain unchanged.

The live source snapshot for this work is `alfred/level-1-replacement` at `34f977c9ada2a7c621a57bcecd5c3d1bb690bc5e`, observed with the 85-branch census at `2026-11-24T20:53:51.979Z`. Integration remains `f74a84a2a288ab3d3935fba7a6cb9b975c2df239`. The cumulative art archive is `01664a73ddf5087f17f7e159fa0b6b4ed71367b5`; the separate opening checkpoint is `469cc1b065f4a94b8cd17f9dc69d414acb3d33e5`. Later movement of the active Level 1 branch must not be overwritten by this snapshot.

## What was located and preserved

| Source set | Located custody | Safe treatment |
|---|---|---|
| Authoritative build plan | `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`, current blob `74a0122eb009fa19904ac1caf0473ecf94f792b7`; 70 numbered definitions | Retain the current file; archive other versions without changing its meaning |
| Operational companion | `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md`, current blob `81f2220ea392875c10942e52b6a9d4a9906625c4` | Retain the current file and prior variants |
| Pre-V2 plan | `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md` and adjacent provenance record | Preserve the already archived original and its supersession boundary |
| Dedicated task packets | 68 task IDs have packets somewhere: T03–T70; T03–T13 are represented in the current baseline | Keep current packets at their original paths; archive external preparation variants |
| T01/T02 | Definitions and verified-completion evidence exist; no dedicated `TASK_PACKET.md` was located | Preserve recorded closure and definition, without manufacturing a modern packet |
| T14–T70 | 57 task IDs have packets outside the current baseline | Make the preserved copies navigable under the inert plan archive; do not activate or assign them |
| T71–T80 | No definitions, packet paths or identifiers located in the scanned current/historical document corpus | Keep ten explicit custody-gap rows and request an authoritative source only if such a plan is later supplied |
| Historical plan/packet/scope variants | 272 reachable path/blob variants, including 23 absent from current tips | Preserve their exact source commits and archival copies; keep current authority distinct |

`SAFE_ADDITIVE_IMPORTS.json` specifies the 807 current-tip variant imports: 77 packet variants, 123 frozen-scope variants, 459 task support/evidence variants, 127 shared governance/support variants, 20 build-plan variants and one supplemental reference document. `HISTORICAL_PLAN_IMPORTS.json` supplies the additional 23 historical copies. Their destination paths do not collide with each other or with the baseline tree.

The 80-row JSON retains each task's definition, dependencies, current registry record, historical accepted source, build-plan narrative state, completion variants, scope variants, packet variants, active visual holds and registry state variants from other branches. Other-branch preparation records are preserved as source evidence, not promoted into the live registry.

## Status preservation: keep the layers separate

The source files contain different historical checkpoints. `AGENTS.md` checkpoint prose stops at T09. The build plan and operational companion describe T10 as approved and T11 as prepared. The exact current registry, dependency graph and task-local completion records preserve T01–T11 historical approvals. T03 also has an older `5df9726e…` plan citation and a later Iteration 11H `e1e7bb2d…` registry/closure record. These records must remain distinguishable rather than being flattened into a single rewritten status.

`Docs/Production/APPROVAL_INVALIDATIONS.json` separately records ACTIVE visual holds for **T03, T04, T05, T08, T09, T10 and T11**. T02's visual hold is recorded as resolved by user acceptance. Historical completion evidence remains preserved; it does not by itself establish current visual acceptance or approval of the changed Level 1 candidate. This consolidation does not clear invalidations, restart approved tasks, alter accepted SHAs, assign builders or satisfy future dependency gates.

`WORKSTREAM_REGISTRY.json`, `DEPENDENCY_GRAPH.json`, `PATH_OWNERSHIP.json`, `task-gates.json`, the style lock and task-local frozen scopes stay byte-identical in the baseline. The proposed archive and navigation are additive. Existing task ownership, running work and source-bound proof remain untouched.

## References and original custody

`REFERENCE_CUSTODY.json` indexes 392 reference/supporting-document variants. It includes the primary video lock and source manifest, supplemental references, historical gameplay lock, runtime contract, style policy, opening recovery documentation, Level 1 one-camp design/ownership and art-source/provenance documents.

The two primary recordings are preserved by exact manifest identity:

| Recording | SHA-256 | Declared bytes |
|---|---|---:|
| `Screen_Recording_20260817_124839_YouTube.mp4` | `62f7cfe644de3826cfdd6d91bc23c0ab8d9e4fde3e175c90f762e604547bb0ca` | 74,486,197 |
| `Screen_Recording_20260817_124510_YouTube.mp4` | `4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2` | 74,298,526 |

The primary manifest specifies 44 timestamp-selected frames and 12 comparison scenarios. This subtask did not recover or play the original recordings and makes no new visual judgment. Preserve their primary authority and exact identities; do not replace them with thumbnails, the supplemental advertisement pack, or a written summary. The root preservation work handles all image/model/render bytes and historical media.

The November 19 framing supplement is separately preserved from `docs/whiteout-reference-framing-20261119` at `40b9ba6569f9be800c507fbf8de19ea21459322c`. Its archival inclusion does not silently adopt an open PR or supersede the locked A/B sources.

## Missing-task search boundary

The refreshed 85-tip scan read 1,709 distinct planning/reference text blobs, 14,437,651 bytes, with zero missing reads and no T71–T80 matches. The one requested historical scan covered 3,159 reachable document-text blobs, 34,859,141 bytes, across all refs plus explicit current Level 1 ancestry. Its extension set is recorded in `t71-t80-historical-text-search.json`; there were zero missing/non-UTF-8 failures and zero matches. All ten current-tip build-plan variants end at T70.

The root separately reported that a bounded Library/personal-context search found no authentic T71–T80 source. This does not prove no external plan exists. It establishes the limit of the located evidence; an actual source can be added later without renumbering or inventing the existing tasks.

## Ready-to-copy navigation

- `publish/REPOSITORY_INDEX.md` provides root navigation without replacing the existing README.
- `publish/Docs/RepositoryArchive/Plans/README.md` explains the archive boundary.
- `publish/Docs/RepositoryArchive/Plans/TASK_CUSTODY_T01_T80.md` provides the complete navigable 80-row catalog and exact per-task source map.
- `publish/Docs/RepositoryArchive/Plans/REFERENCE_CUSTODY.md` connects the existing reference locks, opening recovery and four art archive roots.
- `publish/Docs/RepositoryArchive/Plans/HISTORICAL_PLAN_TASK_VARIANTS.json` records the older historical plan/packet/scope variants.

Root execution should copy these additive files and the exact payload destinations from both import manifests, then validate the assembled candidate. Do not substitute these archival documents for the active governance paths. No branch, PR, runtime, workflow or existing audit file was changed by this subtask.

## Verification and resumption

`VALIDATION.json` records 830 unique destinations, exact Git blob/SHA-256/byte matches, all 80 requested rows, ten explicit missing-definition rows and successful local navigation checks against the proposed baseline/art/opening/import tree. The root must independently validate the actual assembled tree and receive the separate critic's disposition before claiming the consolidation complete.

Reproduction: `build_plan_custody.py` regenerates the current-tip import catalog and `build_reference_custody.py` regenerates reference navigation. Historical additional imports and the final appended historical-index links are recorded as supplied evidence; do not blindly rerun generators over a finalized package without preserving those additions. No remote mutation is part of these analysis scripts.
