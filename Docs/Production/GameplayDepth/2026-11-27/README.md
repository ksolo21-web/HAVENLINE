# Havenline whole-game depth: stakes, capable companions, animation and value

**Planning requirements and source audit — not a runtime implementation or gameplay approval.**

The current user requirements are now attached to the authentic T01–T70 plan: meaningful player stakes; extremely capable and useful survivors/pets; survivor assistance across human work, including delegated plot funding and substantial mixed carrying; complete actor/equipment/enemy animation; and a worthwhile purpose for every shipped material and currency. T71–T80 remain explicit undefined source rows.

## Start here

| Need | Document |
|---|---|
| Binding forward requirements and clearly labeled design recommendations | [Gameplay-depth standard](../../GAMEPLAY_DEPTH_STANDARD.md) |
| Eighteen requirements, owners, consumers, evidence and five open design decisions | [Gameplay-depth contract](../../GAMEPLAY_DEPTH_CONTRACT.json) |
| Each task's additions, preserved dependencies and relevant open decisions | [T01–T80 crosswalk](TASK_GAMEPLAY_DEPTH_T01_T80.md) · [JSON](TASK_GAMEPLAY_DEPTH_T01_T80.json) |
| Current consequences, exact source anchors, all resource/render IDs and recommended purposes | [Stakes/economy audit](STAKES_ECONOMY_AUDIT.md) · [Resource-value ledger](RESOURCE_VALUE_LEDGER.json) |
| Full human work coverage, smart jobs, delegated transactions, seven species and animation scenarios | [Actor/motion audit](ACTORS_MOTION_AUDIT.md) · [Detailed requirements](ACTORS_MOTION_REQUIREMENTS.json) |
| Exact source bytes and limits | [Pinned source bindings](SOURCE_BINDINGS.json) |
| Newer gameplay source observed during the audit | [Current branch note at 3fad812](CURRENT_BRANCH_NOTE.md) · [Source census and hashes](CURRENT_BRANCH_NOTE.json) |
| Checkpoint, actual review and publication status | [Checkpoint](CHECKPOINT.json) |
| Reproducible planning verification and independent verdict | [Validation](VALIDATION.json) · [Scope preservation](SCOPE_VALIDATION.json) · [Independent final review](FINAL_REVIEW.json) · [Frozen candidate](CANDIDATE_FREEZE.json) |

## Newer source supersedes two historical findings

During the audit, the gameplay branch independently advanced to `3fad812b384335bd8ca9b5e47dc9d9557110eb4a`. The [bounded source update](CURRENT_BRANCH_NOTE.md) takes precedence over the Build 11 observations below where behavior changed. It establishes cash collection, carrying, storehouse deposit/withdrawal and a pocket-cash HUD; planks and blocks are also now directly carryable and transferable. These are source-level improvements, not new runtime test results. Cash spending/reinvestment and downstream plank/block consumption remain unproved in the reviewed newer contracts. Pocket, house and till are locations of one earned-cash family, not separate currencies.

The newer source removes the oldest-loose-drop deletion at the field cap; played-time expiry remains. Safe-camp hit rejection and the zero-HP return/reset remain, while gradual camp healing now requires a fired hearth. This guard does not establish fuel drain, hunger, exposure damage or an extinguishing mechanic. New owl-roost ownership and survivor service/mixed-gathering logic are credited in the update, with full intelligence, animation and all-task parity still unverified. The original Build 11 audit, ledger and source receipt are retained unchanged as dated evidence.

## What the inspected risk paths establish

The initial inspected Codex Build 11 source is `989edd9283148e9f712387fb937ea36038cbd9d2`. It is the source identified by the previously verified build receipt; the newer branch snapshot above has also been inspected within its stated bounds. This audit read code; it did not run a new build or playtest.

At that pin, enemies damage the player outside camp; camp rejects those attacks and heals. At zero HP the player falls, work is interrupted, and the reset returns them to the safe start with full health. No material, purchased-plot or companion deduction appears in the inspected defeat/reset path. Paid machine input/work is preserved. That supports an interruption-and-return consequence; it does not establish a complete whole-game loss policy. Loose uncollected drops can expire or be removed at the drop cap during played simulation time. Those losses are distinct from owned inventory and do not prove offline erosion. Exact files/functions are retained in the [source audit](STAKES_ECONOMY_AUDIT.md).

