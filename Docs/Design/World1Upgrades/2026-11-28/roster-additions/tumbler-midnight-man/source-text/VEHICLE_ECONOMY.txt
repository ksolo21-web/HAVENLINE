# Havenline — fuel, fabrication and the world fleet

The current vehicle direction adds **low fuel use**, a meaningful **iron ore → iron bars → sheet metal** chain, coal-powered processing, crude-oil extraction outside camp and fuel refining at camp. Nine new vehicle proposals give each later world a useful machine. The original snow truck and fence-line garage remain part of the design.

The user's fuel instruction supersedes the earlier package's no-fuel scope decision. Original bills, accepted quotes, old saves and dated reviews retain their identity. New truck quotes use a costly eight-input processed-material fixture with a paid initial tank; existing trucks are not charged again. Exact final prices and fuel balance require actual playtests.

## Read and review

- [World 1 vehicle list: snow truck and Tumbler](../Design/WorldVehicles/2026-11-28/README.md)
- [Practical production and vehicle design](VehicleEconomy/2026-11-27/ECONOMY_DESIGN.md)
- [Resource chains, construction profiles and denomination rules](VehicleEconomy/2026-11-27/RESOURCE_CHAINS.json)
- [Nine world-specific vehicle designs](VehicleEconomy/2026-11-27/WORLD_VEHICLES.json)
- [Vehicle render gallery and selected revisions](../Design/WorldVehicles/2026-11-27/README.md)
- [Original snow truck and garage](SNOW_TRUCK_GARAGE.md)
- [Current request and acceptance contract](VehicleEconomy/2026-11-27/ACCEPTANCE.md)
- [Supersession and preserved history](VehicleEconomy/2026-11-27/SUPERSESSION.md)
- [Live source audit and conflicts](VehicleEconomy/2026-11-27/SOURCE_AUDIT.md)
- [Primary factual oil/refining sources](VehicleEconomy/2026-11-27/FACTUAL_SOURCES.md)
- [Resumption checkpoint](VehicleEconomy/2026-11-27/CHECKPOINT.json)

## Implementation boundary

The observed Build14 gameplay source at `ea6e4896cc6692ee84b56f89e127feaa606eb370` already contains truck driving, contact, docking, quotes and destruction handling. This isolated follow-up does not overwrite that actively maintained branch. It supplies new source-bound designs, generated six-view concepts, a tested standalone fuel/custody component and material-graph checks. The [component README](../../tools/havenline/vehicle_rules/README.md) names the actual APIs, adapter obligations and test evidence.

Integration must update the existing typed inventory, purchase/repair/transfer paths and denomination-aware price display together; appending new resource IDs alone is insufficient. Fuel use must authorize actual movement and tool work once, with a persisted active clock and coupled whole-world save. No static sheet or isolated reducer test approves native vehicle geometry, physics, motion, audio, balance or devices.

Fuel exhaustion leaves the truck and its cargo intact, with a walkable manual refueling route. The tank stays aboard during garage unloading; loose fuel in cargo goes to storage with the rest of the load. Destruction outside camp still loses all ordinary cargo and tank fuel. Replacement remains possible before an inside-camp fractional fuel estate is reclaimed into a new tank.
