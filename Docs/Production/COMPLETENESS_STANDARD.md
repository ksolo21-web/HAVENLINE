# Havenline — whole-game completeness and selected decisions

**Every pet attacks.** Guardian dog, gray wolf, fox, owl, lion, tiger and bear each need a useful, species-specific attack **and** a useful specialty. A scout, fetcher or warning effect cannot replace combat. This forward standard turns the known game-design gaps into selected behavior, task responsibilities and evidence requirements. It does not claim the game is finished or that an audit can discover every future defect.

The authoritative decisions and gap rows are in [WHOLE_GAME_COMPLETENESS.json](WHOLE_GAME_COMPLETENESS.json). Read the [dated package](Completeness/2026-11-27/README.md), [all-task map](Completeness/2026-11-27/TASK_COMPLETENESS_T01_T80.md), and [current gameplay source selector](CURRENT_GAMEPLAY_SOURCE.json). The previous [gameplay-depth standard](GAMEPLAY_DEPTH_STANDARD.md) remains binding. The selected CD decisions supersede its **open behavior choices D01–D05**, while preserving the old audit as evidence of what was known then. Numerical tuning and runtime acceptance remain open.

## What the player is protecting

The launch direction is recoverable pressure. The player protects an expedition, working companions, deliveries and the operation of exposed forward works. Hostiles can force a retreat, interrupt a useful trip, temporarily take a companion out of work, or disable an exposed machine/route until it is repaired. Warnings, positioning, the chosen team, equipment and working defenses let the player prevent those setbacks.

Owned materials, earned money, levels, plots, purchased items and named pets/survivors stay protected. A down returns the player to the last restored safe camp, or the guaranteed safe arrival anchor before the first camp exists, at full current health with working controls and camera. Companions retain their identity, upgrades and conserved cargo; a free care interaction restores their ability to work. Repair and care always have an attainable player-performed route. Initial construction/reconstruction of an unowned derelict site has its declared bill; restoration of damage to an already owned site is free. There is no absence damage, compulsory revive purchase, permanent surprise pet death or required hunger/stamina/oxygen meter. Loss/recovery, encounter resets and reward claims must be tested together so deliberate failure cannot duplicate value.

The permanent camp interior remains a sanctuary. Exposed forward work and perimeter defenses have explicit vulnerability and attack domains. A protected actor cannot exploit immunity to attack through a sanctuary boundary. A perimeter defense may engage its declared outside approach only when it participates in the exposed defense rules. Customers wait at safe staging when a route is unsafe; they do not become hunt targets or generate a fine that removes owned money. These are authored design choices, not behavior inferred from a reference still.

## Capable survivors and distinctive attacking pets

Survivors share the player's **unlimited logical mixed carrying policy**. A visible stack is an aggregated representation, never the actual capacity limit. Jobs still have bounded quantities, budgets and useful return conditions: a worker must not gather forever simply because inventory is unlimited. Every survivor can assist with harvesting, mixed hauling/storage, production/restocking, service/cash, authorized plot purchase and upgrades, construction/repair, defense, rescue/care, transport and coordination. All ordinary plot types include conveyors. Reachable equipment and a valid safe route are sensible prerequisites; paid basic intelligence and permanent job-family exclusions are not.

The selected expedition has up to **three pets and two survivor escorts**, with useful eligible camp/local assignments for the rest. The escort limit does not cap separately assigned local workers. When no eligible safe job exists, an honest ready/rest state is valid; useful AI must not become stuck idle while authorized work is available. These are authored starting limits, not performance claims. All seven remain ownable, useful and capable of attacking in suitable environments. Free switching at camp must preserve injury, cargo, jobs and attack recovery. Quality settings cannot silently reduce the number of logical jobs or create a different economy on slower devices.

| Pet | Required attack identity | Additional useful work |
|---|---|---|
| Guardian dog | Lunge, bite and intercept | Escort carriers and recover eligible light cargo |
| Gray wolf | Pursuit, pounce and bite | Track and pursue eligible targets within a safe leash |
| Fox | Quick dart, pounce and bite | Scout on the ground and retrieve suitable light items |
| Owl | Takeoff, bank, dive and talon contact | Aerial reconnaissance, warning and suitable retrieval |
| Male lion | Weighty charge/pounce, claw and bite | Hold an exposed approach and protect working allies |
| White tiger | Low approach, ambush pounce, claw and bite | Reachable flanking and interception |
| Brown bear | Heavy charge, swipe and bite | Suitable heavy hauling and obstacle work |

The [actor contract](Completeness/2026-11-27/ACTORS_COMBAT_GAPS.md) binds all seven to their existing exact GitHub sheets. Every species must prove real damage, a miss, interruption, recall, recovery, return to its specialty and use in later suitable progression. Mouth/talon cargo must be secured before an incompatible bite/strike. Friendly pets, hostile animals and hunt resources have separate identities.

Smart behavior means finishing useful jobs under changing conditions. It includes stable priorities, reservations, route recovery, shared engagement space, truthful intent and safe alternatives when a target is unreachable or a destination is full. Navigation avoidance is one mechanism; it cannot substitute for that job behavior. T07's approved human-context scope stays intact; species/T31 owners implement animal and job arbitration.

## A connected journey with worthwhile materials

The dated [progression and economy plan](Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.md) supplies 100 authored outcomes within the existing ten-region cadence. Each level needs a useful visible payoff, and each region needs a distinct production, route, restoration or defense problem. The original T12 role IDs and resolved T10/T11 bindings are retained; those structural records alone were not 100 authored game outcomes.

