# Havenline Build 14 independent review

I used the shipping Godot field scene and its player camera on a disposable copy of the archived paid-workshops save. Synthetic touch events drove the ordinary thumbstick and tapped the on-screen truck controls. The route never assigned a player, vehicle, or camera transform. I funded the garage and truck with conserved test goods and then walked to each automatic purchase receiver. This setup leaves the time needed to earn the purchase materials for a separate economy test.

## Release candidate

The updated frozen candidate `b92588e389f429776a11e7d0349d2096311000ca` passed 19/19 portrait checks and 23/23 wider-screen checks in two fresh headless runs using on-screen touch and the ordinary native save path. The portrait route again paid and entered the truck, exited the camp, reached 2×, reversed into the bay, and took the east gate in both directions. The wider route repeated real quarry harvesting and forward docking, and the warehouse received three stone and two meat exactly once. Both logs were clean. [Portrait route](Release-route.json) · [Wide quarry route](Release-inner-quarry.json)

The last revision changes eligible-payment detection at optional vehicle plots and the model reference for the self-service counter’s relocation preview. Git confirms byte-identical vehicle models, vehicle controls, snow tracks, and gameplay HUD files between the rendered review below and this release candidate. The saved 1× and 2× captures support the same scoped visual grades. [Visual provenance](Release-visual-provenance.json)

## Visual and gameplay review before the last relocation fix

The exact frozen candidate `4cbde9e76314a7e06beb9965501920e82c1cb09b` passed 19/19 checks in the rendered 460 × 760 field scene using its ordinary native save path. The route used 650 physics ticks of directional touch, paid the relocated plots, approached the rear entry on foot, drove through the exterior shutter, pinched to 2×, reversed in, and returned through the east pedestrian gate. The separate 880 × 942 run passed 23/23 with on-screen touch. It drove a turn toward the existing quarry, collected three stone and two meat, and docked nose-first. The goods banked once and remained correct after dismount. There were no runtime script errors in either route. [Quarry route](Final-inner-quarry.json) · [Final route](Final-route.json) · [Final gameplay](../Play/Gameplay.jpg) · [2× gameplay](Final-2x-gameplay.jpg)

| Scoped visual check | Score | Evidence |
| --- | ---: | --- |
| Truck silhouette and gameplay readability | 9.6/10 | The navy and orange silhouette, articulated wheels, low twin blades, road contact, tracks, and empty cargo bed read at 1× and 2×. |
| Garage art and state readability | 9.5/10 | Snow edges are rounded and the cobalt panels retain their seams. The garage opening, roof cutaway and shutter remain clear. Some timber panels retain a deeper field shadow than the owner turnaround. |
| Truck controls and HP/cargo text | 9.6/10 | The dark-backed HP and cargo text remains legible over snow and trees at both zooms. Drive and Exit truck fit above the bottom dock and accepted actual in-viewport touch. |

These three scoped checks meet 9.5 for this test build. [Final comparison board](Final-gameplay-board.jpg)

## Field routes

The intermediate native reruns confirmed all 21 quarry checks, all 21 wolf and wreck checks, and all five cold reopen checks. These runs used keyboard T for contextual entry and exit with the regular touch thumbstick and pinch outside the vehicle. On the quarry route the truck mined 3 stone, picked up 2 meat in the snow, and banked both when it returned nose-first. A live wolf reduced the stationary truck from 80 to 78 HP without moving it off the driveway. The wreck run then used a deterministic terminal-hit injection and recorded exactly 12 wood and 4 coal lost. Those same ledger counts persisted after restart.


- **Garage and reverse approach.** Open the south pedestrian gate by approaching it, fund both separate plots, walk around the garage to the parked truck, tap Drive, take the vehicle outside, pinch the player camera, reverse through the exterior door, park, tap Exit truck, and walk through the east pedestrian gate in both directions.
- **Quarry and forward approach.** Leave the garage, turn toward the existing starter quarry, break it with the vehicle and collect stone, turn again, then drive nose-first into the bay. The parked vehicle should deliver actual quarry cargo once.
- **Enemy and wreck.** Confirm a live wolf can damage the stopped vehicle without shoving it across the snow. An injected terminal hit exercises the normal wreck custody handler deterministically. Cold reopen checks that lost cargo persists without duplication. The fixture starts with known wood and coal amounts in truck custody.

## Touch controls at two viewport shapes

