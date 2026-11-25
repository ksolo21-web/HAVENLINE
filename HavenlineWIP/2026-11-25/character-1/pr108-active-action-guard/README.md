# Detached PR #108 active-action guard

Exact commit `48c6c53a0dfda117ef12c68b32cfe2b3732d5239`; opening Git blob `6a0f08cffba3d8cacea506e9150e44298e3bc394`. The prior native timing probe observed that a second F about .347 seconds after a successful tree or rock F advanced the resource when the independent .32 s resource cooldown had expired, while the original animation still played. This proposal changes two conditions in opening.gd only, before either request's increment or strike call. Both tree and rock share the same Character 1 active countdown, so switching target also cannot bypass the lock on an in-flight action. A nonempty idle hold pose name does not block because the test uses the existing positive countdown only, not action name, playback state, or a new timeout. Existing installation, first hit, out-of-range behavior, strike cooldowns, and damage policy are otherwise unchanged.

A disposable `git apply --check`, apply and reverse check succeeded; the resulting Git blob is `def0705251628d77607729827e3d9b9008abd16c`. This is based directly on the original PR, NOT the separate LOS proposal. Both patches touch the same rock-request line: if ever composing, hand-reconcile the intended OR predicates and recheck both independently. Neither proposal changes the playable branch or approval status.

## Native replay when serial lease is granted

```sh
bash run.sh <exact-clean-checkout> <pre-authorized-lease> baseline
bash run.sh <exact-clean-checkout> <pre-authorized-lease> repaired
```

The runner archives the exact project into a temporary directory with isolated HOME/XDG, verifies actual PR GLBs, and makes no changes to stock files or saves. The probe reuses the independently walked no-camp approach for each source, passing injected F and touch-drag events through the integrated scene handler and allowing native physics and existing countdowns to advance. No teleport, input clock forcing, scratch ledger mutation, hardware input, or animation-state injection.

| Case | Baseline mode | Repaired mode |
| --- | --- | --- |
| Ready source, timer not active | First F advances one strike and its sequence | Same |
| Resource cooldown expired, actor action timer still positive | Second F reproduces one extra strike and increments the two sequences | Second F changes neither strike, either sequence, source phase/cooldown, original action/clip position/countdown, nor ledger |
| Both existing timers naturally expired | Next F can advance exactly one strike | Same |
| No genuine overlap or required prerequisite | Exit 3; downstream unobserved | Same |

Baseline exit 0 means the deliberate defect control reproduced, not that the original gameplay passed. The legitimate first and next strikes are still immediate on F, before a verified physical contact frame. This guard does not fix that timing defect, provide contact notifications, guarantee restart/animation visual fidelity, verify every switching case, change the tool models, or establish device/gameplay acceptance. Native replay was staged but not yet run at this freeze.
