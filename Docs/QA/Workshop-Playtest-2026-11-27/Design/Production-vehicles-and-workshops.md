# Havenline production vehicles and workshops

The snow truck belongs late in World 1, after the player can get and process all the parts in its recipe. The private playtest uses an accessible wood-and-stone garage quote so early saves can test driving. The production garage uses planks, stone blocks, and metal fittings.

## World 1 materials and machines

| Field source | Processing chain | Use |
|---|---|---|
| Iron-bearing rock in the frozen quarry | Mine iron ore, smelt it into iron bars, then roll the bars into sheet metal | Sheet metal for the truck body and garage siding. Iron bars for frames, fittings, and machine parts. |
| Mineable coal seams | Bring coal to the camp furnace or smelter | Heat for smelting and a spare fuel source for industrial machines. Steel parts open as a later upgrade once both iron and coal routes are reliable. |
| A marked oil seep on a reachable rocky shelf beyond camp | Work a small hand pump, carry sealed crude canisters, then process them at the camp fuel station | Truck fuel and later compatible workshop equipment. A powered pump and automatic hauling become upgrades. |

Existing coal and metal-ore sources give World 1 a starting point. Keep current ore receipts under their saved resource ID and identify which deposits yield iron before adding more ore types. Keep the first supply of every required material reachable without vehicles or other worlds. Use a reserve of salvaged tires and starter parts until there is a repeatable World 1 supply of wheels, rubber, and fittings.

### Assembly and running costs

Use separate garage construction, initial truck assembly, and repair recipes. The truck build should consume sheet metal, a frame and drivetrain kit, wheels, cutting assemblies, fasteners, and a small initial fuel load. Group them by component so the requirements stay legible. The recipe should call for enough resources to reward establishing the supply network. Tune quantities after measuring gathering times, production throughput, and a first truck trip.

Use a modest fuel draw while driving, with a small optional increase under heavy work. Idle and parked vehicles should use no fuel. Keep the tank and reserve separate from cargo. Show the remaining fuel and a low-fuel warning. Support refueling at the garage and from a carried canister in the field. When the tank empties, let the player get out, keep the vehicle and cargo at their saved location, and use a rescue or tow option they can afford without the truck. Preserve outside wreck loss, in-camp recovery, and automatic garage unloading. Keep fuel, cargo, repairs, and assembly transactions safe through pause, save, reload, and repeated taps.

### Manual and automatic operation

Give every paid machine a way for the player to operate it at a safe, reachable position. For production stations, show accepted inputs, what is waiting in the hopper, the selected recipe, processing progress, and finished output. Provide a way to load, start or pause, and collect. A pump can use a short active pumping interaction. The furnace needs clear stoke and heat controls. A guard tower needs a player station with a clear entry, weapon aim, exit and crew handoff. Garage controls cover vehicle service and refueling.

A conveyor or assigned survivor can perform the same work through the same stock and production ledger. Show when a line is feeding a station or clearing its output. Pause or reclaim that assignment at the relevant control. Stock already in transit must have one owner. The current playtest adds manual loading and pickup for the three paid processors. Dedicated player controls for the furnace, tower, pump, refinery and other future machines follow their own playable designs.

### Obtainment check

An unlock, required purchase, replacement, or order needs a usable source, route, input recipe and producer. Check those conditions against the actual save while the offer is visible, including after a raid. An unavailable optional producer should leave an alternate job or obtainable recovery recipe. In the playtest, the counter asks only for cooked meat and serves it when stock is available. Production can introduce mixed orders after the player can satisfy every line in the basket.

## Vehicle concepts for connected worlds

Use each later world's existing work and terrain to choose its vehicle before making renders. Keep travel links and both sides of a return route usable on foot or by basic transport before the regional vehicle is earned.

| World | Vehicle concept | Job it unlocks |
|---|---|---|
| Frozen Home Camp | Snow work truck | Cut, mine, haul and make longer snow runs. |
| Forest and Lakeshore | Compact timber tractor with a winch trailer | Recover logs and haul bulky timber along narrow trails. |
| Desert Canyons | Light sand rover | Reach remote deposits across shifting sand and deliver repair kits to canyon crossings. |
| Underwater Refuges | Shallow utility submersible | Inspect and recover salvage through flooded galleries while the dry route is restored. |
| Sky Islands | Dock-to-dock cargo glider | Ferry freight between established landing pads, with wind conditions that determine when each pad is reachable. |
| Volcanic Forge | Heat-shielded tracked hauler | Cross hot work corridors during safe windows and move heavy ore to the forge. |
| Swamp Boardwalks | Shallow-draft cargo skiff | Carry fish, timber, and supplies across flooded links to raised docks. |
| Ruined Settlement | Small salvage loader with a tow hook | Clear light rubble and recover machinery for the reopened workshop. |
| Underground Mines | Battery-powered mine cart | Move heavy minerals and provide a lit way back on restored tracks. |
| Alien Frontier | Electric relay service rover | Carry parts and service equipment between unstable relay sites. |

For each approved vehicle, render the front, rear, sides, gameplay three-quarter view, empty and loaded states, driver interaction, and its regional dock. Prototype its turning space, paths, refueling or recharging, breakdown and recovery before committing the final mesh. Crossing to another world should require a usable route for the vehicle and cargo. Keep parked vehicles recoverable at their home docks.
