# Axe scale, clearance and head contact

The ordinary axe now spans 66.3 px from blade center to handle end at 1280×720. The previous build measured 73.9 px in the identical camera pose. Its midshaft narrowed from 10.7 to 7.9 px. The revised head measures 36.7 × 33.1 px along and across its handle. The head-center orbit radius remains 130.7 px. The regular side-facing wolf spans 132.9 px. [Reference and native comparison](Source-and-game.jpg) · [Full measurements and donor hashes](Native-projections.json)

| Normal-camera measure | Source B 5.80–6.10 s | Before | Revised |
| --- | ---: | ---: | ---: |
| Handle length / hostile span | 0.47–0.52 | 0.56 | 0.50 |
| Midshaft width / hostile span | 0.042–0.065 | 0.080 | 0.059 |
| Blade aspect along / across handle | 0.99–1.04 | 1.29 | 1.11 |

The native hero covers approximately 90 pixels from head to boot in this pose. The reference’s hostiles overlap, so the estimated endpoints carry about 10–15 reference pixels of uncertainty. Its blue-hooded hero and Havenline’s character have different silhouettes. At 2× the same world-space proportions are preserved. [Before at full pinch](before-2x.jpg) · [Revised at full pinch](after-2x.jpg) · [Original B frame detail at 6.00 s](B006-interest.png)

The baked derivative keeps the original Meshy axe’s head geometry, material, UVs and three texture images. Only the lower wood grip was narrowed about its authored curved centerline. The game applies a separate scale to the axe, including its collision samples. Middle and rear cargo now sit on additional crosspieces copied from the expedition frame’s rounded timbers. The middle support appears with meat or coal. Slate or metal extends both bays. [Reproducible asset recipe](Rebuild-assets.py)

At 120 samples per second the previous axe intersected cargo in 93 tested phase/heading combinations. The revised axe and pick recorded zero positives across base and upgraded modes. All six materials and the full support frame were included. A separate geometric calculation bounds the axe path continuously for every relative facing and all ten packet orientations. [Triangle sweep](Builder-triangle-sweep.json) · [Continuous clearance](Continuous-clearance.json)

The reference-camera walking trial recorded three impacts at each zoom using ordinary touch movement. The blade collision point matched the emitted bark chip on every hit. Walk/run contact tests passed at 30, 60 and 120 physics ticks/s. Camp boundaries passed 51 checks, mining passed 82, tree return passed 16, and the high-load camera suite reported zero failures. [Walking impact at 1×](1x-walk-contact-1.jpg) · [Walking impact at 2×](2x-walk-contact-1.jpg) · [Physics receipts](Contact-and-regression-results.json)
