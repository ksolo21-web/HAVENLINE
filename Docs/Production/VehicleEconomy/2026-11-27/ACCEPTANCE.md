# Havenline — fuel, fabrication and world vehicles

Owner: Kaleb. Continuation of the published snow truck/garage package at `201dcbe4fad5037a33bd619b59285a1ef91599d8`. New authored designs and numerical fixtures remain distinguishable from user requirements and shipped gameplay.

## Current user instruction

> The truck will cunsume fuel when used just not alot. It will cost alot of different processed resources to make. it need fuel sheets of metal...and so on. So we will need a way to get iron to process into iron bars and the into sheet metal. coal will be another useful resource to mine, and oil. Im not sure how we can get the oil outside the camp but we can get fuel from the oil right? What else am i missing? the other worlds will need vehicles to that we have to design and render that will make sense and be helpful in that world for the user.

The earlier instruction **“push it”** authorizes publication of this continuing project work. This package uses an isolated branch; it does not merge the active gameplay branch or transfer its ownership.

## Requirements and acceptance evidence

| ID | Required outcome | Acceptance evidence |
|---|---|---|
| VE01 | The snow truck consumes a small amount of fuel during powered use. | Exact native fuel accounting and active-use/depletion/reload tests; numerical values explicitly remain prototype tuning. |
| VE02 | Iron can become iron bars, then sheet metal. | Typed resources, recipes, producer prerequisites, full quantity expansion, legacy `metal` custody decision. |
| VE03 | Coal is mineable and useful. | Existing source binding; coal feeds the selected smelting/refining recipes without replacing refined fuel. |
| VE04 | Oil can be obtained outside camp and refined into fuel. | Outside oil-well/hand-pump design, camp refinery recipe, walkable bootstrap and recovery chain, primary factual source. |
| VE05 | The truck has a substantial bill using varied relevant processed resources. | Explicit bill and useful component recipes; reachable complete quantities, no self-output prerequisite. Final price balance requires actual playtests. |
| VE06 | Fuel exhaustion remains recoverable. | Driver can leave; no destruction/loss merely for zero fuel; manually reachable extraction/refining/delivery; no fuel-only bootstrap or premium-only recovery. |
| VE07 | Fuel has one authoritative custody history. | Source/tank/cargo/consumption/loss accounting, duplicate requests, fractional remainder, pause, save/reload, garage deposit and destruction checks. |
| VE08 | Worlds 2–10 each have a distinct useful vehicle. | Nine world-bound design records covering travel, work, combat/contact limits, station, materials, recovery and useful ongoing jobs. |
| VE09 | Render those later-world vehicles. | Nine generated concept sheets: front, rear, both sides, useful oblique/detail view and a visible working state; actual independent image inspection. |
| VE10 | Preserve the existing truck and garage contract. | Unlimited mixed cargo; HP; outside-camp loss; garage first and in-camp plot; fence replacement; all-or-hold automatic warehouse deposit; two usable pedestrian exits. |
| VE11 | Preserve ownership, historical evidence, accepted quotes and old saves. | New isolated branch; old approvals/rejections untouched; explicit supersession record; no retroactive material charge or doubled old `metal` quantities. |
| VE12 | Explain the remaining gameplay gaps honestly. | Reachable producer lifecycle, controls, tools/contact, threat rules, recovery, travel, save, onboarding, animation/audio/device and balance integration checklist. |

## Evidence scope

This pass delivers designs, generated multi-view concept renders, executable standalone accounting rules and recipe reachability evidence. A six-view sheet is a turnaround concept, not a rotating 3D file. The historical truck/garage remain selected concepts. Native meshes, driving physics, blade/tool motion, measured clearances, in-game extraction/refining, audio, balance and devices need their actual production evidence. They cannot receive approval from this package's documents or fixtures.

Each functional requirement must pass its applicable checks. General review must be strictly above 9.0; stronger repository rules still control production approval: reference dimensions at least 9.9 and existing exact-10 visual gates. Any missing native/runtime evidence stays explicitly unapproved. Scores are judgments, not measured percentages. An identified defect reopens its affected review.

## Dependency-aware milestones

1. Pin the published base, live source heads, resource identities and existing ten world themes.
2. Define the fabrication/fuel economy, complete bootstrap and recovery, and nine world-specific vehicle designs.
3. Generate and inspect the nine vehicle concept sheets while implementing the bounded fuel component.
4. Freeze candidate identities; independent critic inspects the actual images and runs meaningful native/economy checks; repair and retest affected outputs.
5. Publish the exact reviewed package to the isolated feature branch; read back its commit/tree and files; save the remaining integration checkpoint.

Next action at creation: finish recipe/world design and create the first vehicle renders. Historical T01–T70 identities remain unchanged; T71–T80 remain missing-source questions.
