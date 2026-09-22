# T13 — Test & Evidence Plan

**Status:** PREBUILD / GOVERNANCE ONLY  
**Runtime execution:** prohibited until T13 activation  
**Required critics:** C2, C3, C4, C6, C7

## 1. Acceptance principle

T13 acceptance is evidence-based and candidate-specific. All tests, captures, replay fixtures, critic reviews, configuration hashes, and runtime source hashes must refer to the exact same candidate. A later runtime/config change invalidates affected evidence and reopens the relevant checks.

The core proof question is not merely “does difficulty change?” It is: **for the same gameplay/progression facts, does the normal-player Challenge Director produce the same bounded decision regardless of commerce/VIP/store state, while remaining deterministic, recoverable, and isolated from the owner-only Game Master path?**

## 2. Planned test files

After activation, implement the tests in the reserved T13 paths:

- `HavenlineGodot/tests/test_task13_challenge_director.gd`
- `HavenlineGodot/tests/test_task13_integration.gd`
- `HavenlineGodot/tests/capture_task13_challenge.gd`

Supporting replay fixtures and evidence-generation scripts may be added only under T13-owned runtime/tool paths after ownership is claimed.

## 3. Deterministic replay matrix

Create a fixed replay corpus covering at minimum:

| Case | Progression/performance condition | Required property |
|---|---|---|
| D01 | identical cold-start input repeated | byte-equivalent decision |
| D02 | identical established-player input repeated | byte-equivalent decision |
| D03 | same serialized sequence across fresh director instances | identical sequence of decisions |
| D04 | save/reload of T13-owned deterministic state, if any exists | identical next decision |
| D05 | explicit deterministic seed repeated, if stochastic selection is enabled | identical result |
| D06 | different wall-clock time with identical replay input | unchanged result |
| D07 | reordered irrelevant/unknown keys | unchanged semantic result |
| D08 | policy reload with same canonical content/hash | unchanged result |

If a decision depends on hidden process state, uncontrolled randomness, frame timing, or wall-clock timing, the deterministic replay gate fails.

## 4. Spend-blind equivalence matrix

Build paired fixtures where **only forbidden monetization fields differ**. The normal-player output must remain semantically and numerically identical.

Required pairs include, where the activated surrounding systems expose such values:

- no purchases vs high lifetime purchases;
- zero premium balance vs large premium balance;
- non-VIP vs VIP;
- no store visits vs repeated store visits;
- no entitlements vs many purchased entitlements;
- no advertising engagement vs high engagement;
- payer/cohort label A vs B;
- combinations of all above.

Pass criteria:

- the forbidden values are absent from the normal evaluator input boundary;
- decision output, coefficients, reason codes, and challenge band do not change;
- no derived feature used by the evaluator is sourced from those values;
- logs/evidence do not leak sensitive commerce/account data.

## 5. Performance-signal sensitivity tests

Prove the inverse of spend blindness: legitimate gameplay-performance changes **can** alter the decision when policy rules say they should.

At minimum test:

- sustained successful outcomes across multiple evaluation windows;
- sustained failure/recovery pressure;
- neutral/no-event windows;
- mixed success/failure windows;
- sparse input with optional metrics absent;
- transition across a progression band/milestone supplied by the approved T12 binding.

Each test must assert both the expected band movement and its reason code.

## 6. Bounded escalation tests

Required cases:

- repeated high-performance windows never exceed the configured normal maximum;
- one high-performance outlier cannot exceed the maximum upward step;
- escalation cooldown/hysteresis is enforced;
- malformed or extreme input values cannot generate NaN/Infinity or an out-of-envelope coefficient;
- progression transition does not bypass the challenge envelope;
- evaluation sequence overflow/edge handling is deterministic according to the chosen representation.

## 7. Recovery and anti-spike tests

Required cases:

- sustained difficulty/failure signals produce bounded de-escalation when policy allows;
- recovery movement never falls below configured minimum;
- one noisy failure sample cannot create an unbounded drop;
- alternating strong/weak windows do not oscillate faster than policy hysteresis allows;
- return toward neutral/default behavior is deterministic after the defined recovery period;
- malformed policy fallback never raises difficulty.

## 8. Policy/config validation tests

Create invalid `challenge_director_v1.json` variants and prove fail-closed handling for:

- missing version;
- non-finite values;
- min greater than max;
- invalid step size;
- negative/invalid cooldown/window values;
- duplicate policy/profile IDs;
- missing normal profile;
- malformed GM profile;
- GM profile accidentally aliased to the normal profile;
- unknown policy selection request.

Acceptance evidence records the exact policy/config hash used by valid tests.

## 9. T12 contract/integration tests

Activation must first rebind the T12 consumer contract. Then prove:

- T13 reads only the authorized progression fields;
- missing required T12 fields fail in a defined way;
- additional T12 fields do not silently become challenge inputs;
- T13 never writes T12-owned progression state;
- changed T12 contract/blob hash causes the preflight to stop until reconciled;
- a deterministic progression transition yields the expected T13 decision transition.

## 10. Game Master isolation tests

After current Game Master policy is rebound, test:

