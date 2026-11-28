# T02 independent baseline and reference scope

The previous lake correction at `25cf9ea5a31ef0acc90fbc4612498dc671565ccb` earned a historical 9.5. The owner subsequently requested a persistent world-spanning river. The resulting `river_v1_mapspan` at `1f0ba3bede3d160a34751c2fcdbfa78c1b6785ff` earned the historical scoped river approval. New checks will bind to the actual ten-tool Build16 continuation source. T01's earlier 9.9 reference reading remains recorded.

## Evidence and meaning

- Locked recording A at 5.00 s shows broad blue water, a curved white shoreline and a warm work approach. Locked recording B at 8.00 s shows the matte peach-brown camp floor, clean snow contact, and restrained floor variation. The combined original ground board has exact SHA-256 `3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb`.
- The owner-approved World Biome sheet is from Git `2ae9702b0b6294b6cca3fa0d3098025d72484f06`. It defines stylized ice-blue water, sculpted snow, and softer rock/bank material language. Its frozen-lake illustration contributes visual material reference. The later river layout defines active world geometry.
- Historical river acceptance required the open west/east span, variable widths, continuous banks and dry lanes, camp setback, three clear crossing reserves, same-side old-save recovery, and shared geometry between visible water, bank, contact and save behavior. Two independent roles scored that historical source 10. New exact review carries no historical score over automatically.

## What the current gameplay source does

- `field_lakeshore.gd` samples the historical curve as a rotated closed inlet. It builds a 108-section fan and near-shore mesh on top of the flat foundation. Source-sampled inlet bounds are X -42.739 to -24.103 m and Z -0.800 to 32.800 m. Current World One extends to ±512 m.
- A direct transplant of the old world coordinates wets 14 of 15 measured points from current camp X -10 to +10 and Z -9 to -7. It puts the paid cooker center approximately 0.583 m inside the historical waterline. The migration must preserve the current camp and old purchases while making the chosen compatible river route explicit.
- The current water, terrain, route, and save services are distinct consumers. The player and snow truck call the current `constrain_motion`. Forest and streamed world placement call `reserves`. Home and pack navigation derive inflated outlines from `shore`. A route replacement has to keep those consumers aligned. The existing cookware input/output positions and costs remain a protected integration regression.
- Current water is opaque and uses a pausable runtime tick. Its current elapsed value is local to the inlet instance. Verify continuity under the candidate's actual save/reload and simulation-clock contract. Historical weather and camera proofs cannot be applied by filename to a later gameplay runtime.

## Minimum fresh coverage

Use the actual gameplay camera at normal and true pinch for the dry camp approach, both banks, and terrain contact. Review a full plan and both current world-edge reaches to prove continuity, and uncut nearby views and short gameplay movement to check joins, foil highlights, creek profile, and continuous dry travel. Confirm active same-source water and bank geometry, playable exclusion for actors and truck, stable world streaming, side-preserving reload and resource identity, and no overlap with paid assets. A native high-resolution software picture supports shape and picture resolution. Hardware testing is waived for this playtest.

[Locked recordings and owner biome sheet](/tmp/havenline-t02-independent/Locked-reference-and-owner-biome.jpg) · [Reference hashes](/tmp/havenline-t02-independent/Reference-provenance.json) · [Source geometry comparison](/tmp/havenline-t02-independent/Current-inlet-versus-historical-river.png) · [Sample and source bindings](/tmp/havenline-t02-independent/Source-geometry.json)
