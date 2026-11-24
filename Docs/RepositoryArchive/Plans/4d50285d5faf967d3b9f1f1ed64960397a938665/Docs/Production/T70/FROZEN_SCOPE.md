# T70 — Final production release handoff — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`  

## Required outcome
- Handoff one exact final production release candidate only after both physical-device certifications pass and all prior release-critical tasks remain closed.
- Verify final package/build identity, production signing/OAuth identity, install/update/reinstall/recovery, release notes/versioning, all critic/gate evidence, security/LiveOps/economy/privacy records, resource/tool/actor/animation registry hashes and zero unresolved mandatory defects.
- Verify exactly two Game Master owner slots are provisioned server-side to the designated verified identities and the complete Game Master release audit is closed, without exposing owner identifiers or credentials in public/client artifacts.
- Release handoff must point to immutable exact hashes for source, package, signing/evidence records and cannot claim completion if T68/T69 evidence is stale against the release candidate.

## Release-only rule
No production repair occurs inside T70. Any defect or candidate change invalidates affected certification and reopens the appropriate task/gate before handoff can resume.
