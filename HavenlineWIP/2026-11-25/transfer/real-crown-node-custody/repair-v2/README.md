# Detached four-log custody and flight-path fixture, repair v2

Repairs the two false passes found by independent review of builder archive 7f3427f9cad062837ab89b84fe43967f622e089d (manifest 127164bee909217914f2c21584f8a2ea20d53c201bc869a4d3c342771afea8d8; independent archive 0d013b724b1e703da985b36e4f9322e804b27437). This is a standalone headless Godot test; it is not gameplay or an approval. All three mounts and the five diagnostic stones are synthetic. The only production asset input is the immutable starter ground wood LOD from 11c14a1c41971067c7dc97db69375f720a408f68, SHA-256 31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554. The original crown holds its scale and vertex colors; this archive redistributes no asset bytes.

The observer now recursively inventories all visible nonempty MeshInstance3D nodes under the fixture lab, all four original node IDs, unique slot/owner, one original mesh and unchanged material assignment per slot, and the five actor-relative unrelated slots' direct parent, identities, transforms and materials. Both an unexpected renamed resource clone with no metadata and a second recognizable wood slot fail the audit. It does not claim rendering, support for arbitrary other geometry node classes, or anything outside that isolated subtree.

An independently expressed algebraic oracle checks position in aligned lab coordinates (including XY) and declared owner/phase at the 55 sampled frames. It uses fixed values for the two 0/11,500 µs launch offsets, 285,000 µs durations, -2/2 m endpoints, 1.0/0.5 m heights and 0.65 m hump. XY tolerance is 5 µm and is numerical only, not collision or continuous-coverage proof. The simulated clock is injected; this is not actual game timing. Original independent mutations are replicated separately on disposable copies, without modifying this frozen test. A local wrong XY injection fails at one exact sample; the original full-path mutation fails every sampled in-flight check. The same simple ledger and wrong-row/replay checks are retained.

Run from this directory with Godot 4.7.2 and an existing serial headless lock:
- `bash run.sh /path/to/pinned/starter_ground_wood_lod.glb /path/to/existing/headless.lock clean`: exit 0, 1831 checks, no failures.
- Repeat with `nested-equivalent`, `nested-foreign`, or `wild-xy`: each exits 1 and emits its specific assertion failure in the JSON output.
- `python3 replay_controls.py /path/to/pinned/starter_ground_wood_lod.glb /path/to/existing/headless.lock`: exit 0 only if both exact critic controls failed as expected. Comparable captured outputs are listed in SHA256SUMS.
- `sha256sum -c SHA256SUMS`: checks the complete frozen payload.

No change to gameplay, real character/receiver mounts, collision, actual stone art, render, phone, authoritative persistence, or the 52-piece fixture. No paid service or user save touched. Pending independent replay.
