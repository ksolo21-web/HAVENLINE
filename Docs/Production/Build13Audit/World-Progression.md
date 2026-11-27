# Havenline · World 1 launch and connected-world updates

**Release direction:** Launch with World 1, Frozen Home Camp. Worlds 2–10 arrive as later updates and connect to the existing camps and supply routes. **Progression proposal:** Prototype World 1 with room for up to 50 local levels. The final count depends on how much distinct play the world supports. Fifty levels in each of ten worlds would mean 500 levels overall. Decide how local levels relate to a global level display before changing save IDs or the T12 progression contract. The earlier 100-level campaign supplies goals and region themes. [Earlier authored outcomes](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.md#the-100-authored-outcomes)

## World 1 · Proposed progression

| Local levels | What changes |
|---|---|
| **1–10 · Establish the camp** | Explore the clearing, gather wood, stone and food, build the hearth and gates, and open the first storage, trade and rescue opportunities. |
| **11–20 · Open the supply routes** | Explore the woods, quarry and lakeshore. Choose which routes and producers to open first. Bridges, work shelters and alternate return paths change who can reach a site and how supplies get home. |
| **21–30 · Grow trade and production** | Open more food and workshop options, varied self-service orders, and bulk hauling. Choose where helpers and conveyors will relieve a bottleneck. |
| **31–40 · Defend an expanding camp** | Open new work areas within the frozen world. Choose perimeter and supply improvements, prepare for warned raids, and restore damage afterward. |
| **41–50 · Run a resilient settlement** | Support several work areas by alternate routes, build the garage and earn the snow truck, balance local demand with reserves, and finish major camp projects. The frozen sandbox keeps running after its last milestone. The forest link becomes playable with the World 2 update. |

Each authored level needs a payoff such as a route, recipe, tool, worker capability, or visible camp improvement. Verify how many levels the distinct decisions can support.

## World 1 snow truck and garage

**Owner requirements.** The player builds a garage first. Its door replaces a fence section, opening a wide route between the camp and the field. After the garage is usable, a separate plot inside camp offers the snow truck for a substantial amount of obtainable World 1 resources. The player drives it. Its low horizontal blades damage eligible enemies, cut trees, and break stone and other mineable rock nodes. The truck has its own HP and can hold an unlimited amount of every resource type. Parking it inside the garage automatically transfers cargo to the storage house. If the truck is destroyed outside the camp, all cargo still held by the truck is lost.

### Design recommendations for playtest

- Make the garage and truck a late World 1 project. Start costing the garage with planks and stone blocks, and the truck with metal and parts the player can obtain in World 1. Check both bills against the live resource and unlock rules. Price and exact unlock are tuning decisions.
- Give the garage opening the camp's normal closed-door collision and repair rules. Leave room for the truck to turn and workers to pass. Give the player readable enter, exit, reverse and brake inputs, plus a compact HP bar and cargo count in the gameplay HUD. Use the existing camp boundary to stop the blades inside camp and resume their use on a driven trip outside.
- Apply one valid harvesting result per depleted source. Truck harvesting follows each resource's normal yield and regrowth rules. Cargo credited from a harvest or eligible enemy drop goes into the truck. Use the same collision boundaries that keep attacks from passing through intact obstructions.
- Offer a repair interaction in the garage for a surviving truck, using parts and materials scaled to damage. Apply the equipment repurchase rule to a destroyed truck at Level 1. Decide truck-specific driver recovery, cargo disposition if the truck is destroyed inside the camp, and whether it needs fuel. A destroyed truck must release the driver and leave a playable route to recovery.
- Use a separate cargo ledger with a visible, bounded unloading animation. Commit the warehouse credit and truck cargo removal together. If the warehouse is full or offline, the cargo the warehouse cannot receive stays in the truck and the HUD shows the pending amount. Cargo loss outside and completed unloading must each settle once across save and reload.

### First tests

| Scenario | Pass condition |
|---|---|
| Buy and leave camp | The garage is paid and complete before the truck offer is usable. Entry and exit work from different approaches. The garage door stays solid when closed, ordinary gates stay usable, and the blades are inactive inside. |
| Drive in the field | Use the actual mobile controls through trees, quarry, minerals and enemy encounters. Hits land on valid contact. HP and cargo are readable at normal and pinch zoom. |
| Return fully loaded | Haul a large mixed load, park, and unload into a usable warehouse. Repeat with a full destination, entry from another route, an interrupted unload and a reload. Every received unit settles once. |
| Wreck outside camp | Destroy a loaded truck outside, then reload on either side of the destruction event. Cargo still on the truck is lost once. Previously banked stock and the player's separate inventory are accounted for. Restore player control and verify that replacement is attainable using World 1 resources. |

The existing plan provides interfaces for T03 gates, T07 controls, T08 stock, T09 harvesting, T10–T11 purchases and construction, T14 persistence, and T21–T22 combat and defenses. The new vehicle belongs in the T32 World 1 design. T53 should account for it if it can travel between worlds later. This is recorded for planning and review.

## How the sandbox adapts

- Built and repaired routes, relocated machines, surviving workers, stock and camp damage affect the player's next options.
- Pick optional orders and jobs from reachable routes, usable producers, available materials, stock and eligible goals. Keep accepted costs and orders stable through reload. Space and vary recurring offers and encounters.
- Change the problems as the camp develops. Early choices are about where to gather and build. Later choices include rerouting cargo, opening another food or material line, shifting work to a different station, and deciding how to prepare for or recover from a raid. A larger quantity on the same delivery is insufficient to carry a level.
- Keep the full five-minute raid warning and the separate cadence proposal. Test different threats and attack patterns as the camp grows. Check that ordinary play provides a viable path to recovery.
- Test trade-first, exploration-first and defense-first approaches. Revisit the same places after expansion, damage and layout changes. Use long sessions and return visits to see whether decisions change and whether there is useful play after the final milestone.

## Worlds and future updates

The level ranges and crossing milestones below come from the earlier ten-level-per-world plan. Its world themes, resources and connections guide the later updates. Choose the revised ranges and milestones after the World 1 sandbox trial.

| World | Earlier levels | What players obtain and build | Survival and next connection |
|---|---:|---|---|
| **1 · Frozen Home Camp** · T32 | **1–10** | Wood, stone, hunted meat and the opening mineral sources for coal, slate and metal ore. Start the hearth, stock the warehouse, rescue the first worker, and make planks, blocks and cooked meals. Earn the first service cash. Planned later steps in this band introduce lakeshore fish and wheat for cooked fish and bread. | Snowy forest approaches, hostile wildlife and the first camp defenses. The hearth supports recovery. Open the **forest connection at 10**. |
| **2 · Forest and Lakeshore** · T44 | **11–20** | Renewable timber, eligible game, hides and fur. Supply saws with timber, craft hauling harnesses and cold-weather fittings, and recruit survivors through rescue objectives. Use planks and blocks to bridge the creek. | Dense cover, isolated work parties and branch routes. Escorts, alternate paths and footbridges keep deliveries moving. Open the **canyon pass at 20**. |
| **3 · Desert Canyons** · T45 | **21–30** | Canyon slate and metal ore, a steel workshop supplied by ore and coal, sheltered work gear and reinforced freight landings. Slate and planks build shade and weatherproof work lanes. | Exposed crossings and telegraphed dust gusts. Use shade, switchbacks and fixed bridges. Open the **underwater expedition dock at 30**. |
| **4 · Underwater Refuges** · T46 | **31–40** | Fish, cooked-fish supply, and marked metal and fuel salvage. Build reach and lifting gear, restore pumps and reopen dry loading halls using planks, blocks and steel. | Currents and blocked underwater approaches change which routes are usable. Protected tunnels, dry platforms and fixed transport give people, pets and freight practical access. Open the **highland lift at 40**. |
| **5 · Sky Islands** · T47 | **41–50** | Working cargo lifts, reinforced bridges, sheltered platforms and faster freight links. Build them with planks, steel and harness materials from connected camps. | Strong winds and exposed edges interrupt crossings and freight. Use timed crossing windows, sheltered bridges and safe recovery landings. Open the **volcanic freight link at 50**. |
| **6 · Volcanic Forge** · T48 | **51–60** | Ore and coal in useful quantities, improved steel production, heat-protection equipment and stronger machine parts. Use blocks and slate for protected causeways. | Warned vent bursts and attacks on exposed worksites. Sheltered work islands and cooling points give crews an alternate route. Open the **wetland route at 60**. |
| **7 · Swamp Boardwalks** · T49 | **61–70** | Fish and timber, a second food supply route, raised production platforms and reachable marsh workstations. Use planks and blocks for dry freight routes. | Flooded paths can interrupt a job. Reroute cargo over raised boardwalks and repair damaged crossings. Open the **old settlement road at 70**. |
| **8 · Ruined Settlement** · T50 | **71–80** | Useful salvage and construction stock, restored courtyards and gates, a reopened workshop and counter, and rescued survivors. | Hostile occupation and damaged mechanisms break routes between work areas. Clear and reopen the usable streets, gates and freight yard. Open the **mine gateway at 80**. |
| **9 · Underground Mines** · T51 | **81–90** | Deeper metal ore, coal and stone sources. Build lighting, reinforced passages and mine lifts using blocks and steel. Export minerals to earlier workshops. | Dark galleries, warned blockages and contested work faces. Use lit routes, supported passages and a separate return route. Open the **frontier transport at 90**. |
| **10 · Alien Frontier** · T52 | **91–100** | Finite relay components, restored relay stations and the final network connection. Supply the frontier with food, planks, blocks and steel from the existing network. | Volatile relay states and hostile disruption require staged repairs and secure return points. **Level 100 completes the network and celebrates the campaign finish.** Exploration, trade and production continue afterward. |

## What progress looks like

- Keep useful and visible progression throughout each world. The earlier cadence used visible milestones at relative levels 3, 6 and 9 and a world connection at level 10. Reassess the milestone spacing against the World 1 sandbox trial. [Earlier progression scope](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/T12/FROZEN_SCOPE.md)
- World entry comes through a real crossing or transport link. Players can return to earlier camps with their cargo and eligible companions. Built routes support walking and/or freight as specified. Every world needs an attainable free recovery route if a machine, helper or main crossing is lost. [Transport and region task map](Havenline-Whole-Task-Plan-Audit.md)
- Resource families carry forward. Forest timber supports sky bridges and swamp boardwalks. Desert slate and volcanic steel strengthen landings and mines. Earlier camps feed and equip the frontier. Lake and swamp fish share the food family, and later ore sources feed the same economy. Regional access, jobs and upgrades give routes a reason to exist even when some resources overlap.
- Check the full path to every resource before assigning an order or charging for an upgrade. Include its source, usable route, recipe, inputs, and any producer plot that can be afforded at that stage. Recheck that path after a raid or outage. A required recovery build needs accessible materials. [Build 13 gameplay audit](Havenline-Build-13-Dynamic-Gameplay-Audit.md)
- The opening pet availability is a proposal from the authored plan. It places optional dog, owl and gray wolf opportunities in the frozen band, fox and bear in the forest, and lion and tiger in the canyon band. Companions must be earnable with ordinary gameplay. Your current casualty and repurchase rules govern active actors. Exact offer levels and replacement costs still need balancing. [Proposed pet availability](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.md#free-companion-and-weapon-availability)

## Build 13 baseline

Build 13 already has wood, stone, meat, coal, slate and metal ore, with planks, blocks and cooked meals. The signed playtest has a Level 2 preview. The table records the earlier campaign themes and bands. The final World 1 count, save and update rules, and acceptance scope need to be reconciled with T12, T32, and the earlier Level 1–100 launch requirements before production sign-off. The saved audit governs self-service counters, survivor hunting, raids, structure damage and recovery where the older campaign text differs. Inter-region raid eligibility is still open. [Build 13 inventory](https://github.com/ksolo21-web/HAVENLINE/blob/2654f5019b7212968d28600cb071bf1c231c9030/HavenlineLevel1/field_inventory.gd) · [Current owner decisions](README.md)
