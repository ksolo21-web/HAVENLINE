# Snow truck — standalone native rule component

This package proves exact resource custody and selected purchase, parking and loss
transitions in Godot. It does **not** modify or run the HAVENLINE field game. There
is no driving controller, truck mesh, garage geometry, harvesting implementation,
contact animation, audio, device test, balance approval, or approved game build here.

The current snow-truck feature contract in `Docs/Production/SnowTruckGarage/2026-11-27/`
and the user's latest request take precedence over conflicting older preservation
and sanctuary text in the baseline repository. Exterior truck cargo destruction is
a narrow exception to ordinary equipment salvage. Other objects retain their own rules.

**Current continuation:** the user's later instruction explicitly supersedes the
earlier no-fuel decision. `fuel_rules.gd` now provides the bounded exact fuel layer
described below. Prior frozen source and review receipts remain historical; this
changed component requires a new independent review. This says nothing about the
absence of vehicle work in the separately owned live game branch.

## Implemented behavior

- Freeze an adapter-supplied attainable resource bill against a completed garage,
  its in-camp purchase plot, payer, next vehicle generation and catalogue version.
  Pay that exact bill from real participating account custody once. No default
  price, level unlock, upgrade curve or premium currency is introduced. Fuel rates
  and tank size are explicit prototype calibration, not measured final balance.
- Reserve one pending purchase or live truck per garage bay. Paid replacement has a
  new generation, level 1, empty cargo, and the old destruction tombstone.
- Preserve a frozen quote's bill while rebinding it to an actually rebuilt garage.
- Preserve that same bill and quote identity while rebinding its unpaid funding
  source to a currently available authorized account after payer destruction/recovery.
- Move arbitrary mixed canonical carryable resources from a participating account
  to the truck. Raw goods, processed goods and physical ordinary money use the same
  typed quantities; catalogue registration is not inferred from a render.
- Require zero vehicle and blade speed, a ready garage, every supplied chassis and
  blade corner inside its local parking volume, and its linked operating warehouse.
- Unload the complete map atomically to an all-resource, unlimited logical warehouse.
  A destroyed, disconnected, finite or incompatible receiver holds **all** cargo on
  the truck. Shelf graphics never limit quantities. There is no overflow-depot design.
- Apply one trusted damage contact once. Lethal damage clips the whole planar truck
  footprint against its camp polygon. Any non-negligible exterior area selects the
  exterior-loss rule, including a boundary-straddling truck. A concave camp boundary
  is checked as a shape, not merely by testing its corners.
- Exterior destruction moves every carried unit to durable destruction outflow;
  there is no collectible cargo salvage. Fully interior destruction uses one typed
  estate under the existing salvage rule. The separate player's backpack is unchanged.
- Warehouse destruction moves its existing contents once to a warehouse estate.
  A trusted paid-rebuild callback opens an empty next warehouse generation. The
  truck can then unload; old-generation receiver observations reject.
- A living available actor may claim an interior/warehouse estate once. Claiming
  directly into a storage account is intentionally unsupported so it cannot bypass
  the warehouse's normal destination checks.
- Replay durable successful request receipts without movement. Reject a changed
  payload under the same request ID. A damage contact cannot be applied again with
  a new request ID. Invalid operations make no ledger change.

## Exact quantities and conservation

Resource amounts are canonical nonnegative **decimal strings**, for example
`"18446744073709551617"`. Counts stored in inventory maps must be positive; an absent
key represents zero. Leading zeroes, signs, exponents, decimals, numeric JSON values,
booleans and unknown carryable types reject. `exact_count.gd` adds and subtracts digit
by digit, never through machine-integer or floating-point conversion. The tests
include quantities above 2^53 and 2^64 and a 513-digit carry/borrow.

There is no configured gameplay quantity cap. Available memory and event-journal
growth are engineering constraints, not certified unlimited hardware performance.
The physical inventory display must aggregate representative stacks without changing
these values. Generations and HP are separately bounded exact numeric metadata;
this does not limit resource quantities.

Every commit checks, per resource:

`introduced = accounts + vehicle cargo + estates + construction spending + exterior loss`

Account custody, vehicle custody, salvage, spending, and destroyed value remain
distinct. A dead truck cannot hold a second copy of its disposed cargo. This package
does not fabricate harvest yields or import an unaccounted live-world balance.

## One trusted adapter and one inventory authority

Initialization binds one adapter object. A same-named replacement object cannot
replace that authority on an existing ledger. This is an internal gameplay boundary,
**not** authentication against hostile game code, network clients, a modified save,
or an adversarial adapter.

