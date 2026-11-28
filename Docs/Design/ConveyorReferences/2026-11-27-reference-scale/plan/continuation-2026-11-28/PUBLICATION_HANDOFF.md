# Conveyor continuation — publication handoff

Read-only audit by `/root/conveyor_scope_audit`. Root owns candidate repairs, approval integration and publication. This handoff does not publish, approve changed artwork or change gameplay.

## Current evidence

The prior package contains 24 selected PNGs. All 24 matched their recorded SHA-256 hashes during this audit. Existing reviews cover 27/27 canonical single-unit identities, four fish types with eight raw/cooked depictions, ten animal-meat variants, and 34/36 conveyor static cells. F01 and N02 remain open in the current frozen matrix. Newer conveyor R8 and network R5 candidates exist and need fresh review before further generation.

Exact owner-selected R1 conveyor and R4 core-resource images remain controlling. No new universal multiplier or world-unit dimensions are approved. Static reviews do not certify native geometry, 360-degree assets, moving cycles, collisions or inventory behavior.

## Remote state observed

- Safe origin: `https://github.com/ksolo21-web/HAVENLINE.git`.
- Local art branch: `art/conveyor-reference-scale-2026-11-27`.
- Local and remote parent commit: `2fc474bbbb03d9a242b216d33e8588e028de4ce5`.
- Base tree: `acd72b1cb75178b4463122515e7bed70c794faba`.
- That commit's parent: `d268499d942a9961463cec64c1812da40d56539a`.
- Existing remote branch `art/resources-processing-machines-2026-11-27` still points to `2fc474bbbb03d9a242b216d33e8588e028de4ce5`.
- Intended remote conveyor ref returned 404; exact branch search returned no matches. The new gallery is absent at the base commit.
- Existing other conveyor branches are `art/conveyors-2026-11-26` and `review/beta-conveyor-owl-2026-11-28`; leave them alone.

These observations are time-bound. Re-read the intended ref immediately before creating it or updating it. Blob creation alone is not committed, reachable publication.

## Efficient blob reuse

Package root:

`/workspace/scratch/59f000bd1476/HAVENLINE-processors/Docs/Design/ConveyorReferences/2026-11-27-reference-scale`

Prior successful immutable blob receipts are in both:

- `/workspace/scratch/59f000bd1476/conveyor-reference-revision/publish/receipts/`
- `/workspace/scratch/59f000bd1476/conveyor-reference-revision/publish/root-receipts/`

Together, these contain **86 unique successful blob receipts** that match current file bytes, SHA-256 and Git blob SHA. Use the individual receipts as authority. `root-extra-cache.json` contains only seven entries and is stale; `blob-cache.json` contains the first 35. Do not rely on either cache alone.

The audit snapshot contains 544 paths and 445 distinct blobs. It can reuse 86 prior uploaded blobs and one base-tree blob. At snapshot time, 31 unique PNGs (44,744,190 bytes) and 327 distinct text blobs (1,844,508 bytes) remained without a confirmed upload/base match. New repairs, evidence and reports will alter these counts. `PUBLICATION_BLOB_REUSE_SNAPSHOT.json` maps every path to exact bytes, hashes and a reuse disposition; rescan after final edits.

Recommended GitHub Data API sequence:

1. Freeze approved selections, all attempts, prompts, requests, receipts, reviews and evidence. Preserve the parent tree.
2. Reuse confirmed PNG Git SHAs. Upload only missing/new unique PNG byte strings with `create_blob(encoding="base64")`; verify the returned SHA against the local Git blob SHA and retain a receipt.
3. UTF-8 text can be supplied as `content` entries to `create_tree`, avoiding hundreds of separate blob calls. If response/tool size requires batches, build sequential tree objects from the previous returned tree SHA. Every batch uses exact repository paths and mode `100644` with type `blob`; do not supply both content and SHA on an entry.
4. Begin from base tree `acd72b1cb75178b4463122515e7bed70c794faba`, preserving all earlier assets and plans. Include only the isolated package additions and authorized continuation records.
5. Create the commit with parent `2fc474bbbb03d9a242b216d33e8588e028de4ce5`. If the intended ref remains absent, create it from the final commit. If another worker created it, inspect the new head and use a normal fast-forward update with an expected SHA; never force over concurrent work.
6. Read the committed tree and match every expected package path and blob SHA. Verify the branch points to that exact commit. Confirm unchanged parent paths and no gameplay/workflow changes.

The current `fetch` and `fetch_blob` tools rejected a PNG readback during UTF-8 decoding. This is a binary-decoding limitation, not proof of a missing blob. Use exact create receipts plus committed tree/path SHA readback for custody, and use a supported base64 file route if full binary body rechecking is required.

## Existing gallery builder

Script:

`.../Docs/Design/ConveyorReferences/2026-11-27-reference-scale/tools/build_selected_gallery.py`

Run only after the complete independent row snapshot and selected files are final:

```bash
python3 /workspace/scratch/59f000bd1476/HAVENLINE-processors/Docs/Design/ConveyorReferences/2026-11-27-reference-scale/tools/build_selected_gallery.py --critic-root /workspace/scratch/59f000bd1476/conveyor-reference-revision/critic --coverage-review /workspace/scratch/59f000bd1476/conveyor-reference-revision/critic/CONVEYOR_COVERAGE_CURRENT.json
```

The script does not choose or edit images. It reads the existing `selected/` directory and requires every selection to match either owner approval or an exact independent PASS10 candidate binding. It copies review evidence, writes the selected gallery/manifest, normalizes the full 36-row coverage snapshot, and builds `PACKAGE_FILE_HASHES.json`.

Its `--critic-root` must contain both preserved prior reviews and new reviews, or changed selections will lack bindings. A copied package can use its preserved `reviews/independent` tree after new reports are added. Supply the updated whole matrix; supplying only the two repair reviews cannot close all 36 rows. Retain original reviewer provenance for the six industrial rows.

After any subsequent package mutation, rebuild hashes and rescan the upload inventory. Do not interpret historical PASS10 records as automatic approval of new image bytes.

## Files produced by this audit

- `CONTINUATION_CHECKPOINT.json`: requirements, prior validated counts, remaining two cells, acceptance checks and next action.
- `REMOTE_PUBLICATION_AUDIT.json`: compact current ref/base observations.
- `PUBLICATION_BLOB_REUSE_SNAPSHOT.json`: exact per-blob and per-path upload reuse snapshot.

All files are newly created in the current-session plan directory. Existing art, evidence and git state were left untouched.
