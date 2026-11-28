# Assembly helper r2 — independent review

**Repair required: 8.0/10; 19/22 checks pass.**

AS-01 is closed: unbound and mismatched reports no longer supply current status or score, and exact-hash reports/overrides still work. All 50 package files remain unchanged after the actual dry run.

## New actual-schema issue: AS-02

The newly available saw/storage r4 and crew r2 reports put each candidate hash under `results[].image.sha256`. The helper already finds candidate IDs through `image.path`, but does not read the hash in that same object. Four genuinely hash-bound records therefore become unbound in the inventory. The parser also omits node-level `findings` and the explicit `intermediate_master_score`.

Add these exact known fields while preserving the corrected missing-hash rule. This is incomplete projection of available evidence, not a false approval; original report bytes remain retained.

The JSON report includes all actual field comparisons, check results and evidence hashes. No apply or remote publication was performed.

Reviewed helper SHA256: `85e72e675837c1c9daf32e901b5f5f38761a7bfc7bde67444be8e972595d7d58`.
