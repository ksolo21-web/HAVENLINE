# Level 1 HUD and failed-purchase recovery

Builder: `hud_redesign`. Independent visual reviewer: `root`. The previous Android HUD score was reopened after the owner’s phone test.

The original Archive A at 00:03 shows a short balance beside a large relief icon and a translucent movement control. B at 00:28 and 00:48 keeps the center of the field clear and puts the cost on the object being purchased. The top corners in this build hold the player’s health and cargo. A ticket at the lower edge gives the next destination, actual price and partial receipt. The trial retains required health, home guidance and graphics selection. [Locked source identities](https://github.com/ksolo21-web/HAVENLINE/blob/76645004d91dc6b05425f1ddc8a18017e701b664/Docs/Design/ReferenceVideoLock/reference-video-sources.json)

## Pictures and controls

The Before, Cover and Inner folders contain ordinary touch approaches, an in-flight purchase, the built camp and a real two-finger zoom. Wood was staged in an isolated inventory for these comparisons. The movement thumbstick appears on the current finger and releases on pinch, release, focus loss or display resize. Graphics remains available from the small slider button, whose accessible name and transient caption state the selected quality. The run recorded actual Godot pixels on the desktop compatibility renderer at Fold-shaped resolutions. A physical foldable device was unavailable.

Stock-cover uses an explicitly staged late-game inventory in the live field. All six resources have independent icon and text bounds. Earned planks, stone blocks, meals and cash have their own quantities. A meal held by a survivor or the player is subtracted from the tray exactly once. The ticket shows each stored balance and the next upgrade. A six-balance capture exposed an entrance-frame collision between the last resource and the upgrade caption. The final implementation uses one shared set of row positions for both measurement and drawing. Layout-checks.json includes the regression on cover, inner and landscape screens.

## Art and motion reference

The portrait is a fresh three-quarter render of the game’s Character1Fresh model, showing the glasses, curls and blue parka. The other icons use the existing resource art, the actual furnace, palisade, house tiers, tower, axe, money, planks, dressed block and cooked meal. Purchased equipment uses the approved cooker, saw and quarry markers from assets/paid_workshops. The payable line reads the actual partially funded receipt, separately from workshop activity. Animated quantity feedback and an incoming ticket change never move the hit area.

## Independent purchase review

Side-entry records an approach to the side of the hearth, a retreat, a second visit and the resulting reveal. The first revision kept 17 of 20 payments after the player walked away and allowed the same side to finish the remaining three. Seven physics ticks separated the final payment and the visible furnace. The first rendered candidate lit the snow before the stone appeared neutral and kept the shell too dark throughout the next beat. This reopened the visual criterion. The owner’s recording shows the final payment around B 6.10 s, the new furnace at 6.20 s, an amber shell at 6.30 s and the thaw spreading through 6.60 s. [Source clip](https://github.com/ksolo21-web/HAVENLINE/blob/76645004d91dc6b05425f1ddc8a18017e701b664/Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/Locked-sequences/B-camp-purchase.mp4)

The revised Side-final route passed the independent 9.5/10 criterion for payment, interruption, ignition and thaw. The repeat used the same touch path. At the first furnace frame, the stone rested on neutral snow. At 0.10 s after that frame the shell turned amber. At 0.20 s the visible warm floor expanded. By 0.40 s the floor spread to the perimeter. The side departure still held at 17 of 20 wood and the return completed the last three installments. Reference-and-two-reveals.jpg aligns the two game sequences with source B to the nearest recorded 0.10 s. Havenline’s rectangular perimeter and additional gate reveal remain distinguishable from the curve visible in the last locked frame.

## Final independent HUD decision

Root reviewed the fresh covered and unfolded frames, the 2× view, stocked cutaway and side-payment route. The functional and responsive HUD scored **9.5/10** on these native views. The reference shows fewer permanent controls on screen. Havenline’s HP, home guidance, graphics control and paid-equipment prices are intentional additions. The owner's judgment and physical Fold7 interaction still require phone play. All 44 HUD checks and 35 home navigation checks passed. The ordered Frame 170–213 evidence in Side-final also records the separate 9.5/10 hearth-transition result.
