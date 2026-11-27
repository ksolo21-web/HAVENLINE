# Havenline Build 16 truck purchase review

Independent reviewer `/root/independent`. Runtime builder `/root`. Reviewed source `92fa91760a45eea306d7bda4da4b705b51b6f103`. [Source hashes](Build16-truck-reviewed-source.sha256)

## What blocked the Build 15 purchase

In a returning cooker-only camp, I used the normal touch route through the south gate and paid the 180 wood and 120 stone garage bill. I followed Camp to the separate truck plot at (3.00, −1.05) and paid the available 440 wood and 340 stone. The warehouse balance stayed unchanged throughout this pack-funded route. The truck plot still wanted 240 metal ore and 120 coal. The Build row extended beyond the right side of a 460 × 760 screen and cut off the entire ore charge. After walking to the plot, the top objective showed the missing mineral icons and quantities, but the garage roof overlapped most of the floor marker from the fixed camera. [Clipped Build quote](Build15-build-menu-clipped.jpg) · [Camp menu](Build15-camp-menu-truck.jpg) · [Remaining minerals at the plot](Build15-unfunded-truck-plot.jpg)

The closest seeded metal and coal deposits were approximately 136.6 m and 127.7 m from the camp guidance point. The reference rules require obtainable purchase materials. Neither existing vehicle guidance nor its quoted price identified where to find those deposits. In the reviewed Build 16 route, both truck tiers use wood and stone. The pre-existing automated tier is still distinct. The standard truck tested here costs 240 wood and 160 stone.

## Independent returning camp route

The wrapped candidate passed **19/19** checks in Godot's rendered 460 × 760 mobile viewport and **19/19** with native headless rendering. I staged raw starter goods in a copy of the archived cooker-only save, then used the normal joystick and dock controls. I entered through the south gate and carried those goods to the storehouse loading apron. Both purchases then took all necessary goods directly from the storehouse, with the player's pack empty of tender throughout. Both unbuilt workshops stayed unpaid. I walked from the truck plot to the rear of the bay and tapped **Drive**. The active truck showed 80 HP and an empty bed. The screenshots use the gameplay camera at 1× and 2×. I set 2× through the game zoom function for the second capture. [Rendered route](Build16-mobile-truck-route.json) · [Headless repeat](Build16-headless-truck-route.json) · [Storehouse funding](Build16-fund-from-storehouse.jpg) · [Drive at 1×](Build16-drive-ready-1x.jpg) · [Mounted at 2×](Build16-mounted-2x.jpg)

| Physical plot | Storehouse before | Storehouse after | First launch | First receipt | Installed |
| --- | --- | --- | --- | --- | --- |
| Garage | 1,490 wood and 510 stone | 1,310 wood and 390 stone | 4.767 s | 5.033 s | 5.400 s |
| Standard truck | 1,310 wood and 390 stone | 1,070 wood and 230 stone | 6.100 s | 6.367 s | 6.733 s |

Times come from the field simulation and its spend events. The nearby plot still triggers payment as ordinary material reaches it. The Build menu explains the funding path. The full price stays inside the 437-unit button, accepts touch and shows the player where to go. Longer conveyor offers in the same panel wrap onto a second line. I scored the quote and guidance presentation **9.5/10** and the walk-up payment and Drive path **9.6/10** for the scoped fix. The ordinary objective can still show the saw bench while the player is away from the truck plot. The mounted garage has a deliberate roof cutaway. [Full mobile quote](Build16-mobile-quote.jpg) · [Purchased truck](Build16-paid-truck.jpg)

## Real in-flight upgrade save

I re-opened the actual test save from the Build 15 route above. Version 12 had debited 440 wood and 340 stone for the incomplete truck, with its ore and coal unpaid. Version 13 restored those materials to the pack, kept the garage and stored balances, and exposed the new standard bill. Actual movement back to the physical plot completed the truck once. The pack went from the refunded 1,280 wood and 360 stone to 1,040 wood and 200 stone. No additional goods were added for this retest. [Native update and payment trace](Build15-v12-physical-migration.json)

## Reference scope

The selected art sheets are from `201dcbe4fad5037a33bd619b59285a1ef91599d8`. The truck and garage appearance and model hashes remain the same for this follow-up. The locked B camp purchase excerpt samples 5.4–6.6 seconds of the original recording. It establishes an in-world plot, short tangible payment stream and immediate installation. B42.40–43.00 shows the same purchase sequence for the defense platform. Neither sequence specifies a vehicle price or vehicle acquisition UI. Those are Havenline playtest decisions. [Truck sheet](https://github.com/ksolo21-web/HAVENLINE/blob/201dcbe4fad5037a33bd619b59285a1ef91599d8/Docs/Design/SnowTruckGarage/2026-11-27/selected/snow-truck-360.png) · [Garage sheet](https://github.com/ksolo21-web/HAVENLINE/blob/201dcbe4fad5037a33bd619b59285a1ef91599d8/Docs/Design/SnowTruckGarage/2026-11-27/selected/snow-truck-garage-360.png) · [Source footage timing](https://github.com/ksolo21-web/HAVENLINE/blob/9617201b63318b6f9292a140cbe7eb79560a4b39/Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/Locked-sequences/source-ledger.json)

The initial capture logged a local OpenGL shader-cache warning during export disk pressure. The native scene completed all playthrough checks and produced intact frames. This is native viewport evidence. No physical handset was used.
