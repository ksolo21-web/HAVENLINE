# Combat number review

**Damage-number readability scored 9.5/10.** The repaired 1.00 s frame in the encoded 540 × 1260 gameplay movie shows two distinct gold −1s over the same alpha wolf. Their centers are 67.4 px apart. The earlier hit fades while the newer value stays opaque. The prior close-up showed a doubled glyph that resembled “=1”.

| Rendering | 1× gap | 2× gap |
|---|---:|---:|
| Fold cover, 1080 × 2520 | 77.0 px | 154.0 px |
| Fold inner, 1968 × 2184 | 140.3 px | 280.5 px |

These are horizontal center-to-center distances measured from the source readbacks. I also inspected the actual same-tick pixels at each panel and zoom. Both minus signs and digits remain fully within the image. They clear the wolf’s health bar, the quest prompt and the resource chips. The red incoming −4 and the player HP decrease are visibly distinct at the first bite. The gold values share one style across owl and weapon hits, so identifying the attacker still depends on the owl’s dive and the weapon’s motion. The cooker objective stays on screen and leaves the encounter visible.

I awarded 4/4 for separating concurrent values on both panels and both zooms, 2/2 for legible signs and digits, 2/2 for separating incoming damage from outgoing hits, and 1.5/2 for visual attribution. That final deduction reflects the shared outgoing style. The result covers these real rendered replay samples. The take is a 20 fps export; this review does not measure device frame pacing or physical touch latency.

Source: `field_opening.tscn`, commit `dcad2f2201af34af1fe64dd2f35160c601e1cb81`. See `Independent-popup-measurements.json`, `Independent-popup-comparison.jpg` and `Independent-popup-panels.jpg`.