**The recommended whole-game direction is meaningful, recoverable pressure.** The player protects a working camp, safe routes, useful production, expedition success and people/animals. A threat should create a decision: retreat, defend, escort, rescue, repair, resupply, redirect work or improve preparation. Consequences should affect the activity threatened and lead to a clear recovery action. Losing an optional bonus, needing to repair a machine, retrieving a deliberately designed cargo cache or bringing an incapacitated companion to safety are possible authored designs, not claimed current mechanics.

The standard requires each threat to name its warning, cause, threatened object, consequence, maximum exposure, counterplay, recovery, repeat-failure behavior, offline behavior, save semantics and accessible cues. Exact values remain task-owned tuning. Default protection of completed ownership, named companions and purchased value is recommended; no surprise permanent-loss rule, compulsory paid rescue, arbitrary inventory tax or absence punishment is introduced by this audit. Existing fair-F2P and spend-blind difficulty commitments remain binding.

## Survivors must finish useful work

The plan now covers ten human task families: harvesting/extraction; mixed cargo/storage; processing/restocking; customer service/cash collection; plot purchases/upgrades; construction/repair/recovery; defense/resupply; rescue/escort/care; transport/region logistics; and scouting/coordination. Training and tools may change readiness or efficiency; specialization must not permanently exclude ordinary survivors from most human tasks.

Useful intelligence means selecting a permitted goal, reserving real inputs/work space/destination capacity, navigating safely, using the correct tool, completing the transaction, delivering results, releasing unused reservations and adapting to changed conditions. Workers must handle a depleted node, blocked route, full output, another worker's claim, player intervention, danger, canceled order and save/reload. A job loop that only works in one scripted arrangement is insufficient. Small goal/priority controls preserve the simple interaction design.

The pinned foundation already includes a limited `worker_payment` path using actual worker-carried material; it excludes `Progress.LINES`. It also declares per-kind worker-load limits. These are useful source foundations, not proof of full permission, mixed-load throughput or purchase parity. The user has required substantial useful mixed loads, without choosing a new exact limit. T08/T23/T31 must reconcile finite/upgradable worker capacity with the existing unlimited logical player inventory contract. Large visual stacks must reflect real typed custody; an unlimited pile animation is not capacity evidence.

Delegated purchasing requires the player to authorize a plot, allowlist or goal and an ordinary resource/cash budget. The crew reserves the required goods, protects minimum stock, rechecks price/prerequisites/permission and commits once. Canceling permission releases uncommitted resources; reload cannot double-charge or create a free plot. Autonomous premium spending, real-money checkout and unrequested base rearrangement are outside that delegation.

## Seven pets, seven useful specialties

The existing selected GitHub references and capability matrix remain the source for identity and physical design. The operational roles below are authored recommendations within that capability scope; they are not inferred mechanics from a still render.

| Companion | Recommended useful role | A scenario that must demonstrate value |
|---|---|---|
| Guardian dog | Close escort, guard and interception | Protect a loaded survivor or rescue route, intervene, then resume the assigned escort. |
| Gray wolf | Tracking and pursuit | Find and respond to an eligible threat without abandoning safety or pursuing forever. |
| Fox | Ground scouting and light retrieval | Reach and return suitable items, report danger and avoid a blocked or unsafe route. |
| Owl | Aerial scouting, warnings and light retrieval | Reveal a threat or route opportunity through a clear visible/audible cue and a complete flight/landing cycle. |
| Male lion | Defensive holding and interception | Hold a useful route/position and protect work rather than wander through the same attack loop. |
| White tiger | Flanking and priority interception | Reach a useful target by a viable route, attack with readable timing and disengage appropriately. |
| Brown bear | Heavy hauling, approved obstacle work and defense | Move an appropriate substantial load or clear an authorized obstacle without blocking the settlement. |

Each species needs useful costs/benefits and complete motion for its actual capabilities. Pets do not become human tool users or autonomous financial agents. Friendly companion identity must remain distinct from hostile/wildlife drop eligibility even where species names overlap. Balance, carrying allowances, population limits and physical attachment choices remain open design decisions.

## Complete animation is a state contract

Twelve coverage families span human locomotion/work/cargo/care/combat; animal jobs and owl flight; production equipment; conveyors/storage/service; defenses; enemies; and environmental/event feedback. Each implemented action needs its approach, alignment, preparation, work loop, impact, result, finish and applicable interruption/recovery states. Input empty, output full, waiting, jammed/blocked, denied and restored states must read truthfully.

