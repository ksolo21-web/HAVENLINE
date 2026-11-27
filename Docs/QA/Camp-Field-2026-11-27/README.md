# Havenline Level 1 · Android playtest 13

[Download Build 13](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/Build-13.apk) · [Playtest page](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/) · [View all three corrected characters](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/characters.jpg)

This update uses the existing Android package and signing certificate. An in-place update carries the saved camp forward. Build 13 uses the compact Character 1 by default. Camp → Choose character switches among Character 1 and the three compact characters based on the supplied turnarounds while keeping the active inventory and position.

Character 2 has the asymmetric bob and glasses, Character 3 has loose curls and an open parka over an ivory waistcoat, and Character 4 has the black headband and lace-up boots. Their in-game medallions follow the selected character. Meshy used a front view derived from each owner turnaround, at 45 credits total for the three models. The rig was fitted locally. The final movement review scored all four playable characters and the forester 9.9/10. The neutral-light comparison still shows small skin-tone differences, and the mittens render darker than the guides. [See the three in-game models](References/Owner-identity/Approved-characters-in-game.jpg) · [Color comparison](References/Owner-identity/Neutral-material-swatches.jpg) · [Source and generation receipts](References/Owner-identity/Meshy/Generation-receipt.json)

## Try it in a paid camp

1. Leave through a gate and run alongside a meat drop or a mineable rock. The orbit activates outside the camp. Walk through the drops and watch the separate wood, stone and meat stacks on the pack.
2. Carry supplies alongside the paid cooker, saw or drill. Its inlet accepts the corresponding raw resource when it has room. Walk up to collect finished stock, including cooked meat. Paid conveyors continue to feed the line while you are elsewhere.
3. Run past the upgrade marker on the way to the loading door to unload. Stop beside the upgrade marker to make a purchase. Bring cooked meat to the camp side of the customer counter. Approaching the counter hands over the stack and picks up available cash. Each real order earns a payment. The storage house takes notes as well as raw and finished goods. To withdraw, walk inside and stop beside the stocked shelf. Cash transfers to the pack in the same way as timber or cooked meat. For two goods on one rack, tap the visible stock to choose the item.
4. Find the survivor rescue and owl roost as separate purchases under **Survivors**. A previously earned owl stays with its keeper. A new owl costs 60 meat. The survivor can group up to 500 units per raw resource for a trip. Approach the east gate during a threat to watch the owl and the tower react.

## Verification

Game source `2654f5019b7212968d28600cb071bf1c231c9030` on `trial/world-one-expansion-2026-11-26`. Android package `com.havenline.levelonesettlementtrial`, version code 13, ARM64. The signed file contains 253,643,210 bytes. Its SHA-256 is `af81181c81bc623310b00680ea4467615c6f9ffd4c21c1197bc75aff3b71bd75`. [Signing and package verification](Verification/Android.json)

The native regression suite passed 69 suites across 92 launches. A separate progression replay passed 222 assertions across 16 launches, including interrupted writes, cold restart and Level 2 handoff. 56 commerce checks ran again using the resources extracted from the signed APK. An additional 41 checks exercised all ten withdrawal shelves on the signed Android resources, including a cold restart with seven bills. The touchscreen controls replay also passed all four character selections and verified each HUD portrait. The simulations use isolated profiles. [Native tests](Verification/Native/Native-results.json) · [Progression](Verification/Completion/Completion-results.json) · [APK replay](Verification/Signed-goods.json) · [Touch and character selection](Verification/Signed-controls.json) · [Ten stocked shelves](Verification/Signed-shelf-walk.json)

The reference camera captures and timings use desktop Godot. Physical Galaxy Z Fold7 frame pacing, sustained 4K rendering, and 60–120 Hz operation still require device measurements. [Owner source index](References/Sources.json) · [Field and storage](Field/Field-and-storehouse.md) · [Camp economy](Economy/README.md) · [Survivor and owl](Crew/Field-notes.md) · [Roster motion](Motion/Readme.md)

[Gameplay video](Play/Camp-field-playtest.mp4) · [Independent critic scores](References/Independent-review.md) · [Live customer exchange](Economy/Counter-normal.mp4) · [Survivor delivery](Crew/Worker-returns.mp4) · [Character 1 against the source run](Motion/C1-source-and-field-run.mp4)

Independent reference review was assigned to reference_check. The implementation team comprised stone_harvest for resource collection and bulk storage, automation for workshops and customer payments, tower for the counter and defense tower, belt_layout for survivor work and the owl, furnace_heat for all five motion rigs, and the integration lead for the inventory controls, package and testing.