The adapter provides these methods:

| Method | Responsibility |
|---|---|
| `vehicle_authority_id()` | Stable identity for this exact world. |
| `capture_vehicle_bootstrap()` | Authorized one-time catalogue and participating account migration. |
| `validate_vehicle_bootstrap(snapshot)` | Validate exact canonical source ownership before migration. |
| `capture_vehicle_observation(operation, parameters)` | Capture the actual current world state and facts needed by this command. |
| `validate_vehicle_observation(observation)` | Confirm exact authority, contents and world revision; called before validation and immediately before commit. |
| `authorize_vehicle_restore(snapshot)` | Admit this exact durable full-world epoch; reject stale/rolled-back or cross-world saves. |

Public commands do not accept caller-supplied parking, location, source-contact,
damage, garage-ready or receiver-operational booleans. They obtain an observation
from the already bound adapter. Its envelope is:

```text
{authority_id, revision: canonical_decimal_string, operation, parameters, facts}
```

The native fixture in `tests/world_fixture.gd` supplies deterministic facts solely
for tests. It does not measure a real truck, authenticate a construction payment,
prove a reachable resource recipe, or establish a genuine collision.

The shipping adapter must validate:

- Completed garage construction and the real paid lifecycle receipts, rather than
  accepting a merely nonempty receipt/proof ID from UI or network input.
- Current acquisition and route proof, including the full ordinary purchase bill.
  A quote's bill is frozen here; the actual dynamic economy constructs and proves it.
- Exact chassis/blade envelope transformed into garage-local coordinates. Every
  collision-extreme point must be supplied. Eight invented repeated points would
  pass the count check but would not constitute valid world evidence.
- Real stationary/blade state, warehouse generation/route/admission and actor
  availability; a dead or locked actor cannot become available through this API.
- Actual non-replayed damage contacts and the truck's full planar hull-and-blade
  footprint against the relevant camp's boundary. The native geometric tolerance is
  numerical; its scale and a valid camp polygon require game-unit validation.

**Do not seed the same world goods here and leave another spendable copy in the
player/counter/lifecycle inventory.** In integration, this reducer must operate on
the world's single inventory authority, or its entire participating custody must
move through an authenticated migration/escrow boundary. The test accounts are
isolated starting stocks. They are not a second wallet to poll beside the live game.

Complete-world persistence must atomically include these events, the canonical
inventory, source contacts, HP, quote/lifecycle receipts, garage state and other
systems. Component success alone does not prove that cross-system atomic save.
There is no live harvest-output or arbitrary external-stock-import API here; its
absence cannot be replaced by resynchronizing balances and duplicating ownership.

## Public API

Load `vehicle_rules.gd` within this standalone project's resource root.

| Method | Result |
|---|---|
| `initialize(adapter)` | One authorized initial account/catalogue migration. |
| `admit_quote(quote_id, request_id)` | Freeze the adapter's current supported purchase quote. |
| `purchase(quote_id, request_id)` | Debit the complete bill and create one empty level-1 generation. |
| `rebind_quote_garage(quote_id, request_id)` | Bind the unspent unchanged quote to a real newer garage generation. |
| `rebind_quote_payer(quote_id, payer_id, payer_generation, request_id)` | Change the authorized available funding owner without changing the unpaid bill. |
| `load_cargo(vehicle_id, generation, source_id, source_generation, items, request_id)` | Exact transfer from an available reachable participating source account. |
| `park_and_unload(vehicle_id, generation, request_id)` | Validate full parking and atomically move the complete cargo map. |
| `apply_contact_damage(vehicle_id, generation, contact_id, request_id)` | Apply a current trusted contact once; persist lethal cargo disposition. |
| `storage_destroyed(storage_id, generation, request_id)` | Custody callback: close the actual destroyed warehouse and preserve its contents once. |
| `reopen_storage(storage_id, previous_generation, request_id)` | Custody callback after actual paid rebuilding; create no stock or free rebuild. |
| `claim_inside_salvage(cache_id, account_id, generation, request_id)` | Transfer the reachable estate into an available actor. |
| `state()` | Return a deep copy for display/diagnostics; editing it changes no live state. |
| `snapshot()` / `restore(saved, adapter)` | Export or replay the component's complete durable successful history. |
| `audit()` | Check exact resource conservation; explicitly reports no game integration. |

## Fuel v2: low consumption, exact accounting

