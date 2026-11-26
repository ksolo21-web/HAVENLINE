# Character 1 walk and run

**Independent gait and deformation score: 8.6/10.** The walk now transfers weight from boot to boot, the arms counter the legs, and the run has a shorter cadence and a visible flight phase. The fixed gameplay camera shows those changes most clearly from the front and rear diagonals. At 2×, the face, glasses, hairline, belt and fur collar stay together through the sampled poses. The near boot hides much of the far boot during a side-on passing step.

**Outstanding defects.** A raised boot still intersects the back of the trousers on the run. The largest exposed intersection in the selected problem poses measured about 30 mm from a side/rear heading and 12 mm from the front. This reads as compressed material at boot height. The rear center of the trousers also stretches excessively at one short edge. Planting is much stronger at steady speed than during a hard reversal. These issues keep the rig below the 9/10 clearance and motion threshold.

[Gameplay framing and eight movement details](Gameplay-camera-gait.jpg) · [Frame numbers and crop bounds](Gameplay-camera-frames.json) · [Complete measurements](Measurements.json)

### Camera evidence

The board uses native 3840 × 2160 Godot frames from `orbit_opening.tscn`, with the ordinary camera, actor, movement controller and 1×/2× zoom. The upper strip preserves each entire frame. The lower strip enlarges the actor for inspection. The walk travels at 1.12 m/s and the filmed run at 2.65 m/s. Frame 285 shows opposite arm and leg advancement. Frames 465 and 490 show alternating support. Frame 723 shows the lifted boot from behind. Foreshortening compresses the lateral step at frame 96. The controller also runs a separate full-speed 2.80 m/s test.

The retained source videos show travel, a stop and transfer, including loaded approaches. Carrying obscures the hands and parts of the legs. Those recordings do not establish an exact cycle length for an unloaded walk or run.

### Motion and surface checks

| Check | Walk | Run |
|---|---:|---:|
| Cycle duration | 0.933 s | 0.733 s |
| Opposite arm/leg timing, same-side forward correlation | −0.967 | −0.751 |
| Pelvis / chest / head yaw excursion | 12.6° / 13.0° / 3.2° | 16.0° / 17.8° / 3.2° |
| Fore-and-aft hand excursion | 37.2 cm | 34.3 cm |
| Grounded sole material, median local rearward speed | 1.121 m/s | 2.653 m/s |
| Lowest point of the actual boot mesh in the authored clip | 1.50 mm | 3.76 mm |
| Portion of samples with both soles over 1 cm high | 0% | 15.6% |
| Median / 95th-percentile steady near-ground speed in the engine | 0.007 / 0.072 m/s | 0.021 / 0.049 m/s |

The previous rig had no pelvis, chest or head rotation in either gait, with same-side hand/foot correlations of −0.255 walking and +0.186 running. The current clips start at zero and close within 0.001 mm. Neither ankle crosses the other in the forward loops. Each toe group acts on the visible shoe, including rollover. All 12,656 unique source positions, 25,264 triangles and the three source texture bitstreams are preserved after normalization to 1.75 m. Joint weights sum to one. The locomotion clips do not test finger articulation, facial acting, carrying, backward locomotion or strike poses.

The full skinned surface was evaluated at 120 Hz, including the loop endpoints. After welding coincident vertices and removing intersections already present in the original rest surface, peak additional triangle-pair counts were 11 idle, 109 walking and 394 running. Earlier published gait geometry gave 84, 414 and 444. A pair count measures mesh triangles and can describe multiple triangles in a single clothing fold. The earlier cuff-to-waist faults were also explicitly retested at their original problem poses and cleared on both arms. At 0.650 s in the final run a 17.7 mm edge behind the crotch reaches 3.13 times its rest length. The strongest visible remaining fold is lower on the raised boot.

In the engine's synthetic hard-reversal case the near-ground-point speed reached 5.42 m/s at the 95th percentile during the transition. This includes rotating and releasing soles within 5 mm of ground. It does not isolate a planted heel. The result supports a separate turning or pivot pose before claiming locked-foot reversals. A corrective shape for the flexed rear trouser/boot region would address the remaining surface issue without changing the accepted character design.

**Reviewed GLB** `e52ac41ad523d89da65f095a074a8e27125816bd2505f2486600ed2d63cab45d`. The machine-readable measurements distinguish the selected V4 model from other inspected candidates.