With the viewport placement fix and prototype models, the reverse-and-walk route passed 19/19 at 412 × 924 and the forward quarry route passed 23/23 at 880 × 942. Both runs used the normal on-screen Drive and Exit truck buttons. The rendered 550 × 920 run also passed 19/19 and captured a wolf hit with truck HP declining to 78. The tests require the entire control rectangle to be within the viewport before tapping. The test harness reached the live 2× gameplay pinch in both shapes. [Portrait](Prototype-touch-portrait.json) · [Wider viewport](Prototype-touch-inner.json) · [Native prototype controls](Prototype-controls.jpg)

## Fitted Meshy model candidate

Source `394230f270ae7254eb196b1d8c99520350d96b5f` passed 19/19 portrait input and parking checks, 23/23 wider-screen input and quarry checks, and 19/19 native rendered checks. The video uses the fixed gameplay camera at normal and 2×. It samples every eighth 60 Hz simulation tick and plays at the original speed. [Portrait results](Vehicles-394230f2-portrait.json) · [Wide results](Vehicles-394230f2-inner.json) · [Gameplay video](Gameplay-394230f2.mp4) · [Normal and pinch stills](Vehicle-gameplay-394230f2.jpg)

I rated the truck’s rendering and reference readability at **9.6/10** for this test. The selected proportions and navy/orange palette, two low independent discs, four wheels, and empty cargo bed are visible in the field. The truck makes clean road contact and paired tire tracks. The garage was **9.4/10** in the same candidate. The roll-up opening and garage scale read clearly, while the sawtooth edge on the roof snow and dark side timber are visible even at normal zoom. The Drive and Exit truck touch placement earned **9.6/10**. The separate HP and cargo text over the field earned **9.4/10** due to contrast over bright snow. Both 9.4 scores were below the 9.5 target at this revision. [Garage finish comparison](Garage-roof-before.jpg)

### Garage finish retest

I scored the revised garage **9.5/10** for scoped test quality. In the matched 1× gameplay crops, the new edges round off the snow, and blue panels read as a continuous material with visible seams. The dock, scale, and roll-up shutter still read at play distance. Some camera-facing timber remains in deep shadow. The paired render holds the scene tick and actual game camera constant and changes only the two garage mesh appearances. [Matched gameplay retest](Garage-roof-retest.jpg)

## Bugs reproduced during development

- Vehicle controls had a negative screen position because the manual HUD parent had no size. A direct button-rectangle touch simulation could trigger the off-screen action. The harness now requires the complete button rectangle to be inside the viewport before sending the actual tap.
- Nearby wolves contacted the vehicle's side while it was stationary, moved it away from the driveway, and dealt no damage. Wolf contact also interrupted a short forward approach to the quarry.
- A nose-first truck precisely centered in the garage failed to bank cargo because the longer front of the hull extended just beyond the previous bay check. Backing in worked from the same center.
- Typed array membership produced repeated script errors during resource contact. An earlier integrated revision also called a raid-health method nonexistent at runtime while generating customer orders.

## Visual comparison

The truck's navy cabin and bed, orange guards, four wheel silhouette, and two ground-level discs read at the gameplay scale. The garage has the selected blue roll-up door and roof, and occupies a single fence span at game scale. The in-bay cutaway helps the driver remain visible. At close range the stylized truck has lighter tire tread and simpler curved fenders than the owner turnaround. The garage side looked darker than the other warm timber buildings in the first native capture. The authored 3D assets were reviewed with the exact owner sheets from GitHub commit `201dcbe4f`.

The conveyor before and after captures were made at the same normal and pinch gameplay viewpoints using the same Build 13 paid shop profile and the isolated updated art. The revised orange guards read more clearly. Dark rollers, raised supports, and carried meat are still visible. The original owner sheet uses heavier, visibly braced feet, and its example camp has more space around the machines than the overlapping paths in this fixture. These observations cover art and readability in the captured setup. [Conveyor comparison](../Conveyors/Conveyor-comparison.jpg)

The stag’s antlers and cold-gray fur read close to the selected concept. An initial pose review prompted a rig correction. The refreshed rest and wind-up frames show clean stance and leg silhouettes. The stag and survivor overlap briefly along the camera line at contact. Crew tests show three damage contacts, a physical return through the south gate, and three warehouse deposit receipts. [Rest at 2×](../Crew/Stag-rest-2x.jpg) · [Contact at 2×](../Crew/Hunt-contact-2x.jpg)

The captures use desktop Godot compatibility rendering with virtual touch and a dummy audio driver. Phone installation, sustained outdoor performance, sound playback, and the user’s 9.5/10 build-wide target require their own evidence.
