# Havenline plan archive

This directory adds source custody and navigation. It does not replace the active production plan, task registries, frozen scopes, reference locks, workflows or accepted-source records.

[Open the 80-row task custody catalog](TASK_CUSTODY_T01_T80.md). Seventy task definitions are found; ten remain explicitly unlocated.

The source baseline is `34f977c9ada2a7c621a57bcecd5c3d1bb690bc5e`. Archived files normally use their full source commit and original repository path. Two case-colliding orientation records use `<source-commit>/Variants/<git-blob-SHA>/<original-path>` to retain both distinct files on case-insensitive filesystems. The import manifest preserves each original source path, Git blob identity, SHA-256, bytes, file mode and all current branches carrying the same path/blob.

Copies preserve every selected variant byte-for-byte. A path under this archive is historical evidence and cannot confer assignment, approval, runtime readiness or workflow authority.

## Older historical variants

[Historical plan, packet and frozen-scope catalog](HISTORICAL_PLAN_TASK_VARIANTS.json) records all 272 reachable path/blob variants found in this inventory, including 23 older variants absent from current tips. Those 23 have separately verified source commits and archival copies; they do not replace the current plan or packet.
