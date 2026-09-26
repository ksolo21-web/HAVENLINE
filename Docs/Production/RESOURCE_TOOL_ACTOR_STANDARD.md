# Havenline Resource / Tool / Actor / Animation Standard

This standard supplements `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md` without changing approved T01-T04 work or the already assigned T05 frozen scope.

## Purpose

Havenline must never introduce a resource, helper, survivor, core companion, animal companion, tool, or weapon whose usable gameplay action is undefined or whose production animation is a generic placeholder.

The repository therefore uses three machine-readable contracts:

- `Docs/Production/RESOURCE_ACTION_REGISTRY.json`
- `Docs/Production/ACTOR_CAPABILITY_MATRIX.json`
- `Docs/Production/ANIMATION_ACTION_MATRIX.json`

These contracts are forward-governance inputs to task packets and candidate closure.

## Non-disruption rule

T05 is already assigned. This standard does **not** expand or rewrite the current T05 frozen scope.

If future T09/T16/T19/T21 work needs a physical tool asset that T05 did not create, that later task must either:
1. author it inside its own permitted scope/path, or
2. create a structured change request for the appropriate shared asset path.

No current T05 candidate may be rejected merely because this forward standard was introduced after T05 assignment.

## Resource contract

Every production resource must declare:

- resource class;
- collection method;
- required tool/method profile;
- player animation profile;
- helper/core-companion animation profile;
- survivor animation profile;
- visible carry presentation;
- contextual delivery destination;
- tasks that require it.

A resource introduced by a future biome cannot become production-valid until its registry entry is complete and `production_ready=true`.

No generic fallback such as “use axe for everything” is allowed.

Current opening resource intent is:
- wood -> axe/chop;
- stone -> pickaxe/mine;
- metal -> mine or dismantle; exact production tool is frozen by T09;
- fuel -> extract or salvage; exact production tool is frozen by T09.

Fishing and crop tools are frozen by T16 and T19 respectively.

## Automatic contextual tool/action rule

T07 owns automatic contextual action selection.

The player does not manually choose chop/mine/attack/rescue/deposit buttons. The Context Director selects the correct registered action/tool from proximity, target type, priority, facing, and hysteresis.

The existing orbiting/swiveling placeholder gather/attack presentation is not an approved final visual.

- T09 must replace the gathering side with a polished contextual tool/action presentation.
- T21 must replace the combat side with polished weapon behavior and progression.
- T06/T59/T60/T61 prove character-specific contact, rigging and motion compatibility.

A camera or evidence trick may not be used to hide an unresolved tool/weapon presentation defect.

## Human helper and survivor rule

Core human companions and rescued survivors may gather, carry, deposit, build, repair, guard and attack when their job/capability permits it.

They must not simply replay the player animation.

Same logical action must have role-appropriate authored motion:
- player action;
- core-helper action;
- rescued-survivor action.

All share the same authoritative gameplay impact beat so animation variety cannot duplicate or desynchronize resource/damage logic.

T23 owns survivor-specific work/combat animation requirements.
T31 proves the combined population/companion system.

## Animal companion rule

Assigned production tasks:
- T24 Guardian dog
- T25 Gray wolf
- T26 Fox
- T27 Owl
- T28 Male lion
- T29 White tiger
- T30 Brown bear
- T31 integrated companion jobs/population safety

Every combat-capable animal must have a species-specific attack profile.

Required attack languages:
- dog: lunge/bite/intercept;
- wolf: pursuit/pounce/bite;
- fox: dart/pounce/bite;
- owl: aerial dive/talon strike;
- lion: charge/pounce/claw/bite;
- tiger: low ambush/pounce/claw/bite;
- bear: heavy charge/swipe/bite.

Animals do not silently use human tools.

Species-appropriate work is allowed:
- dog/wolf/fox/owl may retrieve appropriate light resources;
- owl may scout/retrieve through authored aerial motion;
- lion/tiger primarily hunt/guard/attack;
- bear may heavy-haul or break approved obstacles.

T27 must separately prove owl flight, takeoff, landing, wing clearance, aerial navigation and attack motion.

## Task ownership overlay

The existing T01-T70 numbering remains unchanged. These requirements are mandatory scope overlays:

- T06: Character 1 tool/contact/motion foundation.
- T07: automatic contextual action/tool selection.
- T08: visible carrying and transfer presentation.
- T09: resource registry closure for opening resources; harvesting/tool presentation; gathering-side orbiting-placeholder removal.
- T16: fishing method/tool/animation contract.
- T19: crop harvesting method/tool/animation contract.
- T21: combat weapon system/progression; combat-side orbiting-placeholder removal; human attack profiles.
- T23: survivor work, gather, guard, heal and attack animation/capability proof.
- T24-T30: species-specific companion locomotion/work/attack proof.
- T31: integrated helper/survivor/companion capability safety.
- T32: complete Level 1-10 proof that all applicable resource/tool/actor contracts work together.
- T44-T52: every new biome resource must be registered before that region can become `INTEGRATION_READY`.
- T59-T61: Characters 2-4 final tool/weapon/contact compatibility in their final rigging reviews.
- T62/T67/T70: whole-game regression verifies no resource/actor contract drift.

## Motion critic policy

C5 Motion/Rigging remains mandatory where already assigned.

This standard additionally requires C5 for T09, T16, T19, T21 and T23.

For T44-T52, C5 becomes mandatory whenever the candidate introduces a new actor action or animation profile.

## Candidate contract proof

Applicable candidates must populate `resource_actor_contract` in their candidate manifest with:

- applicable;
- validation_passed;
- exact hashes for all three registries;
- introduced resource IDs;
- resource IDs covered;
- actor keys covered;
- animation profiles covered;
- animation_delta;
- validator output path/hash.

The closure validator must fail an applicable task when this proof is missing, stale, incomplete, or inconsistent with the current registry files.

## Fail-closed rules

Candidate closure fails when any of the following is true:

- a required resource remains unresolved for the task that owns its freeze;
- a new resource is introduced but is absent from the resource registry;
- an introduced resource lacks a resolved acquisition method/tool;
- an actor is allowed to attack but its required attack profile is not proven;
- a direct-gather actor lacks a valid tool/action animation profile;
- a pet uses a human-tool fallback;
- T27 lacks the required owl aerial motion set;
- the candidate claims a new animation action but omits C5 when required;
- an applicable contract hash does not match the current canonical registry.

The goal is automatic enforcement, not builder memory.
