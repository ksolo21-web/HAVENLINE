# Repository preservation and consolidation

This directory preserves source identities and historical alternatives while active Level 1 work continues on its existing branch.

## Exact source baseline

- Latest captured Level 1 source: **2706cd6b0c6bfa7b4e8ad31d792a365aaf456d08**
- Existing main before consolidation: **0c3625b745d1729121ec13e3e0a267eb3a91e68b**
- Cumulative art archive: **01664a73ddf5087f17f7e159fa0b6b4ed71367b5**
- Opening recovery: **469cc1b065f4a94b8cd17f9dc69d414acb3d33e5**

The consolidated commit is intended to have exactly one parent at the captured active Level 1 source, 2706cd6b0c6bfa7b4e8ad31d792a365aaf456d08. Original main remains an ancestor, so publication can fast-forward while future Level 1 work retains a natural common ancestor. Source content is copied by exact Git blob/tree identity.

Before main advances, legacy PRs #1 and #2 must be retargeted to archive/legacy-main-2026-08-02 at the identical original main commit. Their heads, comparison bytes, draft state and reviews remain unchanged; any future merge of those legacy PRs would land on that legacy base. All other PR bases remain unchanged. Main publication requires a fresh check that no open PR targets main, followed by verification that all existing PR states are preserved. Adopting source history does not confer new task or gameplay approval.

## Preservation indexes

- SOURCE_SNAPSHOT.json — every captured branch and PR head/base.
- IMPORTED_SOURCE_MANIFEST.json — each copied source path, full source commit, blob and destination.
- MEDIA_CUSTODY.json — all current-tip media plus the audited history-only media.
- PLAN_IMPORTS.json — exact task/build-plan variant imports.
- REFERENCE_CUSTODY.json — original recording and supporting reference identities.
- Plans/ — human-readable task and reference navigation.
- Media/ and Documents/ — otherwise missing media/document variants.
- SourceEntrypoints/ — original README and agent-instruction variants.
- WorkflowSources/ — inert exact original workflow and .github configuration variants.

Preserved source content includes rejected and superseded versions. Their presence is not approval. Use the original source tree and provenance when restoring a model or historical runtime; copying one archived alternative into current gameplay requires a separate review.

## Evidence outside Git

Git history does not include all Actions artifact bytes or separately held private originals. External artifact preservation uses exact original ZIPs, SHA-256/size checks and durable batch receipts. The original artifact/run/source mapping must remain attached. Full recovery may not be declared until the remaining external custody and restore evidence are verified.

All existing active branches and source records are retained. No deletion is required to make this consolidated source navigable.
