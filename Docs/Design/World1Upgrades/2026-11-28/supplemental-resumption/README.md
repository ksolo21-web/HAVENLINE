# Review-package resumption evidence

This is an additive preservation package. The **20 staged source snapshots are evidence only**. Their presence here does not integrate their gameplay code, activate a task, replace a repository contract, or ratify a deployment cap. No previously reviewed planning or design file was edited to create this folder.

## Start here

The [active design README](../README.md) explains the 27 purchase-value ladders and their limits. The [current world plan](../../../../Production/WorldProgression/2026-11-28-10x50/CURRENT_WORLD_PLAN.md) records 10 worlds with 50 local levels each. After root runs the separate assembly step, the [review gallery](../REVIEW_GALLERY.md) and its artifact inventory contain actual images, iteration history and explicitly scoped review results.

This supplemental package is not a final status authority. Root must add the two files listed under `required_final_root_additions` in [RESUMPTION_MANIFEST.json](RESUMPTION_MANIFEST.json) after the remaining art reviews and assembly. Older frozen checkpoints retain their historical pending-review wording. Read the final root checkpoint together with exact review reports; do not infer approval from a filename or score.

## What is preserved

| File or directory | Purpose |
|---|---|
| [Source preservation manifest](SOURCE_PRESERVATION_MANIFEST.json) | Exact preservation map for 52 source records. Twenty staged files differ from, or are absent at, the recorded base commit. The other 32 are byte-identical to that pinned commit and are recorded as fetch metadata. |
| `staged-sources/` | The 20 source snapshots, preserving their repository paths below this evidence-only directory. Total source payload: 4,564,444 bytes. The two code files are passive snapshots and must not be installed or executed as part of publication. |
| [Generation input resolution](GENERATION_INPUT_RESOLUTION.json) | Maps the observed original absolute input paths to pinned GitHub sources, retained generated iterations or the already-packaged storage layout contract. It also retains the known published source catalog for later input resolution. |
| [Publication audit](PUBLICATION_AUDIT.json) | Observed link checks, exact prior package hashes, concrete portability findings and bounded fixes. The gallery check uses the recorded preview snapshot, not an unperformed final assembly. |
| [Reviewed assembly helper](tools/assemble_review_package.py) | Exact helper bytes independently reviewed at SHA256 `8b8000db00d9bc3ac36328834bf32328fbdc4d9fa94242ac5bb7f3e0e356e688`. Its 22/22 review at 10.0 covered helper source and dry-run behavior only. |
| [Inert override template](tools/review_status_overrides.template.json) | An empty schema example. It supplies no candidate status, score, best-draft designation or approval. Root must preserve the actual final override JSON separately. |
| [Read-only resumption verifier](tools/verify_resumption.py) | Verifies this supplemental file inventory, exact staged-source copies and original package bindings without modifying the package. It reports finalization requirements separately. |

Published artwork and sources are not duplicated. Their commit, repository path, SHA256 and Git blob identities remain in the original source manifests and the supplemental resolution map. The four `source-main` entrypoint captures are also recoverable from the pinned commit; the planning source manifest records the exact single-final-LF materialization difference.

## Resume without changing the recorded evidence

1. Open the isolated review branch and read its final root status file and gallery. Keep owner selection, native implementation, full motion/audio and device proof separate from static or document review.
2. Run `python tools/verify_resumption.py` from this folder. This checks preservation only. Use `--require-finalized` after final evidence assembly and root checkpoint creation; missing finalization files must remain explicit failures for that mode.
3. Keep original prompt/error records unchanged. Resolve each declared source using `GENERATION_INPUT_RESOLUTION.json` and verify its SHA256 before reuse. A generated repair input must resolve to that exact retained iteration, never whichever image has the newest filename. New requests beyond the recorded snapshot need the same exact-path and hash resolution.
4. Fetch pinned source files from their recorded commit and repository path if a future operation needs them. Do not substitute a current branch head. The staged snapshots are already copied here because the recorded base cannot reproduce their exact bytes.
5. If reassembling a later review archive, restore the helper's explicit workspace layout: `WORKSPACE/package/` contains a checkout of the review branch; `WORKSPACE/generated/`, `WORKSPACE/prompts/` and `WORKSPACE/reviews/` contain artifacts restored using the final artifact inventory's original workspace-relative paths. The helper is not a standalone arbitrary-repository importer.
6. Invoke the preserved helper with an explicit workspace, for example `python tools/assemble_review_package.py --base /absolute/WORKSPACE --dry-run --overrides /absolute/WORKSPACE/review_status_overrides.json`. Its default dry run writes its report outside the design package. Root can authorize a later `--apply` after inspecting that concrete result. This supplemental preparation did not run `--apply`.

The existing planning verifier is already in the world-progression folder and needs no scratch-only inputs. It writes `VALIDATION.json`; run it in a disposable copy when preserving the reviewed bytes. The original compact independent reports, crops and selected verifier stdout/stderr are copied by the assembly helper. Huge duplicate review worktrees are intentionally excluded.

## Root publication finalization

Preserve the **actual raw** override JSON supplied to assembly at `final/root-review-status-overrides.json`; its SHA256 must match the assembly receipt. Add `final/PUBLICATION_STATUS.json` with the actual review branch/base/commit, exact current image/report hashes, each crew master/use pairing, and remaining gates. Do not replace a source report's rejection with a newer status in that historical report.

The requested armed tower illustration remains a separate blocked visual gate. An unarmed architecture image cannot satisfy it. All images remain unselected by the owner, and neither this package nor a static review establishes gameplay behavior.

The current four repository entrypoints do not navigate to the new art documents. A direct link to `Docs/Design/World1Upgrades/2026-11-28/REVIEW_GALLERY.md` in the review-branch or PR description is the bounded navigation fix; alternatively root can add a separate review navigation file. The frozen planning entrypoints need not be edited for this publication.
