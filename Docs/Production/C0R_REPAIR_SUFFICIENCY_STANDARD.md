# C0R Repair Sufficiency Critic Standard

C0R is Havenline's non-voting **Repair Sufficiency Critic**. Its purpose is to stop a builder from spending another candidate/CI cycle on a repair that is plausible for one observed symptom but insufficient for the complete known failure family.

C0R does not approve gameplay, does not score 0-10, does not replace C1-C11, and may never lower a critic, evidence, performance, device, security, or closure threshold.

## Trigger

Run C0R after C0 has produced a validated complete diagnosis and after a repair plan exists, but **before production/tooling repair implementation begins**. T10 is the first canary.

The required repair loop becomes:

`FAILURE -> C0 COMPLETE DIAGNOSIS -> REPAIR PLAN -> C0R SUFFICIENCY REVIEW -> CAUSAL REPAIR -> ROOT-CAUSE PREFLIGHT -> FREEZE SHA -> PROVE -> C1-C11`

A plan rejected by C0R returns to planning. `INSUFFICIENT_EVIDENCE` gathers only the named missing evidence and then re-runs C0R.

## Questions C0R must answer

1. What exact invariant failed?
2. What complete failure family is currently observable?
3. Why does the proposed change modify the causal mechanism rather than only the observed number?
4. How is this materially different from prior attempts in the same failure family?
5. What counterexamples could make the repair fail?
6. What blast radius could the repair create?
7. What cheap preflight can falsify the proposal before expensive validation?
8. If the proposal is another scalar/configuration adjustment after repeated same-family failures, where is the full-domain proof?

## Required plan contract

`repair_sufficiency` must contain:

- `failure_family.id`, the failed `invariant`, and all applicable `scope_dimensions`;
- known failed cases, unexecuted/unknown cases, and whether exhaustive observable collection is required/complete;
- `strategy_kind`, `causal_mechanism`, `why_this_fixes_cause`, and `why_materially_different`;
- same-family attempt count plus prior attempts and lessons;
- one explicit sufficiency row for every C0 blocker;
- full-domain proof when required;
- cheap falsification preflights;
- counterexamples considered;
- blast-radius hypotheses and residual unknowns;
- an explicit empty `threshold_changes` collection;
- `loop_risk_acknowledged=true`.

## Hard anti-loop rules

- Two or more failed/partial attempts in the same failure family raise `REPEATED_FAILURE_FAMILY`.
- A repeated scalar/configuration/constant adjustment raises `SERIAL_SCALAR_PATCH_RISK` and is rejected unless complete full-domain proof is supplied.
- A product defect cannot be closed by an evidence-only, test-only, or diagnostic-only strategy.
- A plan cannot claim the whole failure family is closed while known required cases remain unexecuted or unknown.
- Every C0 blocker must have its own explanation of why the proposed change alters the cause, expected result, falsifying result, and cheap disproof.
- Any critic/quality threshold weakening rejects the plan.

## Outcomes

- `REPAIR_PLAN_ACCEPTED`: bounded implementation may begin. This is not task approval.
- `REPAIR_PLAN_REJECTED`: revise the proposed repair; do not build another candidate.
- `INSUFFICIENT_EVIDENCE`: collect only the named evidence gap; do not guess.

C0R remains read-only and non-voting. Final task approval remains exclusively with the normal source-bound tests, evidence, C1-C11 critics, integration owner, and closure gates.
