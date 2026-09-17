# Havenline Forward Execution Standard — T10–T70

## Purpose

This standard prevents future Havenline tasks from repeating the T09 pattern of expensive reruns, cancelled evidence, symptom-only repairs, threshold changes, or acceptance tasks mutating runtime to make a gate pass.

The machine authority is `Docs/Production/FORWARD_EXECUTION_PROFILES.json`. The executable resolver/validator is `tools/havenline/production/forward_execution.py`.

## One architecture, task-aware execution

T10–T70 use one shared lifecycle with task-aware execution profiles. Do not copy a bespoke full CI pipeline into every task and allow those copies to drift. Resolve the task plan from the dependency graph, critic matrix and forward execution profile, then implement only the task-owned adapters/captures needed by that plan.

Every task resolves to:

- an execution mode: `build`, `validation_only`, `certification_only`, or `release_only`;
- an archetype describing the dominant technical risk;
- an exact dependency set and current dependency state;
- the applicable C1–C11 critics;
- a task-specific early sentinel;
- an ordered set of proof gates;
- a failure disposition.

## Exact-source rule

A candidate is an exact 40-character commit SHA. Once validation starts, that SHA finishes. Task candidate workflows MUST use `cancel-in-progress: false` or equivalent finish-running-SHA behavior. A newer candidate queues behind the running candidate.

A cancelled/superseded run is not evidence of a product defect. C0 classifies it `SUPERSEDED` with no product judgment.

## Fail-fast order

Run the cheapest decisive checks before expensive evidence fan-out. The canonical order is defined by the profile matrix, with this intent:

1. scope/dependencies and ownership;
2. reference/source contracts;
3. focused unit checks;
4. the task-specific sentinel;
5. specialist preflights/simulations such as C5 motion, C7 progression, C8 economy, C9 security, C10 LiveOps and save/device matrices;
6. impacted regression;
7. performance;
8. expensive visual/device evidence;
9. independent critics;
10. integration and post-integration regression for build-mode tasks only;
11. closeout/release proof.

If a preflight fails, stop the expensive fan-out. Preserve the exact failure evidence and invoke C0.

## C0 before repair

A terminal task failure routes to C0. The builder MUST NOT repair from a red CI line alone. A `FIX_REQUIRED` repair requires a source-bound C0 root-cause report and a machine-checkable repair plan covering the complete known blocker set.

The repair plan must identify:

- causal blocker-to-fix mapping;
- exact files allowed to change;
- protected/must-not-change files;
- repair base SHA;
- blast-radius regression;
- verification for every blocker.

A repeated identical failure fingerprint after one causal repair attempt blocks another blind code change. Re-run C0 and widen diagnosis instead. Infrastructure failures receive at most one no-code retry before C0 reclassification.

Changing a threshold, deleting evidence, changing the camera, or weakening a critic contract solely to turn red into green is not a repair.

## Critic-driven proof injection

The resolver adds required proof from the critic matrix so task packets cannot silently omit specialist evidence:

- C1: authoritative reference lock plus final source-bound visual evidence;
- C5: full-cycle motion/rigging preflight;
- C6: quantitative performance evidence, or physical performance evidence for physical certification tasks;
- C7: progression/difficulty simulation;
- C8: economy/F2P simulation;
- C9: adversarial security/exploit attack phase;
- C10: LiveOps/event simulation;
- C11: phone/tablet/foldable accessibility/device matrix, or physical-device evidence for certification tasks.

C0 never votes in C1–C11 approval math.

## Execution modes

### `build`

May change only its owned runtime paths. Requires candidate guard, impacted regression, task-specific evidence, applicable critics, integration, and post-integration regression. Foreign approved paths require a ChangeRequest and integration-owner disposition.

### `validation_only`

Examples: T58 and T62–T67. These tasks prove integrated behavior; they do not repair runtime. A product defect routes through C0 to the owning build task/change request. Validation workflows must not contain product-repair steps.

### `certification_only`

T68–T69. These tasks require sustained physical-device evidence. Emulator, desktop render, CI timing, or native-resolution screenshots cannot substitute for physical 4K/60 and thermal/device certification. A failure reopens the owning performance/runtime task through C0.

### `release_only`

T70. Release handoff closes provenance, artifact hashes, accepted-source records, rollback/recovery, physical certification and zero open mandatory defects. It does not repair runtime.

## Evidence reuse

Generate one complete source-bound evidence bundle per exact candidate SHA. Reuse already-passing evidence for the same SHA by verified hash instead of recapturing it merely because a later critic is running. Rebuild evidence only when the candidate, evidence-producing harness, or relevant acceptance contract changes.

Critics may inspect different views/summaries of the same source-bound evidence; they must not cause redundant gameplay executions without a documented need.

## Activation readiness

A future task is activation-ready only when:

- every dependency is `APPROVED` in the authoritative dependency/registry state;
- its current task packet/frozen scope is present;
- ownership is reserved without collision;
- the forward execution plan resolves and governance validation passes;
- applicable critic runtimes/safeguards are operational.

Preparation may happen while dependencies are active. Runtime implementation may not begin before activation.

## Packet requirement

Every generated T10+ task packet must include the resolved execution profile: archetype, execution mode, early sentinel, ordered gates, dependency readiness, packet readiness and failure disposition. The packet must direct builders to `forward_execution.py plan <TASK>` rather than duplicating profile logic by hand.

## Acceptance

The existing Havenline acceptance rule is unchanged: every applicable mandatory critic dimension must be strictly greater than 9.0 unrounded, target 10/10, with no unresolved mandatory defect and no averaging waiver.
