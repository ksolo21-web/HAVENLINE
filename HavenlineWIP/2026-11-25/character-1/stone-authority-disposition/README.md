# Level 1 stone authority — read-only design boundary

**Decision:** No real stone acquisition authority may be enabled in the current
replacement preview from the presently pinned evidence. A detached contract
test can use the historical, exact one-unit acquisition behavior as a source
specimen and reject all unbound replacement endpoints; it must not pretend
to be gameplay, add ore/stone to the active ledger or link it to camp payment.

- Canonical T09 [frozen scope](https://github.com/ksolo21-web/HAVENLINE/blob/11c14a1c41971067c7dc97db69375f720a408f68/Docs/Production/T09/FROZEN_SCOPE.md)
  (blob `1fcc85ded7a530307e5a4680bd82f79c87f7ef02`) and
  [resource registry](https://github.com/ksolo21-web/HAVENLINE/blob/11c14a1c41971067c7dc97db69375f720a408f68/Docs/Production/RESOURCE_ACTION_REGISTRY.json#L30-L41)
  (blob `fc867dfbb9bdd25627838e18e3b817287e69dcca`) establish stone as natural,
  mine via an authored pickaxe / `human_player_mine`, exact sim contact is the
  sole grant authority, and the committed stone unit transfers visibly from
  source into the proper T08 carried stack exactly once. The T07 selection
  contract is automatic contextual work; no separate manual pickup, gather,
  inventory or tool-selection button is authorized by it. Control changes for
  the replacement need their own disposition; same control across PC/device
  must not be inferred from T09 or from a candidate keyboard shortcut.
- Historic [main-game sim](https://github.com/ksolo21-web/HAVENLINE/blob/11c14a1c41971067c7dc97db69375f720a408f68/HavenlineGodot/scripts/simulation.gd#L237-L266)
  (blob `24097b56baeb44e0ccf2bc1974c2f6994ef0fe79`) already decrements one
  selected source unit and adds exactly one inventory unit of that kind
  per completed gather, then emits its typed event. Historic
  `HavenlineGodot/data/reference-contract.json` blob
  `5c4ce6470006c5b18735e0835571b817e54e2fdc` has four stone nodes, 14 units
  per node and .7s per unit in that old map: not a single replacement rock,
  not three hits-to-one-drop, and not replacement count, timing, placement,
  progression or an independent new approval. T09 verified completion
  names legacy candidate `5415d85838ecf4bea8b3c71662072670e61797a0`.
- Actual replacement `11c14a1c41971067c7dc97db69375f720a408f68` layout blob
  `5bac3496d3cf1b952736e8ecafa70f9978ffdbf5` has only three wood sources.
  Its [exact ledger](https://github.com/ksolo21-web/HAVENLINE/blob/11c14a1c41971067c7dc97db69375f720a408f68/HavenlineLevel1/opening_ledger.gd)
  (`873def40c950279b210e2b2d0bed5d85625ea189`) fail-closes on extra types
  or unrecognized collected IDs, validates exactly one wood-typed payment,
  and emits only a closed opening-v1 snapshot; changing stock to include
  stone alone would invalidate its strict restore path. None of this
  admits a stone receiver or paid-stage requirement.
- [PR #108](https://github.com/ksolo21-web/HAVENLINE/pull/108), verified open,
  unmerged head `48c6c53a0dfda117ef12c68b32cfe2b3732d5239`, uses the same
  wood-only ledger. Its procedural rock `[-6,3]` and third F hit are
  candidate geometry and a visual tally, not a stone source, temporal impact
  witness, separate drop interaction, typed reward or receipt. Do not import
  the old source coordinates or treat this candidate coordinate as approved.
- Stone art in consolidated main `b80c61f13ba31bb0940792dd47976a8e2878dbf5`:
  `Docs/Design/ResourceTurnarounds/2026-11-23/reviewed-concepts/02-stone.png`
  blob `c2a7e1a7cb2caa8fb1dc80699b5d02604adadbe1`, static 9.2;
  `Docs/Design/ResourceTurnarounds/2026-11-23-plots/reviewed-concepts/05-storage-stone.png`
  blob `4b030b8cd7e6128ad2a1bde50cdc664eca3a23cb`, static 9.3. Neither is a
  game mesh/placement/capability approval or at 9.5. Legacy 3D references
  `HavenlineGodot/assets/environment_v2/stone.glb` (`0904ff6…`),
  `world/stone.glb` (`c9db47d…`), and `stations_v2/stone_stack.glb`
  (`3ed225b…`) are separately recoverable in old source, not admitted in
  `HavenlineLevel1`. Resource and storage props are separate roles.

**What unblocks**: an explicit replacement target contract from the integration
owner or separately approved preview scope: exact admitted mine target/art
and location/timing context; established contextual input and a genuine
T06/T07-aligned, unobstructed contact event with target identity; a one-unit
stone custody bridge distinguishable from wood, including cancellation/replay
and an explicit state/persistence boundary. Optional detached negative cases
now: previously unknown stone source or unbound renderer, blocked/cancelled
contact, repeat contact and non-stone receiver all produce no mutation; use
legacy sim as historical positive-control origin only. Do not authorize
physical loose-stone pickup, starter costs, spawn, mining, tool timing, claim
playability, or alter any source to fill a missing fact. No engine, changes to
external branches, gameplay source, or spend in this intake.
