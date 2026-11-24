# T14 — Test & Evidence Plan

**Status:** PREBUILD / GOVERNANCE ONLY  
**Runtime execution:** prohibited until T14 activation  
**Required critics:** C2, C9

## 1. Acceptance principle

T14 acceptance must prove that versioned save data survives normal round trips, supported upgrades, corruption, and interrupted writes without silently losing or inventing approved game state.

All fixtures, recovery captures, hashes, and critic evidence must refer to the same exact runtime candidate and schema/migration data files. Any change to serialization, migration, validation, or recovery logic invalidates affected evidence.

## 2. Planned runtime test files

After activation:

- `HavenlineGodot/tests/test_task14_save_versioning.gd`
- `HavenlineGodot/tests/test_task14_recovery.gd`

Additional fixtures/tools may be created only inside T14-owned paths after the task is claimed.

## 3. Canonical fixture set

Create deterministic, human-reviewable fixtures for at least:

- empty/new-game approved state;
- minimal valid populated state;
- representative fully populated approved state;
- edge/boundary numeric and collection values allowed by current contracts;
- each supported historical schema version;
- intentionally corrupt variants;
- future/unsupported schema version.

Fixtures must use sanitized synthetic state and must not contain real user credentials or private account identifiers.

## 4. Current-schema round-trip matrix

For every approved upstream section active at T14 activation:

1. construct or capture an approved deterministic state fixture;
2. serialize through T14;
3. close/reopen the save;
4. validate/decode it;
5. restore through the approved adapter boundary;
6. recapture canonical state;
7. compare semantic equality with the original fixture.

Required cases:

| Case | Condition | Required result |
|---|---|---|
| R01 | empty/new state | exact approved defaults after round trip |
| R02 | representative state | semantic equality |
| R03 | max allowed bounded values | semantic equality, no overflow/coercion |
| R04 | optional fields absent | explicit approved defaults only |
| R05 | unknown optional field allowed by policy | deterministic preserve/ignore behavior |
| R06 | repeated save/load cycles | no cumulative drift |
| R07 | canonical serialization repeated | stable canonical result where defined |

Any unowned field mutation is a mandatory defect.

## 5. Schema-validation matrix

Prove defined handling for:

- valid current schema;
- missing schema identifier;
- missing schema version;
- wrong format identifier;
- wrong type for required field;
- missing required upstream section;
- unknown required section;
- duplicate identifiers where representation permits them;
- non-finite/invalid numeric state;
- collection above configured bound;
- unsupported older version;
- future version.

A future or unknown schema must not be guessed into the current format.

## 6. Migration matrix

For every migration path declared in `save_migrations_v1.json`, create a fixture with known source state and expected current-state result.

Required assertions:

- source schema validates before migration;
- exactly the declared migration sequence runs;
- each intermediate state validates;
- final current state matches expected semantic state;
- repeated execution against the same original fixture is deterministic;
- there is no cycle or ambiguous alternate path;
- unsupported source version fails without modifying the original save;
- failed step never promotes the intermediate candidate;
- upstream semantic values not named by the migration are preserved.

If a migration needs an upstream semantic decision rather than a mechanical schema transform, it must be an explicit reviewed migration rule or structured upstream change request.

## 7. Corruption matrix

Generate exact corrupt variants from a valid fixture:

- truncation at several byte/character offsets;
- malformed encoding/data syntax;
- integrity/checksum mismatch;
- missing envelope fields;
- wrong section type;
- semantically invalid upstream section;
- invalid version value;
- duplicated or malformed migration metadata;
- oversized payload/collection beyond declared bound;
- random bit/text mutation where practical.

Required result: the corrupt candidate is rejected before live state mutation. If a valid backup exists, recovery follows the deterministic backup path.

## 8. Atomic-write interruption matrix

Inject a deterministic failure/restart point at every write transition defined by the implementation blueprint:

| Case | Injected interruption | Required state after restart |
|---|---|---|
| I01 | before temp candidate creation | prior valid primary loads |
| I02 | during temp write | prior valid primary loads; partial temp ignored/cleaned safely |
| I03 | after temp write, before validation | prior valid primary remains authoritative |
| I04 | after candidate validation, before backup rotation | prior valid primary remains recoverable |
| I05 | after backup rotation, before promotion | at least one validated last-known-good state remains recoverable |
| I06 | during promotion primitive | deterministic recovery path, no silent partial success |
| I07 | after promotion, before final readback | loader validates primary or falls back safely |
| I08 | final readback failure | failed candidate not accepted as successful save |

The exact injection mechanics must be deterministic and test-only; they must not depend on physically killing CI runners at random timing.

## 9. Migration interruption matrix

For a multi-step migration chain, inject failure:

