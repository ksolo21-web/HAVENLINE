# T07 frozen scope — Havenline Simple Control & Context Director

## Required outcome

Deliver the deterministic context-selection layer that preserves Havenline's
one-joystick control language. The player moves; the director continuously
chooses the single best eligible nearby action, presents that choice clearly,
and starts or advances it only when movement and capability rules permit.
Simulation remains authoritative for outcomes. T06 remains authoritative for
Character 1 body-motion selection and contact timing.

## Mandatory requirement IDs

- **T07-R01 — One-joystick contract.** Preserve one primary movement joystick,
  auto-collect, auto-gather/harvest, auto-attack, contextual deposit/rescue/
  build/repair/service, and no permanent manual action-button strip.
- **T07-R02 — Canonical candidate input.** Accept deterministic candidates with
  stable identity, kind, world position, eligibility, priority, capability and
  optional target/progress metadata. Reject malformed or duplicate identities.
- **T07-R03 — Deterministic ranking.** Rank eligible candidates using explicit
  priority, distance, target relevance, actor capability, facing and stable
  identity tie-breaks. Equal inputs must always produce the same result.
- **T07-R04 — Safety interrupts.** Immediate danger, rescue and other frozen
  higher-priority actions may preempt ordinary work using an explicit priority
  table; no spend, purchase, VIP or hidden personalization signal may affect it.
- **T07-R05 — Hysteresis and anti-thrash.** Apply bounded acquire/release radii,
  dwell/hold timing and switch margins so nearby targets do not flicker or
  oscillate while still allowing urgent interrupts.
- **T07-R06 — Movement owns locomotion.** Nonzero player movement cancels or
  blocks contextual action entry as defined by the action contract. Contextual
  work begins only after the actor is stopped and eligible; simulation-owned
  position and facing are never overwritten.
- **T07-R07 — Canonical output.** Publish one current action descriptor with
  canonical `{kind,id,position,progress}` fields, plus reason/state metadata.
  Output must remain compatible with the T06 selector and never emit gameplay
  rewards, damage, inventory changes or duplicate impacts.
- **T07-R08 — Role/capability discipline.** Resolve only registered actions for
  `player_lead`, `core_human_companion` and `rescued_survivor_helper`. A missing
  or not-ready visible actor cannot become an invisible worker or stand-in.
- **T07-R09 — Presentation contract.** Expose concise focus/progress/cancel/
  blocked feedback that stays readable under the approved T04 camera on phone,
  tablet and foldable layouts without adding permanent controls.
- **T07-R10 — Persistence stability.** Context focus is ephemeral. T07 adds no
  required save field; fresh/current/previous/interrupted/reload/migration
  cases remain stable and reconstruct context deterministically.
- **T07-R11 — Bounded performance.** Candidate evaluation is allocation-aware,
  capped and deterministic under expected nearby populations; preserve full-
  game CPU, memory and animation headroom.
- **T07-R12 — Exact future-boundary discipline.** Do not implement finished
  carrying/transfers (T08), harvesting/tools (T09), construction upgrades
  (T11), inventory/economy/rewards, survivor models/jobs (T23), weapons/damage
  (T21), animal behavior, cloud, LiveOps or release certification.

## Explicit exclusions

- No manual gather, attack, rescue, deposit, build, repair or service button.
- No new resource, inventory, carry, tool, weapon, damage, reward or economy
  outcome. Fixtures may describe candidates but cannot grant production value.
- No edits to approved T01-T06 assets or task-owned runtime files.
- No direct isolated-builder edits to `main.gd`, `outpost_simulation.gd`,
  `outpost_view.gd` or `reference-contract.json`.
- No whole-game, APK or physical-device native-4K/60 completion claim.

## Ownership and integration wiring

The isolated builder owns `@reservation:T07`: the context-director module,
task-specific tests/capture, T07 evidence tools/docs and its workflow. Shipping
wiring is integration-owner-only. Any required call-site change must be filed
under `Docs/Production/ChangeRequests/` with exact behavior and regression
requirements before the integration owner applies it.

## Required acceptance evidence

- Exact base/candidate hashes, authorized changed-file manifest and resource/
  actor/animation registry hashes.
- Deterministic tables for priority, distance, facing, capability, tie-break,
  acquire/release hysteresis, movement cancellation and urgent preemption.
- Continuous traces proving stable focus without thrash, no duplicate action
  start/impact, and canonical output compatibility with T06.
- Player-lead, core-companion and rescued-helper allowed/blocked cases; missing
  actor readiness fails visibly and safely.
- Normal gameplay, phone/tablet/foldable and native 3840×2160 scale-1 evidence.
- Full T01-T06 impacted regression, save/device matrices and fresh integrated
  evidence after merge.
- Required critics C2, C3, C4, C6 and C11; every scored mandatory dimension
  strictly greater than 9.0 unrounded and zero unresolved mandatory defects.