- normal player cannot request/forge the GM profile;
- unauthorized GM request fails closed;
- authorized owner path selects the approved GM profile only;
- GM path remains spend-blind;
- elevated envelope stays within its explicit GM bounds;
- normal-player envelope is unchanged by presence of the GM feature;
- owner authorization data never appears in public/client evidence;
- removing/invalidating authorization immediately removes GM elevation on the next authorized policy evaluation according to the current policy contract.

Required proof flags remain:

- `gm_challenge_profile_implemented`
- `gm_challenge_spend_blind`
- `gm_challenge_elevated_envelope_proven`

## 11. Static input-flow audit

Produce an exact-source audit of the normal-player evaluator:

1. enumerate every field accepted by its public/internal input type;
2. trace each field to its source;
3. search the T13 call graph for purchase, premium, VIP, store, entitlement, payer/cohort, and advertising symbols;
4. prove any matching symbol is outside the normal-player scoring path;
5. verify no generic dictionary/map ingestion can introduce unreviewed features;
6. verify serialized T13-owned state contains no hidden commerce-derived feature.

Any untraceable scoring input is a mandatory defect.

## 12. Runtime capture plan

`capture_task13_challenge.gd` should generate deterministic, reviewable evidence rather than decorative screenshots. Capture at least:

- baseline/default challenge state;
- bounded escalation across multiple windows;
- recovery/de-escalation sequence;
- paired spend-blind equivalence case;
- normal vs authorized GM envelope demonstration using sanitized identities;
- malformed-policy safe fallback.

For visual/UI-facing feedback introduced by T13, capture meaningful before/after states at usable scale. If T13 remains non-visual, machine-readable replay evidence is primary and screenshots are supplemental only.

## 13. Evidence manifest

The future build should produce a manifest under `Docs/Production/T13/` or a task-local evidence path containing, at minimum:

- integration base SHA;
- T13 candidate SHA;
- source file hashes;
- `challenge_director_v1.json` hash;
- current T12 consumer contract hash;
- current Game Master policy/standard hashes used for review;
- replay fixture hashes;
- test command names/results;
- capture/evidence file hashes;
- critic IDs, scores, findings, and repair-loop references;
- unresolved defect count.

No evidence set may claim PASS if any mandatory item is missing or references a different candidate.

## 14. Critic acceptance matrix

The critic IDs and responsibilities below must match the canonical `Docs/Production/CRITIC_MATRIX.json`. T13-specific proof may add requirements inside a critic's real domain, but may not rename or repurpose the critic.

### C2 — Technical / Visual Integrity Critic
Must verify deterministic decision/state consistency, bounded/error behavior, exact T12 integration semantics, no contradictory challenge output, and the functional GM-vs-normal authorization/isolation behavior required by the current Game Master contract.

### C3 — Havenline Gameplay Identity Critic
Must verify challenge behavior reinforces Havenline's physical/simple-context loop, avoids unnecessary control complexity or management-game drift, and makes the elevated GM profile harder through coherent world pressure rather than arbitrary grind.

### C4 — Gameplay UX / Readability Critic
Must verify danger, recovery, world-response and next-action clarity across challenge changes; escalation/de-escalation must remain understandable at gameplay scale without clutter, hidden friction, or unreadable feedback.

### C6 — Performance Critic
Must quantitatively verify bounded Challenge Director CPU/frame-time and memory cost, no per-frame full-history/full-world rebuild, no avoidable allocation spikes, and preserved mobile performance headroom on the exact candidate. C6 is the quantitative specialist gate.

### C7 — Progression / Difficulty Critic
Must verify meaningful rising difficulty, no HP-only inflation, no impossible spikes or boring stretches, bounded normal-player escalation/recovery, spend-blind paired equivalence, and the authorized GM_CHALLENGE envelope without breaking progression fairness.

Spend-blind input-flow proof and GM authorization/non-spoof tests remain mandatory acceptance evidence even though they do not change the canonical critic identities.

Every mandatory reviewed dimension must be **strictly greater than 9.0 unrounded**. Target is 10/10. One mandatory failure blocks approval regardless of average score.

## 15. Repair loop

For every failed test or critic finding:

1. record the defect with exact candidate/evidence reference;
2. identify whether the defect is algorithm, policy data, interface, fairness, isolation, or evidence quality;
3. repair only within T13-owned scope unless a structured upstream change request is required;
4. rebuild/re-run affected tests;
5. rerun every critic/evidence item invalidated by the change;
6. keep the task unapproved until zero mandatory defects remain.

## 16. Final acceptance checklist

T13 future runtime approval requires all of these on the same candidate:

- [ ] dependency rebind and activation preflight passed;
- [ ] deterministic replay matrix passed;
- [ ] spend-blind paired-equivalence matrix passed;
- [ ] legitimate gameplay-sensitivity matrix passed;
- [ ] escalation/recovery/anti-spike tests passed;
- [ ] malformed-policy tests passed;
- [ ] T12 integration tests passed;
- [ ] GM isolation/elevated-envelope tests passed;
- [ ] static input-flow audit has zero unexplained scoring inputs;
- [ ] evidence manifest is complete and hash-consistent;
- [ ] C2/C3/C4/C6/C7 all pass >9.0 unrounded;
- [ ] zero unresolved mandatory defects.
