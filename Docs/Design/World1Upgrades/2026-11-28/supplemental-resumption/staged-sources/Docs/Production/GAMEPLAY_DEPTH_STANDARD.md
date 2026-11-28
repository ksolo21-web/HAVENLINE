# Havenline — stakes, capable companions, animation and resource value

Current forward rules: 2026-11-27, latest user correction **U3**. Historical audit baseline remains `9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c`; current source precedence is recorded in CURRENT_GAMEPLAY_SOURCE.json.

This addendum carries Kaleb's current full-game requirements into the existing T01–T70 plan. It does not renumber tasks, grant an implementation approval, change an active assignment or invent T71–T80. Read the [machine-readable task requirements](GAMEPLAY_DEPTH_CONTRACT.json), [resource/value inventory](GameplayDepth/2026-11-27/RESOURCE_VALUE_LEDGER.json), and [current audit and task crosswalk](GameplayRules/2026-11-27/README.md).

## What is decided, and what still needs design proof

Source observations have a dated precedence rule: the [3fad812 branch update](GameplayDepth/2026-11-27/CURRENT_BRANCH_NOTE.md) supersedes the historical Build 11 cash, carry, drop-cap and hearth observations where specified. It credits new source groundwork without treating code inspection as a game, animation or balance approval. Keep the original historical audit and its hashes intact.

**Existing commitments** remain binding: simple movement/context controls; visible gathering, carrying, delivery and transformation; seven useful animal companions; role-appropriate human and species-specific animal motion; spend-blind challenge; no energy wall or miserable free-player path; one primary premium currency; transparent permanent VIP; and a realistically completable $0 Level 1–100 journey. These are recorded in the build plan and resource/tool/actor standard.

**Current user requirements** are binding forward requirements: explain meaningful player stakes; make pets and survivors intelligent and useful; let survivors assist every physical work task family, including funding approved plots and carrying substantial mixed loads; animate the equipment, enemies, pets and complete interactions; give every shipped resource/currency a clear worthwhile purpose.

**Current selected design and unresolved tuning:** [GAMEPLAY_RULES_STANDARD.md](GAMEPLAY_RULES_STANDARD.md), [GAMEPLAY_RULES_CONTRACT.json](GAMEPLAY_RULES_CONTRACT.json) and the current CD decisions select bulk self-service, unlimited logical survivor carrying, dynamic reachable quotes, hunting/provocation, paid companion replacement, destructible equipment and furnace blackout. Numerical recipes, rates, costs, unlock pacing, pet bonuses and threat timing still require owner measurements. These rules are not observations from footage or proof of implementation. Static art does not establish a recipe, edible species, yield or price.

## 1. Give the player something meaningful to protect

The player should understand: **what is threatened, why it matters, what can be done now, and how to recover if the response fails.** Threats must connect to the visible camp and its working people, animals, machines and supply routes. Difficulty should create decisions about where to go and what to improve while preserving the simple control scheme.

Every threat owner must specify the warning, trigger, threatened object, consequence, maximum exposure, counterplay, retreat/cancel behavior, recovery path, grace period, repeat-failure behavior, offline behavior, save/resume semantics and accessibility equivalent. Unknown numeric limits remain explicit tuning work and block approval of that threat's final balance. A dramatic animation without a meaningful gameplay consequence does not establish stakes; an invisible penalty without a readable cause does not establish fair challenge.

### Current loss and recovery policy

Companions may die and require ordinary paid replacement. Structures have finite HP, material repairs and explicit damage/ruin states. Destroyed equipment restarts at level 1; fence/gate reconstruction retains its purchased tier. Furnace destruction pauses local automation/customer admission and requires a substantial raw-material rebuild, while preserving a manual recovery route. Persistent typed salvage conserves cargo and contents. The player retains owned cargo/progression on down. Permanent entitlements and the realistic $0 route remain protected.

Survivors may hunt and initiate authorized attacks. With a player or eligible defending pet near, enemies cannot directly select an unprovoked survivor, even when their preferred target is blocked. The attacked enemy may retaliate against a provoking survivor; both player and defending pets being far permits all characters and destructible camp equipment as targets. Actual collateral contact is damageable. App background/close pauses ordinary simulation without absence attacks.

Every previous unaffected threat requirement above remains binding: warnings, understandable consequences, counterplay, repeat-loss recovery, accessibility and exact save behavior. The [supersession register](GameplayRules/2026-11-27/SUPERSESSION.json) records the withdrawn gentle-stakes recommendations and the retracted survivor self-defense-only instruction.

