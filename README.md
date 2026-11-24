# HAVENLINE source-history recovery anchor

This branch preserves the original 85 captured branch heads and the source ancestry identified by the frozen 1,217-artifact inventory. The original anchor, 4c160797e686592b5589b7fa1bcae11567b9fc16, remains in the first-parent chain. Its 79 distinct captured heads retain their original source histories.

## Recover the exact source

- [SOURCE_SNAPSHOT.json](SOURCE_SNAPSHOT.json) retains the original branch-to-commit map byte-for-byte.
- [WORKFLOW_SOURCE_CUSTODY.json](WORKFLOW_SOURCE_CUSTODY.json) maps every frozen artifact to its workflow head, native-source markers, artifact-name source identities and metadata-declared sources.
- [SOURCE_ANCESTRY_COVERAGE.json](SOURCE_ANCESTRY_COVERAGE.json) records the 680 verified identities, their original trees and parents, and the exact 279 additional maximal heads needed for retention.
- [TASK_SOURCE_SEARCH.json](TASK_SOURCE_SEARCH.json) records the additional text-history search and the unresolved T71–T80 definitions.

The recovery extension uses 5 commits with additional-parent group sizes 60, 60, 60, 60, 39. Each keeps the preceding archive commit as its first parent. This retains 380 additional historical commits without changing any original source branch. Workflow execution heads, native-source markers, artifact-name identities and metadata-declared sources remain separate categories, even when they name the same commit.

Resolve an original full commit SHA from these indexes, then inspect or restore that source tree. This metadata tree intentionally contains no game runtime or operational .github files. Its parent histories retain the original filenames and exact objects.

## Preserve the branch boundary

Never merge this recovery branch into main or a work branch. Current development continues on alfred/level-1-replacement. The [consolidated build guide](https://github.com/ksolo21-web/HAVENLINE/blob/main/BUILD_GAME.md) provides the production and reference entry points. Keeping a historical source reachable does not approve its task status, artwork, animation, gameplay or device behavior.

No original branch is deleted, renamed or reset by this anchor. No PR is merged or closed. Source histories are retained for recovery, while runtime integration remains a separately reviewed operation.

## Separate byte-custody boundaries

Git reachability retains tracked objects and LFS pointer identities. The original 90 LFS payloads were downloaded and hash/size verified in their canonical GitHub custody; no independent offsite LFS copy is claimed. The 382 newly identified image payloads are recoverable from exact ordinary Git blobs, avoiding reliance on unverified LFS availability for those pointers.

Original Actions ZIPs have a separate durable-backup gate and index. Private original videos and editable studio packages have separate custody receipts. Eight private manifest-declared files and the older V2 pad source remain unlocated in the inspected material. Authentic T71–T80 definitions were not found and are not invented. No private payload or owner storage locator is published in this metadata tree.
