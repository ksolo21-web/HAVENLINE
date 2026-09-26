# T10 frozen scope — World Transformation Framework

## Required outcome

Create the reusable, deterministic framework that turns delivered resources and approved progression conditions into a truthful visible world-state change. T10 owns the transaction/state machinery between the existing physical DELIVER loop and later BUILD/UPGRADE content. It must make a transformation previewable, validate prerequisites and cost without mutation, commit exactly once, publish a stable before/transition/after state for presentation, and survive replay/reload without duplicate charges or skipped progression.

T10 is framework work, not camp-content work. T11 owns the actual camp buildings, upgrade-pad content, authored structure meshes and final camp upgrade presentation that consume this framework.

## Mandatory requirement IDs

- **T10-R01 — Registered transform recipes.** Every transform is identified by a stable recipe/state ID with explicit source state, target state, prerequisites, exact resource costs, progression tags and declared presentation key. Ordering must be deterministic and machine-readable; implicit scene-name or node-order behavior is forbidden.
- **T10-R02 — Pure eligibility preview.** Preview/eligibility queries are read-only. They report ready/blocked, exact missing prerequisites/resources, current state and proposed next state without consuming, granting, spawning, hiding or mutating anything.
- **T10-R03 — Atomic exact-once commit.** A commit validates against current authoritative state, debits the declared cost once, applies the world-state transition once and emits one committed transaction. Any validation or application failure leaves both resource and transform state unchanged. Partial charge/partial transform is forbidden.
- **T10-R04 — Replay and duplicate protection.** Every commit uses a stable transaction identity/idempotency key. Replayed, duplicated, stale, out-of-order or already-applied commits fail closed and never debit resources or advance state again.
- **T10-R05 — Truthful visible lifecycle.** Framework state exposes deterministic `locked`, `ready`, `preview`, `committing`, `complete` and `blocked/error` presentation phases (or an equivalent explicitly mapped set). Presentation can always distinguish before, actionable next change, active transition and completed result. No hidden instant upgrade may masquerade as visible world transformation.
- **T10-R06 — Physical-loop continuity.** Costs consume only authoritative delivered/available resources through the published T08 inventory/stockpile contract. T09-produced resources become eligible only after their authoritative acquisition/delivery path has committed. T10 never edits T08/T09 quantities, yields, harvesting timing or carry rules.
- **T10-R07 — Progression integrity.** A recipe may not skip required states, silently downgrade a state or merge deliberately distinct progression branches. Reversible transforms must opt in explicitly and define their inverse cost/state behavior; otherwise forward state is monotonic.
- **T10-R08 — Separation of authority.** The transformation model owns recipe eligibility, exact-once transaction resolution and component state. Presentation owns visuals only. Simulation/integration remains the authority for shared resource state. `main.gd`, `simulation.gd` and other integration-only files are changed only by the integration owner or an approved ChangeRequest.
- **T10-R09 — Recovery contract without stealing T14.** T10 exposes deterministic component snapshot/import data sufficient to reconstruct transform state and applied transaction identities. It does not define the global save schema/versioning system; T14 owns that. Import rejects malformed, impossible or duplicate state without granting progress.
- **T10-R10 — T11-ready content boundary.** T11 can register camp construction/upgrade recipes, presentation keys and authored assets without changing T10 transaction semantics. T10 test fixtures prove at least branching, multi-resource, insufficient-cost, stale-commit and exact-once cases but do not ship final T11 camp structures.
- **T10-R11 — Readable world response.** Required evidence proves the framework can drive a clearly readable before/ready/transition/after sequence at gameplay camera scale and adaptive phone/tablet/foldable layouts. C1/C2/C3/C4 review judges world-response fidelity/integrity/readability using T10-owned neutral fixtures, not unfinished T11 content.
- **T10-R12 — Bounded performance.** Eligibility evaluation and state publication are event-driven or otherwise bounded; unchanged state does not rebuild presentation. Stress cases cover repeated preview, rejected commits, many registered recipes and repeated valid transforms without unbounded node/event/history growth.
- **T10-R13 — Dependency truth and parallel isolated build.** T10 may enter `ASSIGNED`/`BUILDING_ISOLATED` and may reach `BUILT_PENDING_DEPENDENCY` while T09 is still active, provided all work remains inside the frozen disjoint T10 reservation, no T08/T09/integration-only runtime path is modified, and unresolved upstream behavior is represented only through explicit fixture/adapter contracts. T10 may **not** become `INTEGRATION_READY`, integrate, or claim production approval until T05, T08 and T09 are `APPROVED`, the candidate is reconciled onto the exact post-T09 integration head, the real approved T09/T08 authority interfaces replace fixture assumptions, and all impacted regression/evidence is rerun.
- **T10-R14 — Acceptance gate.** Required critics are C1/C2/C3/C4/C6/C7. Every mandatory dimension must be strictly greater than 9.0 unrounded, target 10/10; all applicable G1-G14 gates and impacted approved-task regression must pass with zero unresolved mandatory defects.

