# Havenline anti-loop and root-cause repair standard

This standard applies to every Havenline critic repair cycle. Evidence exists
to reveal the product; it may not be optimized as a substitute for repairing
the product.

## Required defect ledger

Every mandatory critic finding creates or updates a structured defect record.
The record must contain the visible symptom, triage, affected production
object, probable root cause, implicated production files, causal production
change, expected visible result, proof contract, counters and status.

Allowed statuses are `OPEN`, `DIAGNOSING`, `PRODUCTION_FIX_REQUIRED`,
`PRODUCTION_FIX_IMPLEMENTED`, `READY_FOR_VERIFICATION`, `RESOLVED` and
`REJECTED_AS_INVALID_FINDING`.

`RESOLVED` is forbidden merely because a different camera, crop, lighting
state, prompt or evidence selection makes the defect less visible.

## Repair classifications

Every repair range is classified with one or more of `PRODUCTION_FIX`,
`EVIDENCE_FIX`, `TOOLING_FIX`, `DIAGNOSTIC_ONLY` and `TEST_FIX`.

An open production defect blocks critics when the range contains no causal
`PRODUCTION_FIX`. Evidence, tooling, diagnostics and tests cannot close a
production defect.

## Root-cause match

Every production repair records this chain:

`CRITIC SYMPTOM -> ROOT CAUSE -> PRODUCTION CHANGE -> EXPECTED VISIBLE RESULT -> REQUIRED PROOF`

The affected production file set must intersect the actual changed production
files. Otherwise the repair is blocked.

## Two-strike rule

When two review rounds identify the same defect family, freeze the failed
candidate and perform root-cause diagnosis before another critic run. Do not
rerun unchanged critics, alter only cameras/crops/captions/prompts, lower the
threshold, or reinterpret the same score. If no materially different
production repair is available, mark the task `BLOCKED`.

## Evidence rules

- Rejected candidates remain `REJECTED` and their failures stay preserved.
- Every visual production repair needs normal gameplay-scale proof.
- Closeups and disclosed QA views are supplemental.
- Preserve matched same-object, same-scene, same-camera, same-lighting and
  same-resolution before/after proof wherever practical.
- Evidence-camera changes are allowed only to fill a genuine coverage gap and
  cannot resolve a production defect.

## Pre-critic validator

Before an independent critic starts, automation must confirm that all
mandatory production defects have a causal production change, implicated
production files changed, fresh gameplay-scale evidence exists, the candidate
is new, matched-camera proof is preserved, affected regression passed and the
repair strategy is not another evidence-only attempt. Any failure blocks the
critic job.

## Quick-look visual gate

Before the expensive critic matrix, produce one source-bound quick-look packet
containing the whole-task contact sheet, normal gameplay views, every repaired
object, and matched-camera before/after frames. Run deterministic coverage,
duplicate-frame, aperture, route-continuity, contact-margin and delivered-board
contrast checks first.

Two low-cost visual scouts may inspect the compact packet in parallel. A
finding shared by both scouts, or corroborated by a deterministic check, blocks
the expensive matrix and returns the candidate to diagnosis. A lone scout
finding is `NEEDS_MANUAL_TRIAGE`; it is inspected against full-resolution
pixels before the matrix starts and cannot be hidden with a camera change.

The quick-look gate is defect discovery only. It can reject a visibly weak
candidate early, but it can never approve a task or replace the full critics.

## Isolated dissent adjudication

Do not average scores. A completed score at or below the threshold normally
remains a failure. The only exception is a formally isolated dissent within
one evidence group:

- exactly one of the two primary judgments for that evidence group is below
  the threshold;
- the paired role for the same evidence group is strictly above 9.0 in every
  mandatory dimension with no defect and medium/high confidence;
- source binding, coverage, mechanical gates and evidence integrity all pass;
- full-resolution manual inspection does not corroborate the alleged defect.

An eligible dissent becomes `ADJUDICATION_REQUIRED`, not an automatic task
failure. Preserve the original low verdict unchanged, then run one focused
fresh adjudicator against the exact disputed source-bound pixels and the same
scoring rubric. Use a separately recorded seed and do not disclose the earlier
scores. If the adjudicator is strictly above 9.0 in every dimension with no
defect and medium/high confidence, that group passes by a documented
two-of-three quorum. If the adjudicator corroborates any mandatory defect or
scores at or below 9.0, the candidate fails and requires a production repair.
Several split groups may be adjudicated independently in one focused run; every
split group must earn its own two-of-three quorum.

Missing, truncated, malformed, low-confidence or source-mismatched responses
are tooling failures, not votes. Retry only the incomplete judgment. Two
completed critics failing the same evidence group, any hard mechanical failure,
or any missing required view can never be outvoted.

The required loop is:

`FIND DEFECT -> DIAGNOSE -> REPAIR PRODUCT -> PROVE -> CRITIQUE`