A saw must visibly receive and process wood into the selected product; a conveyor must move the conserved item; a plot payment must correspond to a real committed deduction. Enemies need their own readable anticipation, attack, contact, reaction and recovery. Companion motion must fit its anatomy and job. Reusing generic motion that obscures those differences does not satisfy the requirement.

Approval needs actual full cycles and transitions from meaningful angles and gameplay distance, close contact/grip/foot/clipping views, simultaneous actors/machines, and real listening for audio. Stillness may be correct for a stopped machine or resting animal. Reduced-motion and offscreen presentation may simplify safely while preserving state truth. No artwork or schema score substitutes for animation, audio or on-device performance evidence.

## Does every item already have a worthwhile purpose?

**No. The audit exposes that gap instead of declaring it solved.** Six registry IDs, six foundation raw IDs, three foundation processed IDs and 33 resource render concepts are overlapping inventories. The ledger classifies them; it does not turn every illustrated variant into a separate economy ID. The newer source retains those six raw and three product IDs and adds `money` to the four-key goods-transfer interface. Its cash fields and new owl entitlement fields do not create extra materials or currencies.

At both inspected source pins, wood/stone/meat have immediate uses in the reviewed offers/processors. Coal/slate/metal have no demonstrated spend or processing sink in those reviewed contracts. Planks and blocks have production/storage/milestone uses but no downstream spending or sale found there; the newer source adds direct carrying and warehouse transfers. Meal has real customer consumption. Build 11's cash was a mesh and served-count display; the newer source now has distinct earned-cash custody and conservation code. A meaningful cash-spending/reinvestment loop remains unproved in the reviewed newer files. These findings are bounded to the named source contracts.

The standard now requires every actual item/wallet to name its source, primary use, visible payoff, progression/demand, quantities/effort, custody, presentation and surplus/retirement treatment. One meaningful finite use can be sufficient. More currencies, endless demand or universal sale are not required. A product with no payoff must get a useful role, become an explicit visual/source variant, be deferred or be retired before integration.

Recommended chains include useful wood/plank construction, stone/block structures, an explicit ore/refining/tool-or-machine payoff, a reconciled fuel family, food production/service, and worthwhile hide/fur gear only if those recipes are selected. Species cuts and dried/prepared-food art need identity decisions; art alone does not impose extra recipes, hunger, spoilage or hunting permissions. Earned cash needs a real earn/collect/save/spend loop. The existing one-premium-currency policy remains; its final name is not invented. VIP is an entitlement, XP/counters are not automatically spendable wallets, and cargo is typed contents/presentation unless a separate container mechanic is deliberately chosen.

## Task integration and next executable work

The packet generator now projects the applicable GD requirements and task-specific details. This is a forward planning contract, not an automatic gameplay enforcement or approval gate. Its source checker validates identity, inventory completeness and saved projections. Existing task gates and independent exact-candidate evidence still decide implementation acceptance.

The critical path is shared identity/custody/reservations and delegated purchase permission; one complete survivor gather→carry→deliver→authorized-build loop; one species-specific useful pet loop; complete action/equipment states; then a busy integrated shift with multiple workers, companions, production and a threat. Early feature owners prove their own useful contracts. T31 integrates companions and T33 integrates economics later, so the new plan adds no backward dependency deadlock.

Five decisions remain explicitly unfrozen: the complete loss/recovery baseline, worker capacity policy, canonical recipes/aliases, pet kits/population balance, and currency names/economic/event rules. Final runtime approval requires their selected designs and measured normal-player evidence. Historical task approvals and active gameplay branches are preserved. The existing final reference floor of at least 9.9 per applicable dimension and stronger exact-10 visual rules remain intact.

## Reproduce the planning checks

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/havenline/production/gameplay_depth.py check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/havenline/production/tests -p test_gameplay_depth.py -v
PYTHONDONTWRITEBYTECODE=1 python3 tools/havenline/production/gameplay_depth.py task T23
```

Also run `PYTHONDONTWRITEBYTECODE=1 python3 Docs/Production/GameplayDepth/2026-11-27/verify_scope.py --root .` for change-scope, preserved-source, JSON and relative-link checks.

These checks are source/plan checks. A passing result keeps `runtime_approval_allowed=false` and `game_score=null`. The dated source universe is verified against exact Git commits; missing historical source objects block reproduction rather than silently reducing coverage. The checkpoint and retained independent review record describe review/publication status, including repaired findings. No current game score is assigned.
