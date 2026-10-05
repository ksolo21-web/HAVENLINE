# Havenline Game Master Tasklist Overlay

This overlay augments the existing T01–T70 plan without renumbering tasks and without reopening T01–T08.

| Task | Game Master addition |
|---|---|
| T13 | Build `GM_CHALLENGE`: an elevated owner difficulty profile selected from the Game Master role, not from VIP/purchases/spend. Target 1.35x threat budget, bounded 1.25x–1.60x, more concurrent pressure and shorter recovery windows; avoid HP-sponges and resource-grind difficulty. |
| T33 | Keep Game Master grants/economy activity separately tagged and outside normal F2P population evidence. |
| T34 | Implement the server-authoritative Game Master entitlement/grant path with idempotent audited zero-cost grants. |
| T35 | All approved shop SKUs are claimable at zero real-money cost for Game Master accounts; do not invoke real-money checkout; normal-player pricing is unchanged. |
| T36 | Add permanent owner-only `GAME_MASTER` VIP above public max VIP. It inherits every public VIP perk at maximum plus the exclusive Game Master perks in `GAME_MASTER_ACCOUNT_STANDARD.md`. |
| T37 | Add controlled owner LiveOps preview/administration with audit requirements. |
| T41 | Protect Game Master role/privileged operations as server-authoritative production state. |
| T42 | Keep Game Master activity separately tagged from normal revenue/conversion/difficulty cohorts. |
| T43 | Production Google Sign-In; prove exact release package + signing certificate OAuth identity; bind exactly two owner slots server-side; verify account switching, reinstall/device recovery and cloud-role continuity. |
| T64 | Prove normal-player Purchase Value/Fairness results are not contaminated by Game Master zero-cost grants or owner privileges. |
| T65 | Rehearse Game Master LiveOps owner workflow and rollback. |
| T66 | Validate Game Master authorization boundaries and competitive isolation. |
| T70 | Verify exactly two Game Master owner slots are provisioned and all Game Master release/audit requirements are complete. |

Machine-authoritative requirements live in `GAME_MASTER_POLICY.json`. The candidate manifest contains a `game_master_contract` proof block. Personal Google account identifiers are intentionally not stored in this public repository.
