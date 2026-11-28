# Independent R4 candidate review

Fresh actual pixels; complete eight intended views per candidate plus named closeups. Static illustrated concept only, no actual mesh/animation/runtime approval.

| Machine | Score | Verdict |
|---|---:|---|
| 02-metalworking-bench | 8.5 | REPAIR_REQUIRED |
| 04-assembly-bench | 10.0 | APPROVED_STATIC_CONCEPT |
| 05-manual-oil-pump | 8.5 | REPAIR_REQUIRED |

## 02-metalworking-bench

SHA256 `d7f38d518ea6a1a6c3c313a2ac10443d98e8d7ee0a4dfa9ab9c0a869b1d3736b`;1536 ×1024 RGB. Full eight-view review plus listed JSON closeups.

- M02-R3-GEAR: exactly8 broad teeth, one bore and projecting hub now readable in0/45/315. No clipping with press/tray found in those obliques.

The gear changed from a low lying token to a large upright token in0/45/315, but RIGHT90 still has the original low tray with bolt/bracket and no upright gear edge/hub. The new gear sits forward of the press and rises above the tray, so this changed pose must be visible edge-on in90.

Propagate the new selected gear upright pose toRIGHT90 only: show narrow toothed rim and hub in the front output tray, preserving clear press/tray separation. Preserve the approved0/45/315 gear and all other machine details.

## 04-assembly-bench

SHA256 `f3d79d455002fc0aa0eac3ee7a4a2b09c6d89554088e5605b98e4ad1b3409d2c`;1536 ×1024 RGB. Full eight-view review plus listed JSON closeups.

- M04-R3-GEAR: selected8 broad-tooth token with raised hub now consistent at0/45/315; it fits the front bin, no clipping or output/gantry/camera regression.

No remaining mandatory defect in static artwork scope. Native mesh, animation and runtime processing untested.

## 05-manual-oil-pump

SHA256 `f580f337a8081c2a5c4cd62730046378d0e6f831bb0052c41acd326a36f98ef5`;1536 ×1024 RGB. Full eight-view review plus listed JSON closeups.

- M05-R3-FEED-ENDPOINT: barrel wall penetration/front-facing wellhead flange removed;270/315 valid low blue-buffer feed retained.

At0 the new low visible pipe bends up into the existing high filling pipe/upper blue-tank port, unlike the separate low feed shown270/315. At45 the upper silver outlet stub stops beside/above the orange-valve spout, leaving a visible navy gap rather than a joined short elbow.

Repair only0/45 pipework to rotate the valid270/315 arrangement: one separate fixed wellhead-to-LOW-blue-buffer feed, plus one connected HIGH-blue-buffer-to-orange-valve barrel filling line. Preserve intact barrel and the corrected left outlet/overall orbit. At0 do not tee the feed into the high filling pipe; at45 join upper outlet to valve body with its short sealed elbow.
