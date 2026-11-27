# Havenline Build 15 · Workshop playtest

[Download the private Android playtest](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/Build-15.apk). Install the ARM64 package over Build 14. In the twice-expanded camp, bring **180 wood and 120 stone** to the garage plot near the south fence. The truck opens on its own plot after the garage is complete. Fully paid garages stay paid. Partial plank or block payments from Build 14 reduce the corresponding raw-material balance.

## Workshops and customers

- Open **Camp → Workshops** to find the cooker, saw bench, and quarry drill. Select a paid station, choose **Switch to manual handoff**, and approach its working side. Tap **Load from pack** to feed matching raw materials. When the batch finishes, tap **Collect output**. Walk-up handoff is also available. The manual handoff preference lasts for the current session.
- An operating conveyor uses the same stock accounting as the player. A player working manually leaves the conveyor schedule active.
- Counter orders request cooked meat only. The upgrade replaces an outstanding mixed ticket and preserves completed sales, cash, and stocked goods.

## Crew and tower

An unlocked survivor can chop multiple pines, mine a regrowing stone bank, and carry the bundles back to camp. The survivor holds the same approved Meshy axe and pickaxe models as the player, with a separate grip and strike for each tool. The tower stays opaque when the player passes behind it. A small marker indicates the obscured player.

[Independent controls and field review](Review/Independent-review.md) · [Tower results](Tower/README.md) · [Approved Meshy tools](Crew/Tool-provenance.md) · [Repeat gathering and contact captures](Crew/Verification.md)

## Android verification

The signed app was tested against three saved camps from the preceding build. Each loaded and restarted successfully. The focused regression run passed 16 suites across 21 runs. The market fixture needed a retry after the export filled temporary disk space. The furnace test also passed on retry after an ambient hit changed the earlier run’s starting health. A physical Galaxy Z Fold 7 test is open.

[Android package verification](Verification/Android.json) · [Native test results](Verification/Native/Focused-native-results.json) · [Saved-camp checks](Verification/Signed-returning-camps.json)

## Production direction

Use World 1 iron ore, iron bars and rolled sheet metal for the production truck, plus obtainable mechanical and wheel components. Create a reachable oil source and fuel station before requiring fuel at a vehicle plot. Give the player a way to refuel, return safely after running dry, and recover a stranded vehicle. The regional vehicle concepts and machine controls are recorded in the [production vehicle and workshop design](Design/Production-vehicles-and-workshops.md).
