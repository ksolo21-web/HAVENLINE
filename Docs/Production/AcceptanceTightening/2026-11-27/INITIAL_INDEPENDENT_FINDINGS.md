# Havenline acceptance tightening — independent review working ledger

Candidate worktree: `/workspace/scratch/e15437dc7c94/HAVENLINE-acceptance-tightening`
Base: `7180d1315af56228e7629735c2bd50bda3c43596`
Status: Implementation in progress; not a final verdict. No game score.

## Concrete issues reported to builders

1. Generated task and preparation packets retain >9.0 despite new static standards.
2. Nonvisual specialist reference dimensions are declared only by output, not frozen/propagated from input.
3. C5 model transport sees contact sheets, not actual playback, yet may emit final PASS.
4. Generic visual quorum uses >9.0, treats explicit incomplete coverage as passing, and may outvote an unresolved defect.
5. Forward closure accepts historical style-scope flags without rejecting the non-approving result.
6. Forward closure lacks shipping signoff and active invalidation/effective dependency validation.
7. Unconditional T09 historical byte identity in forward closure prevents all new T09 reviews.
8. T12 resolved-review tool still enforces >9.0; old T10 exporters retain historical rule.
9. Raw critic validator accepts arbitrary empty raw JSON and invalid input-manifest hash.
10. Duplicate JSON score keys are silently collapsed.
11. Shipping final signoff hashes an independent report without binding its decoded claims/identities to signoff.
12. C6 numeric measurements permit NaN, booleans or negative values through comparison-only checks.

## Reproduced probes

On the initial live candidate, a temporary C3 record with exact10 dimension scores/current final policy binding, input_manifest_hash `not-a-hash`, and raw output `{}` returned `passed=true`, `errors=[]` from `critic_harness.validate_raw`.
A duplicate first score key with values 7 then10 also returned `passed=true`, `errors=[]`.
The temporary fixture was outside the candidate; the validator ROOT was monkeypatched to that temp directory. Candidate/provenance labels used the real task/base identities. These are contract adversarial probes, not actual reviews or game acceptance.

## Required retest before approval

Re-read the frozen final code, reproduce each relevant negative with a coherent positive fixture, verify producer/consumer compatibility, check preserved historical bytes and frozen reference package, and verify active roots/owner signoff/invalidation paths fail closed. Final report must identify exact candidate hash/freeze and separate policy/tooling acceptance from deployment and gameplay acceptance.