- before first migration;
- during each individual migration transform;
- after each intermediate transform before validation;
- after final transform before candidate write;
- during migrated candidate promotion.

After restart, the original/last-known-good data must still be recoverable and the migration may be retried deterministically.

## 10. Backup recovery tests

Required cases:

- valid primary + valid backup → primary loads;
- corrupt primary + valid backup → backup recovery result;
- missing primary + valid backup → defined backup recovery result;
- valid primary + corrupt backup → primary loads; corrupt backup not promoted;
- corrupt primary + corrupt backup → typed unrecoverable outcome, no fabricated state;
- future-version primary + older valid backup → behavior follows explicit compatibility policy, never silently downgrades if that would violate contract;
- stale temporary candidate present → ignored/reconciled according to deterministic startup rules.

## 11. Transactional restore tests

Use test adapters that can deliberately fail validation or apply at each upstream section boundary.

Prove:

- no adapter `apply` runs before all sections validate;
- a validation failure leaves live state unchanged;
- if restore uses staged replacement, the old live state remains until commit;
- an injected apply failure cannot be reported as successful partial restore;
- rollback or restart behavior is explicit and deterministic;
- recaptured state after successful restore matches the fixture.

## 12. Dependency adapter tests

After activation-time rebind to approved T08/T10/T12 interfaces, add contract tests for each adapter:

- capture returns only approved serializable fields;
- restore accepts the current approved fixture;
- unknown/unapproved fields do not silently become authoritative;
- adapter failure is typed and propagates to T14 transaction failure;
- T14 does not mutate upstream state during validation;
- interface/hash drift stops preflight until reconciled.

No pre-T13 task must be edited to make a T14 test pass. Any required upstream change goes through its normal structured change process outside this preparation branch.

## 13. First-run/no-save behavior

Test clean install/no-save state separately from corruption:

- no primary and no backup returns the approved first-run outcome;
- no phantom corruption warning is generated;
- T14 does not invent gameplay state beyond approved upstream defaults;
- first successful save produces a valid current-schema envelope.

## 14. Repeated-cycle durability

Run deterministic repeated cycles on representative state:

- save → load → save for a bounded stress count;
- migrate → load → save for every supported old schema;
- backup recovery → save new primary → load.

Assert no semantic drift, schema regression, unbounded backup growth, or generation-sequence ambiguity.

## 15. Evidence manifest

The future build must produce task-local evidence containing at minimum:

- exact integration base SHA;
- exact T14 candidate SHA;
- `save_versioning.gd` hash;
- `save_schema_v1.json` hash;
- `save_migrations_v1.json` hash;
- rebound dependency interface/hash records;
- fixture hashes;
- test suite/command results;
- atomic-write interruption matrix results;
- migration matrix results;
- corruption/recovery results;
- critic IDs, scores, findings, and repair-loop references;
- unresolved mandatory defect count.

## 16. C2 functional critic

C2 must inspect actual tests/evidence for:

- lossless approved-state round trips;
- explicit compatibility handling;
- deterministic migration;
- safe failure behavior;
- transactional restore;
- no false success after partial operation;
- stable typed outcomes.

## 17. C9 data durability / recovery critic

C9 must inspect actual interruption and corruption evidence for:

- last-known-good preservation;
- atomic promotion behavior on the actual target platform/file API;
- bounded backup policy;
- migration rollback/retry safety;
- corrupt-primary backup recovery;
- no destructive promotion before validation;
- no untested assumption that desktop file semantics equal Android semantics.

Both critics must score every mandatory reviewed dimension **strictly greater than 9.0 unrounded**, target 10/10. A failed mandatory durability scenario blocks approval regardless of average score.

## 18. Repair loop

For every failure:

1. record exact fixture, injection point, candidate hash, and observed state;
2. classify schema, serialization, migration, write-atomicity, restore-transaction, or evidence defect;
3. repair only within T14-owned scope unless a structured dependency-interface change is required;
4. rerun the failed case and all cases invalidated by the change;
5. rerun C2/C9 evidence when the runtime behavior changed;
6. keep T14 unapproved until zero mandatory defects remain.

## 19. Final acceptance checklist

- [ ] activation preflight/rebind passed on the exact current integration head;
- [ ] all current-schema round-trip fixtures passed;
- [ ] schema-validation matrix passed;
- [ ] every supported migration fixture passed;
- [ ] corruption matrix passed;
- [ ] atomic-write interruption matrix passed;
- [ ] migration interruption matrix passed;
- [ ] backup recovery matrix passed;
- [ ] transactional restore tests passed;
- [ ] rebound T08/T10/T12 adapter tests passed;
- [ ] repeated-cycle durability tests passed;
- [ ] evidence manifest is hash-consistent and complete;
- [ ] C2 and C9 pass >9.0 unrounded;
- [ ] zero unresolved mandatory defects.
