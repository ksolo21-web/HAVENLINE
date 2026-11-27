# Havenline whole-game gap closure — 2026-11-27

This package records the selected forward design and a bounded audit of Havenline's existing launch plan. **All seven pets must attack and have useful specialties.** Known behavior choices are now selected; actual implementation, numerical tuning, native assets, full motion/audio and device proof remain separate work.

## Read the decisions

- [Completeness standard](../../COMPLETENESS_STANDARD.md) explains stakes, companions, progression, value chains and cross-system behavior.
- [Authoritative contract](../../WHOLE_GAME_COMPLETENESS.json) contains **24 gap dispositions and 12 selected decisions**, including explicit dispositions for prior D01–D05.
- [Actor/combat contract](ACTORS_COMBAT_GAPS.md) contains **12 attack rules**, all seven species/profile/render bindings and their future proof scenarios.
- [Progression/economy design](PROGRESSION_ECONOMY_GAPS.md) contains **100 authored level outcomes**, ten region briefs, 22 resource/product/currency/concept dispositions, and selected/reserved enemy art.
- [Transaction/recovery matrix](TRANSACTIONS_AND_RECOVERY.json) contains ten value-bearing boundaries, including interrupted cash spending, plot contributions, combat rewards and earned event claims.
- [Task crosswalk](TASK_COMPLETENESS_T01_T80.md) covers all 70 authentic tasks and explicitly preserves ten undefined requested IDs. [Structured version](TASK_COMPLETENESS_T01_T80.json).
- [Current source selector](../../CURRENT_GAMEPLAY_SOURCE.json) resolves the conflicting old continuation instructions without changing runtime ownership or branches.
- [Exact source bindings](SOURCE_BINDINGS.json) preserve source identity and distinguish authored decisions from observations.

## Latest observed gameplay and evidence

[Build13/source delta](LATEST_SOURCE_DELTA.md) distinguishes the3fad deep-audit baseline, actual game source `2654f5019b7212968d28600cb071bf1c231c9030` and QA cutoff `2f46e72e300a719f34ca9b0e9b718282a5a88ddd`. It credits direct physical shelf/cash withdrawal, roster/cargo corrections and newly reported test/motion evidence. This audit inspected source and receipts; it did not replay the APK/media or certify the game.

## What changed in executable planning checks

All-seven attack capability, appropriate species profiles and required motion review can no longer be removed silently. Resource-derived player/helper/survivor profiles must appear in the relevant candidate coverage. Earlier tasks retain the explicit future-survivor deferral; applicable survivor and regional integration checks fail while required profiles are unresolved. Closure reruns the current evaluator instead of trusting a stale passing receipt. Regional resource contact review is required even when approved clips are reused.

The mislabeled phone16:9 test fixture now uses1920×1080 instead of duplicating the20:9 case. Layout validation rejects missing, duplicated or wrongly labeled profiles before an adapter runs, while accepting the small rounding in the native2732×2048 tablet profile. This does not certify a physical device or native4K60.

Future task packets include the current CG obligations and CD decisions alongside the earlier GD requirements. The compact crosswalk avoids duplicating the entire contract into every row. The plan checker verifies source identities, complete species/level/value coverage, honest untested states and preserved task authority; it cannot approve gameplay.

## Evidence and limits

The [validation receipt](VALIDATION.json), [scope checks](SCOPE_VALIDATION.json), [candidate freeze](CANDIDATE_FREEZE.json) and [independent final review](FINAL_REVIEW.md) describe only the exact reviewed planning/tooling candidate. Raw rejected reviews and repaired-output checks remain under `Review/`. [Publication receipt](PUBLICATION.json) records the separately verified GitHub update when available. [Checkpoint](CHECKPOINT.json) identifies the resumable state.

Historical source/refinement packages, task definitions, graph edges, statuses, ownership, selected media, accepted receipts, rejected evidence and inactive workflows remain preserved. The main snapshot is not a merge of the newer Codex game branch.

Two source limitations remain explicit: T71–T80 have no located authentic definitions, and full privately held original-video/editable-source custody is still unverified. Neither is fabricated or marked closed. Numeric recipes/prices/pacing, actual100 producer bindings, regional native assets, seven-pet play, complete animation/audio and physical device evidence must be supplied by their existing owners before game approval.

## Reproduce the bounded checks

From the repository root:

```bash
python3 tools/havenline/production/completeness.py check
python3 tools/havenline/production/gameplay_depth.py check
python3 -m unittest discover -s tools/havenline/production/tests -p 'test_completeness.py'
python3 -m unittest discover -s tools/havenline/production/tests -p 'test_resource_actor_contract.py'
python3 -m unittest discover -s tools/havenline/production/tests -p 'test_closure_resource_actor.py'
```

Use `completeness.py task T23` for an individual task's current requirements. Regenerating a canonical task packet writes to its normal evidence path; review captures intercept those writes so old packets stay unchanged.
