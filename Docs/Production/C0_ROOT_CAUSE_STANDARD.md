# C0 Root-Cause Advisor — non-voting diagnostic critic

C0 exists to stop serial symptom-fixing loops. It is a critic because it independently examines failure evidence, but it is **not an approval critic and never casts a PASS/FAIL vote on gameplay quality**. C1-C11 retain all existing approval authority and thresholds.

## Trigger

Run C0 after any mandatory task validation, critic, candidate-guard, integration, evidence, performance, or closure failure **before a builder starts another repair round**. A cancelled/superseded run is also classified by C0 so it cannot be mistaken for a product defect.

C0 is not required for a clean first build, a clean passing validation, or a governance-only edit that did not fail a task gate.

## Required input

C0 receives one immutable failure packet bound to the exact failed SHA. The packet contains, when available:

- task id, failed candidate SHA, integration SHA and workflow run id;
- workflow/job/step conclusions including cancelled/skipped states;
- failed-step logs and relevant successful upstream-step summaries;
- exact changed-file list and candidate branch point;
- task frozen scope, current defect ledger and applicable critic ids;
- artifact/evidence identities and hashes;
- previous failure/repair record when the same defect family has appeared before.

Missing evidence is reported as missing. C0 may never invent an unseen failure.

## Failure taxonomy

Every blocker is classified as exactly one primary class:

- `PRODUCT_DEFECT` — the shipping/runtime product is causally wrong.
- `TOOLING_DEFECT` — the harness, test, capture, scorer or validation implementation is wrong.
- `GOVERNANCE_DEFECT` — ownership, lifecycle, base/reconcile, scope or orchestration logic is wrong.
- `EVIDENCE_DEFECT` — required proof is missing/invalid while the product is not yet disproven.
- `INFRASTRUCTURE_FAILURE` — runner/cache/network/toolchain/runtime failed without a valid product judgment.
- `SUPERSEDED` — the SHA was cancelled/replaced before judgment; no product conclusion is allowed.
- `MIXED` — two or more independently causal classes are present and each must be listed as a separate blocker.

A red UI state is not a classification.

## Mandatory output

C0 emits a source-bound JSON report with:

- `diagnosis_status`: `DIAGNOSIS_COMPLETE` or `INSUFFICIENT_EVIDENCE`;
- `terminal_class`;
- `complete_known_blocker_set`;
- every currently observable blocker, not merely the first failing line;
- concrete evidence supporting each blocker;
- root cause and affected object;
- exact `files_to_change` and `files_not_to_change`;
- the smallest causal fix, not a workaround;
- blast-radius risks to already-approved work;
- dependency-ordered verification steps;
- builder action: `REPAIR`, `RETRY_INFRA`, `NO_PRODUCT_CHANGE`, `FREEZE_AND_VALIDATE`, or `BLOCKED`;
- candidate-freeze requirement.

`DIAGNOSIS_COMPLETE` is forbidden if an actionable failure is left as vague wording such as "CI failed", "critic failed", "visual issue", or "try again".

## Full-blocker-set rule

C0 must examine the complete available failed run before prescribing work. If one failure masks downstream steps, C0 distinguishes:

1. **known blockers** — supported now and must be repaired together when dependencies allow;
2. **unexecuted checks** — unknown, not guessed;
3. **downstream risks** — likely blast radius to retest, not claimed defects.

The builder may not fix only the first red line when the same run already proves additional independent blockers.

## Preserve approved work

C0 must explicitly identify approved assets/runtime/contracts that the repair must not change. If evidence shows a test/harness defect but does not disprove approved production content, C0 must say `NO PRODUCT CHANGE` for that content.

A test may never be made green by weakening an approved product requirement. A product may never be modified merely to satisfy a defective test.

## Candidate freeze

Once the builder produces the candidate described by the accepted repair plan, that SHA is frozen for its validation run. A newer commit may queue as the next candidate, but it must not cancel the already-running frozen-SHA judgment. A cancelled/superseded SHA produces no product verdict.

## Builder handoff

The builder receives C0's report plus a machine-validated repair plan. The builder may change only the causal repair surface authorized by that plan. If new evidence contradicts C0, stop the repair, preserve the evidence and return to C0; do not improvise a wider repair.

## Relationship to C1-C11

C0 never scores 0-10, never appears in per-task approval applicability, never raises or lowers the >9.0 unrounded threshold, and never substitutes for C1-C11. Its only authority is diagnostic: determine **what failed, why, what must change, what must not change, and how to prove the repair** before another build/review loop begins.
