# T11 frozen scope — Camp construction and visual upgrade system

## Required outcome
Turn the approved T10 World Transformation Framework into authored, readable camp construction and upgrade content without changing T10 transaction semantics. T11 owns final camp building/upgrade presentation, authored structure assets and construction/upgrade content.

## Dependencies
- T05 Production station and prop kit — APPROVED.
- T10 World Transformation Framework — APPROVED.
- Consume approved T08/T09 delivered-resource and harvesting interfaces through T10.

## Required behavior
- Register deterministic camp construction/upgrade content through T10's published recipe/presentation boundary.
- Provide authored camp structure/upgrade visuals with readable before, preview, committing and complete states.
- Preserve exact resource costs, prerequisites, state order and exact-once behavior from T10.
- Support phone, tablet and foldable layouts and native 3840×2160 scale-1 evidence where applicable.
- Preserve Havenline's simple MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → BUILD/UPGRADE flow.
- Keep performance bounded with headroom for T12+.

## Explicit exclusions
- No changes to T10 transaction/idempotency/resource-authority semantics.
- No changes to T08 carrying/storage conservation or T09 harvesting yields/timing.
- No Level 1–100 progression architecture or difficulty director; T12/T13 own them.
- No global save schema/versioning; T14 owns it.
- No NPC/customer/economy/combat/companion/biome/release-certification work.
- No new manual action-button or inventory/menu complexity.
- Any protected T10 extension requires an integration-owner ChangeRequest.

## Owned-path reservation
- HavenlineGodot/assets/camp_construction_v1/**
- HavenlineGodot/scripts/camp_construction_view.gd
- HavenlineGodot/data/camp_construction_recipes.json
- HavenlineGodot/tests/test_task11_camp_construction.gd
- HavenlineGodot/tests/test_task11_integration.gd
- HavenlineGodot/tests/capture_task11_camp_construction.gd
- Docs/Production/T11/**
- tools/havenline/task11/**
- .github/workflows/havenline-task11-*.yml

## Acceptance
Required critics: C2, C3, C4, C6. Every mandatory dimension must be strictly >9.0 unrounded, target 10/10, complete coverage and zero unresolved mandatory defects. G1–G14 apply where relevant and final integrated-source regression is mandatory.
