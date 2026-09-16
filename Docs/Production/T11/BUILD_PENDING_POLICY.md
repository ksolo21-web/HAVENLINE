# T11 build-pending policy

This policy implements the authoritative Havenline V2 state `BUILT_PENDING_DEPENDENCY` for T11 and narrows only the dependency-timing language in older T11 preparation text. `FROZEN_SCOPE.md` T11-R15 is authoritative.

## Allowed before T10 approval

T11 may be built and tested on `havenline/T11-camp-construction` using only T11-owned paths and the frozen T10 semantic contract. The candidate may use a deterministic mock/adapter for unavailable T10 runtime so that T11 content-domain logic, presentation, authored stage composition, build/import behavior, route/camera/context regressions, duplicate/replay presentation protection, performance bounds, and evidence tooling can be completed.

The highest truthful state before T10 approval is `BUILT_PENDING_DEPENDENCY`.

## Still blocked

T11 may not become `INTEGRATION_READY`, `INTEGRATING`, final `UNDER_REVIEW`, or `APPROVED` until T10 is APPROVED and integrated. After T10 lands, T11 must reconcile to the exact accepted T10 interface/source, rerun every dependency-sensitive test and affected evidence, pass G1, then pass G14 on the merged integration candidate.

Build-pending evidence is not final T10 compatibility evidence.

## Immutable boundaries

- No edits to T10 transaction/idempotency/atomicity/recovery semantics.
- No edits to T08/T09 authoritative resource behavior.
- No edits to integration-only `main.gd` or `simulation.gd` from the T11 builder.
- No invented shipping construction prices. Test fixtures must remain explicitly non-shipping until an authoritative price source or approved tuning record exists.
- Later T12/T13/T14/T15+/T21/T22 ownership remains excluded.