T13/T33 must demonstrate recovery from compounded low resources, damaged production and unavailable helpers. A novice can make mistakes without entering a state where no free action can restore progress. A recovery loop must resist intentional-failure farming without making honest recovery punitive. Forced app closure, a crash or a reconnect must not duplicate rewards, repeat a committed penalty or erase a valid recovery claim. Whole-game acceptance tests ordinary play, repeated failure and interruptions, not only a winning scripted run.

## 2. Survivors are a capable workforce

Every physical work task family that the player can perform must have a survivor-assistance decision. Required families include harvesting/hunting/fishing/crops, carrying and sorted delivery, machine loading/operation/unloading, cooking, bulk counter stocking for customer self-pickup, collecting/transporting all earned payment, plot funding, building/upgrading/repair, resupply, guarding/escort/combat, rescue/healing, and later-region transport and environment-specific work.

Specialization changes competence, speed, equipment or role preference. It must not become an unexplained permanent ban on the requested task parity. Individual workers may need training, tools, protective equipment, a safe route or a current assignment. Those prerequisites are visible, achievable and recorded. Customer NPCs remain customers; not every human-shaped NPC is automatically a worker. Account purchases, premium spending and major owner choices are not delegated merely because a survivor can carry materials.

### Complete the whole job

A helper recognizes useful work, selects a valid goal, reserves the job and required resources, takes the proper equipment, travels through a reachable route, performs the authored action, carries the result, delivers it to the correct destination and confirms completion. It handles an empty source, missing tool, full destination, blocked gate, canceled goal, changed target generation or invalid acquisition path, interrupting enemy and save/reload. It does not repeatedly run into a wall, oscillate between targets, collect materials with no destination or abandon cargo without a recorded recovery action.

The scheduling layer considers goal priority, urgency, travel distance, supply shortage, skill, cargo, route risk and available destination space. Use stable priorities and reservations so the entire population does not chase the same item. Emergency response and player orders can preempt ordinary work, with safe cargo/transaction handling. Resume or deliberately reassign the suspended job afterward. Preserve simple player controls: a small number of work priorities and approved goals, with short explanations such as “bringing fuel” or “waiting for storage.” Do not require a new management dashboard to make basic helpers useful.

### Large, useful carrying

Survivors use the same typed-custody and readable mixed-resource delivery principles as the player. They use unlimited logical carrying with bounded useful job targets, clear empty/partial/full destination states and visible mixed stacks, including the approved two-row back-carry direction when applicable. Equipment, locomotion, grip and loaded turns must remain believable at gameplay scale.

The historical finite-worker premise is superseded: player and survivors share **unlimited logical mixed carrying**. Job batches, ordinary budgets and demand targets remain bounded. Equipment and efficiency upgrades may improve throughput, without imposing a small inventory limit or charging for basic competence. Logical quantity and rendered stack count are separate; visual aggregation preserves type, ownership and quantity without discarding overflow.

### Survivors may fund and buy approved plots

T10/T23/T31 must support delegated plot contribution and completion, through the same authoritative purchase rules used by the player:

1. The player enables a specific plot, upgrade or bounded goal and a permitted material/ordinary-currency budget. Delegation has a visible off/cancel action.
2. All workers share the same reservations and budget. They respect protected food/fuel/repair reserves and other funded goals.
3. A worker collects and physically delivers appropriate resources. Partial contributions retain exact ownership and progress.
4. Before debit/commit, validate the plot generation, prerequisite/acquisition state, frozen accepted quote and remaining contribution, current authorization and budget. Concurrent player/helper contributions cannot purchase twice or overspend.
5. Interruption, cancellation, full storage, companion death or player-down state, save/reload and retries release or preserve reservations correctly. Unspent cargo returns to an authorized destination. A committed purchase never debits again.

Autonomous premium spending, real-money billing, irreversible owner choices and unapproved expansion are outside delegated plot funding. The player should experience useful assistance without surrendering control over the camp plan.

## 3. Pets need distinct, observable jobs

All seven companions remain in scope. Their existing species-appropriate action language is preserved. The following role emphasis is the **selected authored direction**, with all seven attacks mandatory; it is not footage-derived behavior or a measured statistical kit:

