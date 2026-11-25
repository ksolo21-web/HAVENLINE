# Exact coordinated Character 1 open pose, static only

This detached source-authored **OPEN** specimen is not a grip, baked clip, rendered or in-game result, or an approved new animation. It supersedes neither the former proof about the single thumb hinge nor the rejected held endpoint. It intentionally moves the forearms away from the exact unchanged original axe before proposing any contact. Exact existing 52-joint owner rig and v2 skin, bind mesh, Character 1 identity/scale, material/UVs, source outfit, protected right authored pressure patch, bone lengths, lower body and torso are unchanged. Elbow/shoulder points are fixed. Locally rigid palms, wrist/cuff and thumb web travel with the forearms; they are not pinned in world coordinates or previous invalid held overlay. The right hand remains assigned to original shaft facet 124 and left to 276, whose positions remain exact.

## Construction

For each arm the axis is the cross product of the actual elbow-to-wrist vector and outward normal of that arm's assigned original grip facet. This supplies instant outward wrist motion. A support equation conservatively picks all exact tool facets intersecting the axial range of the pure distal glove's proposed rotation arc (including the authored right palm). It derives a single endpoint from the first scalar support-deficit root plus a small numerical guard, not a pose-offset score sweep. The bracket cap and guard are analytical diagnostics, not a normal/allowed game joint range or a slide/roll contact allowance. This authors a paired 21.374° right, 2.506° left rotation about their respective actual elbow joints. The whole hand subtree rigidly inherits its forearm; no subordinate joint rotation is changed. Source-to-open matrices and paired wrist/reach coordinates are in the result and can reconstruct a no-export candidate.

There is 102.955 mm right and 92.721 mm left shoulder/wrist reach reserve; both true bone lengths are unchanged. The unchanged original band stations are about 118.874 mm away in right palm normal and 14.269 mm left at this sample (the projected tangential errors are also reported; no sliding is implied). This is not even proposed physical contact.

The script confirms the source P/F/W and right pressure input digests, reconstructs the v2 source weight recipe and replays the mixed-arm measurements against the exact held source using dual-quaternion skinning. The frozen pose readback residual across touched rows is <0.44 µm. 368,574 original indexed positions outside selected forearm/descendant weights remain exactly unchanged. All 642 right and 588 left original cuff edge input endpoints inherit the planned same local transform; max tested deviation <0.071 µm. The 57 fixed right authored pressure seam IDs are shared global P/F rows, not fed into a fictitious local-index patch; measured local drift is <0.047 µm. The original bind coordinates, indexed geometry/weights and texture mapping are unchanged; there was no character or actuation export.

## Evidence and limits

Complete original retained body plus full 2,445-triangle authored right patch against all 512 exact tool triangles changes 298 to **0 strict finite face/tool intersections**; contained shape rows go 631 to **0** from winding against the closed shaft. Strict means nondegenerate interior edge/triangle crossing: coplanar surface contact, loops with merely touching edges, and dynamics need other checks. See result for the separate candidate-vs-self/coat gate, which tests relative-motion face pairs in the posed actual source with nonincident contact, not a camera image or whole dynamic validation. No rendered silhouette, material look, true grip, bilateral hold, motion between these source frames or runtime is established; score/adoption stays HOLD.
This direct outward-axis construction is rejected: 447 new strict nonincident character-surface crossings despite the clear axe. The relative-motion body counts are 551 original versus 546 candidate, but 452 original pairs cleared and 447 different pairs arose; a lower total is not a pass. The first named changed family is the posed right forearm sleeve against the stationary right upper-arm sleeve (e.g. original source faces 44477 and 51158). No application or release follows.

To reproduce, use this directory next to the sealed predecessor and its pinned local dependencies; no private geometry is included.

```sh
bash run.sh /path/to/exact/held_owner.npz > replay.json
cmp replay.json result.json
sha256sum -c SHA256SUMS
```
