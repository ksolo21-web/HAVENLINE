# T10 dependency-independent prebuild

This branch is intentionally non-integratable while T09 is not APPROVED.

Allowed prebuild work is limited to T10-owned, T09-independent framework code, deterministic recipe/state contracts, exact-once/replay protection, preview purity, recovery semantics, and isolated tests using fixtures. No T09 runtime path may change and no T10 approval/integration claim may be made.

When T09 becomes APPROVED, this branch must be reconciled onto the exact post-T09 integration head, the real T09 adapter must replace fixtures, all impacted regression must rerun, and C1/C2/C3/C4/C6/C7 must pass strictly above 9.0 before T10 can be approved.
