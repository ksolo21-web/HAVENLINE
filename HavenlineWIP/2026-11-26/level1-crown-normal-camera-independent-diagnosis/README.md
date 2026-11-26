# Independent diagnosis of the held normal-camera log comparison

Source: the immutable six captured PNGs and pinned camera/geometry in the preceding capture record (87e5f292e5edd97a7a6ec7f9d0befcf129870af8). No engine was rerun, no input changed and no score was issued.

| Tick | Pixels outside modeled direct + shadow region, RGB delta >= 2 | Largest channel delta | Inside the modeled character silhouette |
|---|---:|---:|---:|
| 128 | 864 | 91 | 17 |
| 129 | 85 | 98 | 1 |
| 142 | 211 | 130 | 2 |

All of those outside-region changes are darkening, not brightening. At tick 128, 859 of the 864 have all three control channels above 130. The patch is localized over bright snow just left/below the log, up to about 30 pixels beyond the modeled region. A character-only receiving shadow cannot explain most affected pixels. A filtered or cascaded shadow, caster occupancy, or a between-run shadow-state difference is plausible, not yet established. The original hard projection did not sample the actual renderer's shadow receivers or filtering.

As an observation of the rejected comparison only, the visible bark at tick 128 looks white next to the orange end grain. That is consistent with the verified imported bark flag being off; it is not an independently passed appearance or a reason to move the log into the build.

Keep the original guard. If the result needs a causal test, first show that two untouched controls reproduce the same frames. Then separately compare cast-on and cast-off copies of the same transient object at fixed pose, material, camera, and light. Loss of the extra dark patch only when casting is off would support a shadow-path cause. Do not use an expanded tolerance as evidence. No changes to game assets, carry, collision, inventory or the playable build.
