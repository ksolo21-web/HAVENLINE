# Havenline Game Master Account Standard

This is a forward production contract for the two owner accounts designated by the Havenline owner. It does not reopen approved T01–T08 work and it must never be implemented as a client-side cheat flag.

## 1. Role authority

Havenline has exactly two owner Game Master slots: `OWNER_PRIMARY` and `OWNER_SECONDARY`.

The actual people, email addresses and Google subject IDs are **not stored in public source code**. T43 binds those two slots server-side to the two designated owners after successful Google Sign-In using verified Google subject IDs.

Rules:

- `GAME_MASTER` is a server-authoritative account role.
- Email address alone is never sufficient authority.
- Client files, save files, SharedPreferences, local databases, APK resources and remote-config values may not grant the role.
- No Google subject ID, OAuth secret, service-account key or privileged admin credential is embedded in the APK/repository.
- Role resolution is performed after verified Google authentication and returned to the client only as trusted server state.
- Role grants/revocations and privileged actions are auditable.
- Privileged/destructive admin actions require recent authenticated authorization and server-side validation.

## 2. Google Sign-In / T43

T43 owns production Google identity and Game Master binding.

T43 must prove the exact shipping Android package + release-signing certificate combination with the production OAuth client. Debug-signing success is not sufficient.

Required T43 proof includes:

- Google Sign-In succeeds using the release package/certificate identity;
- both owner slots are bound to verified Google subject IDs server-side;
- account switching cannot inherit another owner's role or cloud save;
- sign-out/re-sign-in/reinstall/device-change recovery preserves the correct owner role and cloud profile;
- cancelled/failed authentication safely returns to a non-privileged state;
- forged email/local account state cannot produce `GAME_MASTER`;
- no owner identity or admin credential is exposed in client artifacts.

## 3. Game Master VIP

`GAME_MASTER` is a permanent owner-only VIP tier above the maximum public VIP tier.

It:

- is granted immediately when an owner role resolves successfully;
- never expires and never requires activation;
- cannot be purchased, earned, gifted or transferred;
- inherits every public VIP perk at its maximum applicable value;
- additionally grants the Game Master-only perks below.

Game Master-only perks:

1. **Game Master Shop Access** — every current/future store SKU is claimable at zero real-money cost on a Game Master account.
2. **Master Vault** — all cosmetics, companion cosmetics, themes, passes and other shop-delivered content are claimable without payment.
3. **Game Master Identity** — optional exclusive crown/title/nameplate/aura presentation that may be toggled off.
4. **Unlimited cosmetic/loadout convenience** — no artificial cosmetic/loadout slot friction for Game Master accounts.
5. **Game Master Admin Console** — privileged QA/admin tools described below.
6. **Event Preview/Admin Access** — controlled LiveOps preview/test/administration with server audit and step-up authorization for production-impacting commands.
7. **Game Master Challenge Profile** — the default owner gameplay profile is intentionally harder than the normal player envelope.

The Game Master tier must never become a purchasable public advantage.

## 4. Free shop behavior

T35 implements Game Master shop behavior.

For `GAME_MASTER` accounts:

- every store item is shown as Game Master claimable/free rather than starting Google Play Billing;
- pressing claim must **not** invoke a real-money billing flow;
- the server grants the SKU/entitlement through an idempotent `GM_ZERO_COST_CLAIM` transaction;
- a real/fake Google Play purchase receipt is never manufactured;
- currency packs, passes, cosmetics, companion items and future approved store SKUs are all eligible unless a future safety/legal restriction explicitly excludes an item;
- grants are audited with account, SKU, server time, grant reason and idempotency key;
- Game Master claims are excluded from revenue reporting and normal purchase-conversion metrics;
- Game Master grants cannot be transferred to a normal account.

Normal-player prices, purchase verification and advertised value are unchanged.

## 5. Game Master Challenge profile

The owner accounts should be harder, not easier, despite receiving all VIP/shop privileges.

T13 implements a separate role-authorized challenge profile named `GM_CHALLENGE`.

**Critical separation:** the Challenge Director may use the explicit server-authorized Game Master role/profile selector, but it may not inspect VIP level, store claims, premium balance, purchase history, lifetime spend, recent spend or billing activity.

