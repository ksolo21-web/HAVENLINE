# T13 — Challenge Director Implementation Blueprint

**Status:** PREBUILD / GOVERNANCE ONLY — runtime implementation remains forbidden until T13 is activated.  
**Task:** Progressive Difficulty & spend-blind Challenge Director  
**Future builder branch:** `havenline/T13-challenge-director`  
**Dependency:** T12  
**Forward preparation baseline:** `codex/havenline-sequential-task-01` @ `6db1207b2b8725cb4591d4a55670aa48eeb2c3fb`

## 1. Purpose

T13 owns the decision layer that converts approved progression context plus gameplay-performance history into a bounded challenge profile. Normal-player decisions must be completely spend-blind. T13 does not own enemy/weapon progression, billing, VIP, store logic, telemetry backend infrastructure, or T12 progression state.

This document is an implementation handoff, not permission to build runtime code early. At activation, every external interface and hash must be rebound to the exact current integration head before implementation starts.

## 2. Required runtime files after activation

- `HavenlineGodot/scripts/challenge_director.gd`
- `HavenlineGodot/data/challenge_director_v1.json`
- `HavenlineGodot/tests/test_task13_challenge_director.gd`
- `HavenlineGodot/tests/test_task13_integration.gd`
- `HavenlineGodot/tests/capture_task13_challenge.gd`

No runtime file above may be created or modified while T13 is dependency-locked.

## 3. Input boundary

### 3.1 T12 progression context

T13 may consume only the fields authorized by `T12_CONSUMER_BINDING.json`:

- `current_level_id`
- `current_region_band_id`
- `completed_milestone_ids`
- `progression_intents`

T12 remains the source of progression context. T13 must not require T12 to calculate difficulty, spawn pressure, enemy tuning, adaptive challenge decisions, or payer-related state.

### 3.2 T13-owned performance window

The runtime implementation should normalize gameplay observations into a deterministic, bounded `PerformanceWindow` owned by T13. The concrete event adapters are rebound at activation; the internal normalized shape should contain only gameplay-performance facts needed for challenge decisions, such as:

- recent objective attempts and outcomes;
- recent completion/abandonment timing buckets;
- recent defeat/down/recovery counts where those events exist in the activated runtime;
- recent resource or rescue objective completion outcomes where those events exist;
- a monotonically increasing evaluation sequence number.

Missing optional observations must have explicit neutral defaults. No field may be inferred from commerce, identity tier, entitlements, ad activity, purchases, premium balance, VIP status, or store behavior.

### 3.3 Forbidden normal-player inputs

The normal-player decision path must fail review if it reads, accepts, derives, joins, or caches any of the following:

- purchase history or lifetime spend;
- premium currency balance;
- VIP/subscription status;
- store visits, checkout activity, offers, entitlements, or SKU ownership;
- payer segmentation or monetization cohorts;
- advertising engagement;
- any proxy explicitly derived from those values.

Unknown keys supplied to a normal-player decision request must not silently become scoring inputs.

## 4. Deterministic decision model

Implement one pure decision boundary that can be replayed from serialized inputs. Conceptually:

`ChallengeDecision = evaluate(ProgressionContext, PerformanceWindow, ChallengePolicy, evaluation_sequence)`

The decision result should contain only T13-owned challenge outputs and audit metadata. It must not directly mutate T12 progression or T21 combat data.

Minimum output contract:

- policy/profile identifier;
- discrete challenge band or tier;
- bounded challenge coefficients owned by T13;
- reason codes explaining the decision inputs that mattered;
- evaluation sequence;
- policy version/hash used for the decision;
- explicit indication of normal-player vs authorized Game Master policy path.

If stochastic selection is ever required by the activated design, it must be driven by an explicit deterministic seed included in replay evidence. Hidden wall-clock or process-global randomness is forbidden.

## 5. Bounded escalation and recovery

`challenge_director_v1.json` should contain the tunable envelope rather than scattering tuning constants through code. The activated implementation must validate the data before use.

Required policy properties:

- minimum and maximum normal-player challenge bounds;
- finite step sizes between bands;
- maximum upward movement per evaluation window;
- maximum downward movement per evaluation window;
- escalation cooldown / hysteresis rule to prevent rapid oscillation;
- recovery/de-escalation rule after sustained difficulty signals;
- cold-start/default profile;
- malformed-policy fallback behavior that is safe and deterministic.

A single noisy observation must not create an unbounded challenge spike. The algorithm must prove monotonic bounds and deterministic recovery under the same replay sequence.

## 6. Spend-blind architecture rule

Keep normal-player evaluation behind a narrow typed/data boundary that never receives commerce state. Do not solve spend blindness with a late `if payer: ignore` filter. The forbidden data should be absent from the normal-player evaluator by construction.

The static/dynamic audit should be able to answer:

1. Which fields enter the evaluator?
2. Where did each field originate?
3. Can any commerce/VIP/store field reach that path directly or through a derived feature?
4. Does changing only spend-related fixture data leave every normal-player decision byte-for-byte equivalent?

## 7. Game Master isolation

The owner-only `GM_CHALLENGE` path is a separate authorized policy mode. It may use the approved elevated challenge envelope only after current Game Master policy is rebound at activation.

Mandatory separation:

- normal players can never select or spoof the GM profile;
- GM authorization is validated outside the normal-player scoring inputs;
- GM decisions remain spend-blind;
- GM elevation changes only the allowed challenge envelope/profile, not identity or progression state;
- audit evidence identifies the policy path without exposing owner credentials or private identifiers;
- failure to validate GM authorization falls closed to the normal policy path or rejects the request, according to the activated policy contract.

## 8. Data/config validation

On load, `challenge_director_v1.json` must be rejected or safely defaulted if any required invariant is violated, including:

- non-finite numeric values;
- inverted min/max bounds;
- negative window/cooldown values where forbidden;
- escalation/recovery steps outside the declared envelope;
- duplicate/unknown policy identifiers;
- GM envelope that is not explicitly separated from the normal envelope;
- missing policy version.

The fallback must be deterministic and must never increase challenge because of malformed data.

## 9. Integration behavior

T13 should expose a narrow API that downstream systems can query without learning how the score is calculated. Runtime consumers should receive the resolved `ChallengeDecision` or a stable subset of it, not the raw performance history.

T13 must not:

- rewrite T12 progression state;
- author T21 enemy/weapon progression values;
- write monetization segmentation;
- create a telemetry backend;
- persist hidden user-spend features in challenge state.

## 10. Auditability and local evidence

Every evaluated replay used for acceptance should be serializable into a deterministic fixture containing:

- sanitized input context;
- sanitized performance window;
- policy version/hash;
- expected decision;
- reason codes;
- replay seed if applicable.

Acceptance evidence must make spend blindness inspectable without exposing private account information.

## 11. Activation-time rebind checklist

Before any T13 runtime code is created:

1. Confirm T12 is APPROVED/integrated in graph, registry, and task gates.
2. Confirm T12 active path ownership is released as required.
3. Re-read and hash the current T12 downstream consumer contract.
4. Reconcile `T12_CONSUMER_BINDING.json`; fail closed on drift.
5. Re-read current Game Master policy/account standard and required proof flags.
6. Re-check all T13 planned paths against current active ownership.
7. Refresh forward contract hashes/task packet from the exact integration head.
8. Require zero unresolved T13 preparation defects.
9. Apply `@reservation:T13`, claim T13, and create/rebase the future builder branch only after the preceding gates pass.

## 12. Done definition for the future build

T13 is not complete merely because a difficulty number changes. Completion requires all of the following on the same candidate:

- deterministic replay passes;
- spend-blind equivalence proof passes;
- bounded escalation/recovery and anti-spike proof passes;
- malformed-policy/fallback tests pass;
- GM policy isolation and elevated-envelope proof passes;
- T12 integration contract tests pass;
- required C2/C3/C4/C6/C7 critic evidence is exact-source;
- every mandatory reviewed dimension is strictly greater than 9.0 unrounded, target 10/10;
- zero unresolved mandatory defects.
