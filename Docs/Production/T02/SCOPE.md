# T02 — terrain, snow, warm work floors and lakeshore

Only T02 is being implemented after T01 PASS at 459505adde85b126e38a2313d535b0267d31048b. T03 and later remain locked. Every required task check and both independent role reviews must pass at >=9 in every dimension; target10. Final release is separate.

## Frozen deliverable
Replace the muddy circular clearing with clean peach/brown working ground, blue-white sculpted snow, a connected lakeside working bay and turquoise water with a continuous bank, matching the ground language in BOTH supplied videos. Recompose for the existing landscape map without moving stations/resources or changing the shipping camera. Preserve ground approaches to existing stations and future fishing edge. All 33 original/approved GLBs and approved tree shader/forest logic remain unchanged. Recheck T01 ground contact, cutaway and resource behavior.

One coherent indexed terrain and actual triangle interpolation govern actor/scenery height. A bounded custom water contour avoids fullscreen transparency/refraction. Water animation uses the pausable simulation clock. The same coast equation keeps players, companions and other actors dry; old saves in the new basin relocate without inventory loss and stay inside the existing playable bounds. No fishing, fences, new station models, customer systems or C2-C4 rigging are implemented here. Later-task assets visible in captures remain unapproved.

## Mandatory evidence
All existing regression suites plus T02 topology, contact, dry-route, shoreline, save and water-clock tests pass. No invalid/degenerate/reversed ground triangles; triangle interiors agree with actor height. Terrain<=125000 triangles, water<=256. Preserve 586 approved perimeter trees. Actual Godot Mobile captures must show camp, shore gameplay, overhead layout, front/rear coast details, snow/workfloor joins, tree contact, bay connection, eight camera-route positions, six water states and night. Native>=3840x2160/scale1.0 output and workload observations are additional checks, not physical-FPS proof.

Independent reference-fidelity and visual-integrity roles inspect source-bound captures against actual reference pixels, including detail views and sequence panels. Every mandatory dimension>=9, no unresolved task defect. Preserve raw responses, model/input/source hashes, failed and invalid evidence. No manufactured scores, averaging, score-shopping or self-review called independent.

## Legacy test amendments
The previous terrain assertion hardcoded30752 triangles. The replacement checks exact indexed-grid topology from HALF and STEP and a separate fixed125000-triangle ceiling. Gentle dry-snow normals.y>.9 still applies outside the deliberately steep, nonwalkable submerged bank; all faces separately require finite/upward normals, clockwise winding and nondegeneracy. These are task-driven changes, not removed checks.

## Handoff
No unfinished APK or user testing. Physical sustained phone/tablet4K60, full gameplay, final motion/critic review and release remain unverified. Do not mark T02 complete or advance T03 until actual task evidence passes.