Initial balancing target for T13 validation:

- threat-budget multiplier target: `1.35x` versus the comparable normal-player baseline;
- adaptive bounded range: `1.25x–1.60x`;
- normally allow `+1` concurrent meaningful emergency when the scenario supports it;
- recovery-window multiplier target: `0.85x`;
- hostile-wave delay multiplier target: `0.85x`;
- prioritize smarter coordination, mixed enemy groups, flanking/pressure, weather combinations, route pressure and concurrent objectives;
- raw enemy HP inflation is capped at `1.10x` from the GM modifier;
- raw damage inflation is capped at `1.15x` from the GM modifier;
- do not reduce resource yield merely to create grind;
- do not add extra permanent controls;
- adaptive performance signals may raise/lower challenge inside the GM envelope, but must not drop below the GM minimum solely because the account has powerful entitlements.

This is an explicit owner-role profile, not hidden monetization-based difficulty.

## 6. Game Master play vs admin mutation

Two modes are distinguished:

### GM_PLAY

Normal progression/gameplay with Game Master VIP/free shop and the elevated `GM_CHALLENGE` profile. No privileged world mutation is required.

### GM_ADMIN

Privileged admin/QA commands may include approved forms of:

- inspect actor/world/economy state;
- teleport/stuck recovery;
- preview or set time/weather for QA;
- spawn approved test encounters/resources for QA;
- self-recovery/revive for testing;
- preview/test LiveOps content;
- inspect/reset approved test state;
- invoke approved LiveOps administrative controls.

Every privileged command must be server-authorized and audited. Any admin mutation that could affect competitive value marks the session/state as noncompetitive until a clean authoritative state/session is restored.

Game Master accounts are excluded from public competitive leaderboards/reward rankings by default or placed in a clearly separate Game Master/test pool. They are never used as evidence that normal-player F2P/purchase fairness is healthy.

## 7. Analytics and economy isolation

T33/T34/T42/T64 must ensure:

- Game Master zero-cost grants are separately tagged from normal economy sources/sinks;
- Game Master claims do not count as revenue, ARPU, conversion or normal purchase behavior;
- Game Master accounts are excluded from the `$0 Player Test` and Purchase Value/Fairness population unless a test explicitly targets Game Master behavior;
- normal-player economy, pricing and Challenge Director behavior are unchanged by this role.

## 8. LiveOps/admin safety

T37/T41/T43/T65/T66 must protect Game Master administration:

- no privileged command trusts the client alone;
- production-impacting LiveOps commands require server authorization, audit logging and an explicit confirmation/step-up path;
- rollback/kill-switch controls remain available;
- a compromised normal client cannot promote itself to Game Master;
- a Game Master role cannot be forged through save edits, clock changes, request replay, fake receipts, premium-balance edits or VIP manipulation;
- privileged command replay/parameter tampering is rejected or idempotently reconciled;
- admin actions that affect competitive value cannot submit normal competitive results.

## 9. Task ownership

- **T13** — `GM_CHALLENGE` elevated difficulty profile.
- **T33** — Game Master economy isolation from normal F2P sources/sinks/metrics.
- **T34** — server-authoritative Game Master entitlement/grant ledger.
- **T35** — zero-cost shop claims and explicit no-billing Game Master path.
- **T36** — permanent `GAME_MASTER` VIP tier and inherited/exclusive perks.
- **T37** — audited Game Master LiveOps preview/admin controls.
- **T41** — role/privileged-command security foundation.
- **T42** — Game Master analytics tagging/exclusion from normal cohorts.
- **T43** — production Google Sign-In, exact release signing/OAuth proof, two-owner server binding, recovery/account switching.
- **T64** — prove normal purchase fairness is not contaminated by Game Master grants.
- **T65** — rehearse Game Master LiveOps administration and rollback.
- **T66** — attack Game Master role escalation, command replay/tampering and competitive-isolation boundaries.
- **T70** — release handoff verifies exactly two provisioned owner slots and complete audit/security evidence.

## 10. Non-disruption

This contract is forward-only. T01–T08 accepted/in-flight scope is not reopened. It becomes mandatory automatically only for the tasks listed by `GAME_MASTER_POLICY.json`.