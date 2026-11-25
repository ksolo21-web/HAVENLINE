# Independent custody fixture review: scoped replay pass, coverage hold

The builder fixture is pinned by manifest SHA-256 `127164bee909217914f2c21584f8a2ea20d53c201bc869a4d3c342771afea8d8`. All six governed inputs and evidence files matched. Its protected runner launched native headless Godot 4.7.2 from a fresh disposable profile under the shared lease, verifying the exact original crown GLB input hash `31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554` and upstream planner hash. No authoritative game tree or saves were opened. The new `replay.log` is byte-identical to the builder runtime log: 1,116 assertions passed across 55 injected-clock samples. This confirms the exact observed flat test scene: the original four unscaled 1,300-triangle crown MeshInstance3Ds traverse direct held/flight/landed mounts by identity; the five directly held substitute stone nodes retain actor-local transforms, material identities/color and visibility, and the ledger remains typed. The two historical negative cases are arithmetic controls, not execution of the old runtime. No graphical score is assigned.

Two deliberate mutations, each in its own disposable copy, independently expose coverage gaps. `probe.py` leaves the frozen builder packet unchanged. See `probes.json`:
- Add an extra actually visible source-crown mesh under a wrapper child of the flight mount, reusing slot 0, and the flattened expected row continues to pass all 1,116 (the scan visits direct children only). The same flat-scan architecture does not detect extra nested stone.
- Replace the X/Y flight arc with a wildly off-course path; all 1,116 pass. In-flight checks constrain orientation and Z only, not X/Y, continuity or velocity.

For a successor, use an independently inventoried recursive scene census (expected exact IDs plus any descendant carrying crown mesh/slot, including under wrappers; watch the whole fixture root), and compare the actual sampled world transforms with an independently evaluated launch/arc/land contract. Add nested duplicate and wrong X/Y controls to prove the updated checks fail appropriately. Actual on-screen video, approved anchors, real stone, 52 real moving models, Character 1/receiver obstruction, gameplay timing and phone performance remain unverified. The attached replay is useful evidence for the limited test even though it is not a general regression-safe visual custody oracle.

Reproduce from here with the unchanged builder directory, exact locally provisioned GLB and the existing shared lease:

```sh
sha256sum -c SHA256SUMS
python3 probe.py /path/to/frozen-builder /path/to/starter_ground_wood_lod.glb /tmp/havenline-godot-headless.lock
```
