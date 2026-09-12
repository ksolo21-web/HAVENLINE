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

The required loop is:

`FIND DEFECT -> DIAGNOSE -> REPAIR PRODUCT -> PROVE -> CRITIQUE`