Core resources continue to matter across regions. The selected chains give coal, ore/metal, slate, planks and blocks actual uses, and earned money has real reinvestment sinks. Each shipped identifier has an acquisition path, useful destination, tangible payoff and surplus/retirement policy. Containers and alternate art are not automatically new inventory items. The complete concept dispositions remain separate from the canonical economy.

There is one ordinary earned-money currency and one primary premium currency, **Gems** (`premium_gems`, subject to explicit migration from any already selected wallet ID). Till, pocket and house are custody locations for ordinary money. XP is progression; VIP is an entitlement. Launch events use existing resources/currencies and explicit rewards, without an extra token wallet. Exact quantities, prices, reward amounts and rates require reachable free-player simulations and playtests before producer integration; selecting a recipe does not prove it balanced.

Regions retain credible travel and animal behavior. Underwater work uses dry protected routes/habitats and work positions where equipment reaches salvage; the owl stays on suitable air routes or staging. Sky areas use connected platforms/bridges. Other difficult terrain has restored safe lanes and explicit return routes. Unsuitable pet combat in a location gets a useful safe assignment; it does not remove that species' real attack elsewhere or invent a maintenance meter.

Level 100 completes the restored network with an earned conclusion and celebration, then leaves the existing production, exploration and launch events playable. Additional endgame systems, decoration, co-op, new regions and a higher cap remain in the [post-launch roadmap](POST_LAUNCH_ROADMAP.md).

## The systems must agree at their boundaries

The [transaction and recovery matrix](Completeness/2026-11-27/TRANSACTIONS_AND_RECOVERY.json) covers ten value-bearing boundaries: cargo, plot contributions, machine recipes, sales/cash, attack contact, defeat rewards, actor care, region travel, event rewards and purchases. Each declares precommit state, the authoritative commit, postcommit state, interruption recovery and its clock.

Ordinary simulation pauses while the app is backgrounded or closed. A returning player resumes actual saved state, with no absence penalty or invented offline earnings. Offscreen jobs may advance during an active session using the same conserved ledger. Server time controls event availability and verified purchases/entitlements; changing the phone clock cannot create value. Launch event progress requires a verified connection and pauses clearly offline without consuming event inputs. A verified completion before expiry creates a durable earned claim that remains deliverable after expiry; interrupted delivery grants it once on reconnect. Until that receipt exists, the UI shows pending rather than earned. Ordinary core play and recovery remain usable offline; server-only value stays visibly pending or unavailable until verified.

First-use, returning-player and busy-camp tests must explain the next useful action, material purpose, threat consequence, helper intent and blocked action in context. Existing accessibility requirements apply to these actual states: non-color cues, readable text, touch targets, reduced motion, subtitles and persisted input preferences. A denied payment must not play a success animation or sound. Sound is reviewed through listening, including busy play and muted equivalents.

Every actor, tool, weapon, machine, vehicle and world-change interaction needs its applicable complete use states. Static renders and schema checks cannot prove contact, weight, full cycles, transitions or performance. Current reference dimensions remain at least **9.9 individually**, with all stronger **exact-10 visual gates** retained. Missing evidence blocks approval; no average or historical score can hide a failed area.

## Correct source, layouts and release evidence

Use `CURRENT_GAMEPLAY_SOURCE.json`: the observed newer Codex branch is `trial/world-one-expansion-2026-11-26` at `2f46e72e300a719f34ca9b0e9b718282a5a88ddd`, with Build13 reported game source `2654f5019b7212968d28600cb071bf1c231c9030`, project `HavenlineLevel1/project.godot`, scene `res://field_opening.tscn`. The [latest source note](Completeness/2026-11-27/LATEST_SOURCE_DELTA.md) separately preserves the3fad deep audit, credits new warehouse/roster/cargo work and records the reported9.5/9.9 review limits. Resolve the live head and active ownership before modifying gameplay. Main and the older Alfred checkpoint remain preserved source roles; this plan does not merge or reset them.

Landscape remains the product requirement. The selected baseline is both landscape rotations, with platform export settings in agreement. The observed orientation6 setting permits portrait and requires implementation reconciliation. The phone16:9 fixture is corrected to1920×1080; the separate20:9 case remains2400×1080. Logical layout checks do not replace physical fold/resume/input tests or sustained native4K60 certification.

Existing commerce, LiveOps, security, diagnostics and release contracts already cover their domains. This audit connects them to the new loops: impossible event prerequisites, expiry while absent, duplicated claims, ordinary worker spending, cloud conflicts, analytics failure and actual install/update/recovery. Validation-only tasks route repairs to feature owners. The release still needs exact-source integrated gameplay, free-progression, purchase, event, exploit, accessibility, regression and physical-device evidence.

## Scope and honest completion

The24 CG rows distinguish real specification/documentation defects from existing requirements that need integration or proof. Twelve CD decisions select forward behavior. The authentic plan still contains **70 task definitions**; **T71–T80 remain source gaps**. Levels71–80 are real progression content under T50 and must not be confused with those undefined task IDs. Complete privately held original-video/editable-source custody also remains unverified.

Run `python3 tools/havenline/production/completeness.py check` to verify the bounded plan, exact source bindings and projections. Future task packets include applicable CG requirements and current decisions. The checker approves neither gameplay nor a production task. Existing graph edges, ownership, frozen scopes, historical receipts, rejected evidence and inactive workflows remain preserved.

The next implementation sequence is concrete: reconcile the current Codex owner/source; prove shared custody and T21 combat/contact prerequisites, then the dependent survivor work/cargo/payment/save loop; prove each pet's attack plus specialty and each producer's value chain; integrate the busy Level1–10 experience; then carry the authored outcomes and evidence through Level100. There is no claim that writing these requirements implements them.
