# Havenline Frozen Task Packet — TEMPLATE

> Generated/filled before assignment. A worker may not expand this packet's runtime scope without an integration-owner change request.

## Identity
- Task ID:
- Task name:
- Workstream owner/id:
- Isolated branch:
- Exact base integration commit:
- Packet generated from integration commit:
- Status at generation: PREPARED

## Frozen requirements
- In-scope behavior/art:
- Explicitly out of scope:
- Preserved approved behavior/assets:
- Product-contract constraints:

## Dependencies
- Required APPROVED upstream tasks:
- Interfaces consumed:
- Dependency hashes/versions:

## Path ownership
### Owned production paths
- 

### Protected / foreign-owned paths
- 

If a protected/foreign path must change: **do not modify it.** Create `Docs/Production/ChangeRequests/<task>-<target>-<id>.json` with requesting task, target path, requested change, reason, dependency, expected behavior, and tests required.

## Acceptance gates
- G1 Dependency
- G2 Path ownership
- G3 Scope
- G4 Build/import
- G5 Functional
- G6 Regression
- G7 Evidence provenance
- G8 Performance budget
- G9 Persistence if applicable
- G10 Security/economy if applicable
- G11 Accessibility/adaptive UI if applicable
- G12 Critic coverage
- G13 every mandatory dimension **>9.0 unrounded**, target 10/10
- G14 merged integration candidate regression

## Required tests
- Universal baseline:
- Task-specific:
- Impact-selected prior-task regression:
- Save-state matrix if applicable:
- Device/layout matrix if applicable:

## Required deterministic evidence
- front
- rear
- left
- right
- 3/4
- gameplay scale
- close-up/detail
- relevant overhead
- relevant day/night/weather
- native 3840×2160 scale-1 where applicable

Every capture record must include candidate commit/hash, scene/state, camera, renderer, resolution, timestamp/build ID.

## Motion evidence when applicable
Full real-time cycles, slow review cycles, turns, transitions, feet/toes/knees, hands, gear, tails/wings/mane, ground contact and clipping states.

## Required critics
- Applicable critic IDs from `CRITIC_MATRIX.json`:
- Independent runtime/provider/model:
- Raw input/output destination:

A builder self-review is recorded separately and cannot satisfy an independent critic gate.

## Performance budget
- Assigned subsystem budget:
- Baseline:
- Required metrics:
- Failure threshold / regression rule:

## Evidence package
Destination: `Docs/Production/Evidence/<TASK>/` plus external artifact IDs/hashes for large binary evidence.

Package must contain/source-link: candidate/source hashes, changed-file list, tests/logs, screenshots/videos, performance records, raw critic inputs, raw critic outputs, known failures, dispositions.

## Integration readiness checklist
- [ ] exact branch/base recorded
- [ ] no unauthorized path modification
- [ ] dependency gate satisfied
- [ ] build/import clean
- [ ] task functional tests pass
- [ ] impact-selected regressions pass
- [ ] evidence is source-bound/current
- [ ] performance budget passes
- [ ] persistence/device/security gates pass where applicable
- [ ] required independent critics complete
- [ ] every mandatory dimension >9.0 unrounded
- [ ] no unresolved mandatory defect
- [ ] candidate marked INTEGRATION_READY only; not self-approved
