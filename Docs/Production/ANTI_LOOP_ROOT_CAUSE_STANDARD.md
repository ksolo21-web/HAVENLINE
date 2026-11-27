# Havenline anti-loop and root-cause repair standard

This standard applies to every Havenline critic repair cycle. Evidence exists
to reveal the product; it may not be optimized as a substitute for repairing
the product.

## C0 diagnosis before another repair round

After any mandatory task validation, candidate guard, critic, integration,
evidence, performance or closure failure, run the non-voting C0 Root-Cause
Advisor before a builder starts another repair. C0 must classify the failure as
product, tooling, governance, evidence, infrastructure, superseded, or mixed;
return the complete currently knowable blocker set; identify unexecuted checks;
protect approved files/contracts; and provide a dependency-ordered proof
contract. See `C0_ROOT_CAUSE_STANDARD.md`.

A cancelled/superseded run is not a product judgment. A red UI state is not a
root cause. `FIX_REQUIRED` repair candidates must satisfy
`BUILDER_REPAIR_STANDARD.md` and `builder_repair_gate.py`.

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

## Candidate freeze

Once a repaired candidate begins full validation, that exact SHA is frozen for
the judgment. A later commit may wait as the next candidate, but it must not
cancel the already-running SHA. Let the running SHA finish so its evidence is
usable by C0 even when a newer candidate exists. If a run is cancelled anyway,
classify it `SUPERSEDED` and do not assign a product or critic failure from it.

## Quick-look visual gate

Before the expensive critic matrix, produce one source-bound quick-look packet
containing the whole-task contact sheet, normal gameplay views, every repaired
object, and matched-camera before/after frames. Run deterministic coverage,
duplicate-frame, aperture, route-continuity, contact-margin and delivered-board
contrast checks first.

Two low-cost visual scouts may inspect the compact packet in parallel. A
finding shared by both scouts, or corroborated by a deterministic check, blocks
the expensive matrix and returns the candidate to diagnosis. A lone scout
finding is `NEEDS_MANUAL_TRIAGE`; it is inspected against full-resolution pixels
before the matrix starts and cannot be hidden with a camera change.

The quick-look gate is defect discovery only. It can reject a visibly weak
candidate early, but it can never approve a task or replace the full critics.

## Isolated dissent adjudication

Use the current [reference acceptance policy](REFERENCE_ACCEPTANCE_STANDARD.md), including every stronger exact-10 visual requirement. Do not average scores or promote a low result through a quorum while a mandatory defect remains unresolved. A completed score below its applicable threshold remains a failing result.

A disputed finding may enter `ADJUDICATION_REQUIRED` only after exact-source, complete full-resolution evidence is available. Preserve the original review unchanged. A fresh independent reviewer examines the disputed evidence and complete affected requirement set without being instructed to raise the score. The adjudication records whether the original finding was a demonstrable assessment error, with the supporting evidence and reason. An evidence-based correction does not authorize arbitrary rescoring of unchanged work.

Final acceptance still requires every current mandatory dimension to meet its actual threshold, all required views and states, complete source binding, and zero unresolved mandatory defects. A corroborated defect returns to repair. Missing, truncated, malformed, low-confidence or source-mismatched responses block approval until the required evidence/review exists. No vote can override missing evidence, a hard mechanical failure or Kaleb's explicit rejection. Repairs receive fresh affected evidence and independent retesting.

The required loop is:

`FAILURE -> C0 DIAGNOSE COMPLETE BLOCKER SET -> BUILDER REPAIR PLAN -> CAUSAL REPAIR -> ROOT-CAUSE PREFLIGHT -> FREEZE SHA -> PROVE -> C1-C11 CRITIQUE`