| Companion | Distinct useful role to prove | Visible work/combat examples |
|---|---|---|
| Guardian dog | Protect workers and recover light cargo | Intercept a threat, guard a work party, track/retrieve an eligible item. |
| Gray wolf | Track and pursue threats or eligible wild prey | Scent/alert behavior, controlled pursuit, flank/attack, return to the assigned route. |
| Fox | Ground scouting and agile retrieval | Inspect a reachable side route, locate an eligible cache, retrieve a small item, evade a bad engagement. |
| Owl | Aerial scouting, warning and precise assistance | Take off, inspect above ground obstacles, signal a threat/resource, retrieve only a suitable light object, dive and land safely. |
| Male lion | Frontline protection and interception | Hold a defended approach, intercept a strong threat, charge/pounce/claw/bite with readable commitment and recovery. |
| White tiger | Ambush and priority-target control | Stalk, choose a useful target, pounce and disengage rather than duplicating the lion's job and timings. |
| Brown bear | Heavy support and protection | Authored heavy hauling or approved obstacle breaking, powerful defense, weight-aware turning and contact. |

Each pet must prove at least one useful ordinary-play situation and a reason to choose it over another companion. Cosmetic/stat-only differentiation is insufficient. An upgraded pet still obeys cargo, reachability, target eligibility, conservation and danger rules. No human tool fallback, invisible resource creation, unlimited weightless owl haul or cloned attack cycle. Companion entities are separate from wild prey and resource eligibility; a meat concept bearing a species name does not authorize harvesting the player's companion.

T31 validates the combined population. Workers and pets coordinate, leave openings usable, avoid blocking customers, respond to a changed route and recover when a target disappears. An active-team/population budget must be tested on target devices. Pets should contribute without making the player irrelevant or turning every outing into seven overlapping attacks. The selected starting expedition limit is three pets and two survivor escorts, with separately assigned local workers. Actual population/performance and rotation timing require evidence; offscreen active-session work uses transparent, conserved state.

## 4. Full animation means full state and transition coverage

Every actor, enemy, machine, defense and transport feature needs a state/action table. Record entry/setup, anticipation, action loop, authoritative impact/transfer beat, completion, exit, transition, interruption/cancel, blocked/empty/full state, damage/death/ruin/paid recovery where applicable, and restoration after loading. A row can be genuinely inapplicable with a reason; a missing row is not a pass.

Humans require distinct relevant unloaded/loaded motion, starts/stops/turns, equipment changes, harvesting, interaction, pickup, stack handling, delivery, construction, repair, rescue/care, guard/combat, hit/retreat and recovery. Later region equipment and motion must fit the actual environment. A generic idle pose or a single swinging loop cannot cover this set.

Enemies need role-specific intent and readable anticipation, pursuit/repositioning, attack commitment, hit or miss, recovery, hit reaction, retreat/defeat as designed, and interactions with their actual targets. Damage range and hit timing must agree with what is shown. Higher difficulty adds understandable combinations and counterplay rather than only invisible damage or inflated health.

Machines show the process: material arrives, the relevant parts operate, output appears through the real production transaction and the next transport stage receives it. Conveyors, storage, customer pickup/payment and bulk stocking, fishing equipment, cooking, crop equipment, defenses, gates and vehicles have meaningful empty/running/blocked/full/interrupted/resumed states. A decorative spinning part does not prove a working production chain.

Each important committed event connects to T54's existing audio contract: appropriate SFX, ambience/music response or deliberate silence, timing, priority, concurrency limits, accessible visual equivalents and actual listening evidence. No reward or purchase-success cue on a preview, failed action or replay. Crowd activity remains readable; activity does not justify constant noise or unnecessary camera shake.

Review actual full cycles and transitions at gameplay speed and slow playback, from meaningful different views. Inspect feet/toes/knees, hands/grip, claws/paws/wings/tails, tools, clothing, cargo and contact/clipping. Score under the current reference acceptance policy; all stronger exact-10 requirements remain. Reduced visual detail may change rendering cost while preserving gameplay truth, readable attacks and important action timing.

## 5. Every shipped resource and currency must earn its place

For each actual economy ID, freeze: identity/aliases, acquisition and eligibility, processing input/output relations, primary use, concrete player payoff, cost/yield/availability by phase, intended demand, delivery/carry rules, survivor/pet applicability, surplus/retirement behavior, risk/recovery interactions, audiovisual proof and owner tasks. A primary use can be sufficient when it is meaningful; do not invent extra sinks or universal cash conversion merely to fill a table.

