# T14 — Save-State / Versioning Foundation Implementation Blueprint

**Status:** PREBUILD / GOVERNANCE ONLY — runtime implementation remains forbidden until T14 is activated.  
**Task:** Save-state/versioning foundation  
**Future builder branch:** `havenline/T14-save-versioning`  
**Dependencies:** T08, T10, T12  
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`

## 1. Purpose

T14 owns the foundational versioned-save layer needed by later Havenline systems. It must make approved game state serializable, recoverable, migratable, and testable without taking ownership of upstream gameplay state itself.

The system must protect players from partial writes, incompatible schema changes, malformed payloads, and interrupted migration. A save that cannot be proven valid must never silently replace the last known-good state.

This document is an implementation handoff only. Every dependency interface must be rebound from the exact current integration head at activation before runtime code is created.

## 2. Reserved runtime files after activation

- `HavenlineGodot/scripts/save_versioning.gd`
- `HavenlineGodot/data/save_schema_v1.json`
- `HavenlineGodot/data/save_migrations_v1.json`
- `HavenlineGodot/tests/test_task14_save_versioning.gd`
- `HavenlineGodot/tests/test_task14_recovery.gd`

No runtime file above may be created or modified while T14 is dependency-locked.

## 3. Ownership boundary

T14 owns:

- save envelope/schema versioning;
- serialization/deserialization orchestration;
- schema validation;
- migration sequencing;
- atomic write/replace behavior;
- last-known-good backup/recovery mechanics;
- corruption/interruption detection needed for safe recovery;
- deterministic fixtures and round-trip tests.

T14 does **not** own the semantic truth of T08, T10, or T12 gameplay/progression state. Upstream systems expose approved snapshot/restore contracts at activation; T14 serializes those values without inventing or mutating gameplay rules.

## 4. Save envelope

Use one explicit top-level versioned envelope rather than unversioned ad-hoc dictionaries. The exact activated schema is defined in `save_schema_v1.json`; conceptually it should include:

- save format identifier;
- schema version;
- save generation/sequence;
- creation/update metadata that is not used as gameplay authority;
- upstream state sections keyed by stable contract identifiers;
- optional T14 metadata required for migration/recovery;
- integrity metadata appropriate to corruption detection;
- explicit compatibility flags/metadata if required by the activated platform design.

The envelope must distinguish **format/schema identity** from app/build version. A new app build must not automatically imply an incompatible save schema.

## 5. Upstream state adapters

At activation, define narrow adapters for T08, T10, and T12 against their then-current approved interfaces. Each adapter must provide:

- `capture`/snapshot operation returning only approved serializable state;
- schema/section identifier and version;
- validation operation for decoded state;
- restore/apply operation that returns success/failure without partially mutating live state;
- deterministic test fixture support.

T14 must not scrape arbitrary runtime nodes or serialize entire object graphs as a shortcut. Every persisted field needs an owned source contract.

If an upstream interface is not yet suitable for atomic restore, T14 activation must stop and open a structured interface/change request rather than inventing an unsafe workaround.

## 6. Serialization rules

The activated implementation must define canonical serialization behavior so round-trip and fixture comparisons are stable.

Required rules:

- explicit defaults for optional fields;
- explicit handling of unknown fields by schema version;
- no silent numeric type coercion that can lose precision;
- stable identifiers instead of transient object/node references;
- no runtime-only handles, credentials, or process-specific values in saves;
- deterministic ordering/canonicalization where evidence compares serialized content;
- bounded size/collection validation where unbounded input could cause unsafe load behavior.

## 7. Atomic write protocol

A save operation must never overwrite the last known-good save before the replacement is fully written and validated.

Target protocol:

1. Capture an internally consistent approved-state snapshot.
2. Serialize to a new temporary candidate.
3. Flush/close the candidate using the platform-safe file API.
4. Re-open and decode the candidate.
5. Validate envelope, schema, section contracts, and integrity metadata.
6. Only after validation, rotate/preserve the previous last-known-good save.
7. Atomically promote the validated candidate using the safest available Godot/platform primitive.
8. Re-open the promoted save and perform a final validation/readback.
9. If any step fails, preserve or restore the last-known-good save and report a typed failure.

Activation implementation must document the actual Android/platform file primitive used for the promotion step. Do not assume desktop rename semantics are atomic without evidence.

## 8. Backup and recovery model

Maintain a bounded recovery chain rather than accumulating uncontrolled copies. The minimal model should preserve:

- current validated save;
- one last-known-good backup or another explicitly bounded policy approved at activation;
- temporary candidate only during an in-progress write/migration.

Load order must be deterministic. A corrupt primary may fall back to a validated backup, but the corrupt primary must not be treated as valid or overwrite the backup.

Recovery must emit a typed outcome such as:

- primary loaded;
- backup recovered;
- migration completed;
- recoverable save unavailable;
- incompatible future schema;
- corrupt/unreadable payload.

The exact user-facing handling belongs to the activated UI/product flow; T14 owns the trustworthy state result.

## 9. Schema versioning

`save_schema_v1.json` must explicitly describe the initial supported envelope and section expectations.

Rules:

- every persisted save carries a schema version;
- loaders must know the current version and explicitly enumerate supported older versions;
- future/unknown versions fail closed rather than being guessed into the current schema;
- schema version changes only when compatibility/migration behavior actually requires it;
- build/version strings are informational unless the schema contract explicitly says otherwise.

## 10. Migration registry

`save_migrations_v1.json` should declare the supported migration graph/sequence. Prefer simple, ordered one-step migrations over opaque “jump to latest” logic.

Required properties:

- each migration declares source and destination schema versions;
- the migration path is acyclic and deterministic;
- every supported old version has exactly one approved path to current;
- migrations validate their input before transforming it;
- each step validates its output before the next step;
- original/backup data remains available until the full chain and final readback pass;
- a failed migration never promotes a partial result;
- migration code does not silently repair semantically invalid upstream state unless that repair is explicitly part of the migration contract.

## 11. Transactional load/restore

Decoding a save and applying it to live game state are separate phases.

Required sequence:

1. Read bytes/text.
2. Decode envelope.
3. Validate schema/integrity.
4. Migrate in isolated data form if required.
5. Validate every upstream section through its adapter.
6. Stage a complete restore plan.
7. Apply all sections transactionally or through a defined rollback-safe sequence.
8. Report success only after the full approved state is restored.

If the activated upstream systems cannot support a rollback-safe restore, the design must introduce an explicit staging/validation boundary before any live state mutation.

## 12. Corruption detection

The foundation needs enough integrity metadata to distinguish obvious truncated/modified/corrupt saves from valid saves. The implementation must not present a non-cryptographic checksum as an authentication/security boundary.

Test at least:

- truncation;
- malformed encoding/JSON/data structure;
- wrong field types;
- missing required sections;
- impossible schema version;
- integrity mismatch;
- oversized/bounded collection violations;
- valid envelope with semantically invalid upstream section.

## 13. Interruption safety

Design for interruption at every write/migration transition:

- before candidate creation;
- during candidate write;
- after write before validation;
- after validation before backup rotation;
- during promotion;
- after promotion before final readback;
- during each migration step.

After simulated restart, the loader must deterministically choose a validated recoverable state. No interruption point may leave both primary and backup irrecoverably invalid because of T14’s own procedure.

## 14. Compatibility behavior

Define explicit behavior for:

- current schema;
- each supported older schema;
- unsupported older schema;
- future schema;
- missing schema version;
- clean first-run/no-save state.

“Try to load it anyway” is not an acceptable compatibility strategy.

## 15. Observability without leaking state

T14 should expose typed operational outcomes and sanitized reason codes for tests/support. Logs must not dump entire save payloads or sensitive account identifiers by default.

Useful reason categories include:

- decode failure;
- schema mismatch;
- section validation failure;
- migration unavailable;
- migration failure;
- candidate write failure;
- primary corruption;
- backup recovery success/failure;
- post-promotion readback failure.

## 16. Activation-time reconciliation

Before T14 runtime implementation begins:

1. Confirm T08, T10, and T12 are APPROVED/integrated in graph, registry, and task gates.
2. Confirm required active ownership has been released.
3. Re-read current upstream snapshot/restore interfaces without modifying those tasks.
4. Reconcile any T12 consumer binding or current forward contract used by T14.
5. Re-check T14 planned paths against all active ownership.
6. Refresh current dependency/interface hashes and task packet.
7. Require zero unresolved T14 preparation defects.
8. Apply `@reservation:T14`, claim T14, and create/rebase `havenline/T14-save-versioning` only from the exact post-activation integration head.

## 17. Done definition for the future build

T14 runtime approval requires all of the following on one exact candidate:

- current-schema round trip is lossless for all approved state;
- every supported migration fixture reaches the expected current state;
- corrupt and incompatible saves fail safely;
- interruption matrix preserves a recoverable last-known-good state;
- primary-to-backup recovery is deterministic;
- no partial restore can be accepted as success;
- T08/T10/T12 adapter integration tests pass against current approved interfaces;
- C2 and C9 exact-source evidence each score strictly greater than 9.0 unrounded, target 10/10;
- zero unresolved mandatory defects.
