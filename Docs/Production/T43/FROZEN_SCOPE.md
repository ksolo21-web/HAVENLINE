# T43 — Identity, cloud continuity and recovery — Frozen Preparation Scope

**Preparation status:** PREPARED_GOVERNANCE_ONLY  
**Authoritative runtime status:** LOCKED
**Forward preparation baseline:** `havenline/QA-integration` @ `ac54e55fcf034673b97a1fcb02aba833a3ad2989`  

## Required outcome
- Implement production Google Sign-In identity, cloud profile/save continuity, sign-out/re-sign-in, reinstall/device-change recovery, and safe cancelled/failed-auth fallback.
- Prove the exact shipping Android package + release-signing certificate with the production OAuth client; debug-only success is insufficient.
- Bind exactly two owner slots (`OWNER_PRIMARY`, `OWNER_SECONDARY`) server-side to verified Google subject IDs after authentication. Email alone is never authority.
- Prevent account switching from inheriting another account's role/cloud save; expose no owner identity, OAuth secret, service credential, or admin credential in public source/APK.

## Explicit exclusions
No client-side Game Master cheat flag, no public-source owner identifiers, and no security bypass around T41.

## Acceptance floor
C9 security and C11 identity/device UX are mandatory; recovery/account-switch matrix and release identity proof required; strict >9.0 unrounded.