## Explicit exclusions

- No authored final camp buildings, upgrade pads, camp layout redesign or station-specific final upgrade visuals; T11 owns them.
- No Level 1–100 progression architecture, difficulty director or reward pacing; T12/T13 own those systems.
- No global save/versioning/cloud identity system; T14 and later persistence tasks own those systems.
- No changes to T09 harvesting tools, source reactions, yields or acquisition timing.
- No changes to T08 carrying/transfer conservation semantics except through a structured integration-owned change request if a published interface proves insufficient.
- No customer/NPC, fishing, economy, combat, companion, biome or release-certification work.
- No new manual action button, build menu dependency, inventory grid, capacity/encumbrance wall or control-complexity increase.

## Isolated builder ownership reservation

The T10 isolated builder owns only the following disjoint paths while building and testing ahead of dependency completion:

- `HavenlineGodot/scripts/world_transform.gd`
- `HavenlineGodot/scripts/world_transform_view.gd`
- `HavenlineGodot/data/world_transform_recipes.json`
- `HavenlineGodot/assets/world_transform_v1/**`
- `HavenlineGodot/tests/test_task10_world_transform.gd`
- `HavenlineGodot/tests/test_task10_integration.gd`
- `HavenlineGodot/tests/capture_task10_world_transform.gd`
- `Docs/Production/T10/**`
- `tools/havenline/task10/**`
- `.github/workflows/havenline-task10-*.yml`

These paths do not overlap T09's `harvesting_v1`, `harvest_presentation.gd`, T09 tests/tools/docs/workflow reservation. Shared shipping wiring remains integration-owner work.

## Evidence required to reach BUILT_PENDING_DEPENDENCY

- Exact isolated candidate hash and authorized changed-file manifest.
- Machine-readable recipe/state contract and deterministic order/hash proof.
- Preview purity proof: repeated preview causes zero resource/world mutation.
- Atomicity matrix: success, insufficient resources, missing prerequisite, stale source state, failed application, replay, duplicate and out-of-order transaction.
- Fixture authority proof for T08/T09-shaped resource contracts without claiming the real T09 adapter is certified.
- Neutral fixture sequences showing before, ready/preview, committing and after from gameplay, overhead, side/three-quarter and detail views where applicable; adaptive phone/tablet/foldable coverage.
- Snapshot/import/recovery cases proving no double charge, skip or duplicate transaction after reconstruct/reload.
- Stress/performance metrics for recipe count, preview frequency, commit bursts, event/history bounds and unchanged-state stability.
- No changed T09-owned or integration-only runtime paths.

## Additional evidence required before INTEGRATION_READY

- Exact post-T09 integration base and reconciled candidate hash.
- T09 is APPROVED/integrated and no longer an active conflicting owner.
- Real T08 delivered-resource and T09 acquisition/delivery authority bindings replace fixture assumptions.
- Resource conservation proof against the integrated T08/T09 implementation.
- Full impacted T01-T09 regression after reconciliation.
- Fresh device/save/recovery/performance evidence for the reconciled candidate.
- Independent C1/C2/C3/C4/C7 review plus quantitative C6; strict >9.0 unrounded in every mandatory dimension, target 10/10.
