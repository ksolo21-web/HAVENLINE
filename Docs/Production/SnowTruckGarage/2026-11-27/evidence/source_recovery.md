# Havenline snow truck/garage — source recovery

Observed: 2026-11-27T15:42:15.892896+00:00

This is source recovery and an integration recommendation, not a game approval. Only this record and its JSON companion were written. Existing worktrees, staged packages and live branches were not changed.

## Verified refs

| Role | Ref | Exact observed SHA |
|---|---|---|
| Live repository branch | `main` | `a4e643aeb563b6f9cfda8b840c0651d13326eec8` |
| Live repository branch | `planning/build-13-audit` | `afc6d5da3a8605ba7baeb01b7bcc847c0a814347` |
| Live repository branch | `trial/world-one-expansion-2026-11-26` | `2f46e72e300a719f34ca9b0e9b718282a5a88ddd` |

New extension baseline: `a4e643aeb563b6f9cfda8b840c0651d13326eec8`. The existing rules worktree remains at `a4e643aeb563b6f9cfda8b840c0651d13326eec8`, with 437 changed paths at observation.

Rules freeze: `29b11546165b8a32439a467c9b21cbd48f9c00b894734688468cac611bcb3f51`; 427 frozen inputs. Publication state: `REVIEWED_PACKAGE_PREPARED_AWAITING_EXPECTED_HEAD_PUBLICATION`. Remote readback: `False`.

## Original user request

> Continue with the Havenline gameplay gap fill in. Also lets add a 360 view render of a snow truck with horizontal blades at the bottom. It will be driveable by the user. It can be used to attack, cut down trees, smash rocks and other mining rock resources. It will cost a substantial amount of relevant resources. it will be bought on a plot inside the camp. but 1st the user will have to build a garage for it with the garage door will take place of a section of the fence. The truck can hold any resource and an unlimited amount. It has HP and if destroyed outside the camp, the user will lose all the inventory it has. Once the vehicle is parked back inside the garage, the resources will transfer from the truck to the storage house. So we need renders of the garage too.

## New concurrent progression evidence

