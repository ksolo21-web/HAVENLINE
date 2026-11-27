# Havenline actor-validator repair

Exact base: `fd2e12c8734f49cda7eb3bbf97887406bd03a704`. Scope: production tooling and focused tests. No game, motion, runtime or device approval.

## Outcome

The validators now prevent the declared seven-pet combat roster from being weakened silently, and enforce unresolved survivor profiles at the correct task phase. Current closure reruns the authoritative evaluator; a stored passed receipt cannot substitute for current checks.

## Changes

1. Canonical seven-species presence, attack flag, attack capability, species identity, named attack-profile identity/action/motion declaration and owning-task requirement lists now fail closed; owl accepts aerial_attack without a human attack capability.
2. Pet owning tasks and integrated pet coverage require the canonical attacks and propagate C5 using the current task/critic policies; declared profile presence remains separate from motion review.
3. Task-freeze placeholders are recognized even if configurable tokens omit them. Only the exact survivor_animation_profile=T23_FREEZE_REQUIRED field is deferred before its owner phase; invalid owner/field/unknown or wrong-actor/action bindings reject.
4. T23, T31 and region integration require ready and already-upstream resource survivor bindings. Existing dependency ancestry preserves T09-before-T23 and T23-before-fishing/crop scope; T32 does not pull in unready later-region resources. Full-game acceptance checks all canonical registered resources.
5. Introducing resources derive player coverage plus human roles already required by that task; early T09 does not acquire a future T31-helper or T23-survivor prerequisite. Region/T32/full integration derive all applicable human resource profiles directly. T44–T52 require C5 whenever this evaluation yields resource action profiles, including existing-clip reuse, false animation_delta and an omitted introduction list; the reason is regional_resource_contact.
6. Unknown/invalid coverage, duplicate IDs, malformed animation_delta and supplied stale registry hashes reject. The first evaluator run emits current hashes if no input binding was supplied; terminal closure still requires exact bindings.
7. Closure now reruns the current evaluator on the actual manifest and uses its C5 requirement. Stored receipts must also bind exact candidate, current validator implementation and current registries, and must be coverage evaluation rather than schema-only. Passed historical/stale output cannot waive a live failure.
8. All remaining closure retention, critic, current acceptance, source/signoff, gate and historical-integrity checks are preserved. Historical receipt bytes and canonical task authorities were not edited.

## Phase behavior

| Scope | Expected behavior |
|---|---|
| T09 | PASS for complete declared acquisition coverage, with metal/fuel survivor fields explicitly deferred to T23; no survivor motion claim. |
| T23 | FAIL on current unresolved metal/fuel survivor markers; future unready fish/wheat do not create backward prerequisites. |
| T31_T44_T52_and_final_integration | FAIL when applicable survivor fields remain unresolved, even if a stored validator receipt says passed. |
| T24_T30 | Every species retains a canonical real-attack requirement and C5; declared coverage success is not actual attack or rig proof. |
| T05 | Unrelated frozen scope remains non-applicable when current registries are otherwise valid. |

### Deliberate forward C5 strengthening

For T44–T52, C5 is required when the evaluation derives at least one resource action profile. The reason is `regional_resource_contact`: actual contact/use states need review in the regional geometry and environment. Neither `animation_delta=false` nor an omitted introduction list waives this floor. Existing clips may be reused; no new animation is required merely to satisfy the gate. Root explicitly accepted this strengthening for the accompanying standards.

## Verification

The four assigned files were frozen by SHA-256 before these final focused runs and remained byte-identical throughout. The separate critic independently reran the focused checks and six additional boundary probes; the bounded code retest passed.

| Focused suite | Tests | Result |
|---|---:|---|
| test_resource_actor_contract.py | 30 | PASS |
| test_closure_resource_actor.py | 9 | PASS |
| test_reference_acceptance.py | 18 | PASS |

**57 tests passed across 3 suites on the frozen four-file candidate.** Tests cover every species, named profiles, capabilities, early/late role phases, actor/action references, resource-derived profile coverage, contact-review requirements, unknown coverage, stale bindings and passed stale receipts.

Canonical registries, dependencies, ownership, lifecycle registry and acceptance-policy bytes remain unchanged. The assigned diff is whitespace-clean. Full command outputs and exact source hashes are in the JSON.

## Repair and retest history

- Acquisition-action aliases initially followed profile-name verbs instead of canonical action values. Repair: Use chop→gather_wood and fishing→fishing; preserve unchanged registry and rerun tests. Status: `FIXED_RETEST_PASSED`.
- Independent regional probe found missing derived player/helper profile coverage and false-delta C5 waiver for newly introduced resources. Repair: Derive all applicable regional human profiles, preserve early producer role phases, and require C5 for actual regional resource action coverage even if the introduction list is omitted; allow existing clips. Status: `FIXED_INDEPENDENT_RETEST_PASSED`.
- Regional human-only test fixture inadvertently claimed all animal profiles. Repair: Restrict the fixture to declared human actors/profiles; do not weaken validator identity checks. Status: `FIXED_RETEST_PASSED`.

Rejected runs remain preserved: [ACTOR_VALIDATOR_REPAIR_REJECTED_R1.json](ACTOR_VALIDATOR_REPAIR_REJECTED_R1.json), [ACTOR_VALIDATOR_REPAIR_REJECTED_R2.json](ACTOR_VALIDATOR_REPAIR_REJECTED_R2.json).

## Changed files

| File | Change | Frozen candidate SHA-256 |
|---|---|---|
| `tools/havenline/production/resource_actor_contract.py` | MODIFIED | `7a637cdfd2f31231de355a79c207fb01da9909a06f7984c4ccc0445e2454a434` |
| `tools/havenline/production/tests/test_resource_actor_contract.py` | MODIFIED | `9198ad00426cb0a63a1b43a8854ba1ee5ffa682162d46d454e894fad863a626a` |
| `tools/havenline/production/closure_validator.py` | MODIFIED | `467a68c72a563cf46dd8d46a0e95039749c4f503b647671906248c862f85a9fd` |
| `tools/havenline/production/tests/test_closure_resource_actor.py` | NEW_TEST | `6f2846a1b806ac5bd2605ae8cbe8981a5bee9d0136680c762df7bc08c92df935` |

## Independent review

The separate critic found and requested the alias and regional fixes recorded above, then independently confirmed 39/39 actor/closure tests, 18/18 current-acceptance tests and 6/6 supplemental probes on the frozen hashes. Those probes replay omitted player/helper coverage, omitted introduction flags, reused clips and the early T09 deferral boundary. No substantive blocker remains within this four-file repair scope. The JSON binds the three independent receipts. Whole-candidate approval and actual gameplay remain separate and ungranted.

## Limits

- No runtime, assets, canonical resource/actor/animation registry, task dependencies/states or remote branches changed.
- No actual clips, gameplay, audio playback, balance, Android build or device run was performed.
- The placeholder definitions remain pending production owner work; this repair blocks false approval and does not invent or complete survivor assets.
- The standalone evaluator validates supplied registry hashes when present; terminal closure requires the binding, current receipt and all other existing final evidence.

[Machine-readable repair evidence](ACTOR_VALIDATOR_REPAIR.json)
