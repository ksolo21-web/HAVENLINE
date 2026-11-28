# T04 baseline differences

The station candidate starts at the published T04 review head `33c1855d249c8bf18f6ad49d2130b0b0c353e3dd`. The existing stand-alone HUD suite has an inherited assertion about excluding held meals from the tray count. The legacy isolated counter harness omits the field environment host and raises the same missing river context error on T04 and T05. The shipping-scene counter, paid workshop handoff, floor approach, and connected-line suites are included separately.

The connected-line tests use the published `Build9-raw-in-flight` fixture because they expect an owned transfer already in flight when the game starts. The workshop acquisition and reopen checks use the earlier version-6 save with eight paid expansion receipts and the original pending wood job. Fresh-profile attempts of those scripts are excluded from the pass count because those scripts require the specific saved state.

All game captures and simulations ran in disposable profiles. The initial saved poses in screenshots position the actor at the selected viewing point. Separate touch input tests verify that the approaches are reachable.
