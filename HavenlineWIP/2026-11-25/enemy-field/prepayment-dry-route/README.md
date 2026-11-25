# Detached pre-payment dry field reachability fixture
**Staged for native review; no builder engine run yet.** Only ordinary opening
locomotion before paying, not an encounter or approval. The prior South
field-roundtrip exercised its field path after camp payment and real gate
crossing; this fixture starts at the authored unpaid spawn at the South apron,
uses existing test points as route samples, and returns there with no camp or
progression side effects. The route is not a proposed enemy's spawn position.

Fixture uses the existing integrated scene test harness, which injects
touch/drag into its ordinary handler and observes real physics. New code
samples every measured tick for dry full-footprint, outside crossing
reservation, native ground contact, active gate/payment state, unchanged
serialized ledger and maintained wood pickup visibility. It measures the
closest 3D reach to wood-c, turns, field dwell and return. No E/F input, direct
position writes, save flags, resource grants, art, rendering, fish, enemies,
or playable integration.

```sh
mkdir ./new-empty-output
bash run.sh /path/to/existing/pinned-local-git-repo ./new-empty-output /tmp/havenline-godot-headless.lock
```

The runner only uses local Git commit `11c14a1c41971067c7dc97db69375f720a408f68`
and HavenlineLevel1 tree `d764a05246cbff96983aa27af17e2e919a946ae0`. It acquires an
existing serial lease, rejects concurrent engine/render processes, extracts to
a clean temporary project, reconstructs and checks the existing hearth, checks
all tracked input blobs and exact staged fixture before and after, and confirms
no same-build opening save file/stage. The expected earlier import diagnostic
multiset is explicitly checked; runtime diagnostics must be empty. Leave
existing developer, tracked and user files untouched. Source notes separate
from engineering results: see REFERENCE_TIMING.md.