[World-Progression.md at the inspected commit](https://github.com/ksolo21-web/HAVENLINE/blob/a3c242aba744cc17c93f6e5601bc0e87d968a11a/Docs/Production/Build13Audit/World-Progression.md) contains 10665 bytes; SHA-256 `7bebb965eb2b55d170371bf8ae50d84ad4fd50e3206bc80f91845c8c0944886f`; Git blob `09ccbcc581771879bbe7a1f9a2b15da8b7ac52a6`. Returned and computed blob identities match: `True`. Exact source text is embedded in the JSON companion.

World 1 launch focus and continuous sandbox are current audit direction. Up to 50 local levels is explicitly a proposal, not approved count. Later worlds retained as updates. Global numbering/save IDs/T12 and earlier Level1–100 launch contract require reconciliation.

The truck/garage should use real prerequisites and obtainable materials. Fixed level numbers are not assigned during the numbering reconciliation. No task is created under the missing T71–T80 entries.

## Existing storage policy

- Storage-house visual package assigns no numerical capacity. Source: `Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/README.md`.
- Build13 raw deposit increments typed stored quantity without gameplay-capacity check; storage_open separately gates raw types by paid storage stages. Source: `HavenlineLevel1/field_inventory.gd`.
- Prepared storage ledger has no gameplay-capacity field. deposit_all checks type acceptance, destination operational generation and numeric overflow before one whole-cargo move. Source: `tools/havenline/gameplay_rules/bulk_counter.gd`.
- Existing standalone numeric safety uses MAX_QUANTITY=9007199254740991; this is a technical exactness bound, not approval for a truck gameplay capacity. Source: `tools/havenline/gameplay_rules/bulk_counter.gd`.
- Generic equipment destruction currently creates salvage. Outside-camp truck inventory destruction must explicitly use a lost-value sink rather than generic salvage. Source: `tools/havenline/gameplay_rules/camp_lifecycle.gd`.

## Recommended automatic garage deposit

- **Classification:** Proposed integration choice consistent with current user instruction; not claimed implemented in existing game.
- **Trigger:** Entire truck footprint parked in its own complete operational garage; speed zero, blades off, correct camp/garage/vehicle generation.
- **Destination:** One linked operational warehouse-owned ledger accepts every ordinary resource family, with no gameplay-capacity limit. Bounded visible shelves/stacks are presentation only.
- **Transaction:** Persist one transaction identity that debits all typed truck cargo and credits exactly the same typed quantities to warehouse in one atomic journal/snapshot; replay returns same receipt without a second credit.
- **Storage unavailable:** Leave all cargo in the truck, show explicit transfer hold, and automatically retry after warehouse recovery; no partial unload, type loss, overflow deletion or hidden cargo capacity.
- **Destruction ordering:** Serialize damage and unload commit. If outside-camp destruction commits first, all remaining truck cargo is lost exactly once. If valid unload committed first, transferred warehouse cargo is no longer truck inventory.
- **Numeric requirement:** Use exact logical quantities beyond render counts; decimal strings/arbitrary precision or equivalent proven representation needed if truly uncapped progression can exceed current native exact bound.
- **Backward compatibility:** Truck unlock/deposit contract may not inherit old raw-category storage gates that would reject cargo the truck is explicitly allowed to hold.

## Task mapping

| Existing task | Relevant responsibility |
|---|---|
| T08 | Visible inventory, typed custody and transfers |
| T09 | Harvesting/contact and automatic acquisition |
| T10 | World transformation and purchase state |
| T11 | Camp construction, paid visual transformations |
| T12 | Progression architecture and compatibility |
| T13 | Challenge and threat scheduling |
| T14 | Save/versioning and atomic transactions |
| T20 | Road and vehicle customer service; does not by itself assign player-driveable truck |
| T21 | Visible hostiles, hunting, attacks |
| T22 | Defenses, breaches, repairs |
| T32 | World 1 camp integration |
| T33 | Balance and economy |
| T53 | Transportation/inter-region continuity, no backward dependency for initial local vehicle |

## Source bindings

The JSON companion records byte counts, SHA-256 and Git blob identities for each file below. `.json` standard was requested for inspection but is absent; the `.md` standard plus machine contract are the existing authority.

| Path | Exists | SHA-256 |
|---|---|---|
| `Docs/Production/GAMEPLAY_RULES_STANDARD.md` | True | `b1dcab519fe32639ca9014962f10d9c65fa384eb60d88e4ca14ea3254cbc9423` |
| `Docs/Production/GAMEPLAY_RULES_STANDARD.json` | False | `MISSING` |
| `Docs/Production/GAMEPLAY_RULES_CONTRACT.json` | True | `28e19cd02597040901ab007e72c47eafc55f4680a82ea5820a4d664c7015cba3` |
| `Docs/Production/CURRENT_GAMEPLAY_SOURCE.json` | True | `93b57e4fa5c8d52bfe807d28a89cecc9459e5e7e17649e6f42a784af5c0dcdbf` |
| `Docs/Production/GameplayRules/2026-11-27/INTEGRATION_MAP.md` | True | `e8128d7461a8e29c4a631faa5ae95d89d189efcba0a87ef978ba5c6a846c4479` |
| `Docs/Production/GameplayRules/2026-11-27/CANDIDATE_FREEZE.json` | True | `29b11546165b8a32439a467c9b21cbd48f9c00b894734688468cac611bcb3f51` |
| `Docs/Production/GameplayRules/2026-11-27/CHECKPOINT.json` | True | `7460b1d94f6d1863893a8feafe82fff4545c635584b72d7b526a0619b0ff06f2` |
| `Docs/Production/GameplayRules/2026-11-27/PUBLICATION.json` | True | `f13bb2ee091de9eb7ecfa643144144b3ab02d94263ac2a62630481cf60e98662` |
| `Docs/Production/GameplayRules/2026-11-27/VALIDATION.json` | True | `24e2bb14b2871781d33a82249c72707e871b5e7a1664ae8b49ce8e54ca0174ed` |
| `Docs/Production/GameplayRules/2026-11-27/ECONOMY_COUNTER_API.md` | True | `9d09d9027e08640f0f20d56e762491e0e8fec677573692412154e8488bd171bd` |
| `tools/havenline/gameplay_rules/dynamic_economy.gd` | True | `0cf7a03cff95faf67b150fd5de13272df8750439dd924a423303494144580262` |
| `tools/havenline/gameplay_rules/bulk_counter.gd` | True | `932ec6d70f183a47869c0aaedcaaf40dbf32c5dec6c09c5816a80ce966330744` |
| `tools/havenline/gameplay_rules/camp_lifecycle.gd` | True | `f5b4542803a67d2f7219c17b16c9a60a74eb4ce09b283166a8f293ca805bb270` |
| `tools/havenline/gameplay_rules/threat_policy.gd` | True | `c63959c40adc47abcfb8583d7e01159b2f481755b3b5719dcd8e24062a0ae8fc` |
| `HavenlineLevel1/field_storage_house.gd` | True | `82c05042fbfe54763c0bb6f897f4a3407e39701db705fe71df2d816a473b4185` |
| `HavenlineLevel1/field_inventory.gd` | True | `e29ceacd0006b8697731911ac69bee6c75e49dccebf012ec2fd1465f507af773` |
| `HavenlineLevel1/field_settlement.gd` | True | `29081375e0f121b3b366c0c7bcbafdd971fc237de8f6f482cabcd1129838f27e` |
| `Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/README.md` | True | `bb8a3a8c5300014aca53fcfde4042874c4776a6fef6743ff867e035286455339` |
| `Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/requirements.json` | True | `57a461e68519d03b81904eca38f43ad525d3ef61e7a795921e48ad47914e319b` |

## Evidence limits

Recorded prior component validation: 303 native checks and 78 Python test methods. These counts were read from the source-bound receipt; this recovery task did not rerun those suites.

- No current native-rule import into field game
- No truck driving implementation, collision fit or contact proof
- No full animation/audio review
- No actual prior-save migration or mixed-era transaction adapter proof
- No playtested unlock/cost/HP/speed/raid balance
- No physical-device performance approval

No full-package copy, task approval, live gameplay edit, merge, workflow change or source reassignment was performed.

## Latest concurrent truck/garage addition

The final live read advanced the audit branch to `afc6d5da3a8605ba7baeb01b7bcc847c0a814347`. [The exact updated world source](https://github.com/ksolo21-web/HAVENLINE/blob/afc6d5da3a8605ba7baeb01b7bcc847c0a814347/Docs/Production/Build13Audit/World-Progression.md) already records the current truck/garage owner request and distinguishes it from playtest recommendations. This supersedes the initial world-note observation above for the added vehicle section. Both immutable versions are retained as text in the JSON record.

Source: 14518 bytes; SHA-256 `2c0b00d2bdf1126ecf1733cc6e56d4ca1f57f7f5e54242971ad457bea5452505`; Git blob `1133c145d608e5d0fe275b0a7723666dcd92bad2`; computed identity matches: `True`.

- **Owner truck requirements — MATCH:** The independently published audit records the same current user request; preserve it as supporting authority and avoid a duplicate competing owner specification.
- **Capacity/full destination wording — RECONCILE_RECOMMENDATION:** Audit explicitly labels partial/full-destination unloading as a playtest recommendation. Existing warehouse art does not define a finite cap and live raw storage has no capacity check. Proposed full-cargo transfer to an all-resource uncapped logical warehouse ledger avoids a new artificial cap; destroyed/offline warehouse keeps all cargo in truck on HOLD until automatic retry.
- **Fuel/inside-camp destruction/driver recovery — OPEN_IN_CONCURRENT_AUDIT:** Current new packet must select and clearly label these gameplay gap decisions; they are not asserted by the user request.
- **Task mapping — ADDITIONAL_RELEVANT_TASKS:** T03 gate topology and T07 controls accompany already recorded T08/T09/T10/T11/T14/T21/T22/T32, with T53 only for future regional vehicle travel.

No changed code or art was pulled into this recovery artifact. The new vehicle package can extend these documented requirements without modifying that active audit branch.
