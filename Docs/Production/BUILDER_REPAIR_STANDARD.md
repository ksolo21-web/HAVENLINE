# Havenline Builder Repair Standard

This standard governs repair work after a mandatory task gate fails. Its purpose is to stop builders from chasing one red line at a time, widening scope by instinct, or fixing a test symptom by damaging already-approved production work.

## Before any repair edit

If the task is `FIX_REQUIRED`, the builder must have:

1. a source-bound C0 report with `diagnosis_status=DIAGNOSIS_COMPLETE`;
2. `complete_known_blocker_set=true`;
3. a repair plan that maps every known blocker to one causal change and one proof path;
4. an explicit `files_not_to_change` list protecting approved content/contracts;
5. blast-radius checks for every already-approved task C0 identifies as at risk;
6. a dependency-ordered verification sequence;
7. a frozen-candidate policy of `finish_running_sha`.

If C0 says `INSUFFICIENT_EVIDENCE`, the builder does not guess. Gather only the named missing evidence and return to C0.

If C0 classifies a run `SUPERSEDED`, `INFRASTRUCTURE_FAILURE`, or `EVIDENCE_DEFECT` with `NO_PRODUCT_CHANGE`, production files may not be edited merely to obtain green CI.

## Repair-plan requirements

`Docs/Production/<TASK>/REPAIR_PLAN.json` is the machine-readable handoff. It must contain:

- task id and failed candidate SHA;
- exact C0 report path/hash and diagnosis id;
- `full_blocker_set_acknowledged=true`;
- one fix entry for every C0 blocker;
- causal change, permitted files and verification steps for each fix;
- complete `must_not_change` list;
- blast-radius regression checks;
- `candidate_freeze_after_build=true`;
- `validation_concurrency_policy="finish_running_sha"`.

One fix may resolve multiple blockers only when C0 states they share the same causal root. No blocker may disappear from the repair plan without a recorded C0 disposition.

## Builder execution rules

- Change the smallest causal production/tooling/governance surface that resolves the complete known blocker set.
- Do not weaken tests, critic thresholds, reference requirements or evidence coverage to make a defect disappear.
- Do not alter approved assets/contracts named in `must_not_change`.
- Do not opportunistically refactor unrelated code during a repair candidate.
- Do not create a second repair candidate while the frozen candidate is under validation unless the active run has produced a new terminal diagnosis.
- Do not rerun an unchanged failed candidate.
- Do not use evidence/camera/crop changes to close a production defect.
- A tooling/governance repair must remain a tooling/governance repair unless evidence independently proves a product defect.

## Post-build repair gate

Before expensive validation begins, `builder_repair_gate.py` compares the actual diff with the accepted repair plan. It fails closed when:

- a known C0 blocker is not addressed;
- a changed file is outside the authorized repair surface;
- a protected `must_not_change` file changed;
- a causal fix has no proof step;
- blast-radius regression is missing;
- the candidate-freeze policy is absent;
- C0's diagnosis is incomplete or superseded.

## Verification order

Use cheapest/high-signal checks first:

`STATIC CONTRACT -> ROOT-CAUSE-SPECIFIC PREFLIGHT -> IMPACTED REGRESSION -> SAVE/DEVICE/SECURITY MATRICES AS APPLICABLE -> PERFORMANCE -> EXPENSIVE VISUAL/MOTION EVIDENCE -> INDEPENDENT CRITICS -> CLOSURE`

A late expensive failure should not reveal something that a cheap root-cause-specific preflight could have caught earlier.

## No moving target

Once a candidate SHA starts full validation, it is immutable for that judgment. New commits wait as a separate candidate. The running SHA is allowed to finish so its evidence remains diagnostically useful. Cancellation due to a newer SHA is classified `SUPERSEDED`, never as a task/critic failure.

## Done condition

A builder repair is not complete because CI turned green. It is complete when every C0 blocker has causal proof, blast-radius checks pass, no unauthorized changes exist, the exact frozen SHA finishes its required validation, and the normal C1-C11 task approval flow can resume.
