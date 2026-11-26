# World One camp perimeter

The focused captures below retain their original recording commits. The current playable version is `e978a44b1b112bb598f9ec1724b3616ec80e6970`. Its subsequent runtime change adjusted the backpack display. The geometry and mechanics measured here use the same source assets and implementation.

The camp starts with a furnace and two working gates. Two paid expansions move the eastern and southern gates as the court grows. Each opening has a 2.4 m clear span.

| Paid construction | Court bounds in metres (west, north, east, south) | South gate (x, z) | East gate (x, z) |
|---|---|---|---|
| Hearth | −5, −4, 5, 4 | 0, 4 | 5, 0 |
| First expansion | −5.5, −5.5, 7.5, 5 | 0, 5 | 7.5, 0 |
| Second expansion | −5.5, −7, 10, 5.4 | 0, 5.4 | 10, 0 |

**Commit** `34df87a8195553c4636aa374ac3bfc11054a3bbd`  
**Scene** `res://field_opening.tscn`

Each exterior rail has its own course of crossed cream lashings. On the court side, each course follows the contours of the logs. Snow crowns rise to rounded points with scalloped lower edges. The gateposts carry raised twisted coils, and the outward gate face has rounded hinges and a sliding bolt. The earlier and final native inspection views show how the lashings and snow changed. [Before and after](Wall-lashings-comparison.jpg)

The final hardware matches the archived cardinal and state boards. The front bolt spans about 8% of the gate width. Each leaf has one round rear pin and a slender frame around its vertical boards. [Both hardware faces beside the original boards](Gate-hardware-reference.jpg) · [Original image identities and native hashes](Gate-hardware-reference.json)

**Gameplay views** · [First court](stage-1.jpg) · [First expansion](stage-2.jpg) · [Second expansion](stage-3.jpg) · [First court at 2×](stage-1-gameplay-2x.jpg)

**Construction views** · [Exterior wall](wall-front.jpg) · [Interior wall](wall-rear.jpg) · [Exterior gate](gate-front.jpg) · [Interior gate](gate-rear.jpg) · [Unlatching](gate-unlatching.jpg) · [Gate open](gate-open.jpg)

Godot 4.7.2 rendered the integrated Linux scene at 960 × 540 using Mesa software rendering and a disposable test profile. For repeatability the fixture credits the required materials through inventory and triggers the actual purchase handler. Stage images use the gameplay camera. The detail camera moves outside and inside the court to show each face. These native stills document Linux construction and operation. Phone frame rates were outside this fixture.

The perimeter suite exercises both physical gates and six wall runs through stages 1, 2, 3 and a return to 1. It checks blocking when shut, clearance in both directions when open, the unpaid state and each earned boundary. The final court suite separately steers the player through both gates in both directions. It also checks the northwest storehouse, the shared apron, spatial door cues, deposits and withdrawals on real shelves. All 30 court checks passed. [Perimeter results](perimeter-checks.json) · [Court results](court-checks.json) · [Capture provenance and image hashes](capture-receipt.json) · [Source hashes verified against Git](source-sha256.txt)

The studio boards are also published on the structure-art branch. The side-by-side places three source views next to native frames. The materials receive the actual field lighting, including shade on the inside face. [Source art against the game](Reference-and-runtime.jpg) · [Six original GitHub boards and file hashes](Reference-originals.json)