The [value ledger](GameplayDepth/2026-11-27/RESOURCE_VALUE_LEDGER.json) distinguishes the six canonical registry IDs, current-foundation observations, the 33 resource/material render rows, currency policy slots and future-region decisions. Render variants, cargo containers, money art, XP, VIP entitlements and recipe states must not silently become extra currencies or duplicated economy IDs. Every rendered concept receives an explicit disposition: map to a real ID, remain a cosmetic/visual variant, defer with an owner, or exclude from gameplay while preserving its asset.

Wood/stone/metal/fuel need continuing useful demand, visible construction/production payoffs and sensible substitutes where authored. Food and processed goods must connect gathering to actual care/service/trade or another selected purpose. Slate/steel/planks/firewood/hide/fur and species cuts need explicit mappings and recipe/eligibility decisions; do not infer those rules from the picture. Unknown future-region materials remain unknown until the region owner specifies their purpose.

Earned ordinary money and the single primary premium currency have separate roles; launch events use existing rewards without a separate token wallet. XP measures progression and VIP grants entitlement; neither is automatically a spendable currency. Optional premium purchases preserve their stated value and cannot become the only recovery, required-worker-intelligence or basic carrying path. Preserve verified earned event claims through expiry and reconnect; do not add several currencies that buy the same mandatory progress.

T33/T63 must simulate early/mid/late-game supply, realistic play sessions, helper throughput, worst-case interruptions, recovery, storage pressure and all critical recipes. There must be a reachable free route through the progression dependency graph, no circular prerequisite lock, no dominant infinite conversion loop, no currency stranded behind an unavailable sink and no material whose intended phase ends without a stated retirement/use policy. Numerical costs and rates require actual balance evidence; edited reference videos do not supply those values.

## 6. Ownership, evidence and the next executable work

The contract maps each requirement to its existing owner and consumers. T13 owns the stakes/challenge design; T08/T10/T14 own carrying, plot transactions and persistence interfaces; T23 owns survivor behavior; T24–T30 own the individual companions; T31 owns coordination; T33 owns value/balance; feature owners supply full motion/event states; T54 owns final audio integration. T32/T62/T63/T67/T70 exercise the combined game. T44–T53 extend the contract for actual new regions and transport.

These are planning and evidence responsibilities, not new dependency-graph edges. Each introducing feature freezes its own useful resource/action contract before implementation; T33 later validates the combined economy and cannot become a circular prerequisite for earlier producers that it already depends on. Each animal task proves its standalone useful behavior before T31 tests the combined population. Shared interfaces can be prepared in parallel under existing ownership.

Start with the shared task, typed-custody, destination/reservation and plot-budget interfaces before adding more autonomous actors. Then prove one complete survivor work loop and one useful pet loop under interruptions before expanding the roster. Keep independent authorized work moving while failures route to the owning task; a failed feature's approval does not prohibit unrelated preparation or production.

The integration evidence includes a busy shift with concurrent workers, pets, machinery, deliveries and threats, followed by interruption and recovery. T31/T32 and T56/T58/T68–T69 record source-bound performance and visual evidence at the selected population and device settings. Full animation does not require constant motion from idle objects; meaningful stillness, reduced-motion alternatives and offscreen presentation rules must retain gameplay correctness. No population or frame-rate result is inferred from a planning check.

The plan helper validates source coverage and prints each task's addendum; it never approves gameplay. Generated task packets include their applicable IDs and required evidence. Existing closure, source, critic, device and ownership requirements still apply. No live branch is modified or unlocked by this document, and no historical completion receipt is rewritten.

### Implementation references

Godot's [NavigationAgents documentation](https://docs.godotengine.org/en/4.7/tutorials/navigation/navigation_using_navigationagents.html) separates route following, custom actor movement and avoidance; navigation alone therefore does not implement the job/reservation logic above. Its [AnimationTree documentation](https://docs.godotengine.org/en/4.7/tutorials/animation/animation_tree.html) provides blend/state-machine tools for authored transitions. These are implementation references checked on 2026-11-27, not evidence of Havenline feature completion or permission to change the project's pinned engine version.

The current GR/CG/GD task projections preserve unaffected prior obligations. Native rule components and headless tests are preparation for actual scene integration, never a new game, animation, audio, balance or device approval. Reference-sensitive final dimensions remain at least 9.9 each, with stronger exact-10 visual gates.
