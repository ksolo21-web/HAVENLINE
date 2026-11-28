# Publication planner — bounded independent retest

**Pass: 15/15 checks, 10.0 within tool source and clean disposable-manifest scope.**

Exact reviewed source: `b52dda12c99ef594dc2db586ac7097ce44a0eff05b4399f803690213f43daeef`. No tool-source changes were required. Root removed only the unwanted generated Python cache; the earlier failed run remains preserved. The manifest command was repeated with `PYTHONDONTWRITEBYTECODE=1`.

The actual copied package contained 294 files: 93 binary SHA entries and 201 UTF-8 content entries. Every SHA256, Git blob identity and byte count matched; each UTF-8 payload re-encoded to the exact source bytes. Repeat runs were byte-deterministic. Every package path appeared exactly once, no entry encoded a deletion, and output inside the package was rejected before creation. Parent/tree/branch values were carried exactly.

The 250,000-byte batch threshold is a soft partition target. Four large individual text files produced larger one-entry batches; the largest was 2,085,313 bytes. The caller must ensure transport accepts those concrete payload sizes.

Publication must upload binary blobs and verify their returned Git SHAs, consume only batches listed by `MANIFEST.json`, and use each prior returned tree as the next batch base. The complete resulting remote base-plus-overlay tree must still be verified before creating the review branch. This local tool review cannot establish remote preservation.

The planning critic owns the replacement assembly-receipt/final-archive review. No remote write, frozen-document edit, owner art selection, native approval or whole-task approval is claimed.
