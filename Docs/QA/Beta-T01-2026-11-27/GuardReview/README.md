# Guard sightline review

[Final 6 cm and cached mask review](FinalCandidate/README.md)

[Newer exact foreground-depth retest](ExactDepthRetest/README.md)

[Newer tower-only depth mask retest](TowerMaskRetest/README.md)

The Beta T01 guard effect fails the visibility check. Cyan bands cross the gunner’s exposed face, collar, jacket, and legs at normal and 2× zoom. All 11 tower and weapon meshes remain opaque, have emission disabled, and carry no overlay. The guard’s opaque body contributes to the sampled depth, so its own overlapping surfaces activate the effect. [Paired gameplay frames](Guard-effect-comparison.jpg) · [Native capture](Native-capture.log)

I captured the paid east tower in the same position at northeast and southeast aim bearings. Each pose has a frame with the effect, a frame with the effect disabled, and a control with the guard hidden. The captures use the normal 720×960 desktop gameplay camera and Godot’s OpenGL compatibility renderer. The visible guard mask keeps the interior of pixels that change when the guard is hidden. Cyan from the effect appears over 34.57% and 28.59% of those pixels at the northeast bearing, and 17.43% and 15.53% at the southeast bearing, at 1× and 2× respectively. [Pixel measurements and tested source hashes](Guard-render-measurements.json)

The fitted wooden and stone platform, mounted bow, and opaque tower were compared with the owner’s selected ballista sheet and locked video B at 43.00 seconds. The ballista sheet on `main` still has the same underlying image as the pinned sheet. This review covers the sightline effect and tower opacity. The 9.9 character and survivor animation reviews retain their separate evidence. [Selected ballista sheet](https://github.com/ksolo21-web/HAVENLINE/blob/2ae9702b0b6294b6cca3fa0d3098025d72484f06/Docs/Design/RenderArchive/2026-11-23/selected/equipment/ballista_tower.png) · [Locked reference frames](../../camp12/References/Owner-matched-B-defense.jpg)
