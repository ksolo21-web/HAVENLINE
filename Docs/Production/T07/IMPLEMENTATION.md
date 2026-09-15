# T07 context director implementation

## Owned module

`HavenlineGodot/scripts/context_director.gd` is a deterministic, ephemeral
selection layer. It accepts canonical candidate fixtures, rejects malformed or
duplicate identities, filters them through the registered actor capability
matrix, applies the frozen safety bands and stable ranking order, and publishes
one canonical action descriptor.

The director never mutates simulation state. It does not perform actions, emit
damage/reward/inventory events, own position or facing, add a save field, or
create a control. The approved simulation remains authoritative for impacts;
T06 remains authoritative for body-motion selection.

## Frozen ranking order

1. Frozen action-kind safety band.
2. Candidate-declared priority, clamped to a bounded range.
3. Normalized distance inside the candidate radius.
4. Target relevance.
5. Facing alignment.
6. Lexical canonical `kind:id` identity.

Purchase, spend, VIP, telemetry and personalization metadata are ignored.
Duplicate canonical identities reject all ambiguous copies.

## Stability behavior

- Ordinary context requires 0.12 seconds of stopped acquire dwell.
- Equal-priority ordinary context is held for at least 0.18 seconds.
- Every finite nonzero movement input, or residual speed at/above 0.20, blocks
  entry and resets acquire dwell.
- The current candidate can remain within a bounded 0.55-world-unit release
  margin.
- Same-band switches require a 0.16 normalized advantage.
- Frozen danger/rescue interrupts can preempt ordinary work immediately.
- `action_token` changes only when canonical focus identity changes; it is
  presentation metadata and is not persisted.

## Bounded evaluation

Inputs above 128 candidates fail closed before evaluation. Within that bound,
all canonical identities are inspected, duplicate identities are rejected, and
the deterministic ranking is applied before retaining the best 96 eligible
candidates. Metrics disclose the original population and cap state. The engine
test benchmarks 2,000 worst-population evaluations and the deterministic C6
gate rejects an average at or above 2,500 microseconds, a p95 at or above 3,500
microseconds, or any sample at or above 20,000 microseconds. It also records a
ten-second focus-jitter switch rate, retained engine-object delta, static-memory
delta and Linux process-RSS delta against explicit budgets. Shipping-scene
frame/submission deltas remain a required integration-owner measurement and
cannot be satisfied by the isolated component benchmark.

## Integration-owner call-site request

After isolated acceptance, the integration owner should:

1. Give the approved simulation one `HavenlineContextDirector` instance.
2. Replace the legacy `choose_action()` call in `simulation.gd` with
   `build_simulation_candidates()` plus `advance()`.
3. Call `perform_action()` only when the returned descriptor is `actionable`.
4. Preserve `choose_action()` as a pure preview compatibility surface for the
   inherited tests.
5. Reset ephemeral focus on lead change and successful restore.
6. In `main.gd`, pass only actionable descriptors to T06 body motion while
   continuing to show concise focus/blocked/progress text from the descriptor.
7. Re-run all T01–T07 suites, save/device/resource/performance gates and fresh
   visual evidence on the integrated commit.

The adapter also consumes the approved population simulation's already-visible
survivor-rescue and customer-service possibilities. Its existing presentation
gate remains authoritative: an encounter/customer omitted from `presented_ids`
cannot produce a contextual action.

No `outpost_simulation.gd`, `outpost_view.gd`, reference contract, asset,
economy, tool, weapon, transfer, construction-upgrade or future-task change is
requested.
