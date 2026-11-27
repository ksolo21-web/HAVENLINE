# Havenline — snow truck and garage concepts

These are the authored visual proposals for Kaleb's player-drivable harvesting/combat truck and its fence-integrated garage. They are static generated turnaround sheets, not a native mesh, animation, measured scene or playable build.

## Current presentation candidates

| Asset | Selected file | Coverage |
|---|---|---|
| Snow truck | [snow-truck-360.png](selected/snow-truck-360.png) | Front, right, rear, left, three-quarter and horizontal blade detail |
| Garage | [snow-truck-garage-360.png](selected/snow-truck-garage-360.png) | Front, right, rear/camp side, left, open garage and rear docking cutaway |

The word **selected** identifies the current delivery candidate after repair. It does not manufacture Kaleb's visual approval or a production reference lock. An actual model must reconcile geometry and incidental fittings against the owner's selected design before runtime acceptance.

## Design decisions

The truck uses a rounded cobalt-blue cab, orange fenders and a navy mixed-resource bed with four substantial snow tires. Two broad circular steel blades lie horizontally on a low front deck. They rotate about vertical spindles; vertical saw wheels, a snowblower and a plow scoop are not this design. Small visible resource stacks are representative, not a capacity limit.

The garage extends inward from the fence. Its outer roll-up door replaces a fence segment, and its open camp-side rear gives access from inside. Thick palisade wings meet the front corner posts. The workshop carries the existing blue roof, orange timber, gray stone and rounded snow language. Its parked view keeps the full blade assembly behind the outside door plane. The normal pedestrian camp exits must remain usable separately; a concept sheet cannot prove that scene layout.

The roof-removed view is a cutaway of the same single bay. It is not an alternate building or a garage upgrade. Both garage use-state panels contain one instance of the truck.

## Repair history

| Revision | Disposition |
|---|---|
| Truck R1 | Current static concept candidate. Four cardinal views and blade plane inspected. |
| Garage R1 | Rejected: duplicate cab/truck in cutaway and different truck proportions in use-state panels. |
| Garage R2 | Intermediate: duplicate removed; vehicle identity still mismatched. |
| Garage R3 | Intermediate: identity improved; rear cab orientation and exterior door clearance still wrong. |
| Garage R4 | Current static concept candidate: rear cab bulkhead/window corrected, truck parked deeper with full blade clearance. |

All attempts are retained under [attempts](attempts). The original built-in image-generation prompts are retained in [PROMPTS.json](PROMPTS.json) and [GARAGE_R4_PROMPT.json](GARAGE_R4_PROMPT.json). The original outputs were copied without retouching or replacing their bytes. Review crops are inspection evidence only.

## References and authorship

The storage-house reference is the existing reinforced storage concept at `Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/selected/storage-house-reinforced.png` on `art/storage-house-2026-11-26`. The gate reference is the already retained camp-gate image. Local copies and content hashes are retained here for repeatable comparison. They establish material and camp language, not the new vehicle's shape or mechanics; the truck and garage are newly authored in response to the current request.

Source and feature decisions: [Snow truck and garage gameplay package](../../../Production/SNOW_TRUCK_GARAGE.md).

## Approval boundaries

Independent static review checks the actual sheets, their views, identity, blade orientation, doorway relationship and visual family. It does not test driving, steering, braking, blade rotation, harvesting/mining contact, attack hit detection, inventory transfer, HP/damage, full garage-door cycles, sounds, performance or device behavior.

The project still requires its stronger final reference gates for an implemented asset. These concept sheets cannot close those gates. The raw critic review and candidate hashes are retained with the package; failed earlier views remain evidence.