The selected prototype uses a **60-unit operational tank**. Unlimited `fuel` cargo
remains ordinary whole-unit inventory. The tank is a distinct owner inside this
same conserved ledger; it does not impose a cargo capacity or automatically burn
fuel stored in a backpack, warehouse, or truck bed.

| Prototype calibration | Exact representation |
|---|---|
| One fuel unit | 120,000 subunits |
| Tank capacity | 7,200,000 subunits / 60 units |
| Driving | 2 subunits per active millisecond; 1 unit per 60 seconds |
| Blades operating | 1 subunit per active millisecond; 1 unit per 120 seconds |
| Driving and blades together | 3 subunits per active millisecond |
| Parked, idle, paused, menus/background | No consumption |

These starting rates target modest use. They do not establish final trip duration,
fuel affordability, vehicle balance, or how the actual world reports active use.
At these constants a full tank would fund 60 minutes of driving alone, 120 minutes
of blades alone, or 40 minutes of continuous combined use. Actual play needs testing.

Every subsecond remainder persists as an exact decimal subunit balance. No floating
timer, fractional debt reset, integer-unit rounding loss or independent fuel wallet
is used. Fuel conservation converts ordinary whole units to subunits exactly:

`introduced fuel × 120000 = ordinary custody/spending/loss × 120000 + tanks + burning + tank loss + fractional estates`

The conversion uses arbitrary-length decimal multiplication. Only the deliberately
bounded tank and at-most-1,000ms work slice are converted to native integers.

### Paid initial fuel and legacy saves

A new authored quote may declare `initial_tank_fuel_units: "60"`. Its ordinary
`bill.fuel` must contain at least those 60 paid units. Purchase debits the entire
actual bill once, then assigns the named 60 units to the tank and only the remainder
to construction spending. Its receipt separates `debited_bill` from `consumed`
materials. The funded portion cannot be counted as both burnt construction fuel
and tank stock. A future catalog must bind this field for the newly specified truck
offer, along with its expensive varied attainable processed-material bill.

Old accepted quotes retain their original terms. Old quotes without that field
receive an empty tank and no retrospective fuel charge. The explicit trusted
`activate_fuel_policy` migration creates empty tank records for existing vehicles;
it does not mint starter fuel or erase their carried goods. The actual game must
provide the attainable first refill and let the player exit at zero fuel. Manual
oil extraction and a coal-fired refinery without a truck-fuel prerequisite belong
to the world economy; this component neither implements nor simulates those producers.

`evidence/fuel-v2/legacy-v1-snapshot.json` was genuinely captured from the unchanged
201dcbe predecessor before editing this source. Its provenance records the original
module and snapshot hashes. The fuel test replays that old snapshot before applying
the new migration and verifies its unchanged cargo and exact later fuel history.

### Fuel API and world-adapter facts

All these commands use the same already-bound adapter and its revision recheck.

| Method | Required behavior |
|---|---|
| `activate_fuel_policy(request_id)` | Accept one trusted migration receipt, prototype policy ID, active-play timeline ID and decimal active tick; existing tanks start empty. |
| `refuel(vehicle_id, generation, source_kind, source_id, source_generation, units, request_id)` | Move requested whole `fuel` units from available `account` or that truck's `truck` cargo while stationary, engine off and blades stopped. |
| `grant_powered_use(vehicle_id, generation, usage_id, request_id)` | Admit a bounded current active-input slice and return only its affordable powered milliseconds. |
| `recover_tank_fuel(vehicle_id, generation, cache_id, request_id)` | Move reachable fractional estate fuel directly into available tank space; retain any remainder in that same estate. |

Refueling and fractional recovery require adapter facts `contact_id`,
`source_available`, `speed: 0`, `blade_speed: 0`, and `engine_running: false`.
Refuel uses complete whole units and rejects a requested amount that exceeds tank
space; it does not discard the fraction above capacity. It can refill from a valid
player, warehouse or own-cargo source. A source generation must still match.

Fuel-enabled purchase additionally requires `fuel_clock: {timeline_id, active_tick}`.
The adapter verifies this is the authoritative current clock, never a price/UI input.
The clock cannot precede migration or already-recorded vehicle windows.

Powered use requires facts `{timeline_id, from_tick, elapsed_ms, active_play,
driving, blades}`. The active slice must be an integer from 1 through 1,000ms.
`from_tick` is a canonical decimal string and cannot overlap a previously consumed
range. Gaps may represent dormant/idle time; they confer no powered permission and
are not retroactively charged. A paused observation has zero elapsed time and no
driving/blade input. Offline catch-up burn is rejected.

