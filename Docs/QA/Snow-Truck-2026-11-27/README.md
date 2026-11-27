# Havenline Build 14 · Snow truck playtest

Install the ARM64 APK over the existing Havenline playtest to continue your saved camp. This is a private test build for the World 1 camp and field.

## Drive the truck

1. In the twice-expanded camp, bring 24 planks and 20 stone blocks to the snow garage plot by the south fence. If a moved building blocks the bay, clear that space in Camp Layout.
2. Fund the separate truck plot. The standard quote is 440 wood, 340 stone, 240 metal ore, and 120 coal. If both camp conveyor upgrades were completed before the garage, the quote is 500 wood, 380 stone, 260 metal ore, and 120 coal. The quote is fixed when the plot opens.
3. Approach the truck and tap **Drive**. Steer with the regular movement stick. The shutter opens as you approach. The blades activate outside the perimeter and only affect targets they reach.
4. Stop with the entire truck inside the garage to send its cargo to the advanced storehouse. Tap **Exit truck** to go on foot. A wreck entirely within camp keeps its cargo for recovery. A wreck outside camp loses its onboard cargo, and a replacement can be bought at the garage.

## Other changes in this test

- Customers take stocked products and leave cash in a separate pile on the counter. The player and unlocked survivor can stock and collect in bulk. Orders adapt across meals, planks, and blocks the camp can supply.
- The survivor can hunt, haul, help fund plots, and stock the counter. Survivors and owls can fall in combat and be purchased again separately.
- Raids give a five-minute **active-play** warning once scheduled. Gates and supported fence sections can be damaged and repaired. The furnace and supported workshops can be disabled and rebuilt. The first raid becomes eligible after the expanded defense camp has accumulated 20 minutes of active play. Repeat timing and the prices remain playtest tuning.
- Conveyor rails, rollers, and feet were revised. The paid lines continue to move resources without manual transfer.

This test still has limited destruction coverage. The garage, storehouse, counter, and some fence sections are outside that coverage. Progression-dependent plot pricing in this build applies to the truck. The gameplay evidence uses Godot on desktop at narrow and nearly square screen sizes. A physical Galaxy Z Fold 7 run remains open.

## Verification

The independent gameplay review scored the truck 9.6/10, garage 9.5/10, and vehicle controls and status 9.6/10. The camera-facing garage timber remains dark under some lighting. [Independent review](Review/Independent-review.md)

The package uses the same Android application ID and signing certificate as Build 13. The exact packaged game replayed all 34 truck assertions. Three prior camp layouts were exercised through Build 13, the updated package, and a cold restart. All eleven focused native suites passed across twelve runs, including moving the cooker and counter, handoff to the moved cooker, and reloading those purchases. [Package verification](Verification/Android.json) · [Returning saves](Verification/Signed-returning-camps.json) · [Native suites](Verification/Native/Focused-native-results.json)

Meshy generated both vehicle assets from selected turnaround crops for 60 credits total. Integration kept the generated truck body and garage structure and fitted moving wheels, blades, and shutter parts. The garage roof finish was adjusted after gameplay review. [Art provenance and fits](VehicleArt/Model-proof.json)
