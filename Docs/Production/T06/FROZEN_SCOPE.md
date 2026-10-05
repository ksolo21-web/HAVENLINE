# T06 frozen scope — Character 1 complete movement/interactions

## Required outcome

Deliver a complete, deterministic Character 1 motion and interaction foundation
for the current Havenline runtime while preserving the exact supplied
`HavenlineGodot/assets/characters/Character1.glb` bytes. Character 1 must remain
credible both as the selected player lead and as the unselected core human
companion, with grounded locomotion, readable contact beats, clean transitions
and no foot/knee/hand/gear clipping across normal gameplay scale.

T06 authors the Character 1 body-motion and contact contract. T07 owns automatic
context selection, T08 owns final visible carrying/transfers, T09 owns finished
harvesting tools/presentation, and T21 owns finished combat weapons/progression.

## Mandatory requirement IDs

- **T06-R01 — Immutable source identity.** Preserve the Character 1 GLB at
  SHA-256 `95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099`.
  Do not alter geometry, skinning, UVs, textures, skeleton hierarchy or source
  animation bytes.
- **T06-R02 — Complete grounded locomotion.** Provide production-ready idle,
  walk and run cycles plus start, stop and left/right 30°, 90° and 180° turn
  transitions. Preserve in-place simulation authority and eliminate visible
  foot sliding, flat-foot running, inward knee collapse and abrupt pose pops.
- **T06-R03 — Foot and lower-body mechanics.** Prove heel/forefoot strike,
  toe-off, ankle articulation, stable foot roll, hip weight transfer and knee
  tracking through full real-time and slow cycles on level and sloped ground.
- **T06-R04 — Current interaction body set.** Provide body-motion foundations
  for gather/chop, mine, dismantle, deposit/transfer, build, repair, rescue,
  customer service and attack/contact. Every clip has deterministic anticipation,
  contact/impact and recovery beats without implementing future task systems.
- **T06-R05 — Contact and attachment contract.** Publish stable left-hand,
  right-hand, two-hand, carry, rescue and forward-impact contact metadata with
  exact normalized beat timing. T09/T21 may attach finished tools/weapons later
  without hiding hand separation or contact errors.
- **T06-R06 — Role-aware use.** Character 1 supports the same authored body set
  when selected as `player_lead` and when serving as `core_human_companion`.
  Helper timing may be offset for natural staging but may not duplicate gameplay
  grants or desynchronize the authoritative impact beat.
- **T06-R07 — Action selection API.** Expose a deterministic motion selector
  driven by speed, facing, current contextual action, normalized action progress
  and role. It adds no manual action button and never owns gameplay outcomes.
- **T06-R08 — Transition integrity.** Blend locomotion/action entry and exit;
  preserve facing, terrain contact and simulation position; prevent looping
  one-shots, frozen end poses, snapping, tunneling and duplicate impact signals.
- **T06-R09 — Gameplay-scale compatibility.** Character 1 remains readable and
  unclipped under the approved T04 landscape camera, T03 gates/work lanes and
  T05 station arrangements across phone, tablet and foldable framing.
- **T06-R10 — Deterministic evidence.** Capture source-bound front, rear, left,
  right, three-quarter, close foot/knee/hand/contact, gameplay and native-4K
  views plus every full real-time/slow cycle and required transition.
- **T06-R11 — Performance and persistence headroom.** Add no new physics body,
  no model/texture duplication and no saved gameplay field. Keep animation CPU,
  memory and storage within the characters/companions/NPC subsystem share and
  preserve all current save/reload/migration behavior.
- **T06-R12 — Exact future-boundary discipline.** Do not implement T07 context
  decision logic, T08 inventory/carry-system behavior, T09 finished tools or
  harvesting outcomes, T21 weapon progression/damage, C2-C4 rig repairs, new
  NPCs/companions, economy, LiveOps, cloud services or final device certification.

## Explicit exclusions

- No edits to any GLB, approved T01-T05 asset/runtime path, or the authoritative
  `reference-contract.json`.
- No manual gather, attack, rescue, deposit, build or repair buttons.
- No finished tool/weapon model, tool selection, damage, reward, inventory,
  economy or progression logic.
- No C2-C4 rigging/final review, animal motion, customer/survivor model work or
  whole-game/release completion claim.
- No unfinished APK delivery and no request for Kaleb to test or benchmark.

## Ownership and integration wiring

The isolated builder owns `@reservation:T06`. The original Character 1 GLB is
protected and read-only. Shipping attachment requires a minimal call-site edit
in `HavenlineGodot/scripts/main.gd`; the isolated builder must request it through
`Docs/Production/ChangeRequests/`, and only the integration owner may apply it
after candidate readiness.

## Required acceptance evidence

- Exact source/base/candidate hashes and changed-file/path-ownership manifest.
- Full cycles and transitions at real-time and slow review speed, including
  feet, toes, knees, hips, hands, coat/gear, ground contact and clipping.
- Player-lead and core-companion states; level/slope/gameplay contact; front,
  rear, sides, three-quarter, overhead/detail and T04 normal gameplay framing.
- Action anticipation/contact/recovery timing mapped to the published contact
  contract with no duplicate gameplay event.
- Phone/tablet/foldable composition and native 3840×2160 scale-1 frames; these
  do not certify physical device FPS.
- Full T01-T05 impacted regression, save-state continuity, task tests, resource/
  actor/animation contract proof and C1+C2+C5+C6 review.
- Every mandatory dimension strictly greater than 9.0 unrounded, target 10/10,
  complete coverage and zero unresolved mandatory defects.