Usage identities are canonical tuples of vehicle ID, normalized generation and
usage ID. Colons, slashes and JSON escapes inside IDs cannot alias a different
vehicle's grant, including after JSON save/restore. Reusing an already-consumed
tuple with a new request ID rejects; replaying its original request returns only
the existing receipt. The rejected delimiter-concatenation candidate and its
independent finding are preserved under `evidence/fuel-v2/rejected-usage-identity-r1/`.

**The grant precedes powered movement and harvesting.** The world may apply only
the returned `powered_ms`, and must apply each exact grant ID/receipt once as part
of its durable action transaction. A duplicate receipt is the same already-issued
grant, not permission to move or harvest again. Driving and blade results must obey
the same granted duration. When fuel runs short, the response can grant a smaller
slice; at zero fuel it durably denies powered use with `powered_use_allowed: false`
and `powered_ms: 0`. Its `ok: true` means the denial was processed and journaled,
not that driving was approved. This preserves the time frontier so refilling cannot
retroactively turn an already-denied old window into free activity.

The standalone fixture cannot establish honest active time, collision travel,
actual blade work, motion once per grant, refinery output or a real paid receipt.
The live adapter must bind these facts to its current vehicle/input/save APIs.

### Garage return, depletion and destruction

Docking unloads all ordinary cargo, including its fuel, to the warehouse. It leaves
the operational tank alone. There is no automatic refill, automatic tank unload,
idle consumption or invisible siphon from the unlimited cargo map.

Outside-camp destruction moves remaining tank subunits to permanent loss along
with all ordinary carried cargo. Inside-camp destruction retains the exact tank
remainder as a persistent fractional fuel estate alongside ordinary salvage. A
real service interaction can recover that estate into a live truck tank, bounded
by its available space; the remainder persists without rounding. Neither a paid
replacement nor replaying death/refill/dock can clone any fuel.

No-fuel behavior must allow driver exit, continued on-foot play and an attainable
refill/recovery route. Those controls and routes remain actual-game acceptance
requirements, not claims established by this native ledger.

Successful operations receive an immutable receipt and ordered sequence. Failed
operations do not consume the request ID, so a receiver HOLD may retry when the
same operation becomes valid. Successful receipt replay does not emit another
transfer or damage event; consumers must not replay success animation/rewards.

Snapshot restoration replays every event from the original authorized migration,
verifies the legal transition and receipt, rejects duplicate request IDs, verifies
the final state digest, and checks conservation before assignment. JSON's numeric
metadata is normalized so saving and parsing do not change integer identities or
HP. Decimal resource strings remain unchanged. These checks detect malformed or
internally inconsistent state; the actual save authority must prevent an attacker
from forging an entirely self-consistent replacement history or restoring an old one.

## Required integration work

Garage placement, atomic fence replacement, two usable bidirectional exits, door
obstruction, actual driving/turning/braking/reversing, enemy targeting while driven,
tree/mineral attacks and yield, driver exit/recovery, repair, warehouse/lifecycle
receipt authenticity, external producer inventories, full-world save transactions,
actual animations/audio, progression affordability and physical-device performance
remain unimplemented here. These are not passing gates for this component.

Exact values in the fixture are **test data**, not approved gameplay tuning. The
truck and warehouse follow unlimited logical cargo policy. Account entitlements
and premium wallet balances must not be included in the carryable catalogue.

Purchases here use one full-bill payment. Existing partial plot contributions and
escrow are not implemented by this component; the real quote/custody adapter must
preserve them once and deduct only the actual unpaid remainder. Payer/garage
rebinding here applies to an unspent whole-bill quote, with no escrow to refund.
Future catalogue additions and actor account lifecycle migrations also require an
explicit world migration; an unknown identifier cannot be accepted by silently
reinitializing this ledger and losing or duplicating its history.

## Run the focused native proof

From the repository root:

```sh
godot --headless --path tools/havenline/vehicle_rules --script tests/run_all.gd
```

The original 107-check runner now writes `evidence/fuel-v2/legacy-regression.json`;
the predecessor's `evidence/native-results.json` and source manifest are preserved
as historical receipts. Run the new fuel suite with:

```sh
godot --headless --path tools/havenline/vehicle_rules --script tests/run_fuel_v2.gd
```

New source hashes, engine identity, logs and both results belong in
`evidence/fuel-v2/`. Parse/assertion errors and incomplete coverage are failures even
if the engine happens to return exit code zero. Independent review and actual scene
approval remain separate evidence.
